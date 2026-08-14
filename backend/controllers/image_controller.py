"""
Orchestration layer for /api/encrypt, /api/decrypt, and /api/base-image.

The controller is intentionally thin: it does file I/O, calls the pure
DRPE service, manages the in-memory message store, and shapes the
response. All real logic lives in services/.
"""

from __future__ import annotations

import numpy as np
from fastapi import Form, HTTPException, UploadFile

from schemas.image_schema import (
    BaseImageResponse,
    DecryptResponse,
    EncryptResponse,
)
from services.base_image import get_base_image
from services.drpe import (
    drpe_decrypt,
    drpe_encrypt,
    energy,
)
from services.image_utils import (
    array_to_base64,
    b64_to_complex,
    complex_to_b64,
    file_to_array,
)


# Cover image is the *last* one we encrypted, kept for the "match with
# cover" readout. Resets on every /api/encrypt call.
_last_cover: np.ndarray | None = None


async def encrypt_controller(
    cover_image: UploadFile,
    seed_p1: str = Form(...),
    seed_p2: str = Form(...),
) -> EncryptResponse:
    """
    Sender side. Reads the cover image, runs DRPE with the
    predetermined base image + dual seeds (seed_p1, seed_p2),
    and returns the complex ciphertext payload + amplitude display image.
    """
    global _last_cover

    base = get_base_image()
    try:
        cover_arr = await file_to_array(cover_image, target_shape=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        out = drpe_encrypt(cover_arr, base, seed_p1, seed_p2, frame_index=0)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    _last_cover = cover_arr

    c_complex = out["complex"]
    return EncryptResponse(
        ciphertext_b64=complex_to_b64(c_complex),
        ciphertext_shape=list(c_complex.shape),
        image=array_to_base64(out["amplitude"]),
        energy=energy(out["amplitude"]),
        cover_energy=energy(cover_arr),
    )


async def decrypt_controller(
    ciphertext_b64: str = Form(...),
    ciphertext_height: int = Form(...),
    ciphertext_width: int = Form(...),
    seed_p1: str = Form(...),
    seed_p2: str = Form(...),
) -> DecryptResponse:
    """
    Receiver side. Decodes the complex ciphertext payload, re-derives
    phase masks from the provided dual seeds (seed_p1, seed_p2), and inverts.
    A wrong seed dynamically recovers the exact phase noise corresponding to that key.
    """
    base = get_base_image()
    try:
        ciphertext_complex = b64_to_complex(
            ciphertext_b64, (ciphertext_height, ciphertext_width)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ciphertext payload: {e}")

    try:
        recovered = drpe_decrypt(
            ciphertext_complex=ciphertext_complex,
            base_image=base,
            seed_p1=seed_p1,
            seed_p2=seed_p2,
            frame_index=0,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    match = False
    if _last_cover is not None and _last_cover.shape == recovered.shape:
        # Same-seed decrypt matches original cover exactly with zero pixel error (atol=1e-15).
        match = bool(np.allclose(_last_cover, recovered, atol=1e-15))

    return DecryptResponse(
        image=array_to_base64(recovered),
        energy=energy(recovered),
        match_with_cover=match,
    )


def get_base_image_controller() -> BaseImageResponse:
    """Returns the predetermined base image so the demo can show it."""
    base = get_base_image()
    return BaseImageResponse(
        image=array_to_base64(base),
        shape=list(base.shape),
    )
