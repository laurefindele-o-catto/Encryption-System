"""Receiver-side Phase 2 encrypted-frames-to-text pipeline."""

from __future__ import annotations

import numpy as np

from services.drpe import drpe_decrypt, generate_phase_masks
from services.encoding.morse_to_symbol_sequence import SymbolState, symbol_sequence_to_morse
from services.encoding.morse_to_text import is_valid_morse, morse_to_text
from services.encoding.symbol_image import differential_brightness_metrics, read_differential_brightness
from services.image_utils import (
    array_to_base64,
    canonicalize_key_image,
    hash_canonical_key_image,
)
from services.keys import derive_frame_key, derive_master_key, derive_password_key
from services.messages import (
    TEXT_MESSAGE,
    get_message,
    get_ordered_frames,
)

SYMBOL_NAMES = {
    SymbolState.DOT: "DOT",
    SymbolState.DASH: "DASH",
    SymbolState.LETTER_GAP: "LETTER_GAP",
    SymbolState.WORD_GAP: "WORD_GAP",
}


def decrypt_text_message(
    message_id: str,
    secret_key_image: bytes,
    secret_password: str,
) -> dict:
    """Reconstruct secret text from stored encrypted frames using Bob's credentials.

    Args:
        message_id: ID of the stored text message.
        secret_key_image: Raw bytes of Bob's uploaded key image.
        secret_password: Bob's password string.

    Returns:
        dict containing decoded text, reconstructed morse, symbol list,
        per-frame diagnostics, and success status.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("message_id is required")
    if not isinstance(secret_password, str) or not secret_password:
        raise ValueError("secret_password is required")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")

    message = get_message(message_id)
    if message.message_type != TEXT_MESSAGE:
        raise ValueError(f"Message {message_id} is not a text message (type={message.message_type})")

    ordered_frames = get_ordered_frames(message, require_complete=True)
    if not ordered_frames:
        raise ValueError("No frames found for this message")

    message.receiver_secret_key_image = secret_key_image
    message.receiver_password = secret_password

    key_pixels = canonicalize_key_image(secret_key_image)
    image_digest = hash_canonical_key_image(key_pixels)
    password_key = derive_password_key(secret_password, message.salt)
    master_key = derive_master_key(password_key, image_digest)

    recovered_symbols: list[SymbolState] = []
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
        symbol = read_differential_brightness(recovered_image)

        recovered_symbols.append(symbol)
        frame_diagnostics.append({
            "frame_index": frame_idx,
            "symbol": int(symbol),
            "symbol_name": SYMBOL_NAMES.get(symbol, str(symbol)),
            **differential_brightness_metrics(recovered_image),
        })

    morse = symbol_sequence_to_morse(recovered_symbols)
    text = morse_to_text(morse)
    valid_morse = is_valid_morse(morse)

    recovered_image_b64 = None
    if first_recovered_image is not None:
        recovered_image_b64 = array_to_base64(first_recovered_image)
    elif ordered_frames:
        recovered_image_b64 = array_to_base64(recovered_image)

    return {
        "message_id": message_id,
        "text": text,
        "morse": morse,
        "symbols": [int(s) for s in recovered_symbols],
        "frame_count": len(recovered_symbols),
        "success": valid_morse,
        "image": recovered_image_b64,
        "frames": frame_diagnostics,
    }
