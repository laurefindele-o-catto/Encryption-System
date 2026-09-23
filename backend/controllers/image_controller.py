"""
Controller for image encryption and decryption requests.
"""

from __future__ import annotations

import base64

from fastapi import HTTPException, UploadFile

from schemas.image_schema import DecryptResponse, EncryptResponse
from services.image_decryption import decrypt_image_message
from services.image_encryption import encrypt_image_message
from services.image_utils import file_to_array


async def encrypt_controller(
    cover_image: UploadFile,
    secret_key_image: UploadFile,
    secret_password: str,
    message_id: str | None = None,
    frame_index: int = 0,
) -> EncryptResponse:
    """Read Alice's uploads and create a stored encrypted image message."""
    try:
        cover_array = await file_to_array(cover_image, target_shape=None)
        key_image_bytes = await secret_key_image.read()
        result = encrypt_image_message(
            cover_image=cover_array,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
            message_id=message_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image encryption failed: {exc}") from exc

    return EncryptResponse(
        image=result["image"],
        energy=result["energy"],
        cover_energy=result["cover_energy"],
        message_id=result["message_id"],
        salt_b64=base64.b64encode(result["salt"]).decode("ascii"),
        stages=result["stages"],
    )


async def decrypt_controller(
    message_id: str,
    secret_key_image: UploadFile,
    secret_password: str,
    frame_index: int = 0,
    **kwargs,
) -> DecryptResponse:
    """Read Bob's uploads and decrypt the stored image message."""
    try:
        key_image_bytes = await secret_key_image.read()
        result = decrypt_image_message(
            message_id=message_id,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
            frame_index=frame_index,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image decryption failed: {exc}") from exc

    return DecryptResponse(
        image=result["image"],
        energy=result["energy"],
        match_with_cover=result["match_with_cover"],
        stages=result["stages"],
    )
