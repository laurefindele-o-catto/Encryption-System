"""
Sender-side image encryption service.
"""

from __future__ import annotations

import secrets
import numpy as np

from services.drpe import drpe_encrypt, energy
from services.image_utils import (
    array_to_base64,
    canonicalize_key_image,
    hash_canonical_key_image,
)
from services.keys import derive_image_password_keys
from services.messages import (
    Frame,
    IMAGE_MESSAGE,
    add_frame,
    create_message,
    new_message_id,
)


def encrypt_image_message(
    cover_image: np.ndarray,
    secret_key_image: bytes,
    secret_password: str,
    message_id: str | None = None,
) -> dict:
    """Encrypt a cover image using DRPE and store the complex ciphertext.

    Args:
        cover_image: 2D or 3D numpy array representing the cover image.
        secret_key_image: Raw image bytes of the sender's secret key image.
        secret_password: Sender's secret password string.
        message_id: Optional unique message ID (auto-generated if None).

    Returns:
        Dictionary containing message_id, salt, base64 amplitude display image,
        and energy metrics.
    """
    if cover_image is None or not isinstance(cover_image, np.ndarray):
        raise ValueError("cover_image must be a valid numpy array")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")
    if not secret_password:
        raise ValueError("secret_password is required")

    normalized_cover = np.asarray(cover_image, dtype=np.float64)
    salt = secrets.token_bytes(16)
    generated_message_id = message_id or new_message_id()

    key_pixels = canonicalize_key_image(secret_key_image)
    image_digest = hash_canonical_key_image(key_pixels)

    p1_material, p2_material = derive_image_password_keys(
        password=secret_password,
        salt=salt,
        secret_image_digest=image_digest,
        message_id=generated_message_id,
        frame_index=0,
    )

    out = drpe_encrypt(normalized_cover, p1_material, p2_material)

    message = create_message(
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        salt=salt,
        message_id=generated_message_id,
        message_type=IMAGE_MESSAGE,
        base_image=normalized_cover.copy(),
        total_frames=1,
    )

    add_frame(
        message,
        Frame(
            frame_index=0,
            ciphertext_complex=out["complex"],
            amplitude=out["amplitude"],
        ),
    )

    return {
        "message": message,
        "message_id": generated_message_id,
        "salt": salt,
        "image": array_to_base64(out["amplitude"]),
        "energy": energy(out["amplitude"]),
        "cover_energy": energy(normalized_cover),
    }
