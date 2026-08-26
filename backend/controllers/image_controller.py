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
    generate_phase_masks,
)
from services.image_utils import (
    array_to_base64,
    b64_to_complex,
    b64_to_float,
    complex_to_b64,
    file_to_array,
    float_to_b64,
)


import hashlib

# Cover image is the *last* one we encrypted, kept only as an optional
# fallback for single-client local testing. Production/multi-frame uses cover_hash.
_last_cover: np.ndarray | None = None


async def encrypt_controller(
    cover_image: UploadFile,
    seed_p1: str = Form(...),
    seed_p2: str = Form(...),
    frame_index: int = 0,
) -> EncryptResponse:
    """
    Sender side. Reads the cover image, runs DRPE with the
    predetermined base image + dual seeds (seed_p1, seed_p2) and frame_index,
    and returns the complex ciphertext payload, phase masks P1/P2, display image, and cover_hash.
    """
    global _last_cover

    base = get_base_image()
    try:
        cover_arr = await file_to_array(cover_image, target_shape=None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        out = drpe_encrypt(cover_arr, base, seed_p1, seed_p2, frame_index=frame_index)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    _last_cover = cover_arr
    cover_hash = hashlib.sha256(cover_arr.tobytes()).hexdigest()

    c_complex = out["complex"]
    return EncryptResponse(
        ciphertext_b64=complex_to_b64(c_complex),
        ciphertext_shape=list(c_complex.shape),
        p1_b64=float_to_b64(out["p1"]),
        p2_b64=float_to_b64(out["p2"]),
        image=array_to_base64(out["amplitude"]),
        energy=energy(c_complex),
        cover_energy=energy(cover_arr),
        cover_hash=cover_hash,
        frame_index=frame_index,
    )


async def decrypt_controller(
    ciphertext_b64: str,
    ciphertext_shape: list[int],
    p1_b64: str | None = None,
    p2_b64: str | None = None,
    seed_p1: str | None = None,
    seed_p2: str | None = None,
    frame_index: int = 0,
    cover_hash: str | None = None,
) -> DecryptResponse:
    """
    Receiver side. Decodes the complex ciphertext payload and inverts using
    either user-provided seeds (seed_p1, seed_p2) or direct phase masks (p1_b64, p2_b64).
    """
    try:
        ciphertext_complex = b64_to_complex(ciphertext_b64, tuple(ciphertext_shape))
        if seed_p1 is not None and seed_p2 is not None:
            base = get_base_image()
            p1, p2 = generate_phase_masks(tuple(ciphertext_shape), base, seed_p1, seed_p2, frame_index=frame_index)
        elif p1_b64 and p2_b64:
            p1 = b64_to_float(p1_b64, tuple(ciphertext_shape))
            p2 = b64_to_float(p2_b64, tuple(ciphertext_shape))
        else:
            raise ValueError("Either (seed_p1, seed_p2) or (p1_b64, p2_b64) must be provided.")
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
    if cover_hash:
        rec_hash = hashlib.sha256(recovered.tobytes()).hexdigest()
        match = (rec_hash == cover_hash)
    elif _last_cover is not None and _last_cover.shape == recovered.shape:
        # Same-mask decrypt matches original cover exactly with zero pixel error (atol=1e-15).
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

