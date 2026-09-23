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
from services.drpe import drpe_decrypt, drpe_decrypt_with_stages, drpe_encrypt, energy
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
    """Verify the current key-material flow reconstructs the cover exactly."""
    rng = np.random.default_rng(42)
    cover = np.round(rng.uniform(0, 255, size=(64, 64, 3)))

    p1_material = b"roundtrip-p1-material"
    p2_material = b"roundtrip-p2-material"
    enc = drpe_encrypt(cover, p1_material, p2_material)
    dec = drpe_decrypt(enc["complex"], p1=enc["p1"], p2=enc["p2"])

    max_err = np.max(np.abs(cover - dec))
    assert max_err < 1e-15, f"Roundtrip max error {max_err} exceeds threshold 1e-15"


def test_drpe_partial_and_wrong_mask_rejection():
    """Verify wrong P1, wrong P2, or both wrong yield garbled output."""
    cover = np.full((32, 32, 3), 128.0)

    p1_material = b"wrong-mask-p1"
    p2_material = b"wrong-mask-p2"
    enc = drpe_encrypt(cover, p1_material, p2_material)

    wrong_p1 = np.random.default_rng(101).uniform(0, 2 * np.pi, size=cover.shape)
    wrong_p2 = np.random.default_rng(102).uniform(0, 2 * np.pi, size=cover.shape)

    dec_wrong_p1 = drpe_decrypt(enc["complex"], p1=wrong_p1, p2=enc["p2"])
    assert np.max(np.abs(cover - dec_wrong_p1)) > 10.0, "Wrong P1 mask must fail to recover cover"

    dec_wrong_p2 = drpe_decrypt(enc["complex"], p1=enc["p1"], p2=wrong_p2)
    assert np.max(np.abs(cover - dec_wrong_p2)) > 10.0, "Wrong P2 mask must fail to recover cover"

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


def test_api_encrypt_decrypt_flow():
    """Verify end-to-end API encrypt and decrypt workflow with key image and password."""
    rng = np.random.default_rng(42)
    random_pixels = rng.integers(0, 256, size=(300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(random_pixels, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    key_img = Image.new("RGB", (64, 64), color=(80, 120, 160))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_buf.seek(0)

    # 1. POST /api/encrypt with secret_password and secret_key_image
    response = client.post(
        "/api/encrypt",
        data={"secret_password": "test-password-123"},
        files={
            "cover_image": ("test.png", buf, "image/png"),
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "image" in data
    assert "message_id" in data
    assert "salt_b64" in data
    assert data["cover_energy"] > 0
    
    msg_id = data["message_id"]

    # 2. POST /api/decrypt-with-key-images with correct password and key image
    key_buf.seek(0)
    dec_response = client.post(
        "/api/decrypt-with-key-images",
        data={
            "message_id": msg_id,
            "secret_password": "test-password-123",
        },
        files={
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert dec_response.status_code == 200
    dec_data = dec_response.json()
    assert dec_data["match_with_cover"] is True

    # 3. POST /api/decrypt-with-key-images with wrong password
    key_buf.seek(0)
    wrong_pw_response = client.post(
        "/api/decrypt-with-key-images",
        data={
            "message_id": msg_id,
            "secret_password": "wrong-password",
        },
        files={
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert wrong_pw_response.status_code == 200
    assert wrong_pw_response.json()["match_with_cover"] is False


def test_variable_size_image_encryption():
    """Verify that RGB images of non-square shapes retain their dimensions (H, W, 3)."""
    cover = np.round(np.random.uniform(0, 255, size=(384, 512, 3)))

    enc = drpe_encrypt(cover, b"var-p1", b"var-p2")
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

    key_img = Image.new("RGB", (64, 64), color=(20, 40, 60))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_buf.seek(0)

    res = client.post(
        "/api/encrypt",
        data={"secret_password": "var-password"},
        files={
            "cover_image": ("rect.png", buf, "image/png"),
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert res.status_code == 200
    res_data = res.json()

    key_buf.seek(0)
    dec_res = client.post(
        "/api/decrypt-with-key-images",
        data={
            "message_id": res_data["message_id"],
            "secret_password": "var-password",
        },
        files={
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["match_with_cover"] is True


def test_rgb_stage_differentiation_encryption():
    """Verify Alice's stages 1-2 and 3-4 differ visually and mathematically."""
    rng = np.random.default_rng(42)
    cover = rng.uniform(20.0, 240.0, size=(64, 64, 3))

    p1_mat = b"test-diff-p1"
    p2_mat = b"test-diff-p2"
    enc = drpe_encrypt(cover, p1_mat, p2_mat, include_stages=True)
    stages = enc["stages"]

    # 1. Stage 1 and Stage 2 have non-zero visual difference
    assert np.any(stages["original"] != stages["spatial_rotation"])
    assert np.max(np.abs(stages["original"] - stages["spatial_rotation"])) > 5.0

    # 2. Stage 3 and Stage 4 have non-zero visual difference
    assert np.any(stages["frequency_spectrum"] != stages["frequency_rotation"])
    assert np.max(np.abs(stages["frequency_spectrum"] - stages["frequency_rotation"])) > 5.0


def test_rgb_stage_differentiation_decryption():
    """Verify Bob's stages 2-3 and 4-5 differ visually and mathematically."""
    rng = np.random.default_rng(42)
    cover = np.round(rng.uniform(20.0, 240.0, size=(64, 64, 3)))

    p1_mat = b"test-diff-p1"
    p2_mat = b"test-diff-p2"
    enc = drpe_encrypt(cover, p1_mat, p2_mat, include_stages=True)

    recovered, stages = drpe_decrypt_with_stages(enc["complex"], p1=enc["p1"], p2=enc["p2"])

    # 1. Decryption fidelity is 100% bit-exact
    assert np.allclose(recovered, cover, atol=1e-15)

    # 2. Stage 2 and Stage 3 differ visually
    assert np.any(stages["frequency_spectrum"] != stages["frequency_phase_removed"])
    assert np.max(np.abs(stages["frequency_spectrum"] - stages["frequency_phase_removed"])) > 5.0

    # 3. Stage 4 and Stage 5 differ visually
    assert np.any(stages["spatial_phase_removed"] != stages["recovered"])
    assert np.max(np.abs(stages["spatial_phase_removed"] - stages["recovered"])) > 5.0


def test_api_stages_payload():
    """Verify API returns stages with distinct previews."""
    rng = np.random.default_rng(42)
    pixels = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(pixels, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    key_img = Image.new("RGB", (64, 64), color=(30, 60, 90))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_buf.seek(0)

    res = client.post(
        "/api/encrypt",
        data={"secret_password": "stage-test-password"},
        files={
            "cover_image": ("test.png", buf, "image/png"),
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "stages" in data
    assert len(data["stages"]) == 5

    stage_names = [s["name"] for s in data["stages"]]
    assert stage_names == ["original", "spatial_rotation", "frequency_spectrum", "frequency_rotation", "ciphertext"]
    for s in data["stages"]:
        assert "image" in s
        assert len(s["image"]) > 0




