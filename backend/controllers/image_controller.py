"""
Orchestration layer for the current image encryption workflow.

The controller does file I/O, calls the pure DRPE service, manages the
in-memory message store, and shapes the responses. All real logic lives
in services/.
"""

from __future__ import annotations

import base64
import secrets

import numpy as np
from fastapi import Form, HTTPException, UploadFile

from schemas.image_schema import (
    DecryptResponse,
    EncryptResponse,
)
from services.drpe import (
    drpe_decrypt,
    drpe_encrypt,
    energy,
    generate_phase_masks,
)
from services.image_utils import (
    array_to_base64,
    b64_to_complex,
    complex_to_b64,
    file_to_array,
    key_image_digest,
)
from services.messages import Frame, add_frame, create_message, get_frame, get_message, new_message_id
from services.keys import derive_image_password_keys


# Cover image is the *last* one we encrypted, kept for the "match with
# cover" readout. Resets on every /api/encrypt call.
_last_cover: np.ndarray | None = None


async def encrypt_controller(
    cover_image: UploadFile,
    secret_key_image: UploadFile,
    secret_password: str,
    message_id: str | None = None,
    frame_index: int = 0,
) -> EncryptResponse:
    """
    Sender side. Reads the cover and secret key image, derives per-frame
    P1/P2 material, and returns the complex ciphertext plus display metadata.
    """
    global _last_cover

    try:
        cover_arr = await file_to_array(cover_image, target_shape=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if frame_index < 0:
        raise HTTPException(status_code=400, detail="frame_index must be non-negative.")

    secret_image_bytes = await secret_key_image.read()
    if not secret_password:
        raise HTTPException(status_code=400, detail="secret_password is required.")
    await secret_key_image.seek(0)
    try:
        image_digest = await key_image_digest(secret_key_image)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    salt = secrets.token_bytes(16)
    generated_message_id = message_id or new_message_id()
    await secret_key_image.seek(0)
    p1_material, p2_material = derive_image_password_keys(
        secret_password,
        salt,
        image_digest,
        generated_message_id,
        frame_index,
    )

    try:
        out = drpe_encrypt(cover_arr, p1_material, p2_material)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    _last_cover = cover_arr

    # Transition storage only: steps 1-3 will replace the legacy seeds with
    # these uploaded key images and secret_password in the KDF.
    message = create_message(
        secret_key_image=secret_image_bytes,
        secret_password=secret_password,
        salt=salt,
        message_id=generated_message_id,
    )

    c_complex = out["complex"]
    add_frame(
        message,
        Frame(
            frame_index=frame_index,
            ciphertext_complex=c_complex,
            amplitude=out["amplitude"],
        ),
    )
    return EncryptResponse(
        ciphertext_b64=complex_to_b64(c_complex),
        ciphertext_shape=list(c_complex.shape),
        image=array_to_base64(out["amplitude"]),
        energy=energy(out["amplitude"]),
        cover_energy=energy(cover_arr),
        message_id=message.message_id,
        salt_b64=base64.b64encode(salt).decode("ascii"),
    )


async def decrypt_controller(
    ciphertext_b64: str | None,
    ciphertext_shape: list[int] | None,
    secret_key_image: UploadFile,
    secret_password: str,
    salt_b64: str,
    frame_index: int = 0,
    message_id: str | None = None,
) -> DecryptResponse:
    """
    Receiver side. Reproduces the P1/P2 materials from the receiver key image,
    password, salt, message ID, and frame index, then decrypts the ciphertext.
    """
    try:
        if message_id:
            message = get_message(message_id)
            frame = get_frame(message, frame_index)
            ciphertext_complex = frame.ciphertext_complex
            ciphertext_shape = list(ciphertext_complex.shape)
        elif ciphertext_b64 and ciphertext_shape:
            ciphertext_complex = b64_to_complex(ciphertext_b64, tuple(ciphertext_shape))
        else:
            raise ValueError("message_id is required when ciphertext is not supplied")
        receiver_image_bytes = await secret_key_image.read()
        await secret_key_image.seek(0)
        image_digest = await key_image_digest(secret_key_image)
        if message_id:
            message.receiver_secret_key_image = receiver_image_bytes
            message.receiver_password = secret_password
        salt = base64.b64decode(salt_b64, validate=True)
        p1_material, p2_material = derive_image_password_keys(
            secret_password,
            salt,
            image_digest,
            message_id or "",
            frame_index,
        )
        p1, p2 = generate_phase_masks(
            tuple(ciphertext_shape), p1_material, p2_material
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ciphertext or decryption parameters: {e}")

    try:
        recovered = drpe_decrypt(
            ciphertext_complex=ciphertext_complex,
            p1=p1,
            p2=p2,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    match = False
    if _last_cover is not None and _last_cover.shape == recovered.shape:
        # Same-mask decrypt matches original cover exactly with zero pixel error (atol=1e-15).
        match = bool(np.allclose(_last_cover, recovered, atol=1e-15))

    return DecryptResponse(
        image=array_to_base64(recovered),
        energy=energy(recovered),
        match_with_cover=match,
    )


