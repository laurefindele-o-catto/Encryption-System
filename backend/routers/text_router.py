"""Phase 2 text transmission routes."""

from fastapi import APIRouter, File, Form, UploadFile

from controllers.text_controller import (
    decrypt_basic_energy_controller,
    decrypt_text_controller,
    encrypt_basic_energy_controller,
    encrypt_text_controller,
    predict_basic_energy_controller,
)
from schemas.image_schema import (
    BasicEnergyDecryptResponse,
    BasicEnergyEncryptResponse,
    BasicEnergyPredictResponse,
    TextDecryptResponse,
    TextEncryptResponse,
)


router = APIRouter(prefix="/api/text")


@router.post("/encrypt", response_model=TextEncryptResponse)
async def encrypt_text(
    secret_text: str = Form(...),
    base_image: UploadFile = File(...),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
) -> TextEncryptResponse:
    """Encrypt Alice's secret text as an ordered Morse frame sequence (differential technique)."""
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
    """Decrypt Bob's message frames back into Morse and plaintext (differential technique)."""
    return await decrypt_text_controller(
        message_id=message_id,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
    )


@router.post("/basic-energy/encrypt", response_model=BasicEnergyEncryptResponse)
async def encrypt_basic_energy(
    secret_text: str = Form(...),
    base_image: UploadFile = File(...),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
) -> BasicEnergyEncryptResponse:
    """Encrypt secret text using basic Morse without differential cancellation."""
    return await encrypt_basic_energy_controller(
        secret_text=secret_text,
        base_image=base_image,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
    )


@router.post("/basic-energy/decrypt", response_model=BasicEnergyDecryptResponse)
async def decrypt_basic_energy(
    message_id: str = Form(...),
    secret_key_image: UploadFile = File(...),
    secret_password: str = Form(...),
) -> BasicEnergyDecryptResponse:
    """Normal DRPE decryption path: decrypt frames with credentials and extract Morse."""
    return await decrypt_basic_energy_controller(
        message_id=message_id,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
    )


@router.post("/basic-energy/predict", response_model=BasicEnergyPredictResponse)
async def predict_basic_energy(
    message_id: str = Form(...),
) -> BasicEnergyPredictResponse:
    """Side-channel energy prediction: predict Morse directly from ciphertext energy without decrypting."""
    return await predict_basic_energy_controller(
        message_id=message_id,
    )