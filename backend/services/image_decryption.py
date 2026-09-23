"""
Receiver-side image decryption service.
"""

from __future__ import annotations

import numpy as np

from services.drpe import drpe_decrypt, drpe_decrypt_with_stages, energy, generate_phase_masks
from services.image_utils import (
    array_to_base64,
    array_to_base64_preview,
    canonicalize_key_image,
    hash_canonical_key_image,
)
from services.keys import derive_image_password_keys
from services.messages import IMAGE_MESSAGE, get_frame, get_message


def decrypt_image_message(
    message_id: str,
    secret_key_image: bytes,
    secret_password: str,
    frame_index: int = 0,
) -> dict:
    """Decrypt an encrypted image frame using Bob's credentials.

    Args:
        message_id: ID of the stored encrypted image message.
        secret_key_image: Raw image bytes of Bob's secret key image.
        secret_password: Bob's password string.
        frame_index: Index of the frame to decrypt (default 0).

    Returns:
        Dictionary containing the base64 recovered image, energy, and match_with_cover boolean.
    """
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("message_id is required")
    if not secret_key_image:
        raise ValueError("secret_key_image is required")
    if not isinstance(secret_password, str) or not secret_password:
        raise ValueError("secret_password is required")

    message = get_message(message_id)
    if message.message_type != IMAGE_MESSAGE:
        raise ValueError(f"Message {message_id} is not an image message (type={message.message_type})")

    frame = get_frame(message, frame_index)

    message.receiver_secret_key_image = secret_key_image
    message.receiver_password = secret_password

    key_pixels = canonicalize_key_image(secret_key_image)
    image_digest = hash_canonical_key_image(key_pixels)

    p1_material, p2_material = derive_image_password_keys(
        password=secret_password,
        salt=message.salt,
        secret_image_digest=image_digest,
        message_id=message_id,
        frame_index=frame_index,
    )

    c_shape = frame.ciphertext_complex.shape
    p1, p2 = generate_phase_masks(c_shape, p1_material, p2_material)

    recovered, stages = drpe_decrypt_with_stages(
        ciphertext_complex=frame.ciphertext_complex,
        p1=p1,
        p2=p2,
    )

    match = False
    if message.base_image is not None and message.base_image.shape == recovered.shape:
        match = bool(np.allclose(message.base_image, recovered, atol=1e-15))

    return {
        "message_id": message_id,
        "image": array_to_base64(recovered),
        "energy": energy(recovered),
        "match_with_cover": match,
        "stages": [
            {"name": name, "image": array_to_base64_preview(image, max_size=512)}
            for name, image in stages.items()
        ],
    }
