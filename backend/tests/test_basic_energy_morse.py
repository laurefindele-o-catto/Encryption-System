"""
Tests for Basic Morse Image Encryption and Dual Extraction:
1. Normal DRPE Decryption
2. Total Energy Side-Channel Prediction (Zero Decryption)
"""

import io
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from services.basic_energy_service import (
    decrypt_basic_morse_normal,
    encrypt_basic_morse_message,
    predict_basic_morse_from_energy,
)
from services.drpe import drpe_encrypt, energy
from services.encoding.basic_energy_morse import (
    compute_expected_energy_levels,
    decode_symbols_to_morse_and_text,
    encode_text_to_symbols,
    generate_basic_symbol_image,
    predict_symbol_from_energy,
)
from services.encoding.morse_to_text import is_valid_morse, morse_to_text
from services.encoding.text_to_morse import text_to_morse

client = TestClient(app)


def test_basic_morse_encoding_and_decoding():
    """Verify that text maps to Morse with spaces and slashes, and decodes back."""
    phrases = [
        "SOS",
        "HELLO WORLD",
        "BUET CSE 2026",
        "SIGNAL AND SYSTEMS",
    ]
    for phrase in phrases:
        morse, symbols = encode_text_to_symbols(phrase)
        # Check formatting: words separated by '/', letters by ' '
        assert '/' in morse or ' ' not in morse or len(phrase.split()) == 1
        decoded_morse, decoded_text, success = decode_symbols_to_morse_and_text(symbols)
        assert decoded_text == phrase.upper()
        assert success is True


def test_unrecognized_codes_mapped_to_question_mark():
    """Verify that unrecognized morse codes map to '?' via the ITU table."""
    morse_with_invalid = "... --- ... / .--.-.-"
    decoded = morse_to_text(morse_with_invalid)
    assert decoded.endswith("?")
    assert not is_valid_morse(morse_with_invalid)


def test_energy_monotonic_separation():
    """Verify that E(DOT) < E(DASH) < E(LETTER_GAP) < E(WORD_GAP)."""
    base_image = np.full((64, 64, 3), 120.0, dtype=np.float64)
    energies, thresholds = compute_expected_energy_levels(base_image)

    assert len(energies) == 4
    assert len(thresholds) == 3
    assert energies[0] < energies[1] < energies[2] < energies[3]
    assert thresholds[0] < thresholds[1] < thresholds[2]

    # Verify classification of each exact level
    for state, e_val in enumerate(energies):
        pred = predict_symbol_from_energy(e_val, thresholds)
        assert pred == state


def test_drpe_parseval_conservation_on_basic_frames():
    """Verify that DRPE ciphertext amplitude energy matches spatial frame energy."""
    base_image = np.full((64, 64, 3), 110.0, dtype=np.float64)
    p1_mat = b"test-p1-material"
    p2_mat = b"test-p2-material"

    for symbol in range(4):
        spatial_frame = generate_basic_symbol_image(symbol, base_image)
        spatial_energy = energy(spatial_frame)

        enc = drpe_encrypt(spatial_frame, p1_mat, p2_mat)
        cipher_energy = energy(enc["amplitude"])

        # Energy should be conserved to high numerical precision
        assert np.isclose(spatial_energy, cipher_energy, rtol=1e-5)


def test_end_to_end_service_encryption_and_prediction():
    """Verify that ciphertext energy prediction recovers Morse and plaintext with NO keys."""
    secret_text = "SOS 123"
    base_image = np.full((64, 64, 3), 115.0, dtype=np.float64)

    key_img = Image.new("RGB", (32, 32), color=(50, 80, 120))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_bytes = key_buf.getvalue()

    password = "secret-passphrase"

    # 1. Encrypt
    enc_res = encrypt_basic_morse_message(
        secret_text=secret_text,
        base_image=base_image,
        secret_key_image=key_bytes,
        secret_password=password,
        include_previews=True,
    )
    msg_id = enc_res["message_id"]
    assert enc_res["frame_count"] > 0
    assert len(enc_res["previews"]) == enc_res["frame_count"]

    # 2. Predict purely from total energy (ZERO DECRYPTION, NO KEYS)
    pred_res = predict_basic_morse_from_energy(msg_id)
    assert pred_res["bypassed_decryption"] is True
    assert pred_res["predicted_text"] == secret_text
    assert pred_res["predicted_morse"] == enc_res["morse"]
    assert pred_res["predicted_symbols"] == enc_res["symbols"]
    assert pred_res["success"] is True
    assert len(pred_res["frames"]) == len(enc_res["symbols"])
    for f in pred_res["frames"]:
        assert "total_energy" in f
        assert "energy" in f
        assert f["total_energy"] == f["energy"]
        assert f["symbol"] == f["predicted_symbol"]
        assert f["expected_energy"] is not None
        assert f["energy_deviation"] is not None
        assert f["decision_threshold"] is not None

    # 3. Normal Decryption with correct credentials
    dec_res = decrypt_basic_morse_normal(
        message_id=msg_id,
        secret_key_image=key_bytes,
        secret_password=password,
    )
    assert dec_res["success"] is True
    assert dec_res["text"] == secret_text
    assert dec_res["morse"] == enc_res["morse"]
    assert dec_res["symbols"] == enc_res["symbols"]
    assert dec_res["image"] is not None

    # Verify frame diagnostics report block-level brightness delta (~k * 20.0)
    assert len(dec_res["frames"]) == len(enc_res["symbols"])
    for f in dec_res["frames"]:
        expected_delta = f["symbol"] * 20.0
        assert np.isclose(f["brightness_delta"], expected_delta, atol=1.0)

    # 4. Normal Decryption with wrong password fails to recover text
    dec_wrong_pw = decrypt_basic_morse_normal(
        message_id=msg_id,
        secret_key_image=key_bytes,
        secret_password="wrong-password",
    )
    assert dec_wrong_pw["text"] != secret_text


def test_block_spatial_isolation():
    """Verify that only the designated block is modified and outside pixels remain untouched."""
    base_image = np.full((64, 64, 3), 100.0, dtype=np.float64)
    block_coords = (12, 14)
    block_size = 16
    offset_step = 25.0

    symbol_frame = generate_basic_symbol_image(
        symbol=2,
        base_image=base_image,
        offset_step=offset_step,
        block_coords=block_coords,
        block_size=block_size,
    )
    r, c = block_coords
    # Check inside block: offset of 2 * 25.0 = 50.0 added
    assert np.allclose(symbol_frame[r:r + block_size, c:c + block_size], 100.0 + 2 * offset_step)

    # Check outside block: remains unchanged
    mask = np.ones((64, 64), dtype=bool)
    mask[r:r + block_size, c:c + block_size] = False
    assert np.allclose(symbol_frame[mask], 100.0)


def test_api_basic_energy_endpoints_flow():
    """Verify HTTP API endpoints for encrypt, predict (no keys), and normal decrypt."""
    base_img = Image.new("RGB", (64, 64), color=(125, 125, 125))
    base_buf = io.BytesIO()
    base_img.save(base_buf, format="PNG")
    base_buf.seek(0)

    key_img = Image.new("RGB", (64, 64), color=(30, 60, 90))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_buf.seek(0)

    # 1. Encrypt via API
    enc_response = client.post(
        "/api/text/basic-energy/encrypt",
        data={
            "secret_text": "HELLO WORLD",
            "secret_password": "api-energy-pass",
        },
        files={
            "base_image": ("base.png", base_buf, "image/png"),
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert enc_response.status_code == 200, enc_response.text
    enc_data = enc_response.json()
    msg_id = enc_data["message_id"]
    assert enc_data["frame_count"] > 0
    assert len(enc_data["thresholds"]) == 3

    # 2. Predict via API (No keys or password provided!)
    pred_response = client.post(
        "/api/text/basic-energy/predict",
        data={"message_id": msg_id},
    )
    assert pred_response.status_code == 200, pred_response.text
    pred_data = pred_response.json()
    assert pred_data["bypassed_decryption"] is True
    assert pred_data["predicted_text"] == "HELLO WORLD"
    assert pred_data["success"] is True
    assert len(pred_data["frames"]) == pred_data["frame_count"]
    for f in pred_data["frames"]:
        assert f["total_energy"] is not None
        assert f["symbol"] is not None
        assert f["expected_energy"] is not None
        assert f["decision_threshold"] is not None

    # 3. Normal Decrypt via API
    key_buf.seek(0)
    dec_response = client.post(
        "/api/text/basic-energy/decrypt",
        data={
            "message_id": msg_id,
            "secret_password": "api-energy-pass",
        },
        files={
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert dec_response.status_code == 200, dec_response.text
    dec_data = dec_response.json()
    assert dec_data["text"] == "HELLO WORLD"
    assert dec_data["success"] is True
    assert len(dec_data["frames"]) > 0
    for frame_info in dec_data["frames"]:
        expected_delta = frame_info["symbol"] * 20.0
        assert abs(frame_info["brightness_delta"] - expected_delta) < 1.0
