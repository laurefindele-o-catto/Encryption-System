"""
Unit and API integration tests for DRPE Phase 1 with dual seeds (P1 and P2).
"""

import io
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from services.drpe import drpe_encrypt, drpe_decrypt, energy
from services.base_image import get_base_image
from services.keys import derive_key

client = TestClient(app)


def test_key_derivation():
    """Verify key derivation is deterministic and distinct per seed/frame."""
    k1 = derive_key("seed-a", 0)
    k2 = derive_key("seed-a", 0)
    k3 = derive_key("seed-a", 1)
    k4 = derive_key("seed-b", 0)

    assert k1 == k2, "Same seed and frame_index must produce identical keys"
    assert k1 != k3, "Different frame_index must produce different keys"
    assert k1 != k4, "Different seed string must produce different keys"


def test_drpe_roundtrip_fidelity():
    """Verify correct seed_p1 and seed_p2 recover cover image with zero error (< 1e-15)."""
    base = get_base_image()
    rng = np.random.default_rng(42)
    cover = np.round(rng.uniform(0, 255, size=base.shape))

    seed_p1 = "correct-p1-seed"
    seed_p2 = "correct-p2-seed"
    enc = drpe_encrypt(cover, base, seed_p1=seed_p1, seed_p2=seed_p2)
    dec = drpe_decrypt(enc["complex"], base, seed_p1=seed_p1, seed_p2=seed_p2)

    max_err = np.max(np.abs(cover - dec))
    assert max_err < 1e-15, f"Roundtrip max error {max_err} exceeds threshold 1e-15"


def test_drpe_partial_and_wrong_seed_rejection():
    """Verify wrong P1, wrong P2, or both wrong yield garbled output."""
    base = get_base_image()
    cover = np.full(base.shape, 128.0)

    seed_p1 = "correct-p1"
    seed_p2 = "correct-p2"
    enc = drpe_encrypt(cover, base, seed_p1=seed_p1, seed_p2=seed_p2)

    # 1. Wrong P1, correct P2
    dec_wrong_p1 = drpe_decrypt(enc["complex"], base, seed_p1="wrong-p1", seed_p2=seed_p2)
    assert np.max(np.abs(cover - dec_wrong_p1)) > 10.0, "Wrong P1 seed must fail to recover cover"

    # 2. Correct P1, wrong P2
    dec_wrong_p2 = drpe_decrypt(enc["complex"], base, seed_p1=seed_p1, seed_p2="wrong-p2")
    assert np.max(np.abs(cover - dec_wrong_p2)) > 10.0, "Wrong P2 seed must fail to recover cover"

    # 3. Both wrong
    dec_wrong_both = drpe_decrypt(enc["complex"], base, seed_p1="wrong-p1", seed_p2="wrong-p2")
    assert np.max(np.abs(cover - dec_wrong_both)) > 10.0, "Both wrong seeds must fail to recover cover"


def test_parseval_energy_invariance():
    """Verify energy Σ(pixel²) is computed accurately."""
    arr = np.array([[10.0, 20.0], [30.0, 40.0]])
    # 100 + 400 + 900 + 1600 = 3000
    assert energy(arr) == 3000.0


def test_api_health():
    """Verify GET /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_base_image():
    """Verify GET /api/base-image."""
    response = client.get("/api/base-image")
    assert response.status_code == 200
    data = response.json()
    assert "image" in data
    assert "shape" in data
    assert len(data["shape"]) == 2


def test_api_encrypt_decrypt_flow():
    """Verify end-to-end API encrypt and decrypt workflow with dual seeds and stateless payload."""
    img = Image.new("L", (300, 300), color=100)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # 1. POST /api/encrypt with seed_p1 and seed_p2
    response = client.post(
        "/api/encrypt",
        data={"seed_p1": "api-p1-seed", "seed_p2": "api-p2-seed"},
        files={"cover_image": ("test.png", buf, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ciphertext_b64" in data
    assert "ciphertext_shape" in data
    assert "image" in data
    assert data["cover_energy"] > 0
    
    cb64 = data["ciphertext_b64"]
    cshape = data["ciphertext_shape"]

    # 2. POST /api/decrypt with correct seeds
    dec_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_height": cshape[0],
            "ciphertext_width": cshape[1],
            "seed_p1": "api-p1-seed",
            "seed_p2": "api-p2-seed",
        },
    )
    assert dec_response.status_code == 200
    dec_data = dec_response.json()
    assert dec_data["match_with_cover"] is True

    # 3. POST /api/decrypt with wrong P1 seed
    wrong_p1_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_height": cshape[0],
            "ciphertext_width": cshape[1],
            "seed_p1": "wrong-p1",
            "seed_p2": "api-p2-seed",
        },
    )
    assert wrong_p1_response.status_code == 200
    assert wrong_p1_response.json()["match_with_cover"] is False

    # 4. POST /api/decrypt with wrong P2 seed
    wrong_p2_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_height": cshape[0],
            "ciphertext_width": cshape[1],
            "seed_p1": "api-p1-seed",
            "seed_p2": "wrong-p2",
        },
    )
    assert wrong_p2_response.status_code == 200
    assert wrong_p2_response.json()["match_with_cover"] is False


def test_variable_size_image_encryption():
    """Verify that images of non-square and non-256x256 shapes retain their dimensions with dual seeds."""
    base = get_base_image()
    cover = np.round(np.random.uniform(0, 255, size=(384, 512)))

    enc = drpe_encrypt(cover, base, seed_p1="var-p1", seed_p2="var-p2")
    assert enc["complex"].shape == (384, 512)
    assert enc["amplitude"].shape == (384, 512)

    dec = drpe_decrypt(enc["complex"], base, seed_p1="var-p1", seed_p2="var-p2")
    assert dec.shape == (384, 512)
    assert np.max(np.abs(cover - dec)) < 1e-15

    # Test via API with rectangular image upload
    img = Image.new("L", (512, 384), color=150)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/encrypt",
        data={"seed_p1": "var-api-p1", "seed_p2": "var-api-p2"},
        files={"cover_image": ("rect.png", buf, "image/png")},
    )
    assert res.status_code == 200
    res_data = res.json()

    dec_res = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": res_data["ciphertext_b64"],
            "ciphertext_height": res_data["ciphertext_shape"][0],
            "ciphertext_width": res_data["ciphertext_shape"][1],
            "seed_p1": "var-api-p1",
            "seed_p2": "var-api-p2",
        },
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["match_with_cover"] is True
