"""Phase 2 text transmission routes."""

from fastapi import APIRouter, File, Form, UploadFile

from controllers.text_controller import encrypt_text_controller
from schemas.image_schema import TextEncryptResponse


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