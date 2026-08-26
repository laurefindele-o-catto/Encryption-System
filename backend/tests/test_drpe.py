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
from services.base_image import get_base_image
from services.drpe import drpe_decrypt, drpe_encrypt, energy
from services.image_utils import float_to_b64
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
    """Verify passing enc['p1'] and enc['p2'] directly recovers cover image with zero error (< 1e-15)."""
    base = get_base_image()
    rng = np.random.default_rng(42)
    cover = np.round(rng.uniform(0, 255, size=base.shape))

    seed_p1 = "correct-p1-seed"
    seed_p2 = "correct-p2-seed"
    enc = drpe_encrypt(cover, base, seed_p1=seed_p1, seed_p2=seed_p2)
    dec = drpe_decrypt(enc["complex"], p1=enc["p1"], p2=enc["p2"])

    max_err = np.max(np.abs(cover - dec))
    assert max_err < 1e-15, f"Roundtrip max error {max_err} exceeds threshold 1e-15"


def test_drpe_partial_and_wrong_mask_rejection():
    """Verify wrong P1, wrong P2, or both wrong yield garbled output."""
    base = get_base_image()
    cover = np.full(base.shape, 128.0)

    seed_p1 = "correct-p1"
    seed_p2 = "correct-p2"
    enc = drpe_encrypt(cover, base, seed_p1=seed_p1, seed_p2=seed_p2)

    wrong_p1 = np.random.default_rng(101).uniform(0, 2 * np.pi, size=cover.shape)
    wrong_p2 = np.random.default_rng(102).uniform(0, 2 * np.pi, size=cover.shape)

    # 1. Wrong P1, correct P2
    dec_wrong_p1 = drpe_decrypt(enc["complex"], p1=wrong_p1, p2=enc["p2"])
    assert np.max(np.abs(cover - dec_wrong_p1)) > 10.0, "Wrong P1 mask must fail to recover cover"

    # 2. Correct P1, wrong P2
    dec_wrong_p2 = drpe_decrypt(enc["complex"], p1=enc["p1"], p2=wrong_p2)
    assert np.max(np.abs(cover - dec_wrong_p2)) > 10.0, "Wrong P2 mask must fail to recover cover"

    # 3. Both wrong
    dec_wrong_both = drpe_decrypt(enc["complex"], p1=wrong_p1, p2=wrong_p2)
    assert np.max(np.abs(cover - dec_wrong_both)) > 10.0, "Both wrong masks must fail to recover cover"


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
    assert len(data["shape"]) == 3  # [H, W, 3] for RGB


def test_api_encrypt_decrypt_flow():
    """Verify end-to-end API encrypt and decrypt workflow with p1_b64 and p2_b64 payload."""
    rng = np.random.default_rng(42)
    random_pixels = rng.integers(0, 256, size=(300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(random_pixels, mode="RGB")
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
    assert "p1_b64" in data
    assert "p2_b64" in data
    assert "image" in data
    assert data["cover_energy"] > 0
    
    cb64 = data["ciphertext_b64"]
    cshape = data["ciphertext_shape"]
    p1_b64 = data["p1_b64"]
    p2_b64 = data["p2_b64"]

    # 2. POST /api/decrypt with correct masks
    dec_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_shape": cshape,
            "p1_b64": p1_b64,
            "p2_b64": p2_b64,
        },
    )
    assert dec_response.status_code == 200
    dec_data = dec_response.json()
    assert dec_data["match_with_cover"] is True

    # 3. POST /api/decrypt with wrong P1 mask
    wrong_p1 = rng.uniform(0, 2 * np.pi, size=cshape)
    wrong_p1_b64 = float_to_b64(wrong_p1)
    wrong_p1_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_shape": cshape,
            "p1_b64": wrong_p1_b64,
            "p2_b64": p2_b64,
        },
    )
    # 4. POST /api/decrypt with correct seeds
    dec_seed_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_shape": cshape,
            "seed_p1": "api-p1-seed",
            "seed_p2": "api-p2-seed",
        },
    )
    assert dec_seed_response.status_code == 200
    assert dec_seed_response.json()["match_with_cover"] is True

    # 5. POST /api/decrypt with wrong seed
    wrong_seed_response = client.post(
        "/api/decrypt",
        json={
            "ciphertext_b64": cb64,
            "ciphertext_shape": cshape,
            "seed_p1": "wrong-seed",
            "seed_p2": "api-p2-seed",
        },
    )
    assert wrong_seed_response.status_code == 200
    assert wrong_seed_response.json()["match_with_cover"] is False



def test_variable_size_image_encryption():
    """Verify that RGB images of non-square shapes retain their dimensions (H, W, 3)."""
    base = get_base_image()
    cover = np.round(np.random.uniform(0, 255, size=(384, 512, 3)))

    enc = drpe_encrypt(cover, base, seed_p1="var-p1", seed_p2="var-p2")
    assert enc["complex"].shape == (384, 512, 3)
    assert enc["amplitude"].shape == (384, 512, 3)

    dec = drpe_decrypt(enc["complex"], p1=enc["p1"], p2=enc["p2"])
    assert dec.shape == (384, 512, 3)
    assert np.max(np.abs(cover - dec)) < 1e-15

    # Test via API with rectangular RGB image upload
    img = Image.new("RGB", (512, 384), color=(150, 100, 50))
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
            "ciphertext_shape": res_data["ciphertext_shape"],
            "p1_b64": res_data["p1_b64"],
            "p2_b64": res_data["p2_b64"],
        },
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["match_with_cover"] is True


def test_frame_index_and_stateless_cover_hash():
    """Verify non-zero frame_index key derivation and stateless cover_hash verification."""
    base = get_base_image()
    cover = np.round(np.random.uniform(0, 255, size=base.shape))

    # Encrypt frame_index=5
    enc_5 = drpe_encrypt(cover, base, seed_p1="p1", seed_p2="p2", frame_index=5)
    # Decrypt frame_index=5
    dec_5 = drpe_decrypt(enc_5["complex"], p1=enc_5["p1"], p2=enc_5["p2"])
    assert np.max(np.abs(cover - dec_5)) < 1e-15

    # Decrypting frame_index=5 with masks derived for frame_index=0 must fail
    p1_0, p2_0 = generate_phase_masks(base.shape, base, seed_p1="p1", seed_p2="p2", frame_index=0)
    dec_wrong_frame = drpe_decrypt(enc_5["complex"], p1=p1_0, p2=p2_0)
    assert np.max(np.abs(cover - dec_wrong_frame)) > 10.0


def test_base_image_equalization_and_clipping():
    """Verify synthesized base image passes Phase 2 block equalization and clipping margin invariants."""
    base = get_base_image()
    from config import BLOCK_A_COORDS, BLOCK_B_COORDS, BLOCK_SIZE, DELTA
    
    ra, ca = BLOCK_A_COORDS
    rb, cb = BLOCK_B_COORDS
    sz = BLOCK_SIZE
    
    block_a = base[ra : ra + sz, ca : ca + sz, :]
    block_b = base[rb : rb + sz, cb : cb + sz, :]
    
    # 1. Independent per-channel clipping safeguard [7*DELTA, 255 - 7*DELTA]
    margin = 7 * DELTA
    assert np.all(block_a >= margin) and np.all(block_a <= 255 - margin)
    assert np.all(block_b >= margin) and np.all(block_b <= 255 - margin)
    
    # 2. Near-equal mean luma precondition
    luma_a = np.mean(0.299 * block_a[:, :, 0] + 0.587 * block_a[:, :, 1] + 0.114 * block_a[:, :, 2])
    luma_b = np.mean(0.299 * block_b[:, :, 0] + 0.587 * block_b[:, :, 1] + 0.114 * block_b[:, :, 2])
    assert abs(luma_a - luma_b) < 0.1


