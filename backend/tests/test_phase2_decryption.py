"""
Unit and integration tests for Phase 2 Morse text encryption and decryption.
"""

import io
import os
import sys

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from main import app
from services.encoding.morse_to_symbol_sequence import (
    SymbolState,
    morse_to_symbol_sequence,
    symbol_sequence_to_morse,
)
from services.encoding.morse_to_text import is_valid_morse, morse_to_text
from services.encoding.text_to_morse import text_to_morse
from services.text_decryption import decrypt_text_message
from services.text_encryption import encrypt_text_message


client = TestClient(app)


def test_morse_roundtrip():
    """Verify text -> morse -> text matches original uppercase string."""
    phrases = [
        "HELLO WORLD",
        "SOS",
        "ATTACK AT DAWN 0600",
        "CAT",
        "1234567890",
        "HELLO, WORLD. OK?",
    ]
    for phrase in phrases:
        morse = text_to_morse(phrase)
        recovered = morse_to_text(morse)
        assert recovered == phrase.upper(), f"Failed roundtrip for '{phrase}' -> '{morse}' -> '{recovered}'"
        assert is_valid_morse(morse) is True


def test_symbol_sequence_roundtrip():
    """Verify morse -> symbol sequence -> morse is identical."""
    morse_inputs = [
        ".-",
        "-... .-.. --- -.-.",
        "... --- .../.---- ..---",
        "-.-. .- -/--. ---",
    ]
    for morse in morse_inputs:
        symbols = morse_to_symbol_sequence(morse)
        recovered_morse = symbol_sequence_to_morse(symbols)
        assert recovered_morse == morse, f"Symbol sequence mismatch for '{morse}' -> '{recovered_morse}'"


def test_text_encryption_decryption_service():
    """Verify end-to-end service encrypt_text_message and decrypt_text_message."""
    secret_text = "SECRET 42"
    base_image = np.full((64, 64, 3), 128.0, dtype=np.float64)

    # Generate dummy key image bytes
    key_img = Image.new("RGB", (32, 32), color=(100, 150, 200))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_bytes = key_buf.getvalue()

    password = "super-secret-pass"

    # Encrypt
    enc_res = encrypt_text_message(
        secret_text=secret_text,
        base_image=base_image,
        secret_key_image=key_bytes,
        secret_password=password,
        include_previews=True,
    )

    msg_id = enc_res["message_id"]
    assert enc_res["frame_count"] > 0
    assert len(enc_res["previews"]) == enc_res["frame_count"]

    # Decrypt with correct credentials
    dec_res = decrypt_text_message(
        message_id=msg_id,
        secret_key_image=key_bytes,
        secret_password=password,
    )

    assert dec_res["success"] is True
    assert dec_res["text"] == secret_text
    assert dec_res["morse"] == enc_res["morse"]
    assert dec_res["symbols"] == enc_res["symbols"]
    assert len(dec_res["frames"]) == enc_res["frame_count"]
    assert dec_res["image"] is not None
    assert isinstance(dec_res["image"], str)


def test_text_decryption_wrong_password_or_key():
    """Verify decrypting with wrong password or key does not recover plaintext."""
    secret_text = "TOP SECRET"
    base_image = np.full((64, 64, 3), 120.0, dtype=np.float64)

    key_img = Image.new("RGB", (32, 32), color=(10, 20, 30))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_bytes = key_buf.getvalue()

    password = "correct-password"

    enc_res = encrypt_text_message(
        secret_text=secret_text,
        base_image=base_image,
        secret_key_image=key_bytes,
        secret_password=password,
    )
    msg_id = enc_res["message_id"]

    # Decrypt with wrong password
    dec_wrong_pw = decrypt_text_message(
        message_id=msg_id,
        secret_key_image=key_bytes,
        secret_password="wrong-password",
    )
    assert dec_wrong_pw["text"] != secret_text
    assert dec_wrong_pw["image"] is not None
    assert isinstance(dec_wrong_pw["image"], str)

    # Decrypt with wrong key image
    wrong_key_img = Image.new("RGB", (32, 32), color=(200, 210, 220))
    wrong_key_buf = io.BytesIO()
    wrong_key_img.save(wrong_key_buf, format="PNG")
    wrong_key_bytes = wrong_key_buf.getvalue()

    dec_wrong_key = decrypt_text_message(
        message_id=msg_id,
        secret_key_image=wrong_key_bytes,
        secret_password=password,
    )
    assert dec_wrong_key["text"] != secret_text
    assert dec_wrong_key["image"] is not None
    assert isinstance(dec_wrong_key["image"], str)


def test_api_text_encrypt_and_decrypt_flow():
    """Test POST /api/text/encrypt and POST /api/text/decrypt API endpoints."""
    # Create base image
    base_img = Image.new("RGB", (64, 64), color=(140, 140, 140))
    base_buf = io.BytesIO()
    base_img.save(base_buf, format="PNG")
    base_buf.seek(0)

    # Create key image
    key_img = Image.new("RGB", (64, 64), color=(50, 100, 150))
    key_buf = io.BytesIO()
    key_img.save(key_buf, format="PNG")
    key_buf.seek(0)

    # 1. Encrypt via API
    enc_response = client.post(
        "/api/text/encrypt",
        data={
            "secret_text": "HELLO WORLD",
            "secret_password": "api-test-pass",
        },
        files={
            "base_image": ("base.png", base_buf, "image/png"),
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert enc_response.status_code == 200, enc_response.text
    enc_data = enc_response.json()
    assert "message_id" in enc_data
    assert enc_data["frame_count"] > 0
    assert len(enc_data["previews"]) == enc_data["frame_count"]

    msg_id = enc_data["message_id"]

    # 2. Decrypt via API
    key_buf.seek(0)
    dec_response = client.post(
        "/api/text/decrypt",
        data={
            "message_id": msg_id,
            "secret_password": "api-test-pass",
        },
        files={
            "secret_key_image": ("key.png", key_buf, "image/png"),
        },
    )
    assert dec_response.status_code == 200, dec_response.text
    dec_data = dec_response.json()
    assert dec_data["success"] is True
    assert dec_data["text"] == "HELLO WORLD"
    assert dec_data["morse"] == enc_data["morse"]
    assert dec_data["symbols"] == enc_data["symbols"]
    assert dec_data["image"] is not None
    assert isinstance(dec_data["image"], str)
