"""Phase 2 text transmission routes."""

from fastapi import APIRouter, File, Form, UploadFile

from controllers.text_controller import decrypt_text_controller, encrypt_text_controller
from schemas.image_schema import TextDecryptResponse, TextEncryptResponse


router = APIRouter(prefix="/api/text")


@router.post("/encrypt", response_model=TextEncryptResponse)
async def encrypt_text(
    secret_text: str = Form(...),
    base_image: UploadFile = File(...),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
) -> TextEncryptResponse:
    """Encrypt Alice's secret text as an ordered Morse frame sequence."""
    return await encrypt_text_controller(
        secret_text=secret_text,
        base_image=base_image,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
    )


@router.post("/decrypt", response_model=TextDecryptResponse)
async def decrypt_text(
    message_id: str = Form(...),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
) -> TextDecryptResponse:
    """Decrypt Bob's message frames back into Morse and plaintext."""
    return await decrypt_text_controller(
        message_id=message_id,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
    )