"""Controller for Alice's Phase 2 text-encryption request."""

from __future__ import annotations

import base64

from fastapi import HTTPException, UploadFile

from schemas.image_schema import TextEncryptResponse, TextFramePreview
from services.image_utils import file_to_array
from services.text_encryption import encrypt_text_message


async def encrypt_text_controller(
    secret_text: str,
    base_image: UploadFile,
    secret_key_image: UploadFile,
    secret_password: str,
) -> TextEncryptResponse:
    """Read Alice's uploads and create a stored encrypted text message."""
    try:
        base_image_array = await file_to_array(base_image, target_shape=None)
        key_image_bytes = await secret_key_image.read()
        result = encrypt_text_message(
            secret_text=secret_text,
            base_image=base_image_array,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
            include_previews=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Text encryption failed: {exc}") from exc

    previews = [TextFramePreview(**preview) for preview in result["previews"]]
    return TextEncryptResponse(
        message_id=result["message_id"],
        salt_b64=base64.b64encode(result["salt"]).decode("ascii"),
        morse=result["morse"],
        symbols=result["symbols"],
        frame_count=result["frame_count"],
        base_image_shape=result["base_image_shape"],
        previews=previews,
    )