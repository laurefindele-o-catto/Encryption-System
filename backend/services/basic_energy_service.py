"""
Service implementing Basic Morse Image Encryption and Dual Extraction:
1. Normal Decryption (with DRPE, key image, and password)
2. Energy Bug Side-Channel Prediction (purely from ciphertext Parseval energy, zero decryption)
"""

from __future__ import annotations

import secrets
import numpy as np

from services.drpe import drpe_decrypt, drpe_encrypt, energy, generate_phase_masks
from services.encoding.basic_energy_morse import (
    SYMBOL_NAMES,
    compute_expected_energy_levels,
    decode_symbols_to_morse_and_text,
    encode_text_to_symbols,
    extract_symbol_from_decrypted_image,
    generate_basic_symbol_image,
    predict_symbol_from_energy,
)
from services.image_utils import (
    array_to_base64,
    array_to_base64_preview,
    canonicalize_key_image,
    hash_canonical_key_image,
)
from services.keys import derive_frame_key, derive_master_key, derive_password_key
from services.messages import (
    BASIC_ENERGY_MESSAGE,
    Frame,
    add_frame,
    create_message,
    get_message,
    get_ordered_frames,
    new_message_id,
)


def encrypt_basic_morse_message(
    secret_text: str,
    base_image: np.ndarray,
    secret_key_image: bytes,
    secret_password: str,
    message_id: str | None = None,
    salt: bytes | None = None,
    include_previews: bool = False,
) -> dict:
    """Encrypt secret text as basic Morse frames without differential cancellation."""
    if not isinstance(secret_text, str) or not secret_text.strip():
        raise ValueError("secret_text is required")
    if not isinstance(secret_password, str) or not secret_password:
        raise ValueError("secret_password is required")
    if not isinstance(base_image, np.ndarray) or base_image.ndim != 3 or base_image.shape[2] != 3:
        raise ValueError("base_image must be an RGB array with shape (height, width, 3)")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")

    normalized_base = np.asarray(base_image, dtype=np.float64)
    morse, symbols = encode_text_to_symbols(secret_text)

    if not symbols:
        raise ValueError("secret_text produced no encodable symbols")

    energy_levels, thresholds = compute_expected_energy_levels(normalized_base)

    generated_message_id = message_id or new_message_id()
    generated_salt = salt or secrets.token_bytes(16)
    key_pixels = canonicalize_key_image(secret_key_image)
    image_digest = hash_canonical_key_image(key_pixels)
    password_key = derive_password_key(secret_password, generated_salt)
    master_key = derive_master_key(password_key, image_digest)

    message = create_message(
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        salt=generated_salt,
        message_id=generated_message_id,
        message_type=BASIC_ENERGY_MESSAGE,
        base_image=normalized_base.copy(),
        total_frames=len(symbols),
        metadata={
            "morse": morse,
            "symbols": [int(s) for s in symbols],
            "thresholds": thresholds,
            "energy_levels": energy_levels,
        },
    )

    previews = []

    for frame_index, symbol in enumerate(symbols):
        symbol_image = generate_basic_symbol_image(symbol, normalized_base)

        p1_material = derive_frame_key(master_key, generated_message_id, frame_index, b"DRPE/P1")
        p2_material = derive_frame_key(master_key, generated_message_id, frame_index, b"DRPE/P2")

        encrypted = drpe_encrypt(symbol_image, p1_material, p2_material)

        add_frame(
            message,
            Frame(
                frame_index=frame_index,
                ciphertext_complex=encrypted["complex"],
                amplitude=encrypted["amplitude"],
            ),
        )

        frame_energy = energy(encrypted["amplitude"])

        if include_previews:
            previews.append({
                "frame_index": frame_index,
                "image": array_to_base64_preview(encrypted["amplitude"]),
                "energy": frame_energy,
            })

    return {
        "message_id": generated_message_id,
        "salt_b64": array_to_base64(np.frombuffer(generated_salt, dtype=np.uint8)),
        "morse": morse,
        "symbols": [int(s) for s in symbols],
        "frame_count": len(symbols),
        "base_image_shape": list(normalized_base.shape),
        "thresholds": thresholds,
        "energy_levels": energy_levels,
        "previews": previews,
    }


def decrypt_basic_morse_normal(
    message_id: str,
    secret_key_image: bytes,
    secret_password: str,
) -> dict:
    """
    Normal Decryption Path:
    Decrypt each frame with DRPE using Bob's credentials,
    then extract the Morse symbol from the recovered image.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("message_id is required")
    if not isinstance(secret_password, str) or not secret_password:
        raise ValueError("secret_password is required")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")

    message = get_message(message_id)
    if message.message_type != BASIC_ENERGY_MESSAGE:
        raise ValueError(
            f"Message {message_id} is not a basic_energy_morse message (type={message.message_type})"
        )

    ordered_frames = get_ordered_frames(message, require_complete=True)
    if not ordered_frames:
        raise ValueError("No frames found for this message")

    message.receiver_secret_key_image = secret_key_image
    message.receiver_password = secret_password

    key_pixels = canonicalize_key_image(secret_key_image)
    image_digest = hash_canonical_key_image(key_pixels)
    password_key = derive_password_key(secret_password, message.salt)
    master_key = derive_master_key(password_key, image_digest)

    recovered_symbols: list[int] = []
    frame_diagnostics: list[dict] = []
    first_recovered_image = None

    for frame in ordered_frames:
        frame_idx = frame.frame_index
        p1_material = derive_frame_key(master_key, message_id, frame_idx, b"DRPE/P1")
        p2_material = derive_frame_key(master_key, message_id, frame_idx, b"DRPE/P2")

        c_shape = frame.ciphertext_complex.shape
        p1, p2 = generate_phase_masks(c_shape, p1_material, p2_material)

        recovered_image = drpe_decrypt(frame.ciphertext_complex, p1=p1, p2=p2)
        if first_recovered_image is None:
            first_recovered_image = recovered_image

        symbol = extract_symbol_from_decrypted_image(
            recovered_image, message.base_image
        )

        recovered_symbols.append(int(symbol))

        frame_diagnostics.append({
            "frame_index": frame_idx,
            "symbol": int(symbol),
            "symbol_name": SYMBOL_NAMES.get(symbol, str(symbol)),
            "mean_brightness": float(recovered_image.mean()),
            "brightness_delta": float(recovered_image.mean() - message.base_image.mean()),
            "total_energy": energy(recovered_image),
        })

    morse, text, success = decode_symbols_to_morse_and_text(recovered_symbols)


    recovered_image_b64 = None
    if first_recovered_image is not None:
        recovered_image_b64 = array_to_base64(first_recovered_image)

    return {
        "message_id": message_id,
        "text": text,
        "morse": morse,
        "symbols": recovered_symbols,
        "frame_count": len(recovered_symbols),
        "success": success,
        "image": recovered_image_b64,
        "frames": frame_diagnostics,
    }


def predict_basic_morse_from_energy(message_id: str) -> dict:
    """
    Energy Bug Side-Channel Path:
    Predicts Morse code directly from the ciphertext Parseval energy,
    WITHOUT decrypting the image, and WITHOUT requiring any key image or password.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("message_id is required")

    message = get_message(message_id)
    if message.message_type != BASIC_ENERGY_MESSAGE:
        raise ValueError(
            f"Message {message_id} is not a basic_energy_morse message (type={message.message_type})"
        )

    ordered_frames = get_ordered_frames(message, require_complete=True)
    if not ordered_frames:
        raise ValueError("No frames found for this message")

    thresholds = message.metadata.get("thresholds")
    if not thresholds:
        _, thresholds = compute_expected_energy_levels(message.base_image)

    predicted_symbols: list[int] = []
    frame_energies: list[float] = []
    frame_details: list[dict] = []

    for frame in ordered_frames:
        # Compute Parseval energy directly from the complex ciphertext or amplitude
        c_energy = energy(frame.amplitude)
        frame_energies.append(c_energy)

        pred_symbol = predict_symbol_from_energy(c_energy, thresholds)
        predicted_symbols.append(pred_symbol)

        frame_details.append({
            "frame_index": frame.frame_index,
            "energy": c_energy,
            "predicted_symbol": pred_symbol,
            "symbol_name": SYMBOL_NAMES.get(pred_symbol, str(pred_symbol)),
        })

    morse, text, success = decode_symbols_to_morse_and_text(predicted_symbols)

    return {
        "message_id": message_id,
        "predicted_text": text,
        "predicted_morse": morse,
        "predicted_symbols": predicted_symbols,
        "frame_count": len(predicted_symbols),
        "thresholds": thresholds,
        "energy_levels": message.metadata.get("energy_levels", []),
        "frame_energies": frame_energies,
        "frames": frame_details,
        "success": success,
        "bypassed_decryption": True,
    }
