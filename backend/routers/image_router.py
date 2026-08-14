"""
Thin route handlers. The controller does the work; the router just
unpacks the request and returns the schema object.
"""

from fastapi import APIRouter, Form, UploadFile

from controllers.image_controller import (
    decrypt_controller,
    encrypt_controller,
    get_base_image_controller,
)
from schemas.image_schema import (
    BaseImageResponse,
    DecryptRequest,
    DecryptResponse,
    EncryptResponse,
)

router = APIRouter(prefix="/api")


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt(
    cover_image: UploadFile,
    seed_p1: str = Form(...),
    seed_p2: str = Form(...),
) -> EncryptResponse:
    """
    Encrypt `cover_image` with the predetermined base image + `seed_p1` and `seed_p2`.
    Returns the (visually noise-like) ciphertext image, the ciphertext payload,
    and energies for the Parseval readout.
    """
    return await encrypt_controller(cover_image, seed_p1, seed_p2)


@router.post("/decrypt", response_model=DecryptResponse)
async def decrypt(req: DecryptRequest) -> DecryptResponse:
    """
    Decrypt the complex ciphertext payload using user-provided `seed_p1` and `seed_p2`.
    Stateless endpoint: user inputs any seeds to see the corresponding decrypted output.
    """
    return await decrypt_controller(
        req.ciphertext_b64, req.ciphertext_height, req.ciphertext_width, req.seed_p1, req.seed_p2
    )


@router.get("/base-image", response_model=BaseImageResponse)
def base_image() -> BaseImageResponse:
    """Returns the predetermined base/reference image (demo transparency)."""
    return get_base_image_controller()
