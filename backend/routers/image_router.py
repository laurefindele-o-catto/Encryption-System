"""
Thin route handlers. The controller does the work; the router just
unpacks the request and returns the schema object.
"""

from fastapi import APIRouter, File, Form, UploadFile

from controllers.image_controller import (
    decrypt_controller,
    encrypt_controller,
)
from schemas.image_schema import DecryptResponse, EncryptResponse

router = APIRouter(prefix="/api")


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt(
    cover_image: UploadFile,
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
    message_id: str | None = Form(None),
    frame_index: int = Form(0),
) -> EncryptResponse:
    """
    Encrypt `cover_image` using the uploaded secret image and password.
    Returns the complex ciphertext and metadata needed for decryption.
    """
    return await encrypt_controller(
        cover_image,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        message_id=message_id,
        frame_index=frame_index,
    )


@router.post("/decrypt-with-key-images", response_model=DecryptResponse)
async def decrypt_with_key_images(
    ciphertext_b64: str | None = Form(None),
    ciphertext_shape: str | None = Form(None),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
    frame_index: int = Form(0),
    message_id: str = Form(...),
    salt_b64: str = Form(...),
) -> DecryptResponse:
    """Decrypt using the receiver's secret image and password."""
    import json

    try:
        shape = json.loads(ciphertext_shape) if ciphertext_shape else None
    except json.JSONDecodeError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="ciphertext_shape must be JSON.") from exc

    return await decrypt_controller(
        ciphertext_b64,
        shape,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        salt_b64=salt_b64,
        frame_index=frame_index,
        message_id=message_id,
    )

