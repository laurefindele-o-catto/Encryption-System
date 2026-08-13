from fastapi import APIRouter, Form, UploadFile

from controllers.image_controller import (
    decrypt_controller,
    encrypt_controller,
    get_encrypted_image_controller,
)
from schemas.image_schema import ImageResponse

router = APIRouter(prefix="/api")


@router.post("/encrypt", response_model=ImageResponse)
async def encrypt(cover_image: UploadFile, key_image: UploadFile, x: int = Form(...), y: int = Form(...)):
    return await encrypt_controller(cover_image, key_image, x, y)


@router.get("/encrypted-image", response_model=ImageResponse)
def get_encrypted_image():
    return get_encrypted_image_controller()


@router.post("/decrypt", response_model=ImageResponse)
async def decrypt(key_image: UploadFile):
    return await decrypt_controller(key_image)