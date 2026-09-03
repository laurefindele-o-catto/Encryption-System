"""Sender-side Phase 2 text-to-encrypted-frame pipeline."""

from __future__ import annotations

import secrets

import numpy as np

from services.drpe import drpe_encrypt, energy
from services.encoding.morse_to_symbol_sequence import morse_to_symbol_sequence
from services.encoding.symbol_image import generate_symbol_image
from services.encoding.text_to_morse import text_to_morse
from services.image_utils import (
    array_to_base64,
    array_to_base64_preview,
    canonicalize_key_image,
    hash_canonical_key_image,
)
from services.keys import derive_frame_key, derive_master_key, derive_password_key
from services.messages import (
    Frame,
    TEXT_MESSAGE,
    add_frame,
    create_message,
    new_message_id,
)


def encrypt_text_message(
    secret_text: str,
    base_image: np.ndarray,
    secret_key_image: bytes,
    secret_password: str,
    message_id: str | None = None,
    salt: bytes | None = None,
    include_previews: bool = False,
) -> dict:
    """Convert text to Morse symbols and encrypt one frame per symbol.

    The function is deliberately independent of FastAPI. A controller can
    read uploaded files and pass their bytes/arrays here. Complex ciphertext
    remains in the in-memory message store; the returned previews are display
    data only.
    """
    if not isinstance(secret_text, str) or not secret_text.strip():
        raise ValueError("secret_text is required")
    if not isinstance(secret_password, str) or not secret_password:
        raise ValueError("secret_password is required")
    if not isinstance(base_image, np.ndarray) or base_image.ndim != 3 or base_image.shape[2] != 3:
        raise ValueError("base_image must be an RGB array with shape (height, width, 3)")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")

    normalized_base = np.asarray(base_image, dtype=np.float64)
    morse = text_to_morse(secret_text)
    symbols = morse_to_symbol_sequence(morse)
    
    if not symbols:
        raise ValueError("secret_text produced no encodable symbols")

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
        message_type=TEXT_MESSAGE,
        base_image=normalized_base.copy(),
        total_frames=len(symbols),
        metadata={"morse": morse, "symbols": [int(symbol) for symbol in symbols]},
    )

    previews = []
    
    for frame_index, symbol in enumerate(symbols):
        symbol_image = generate_symbol_image(symbol, normalized_base)
        #this is the func that tweaks the brightness
        
        p1_material = derive_frame_key(master_key, generated_message_id, frame_index, b"DRPE/P1")
        p2_material = derive_frame_key(master_key, generated_message_id, frame_index, b"DRPE/P2")
        #from the password and the key image
        
        encrypted = drpe_encrypt(symbol_image, p1_material, p2_material)
        
        add_frame(
            message,
            Frame(
                frame_index,
                ciphertext_complex= encrypted["complex"],
                amplitude=encrypted["amplitude"]
            ), #frame is a defined class
        )
        
        #adds this frame to the global frames array
        
        if include_previews:
            previews.append({
                "frame_index": frame_index,
                "image": array_to_base64_preview(encrypted["amplitude"]),
                "energy": energy(encrypted["amplitude"]),
            })
        

    return {
        "message": message,
        "message_id": generated_message_id,
        "salt": generated_salt,
        "morse": morse,
        "symbols": [int(symbol) for symbol in symbols],
        "frame_count": len(symbols),
        "base_image_shape": list(normalized_base.shape),
        "previews": previews,
    }