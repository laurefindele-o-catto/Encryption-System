import base64
import io
import hashlib

import numpy as np
from fastapi import UploadFile
from PIL import Image



async def file_to_array(
    upload: UploadFile,
    target_shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    """
    Read an uploaded image file into an RGB numpy array (float64, shape (H, W, 3)).
    If target_shape (height, width) is provided, resize the image to match.
    """
    raw = await upload.read()
    if not raw or len(raw) < 8:
        raise ValueError("Uploaded file is empty or corrupted.")
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image format: {e}")

    if target_shape is not None and img.size != (target_shape[1], target_shape[0]):
        # PIL size is (width, height), target_shape is (height, width)
        img = img.resize((target_shape[1], target_shape[0]), Image.Resampling.BICUBIC)
    return np.array(img, dtype=np.float64)


def array_to_base64(arr: np.ndarray) -> str:
    """Turn a numpy array (RGB or grayscale) back into a base64-encoded PNG string."""
    clipped = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    img = Image.fromarray(clipped)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def array_to_base64_preview(arr: np.ndarray, max_size: int = 512) -> str:
    """Encode a resized PNG preview without changing the source array."""
    clipped = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    image = Image.fromarray(clipped)
    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")






def canonicalize_key_image(raw: bytes) -> np.ndarray:
    """
    Decode and normalize a key image to RGB uint8 pixels.
    """
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image = image.resize((256, 256), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def hash_canonical_key_image(pixels: np.ndarray) -> bytes:
    """
    Hash canonical RGB uint8 pixels.
    """
    header = b"DRPE-KEY-IMAGE-v1"
    shape = np.asarray(pixels.shape, dtype=np.uint32).tobytes()
    return hashlib.sha256(
        header + shape + pixels.tobytes()
    ).digest()
    

async def key_image_digest(upload: UploadFile) -> bytes:
    raw = await upload.read()

    if not raw:
        raise ValueError("Key image is empty.")

    pixels = canonicalize_key_image(raw)
    return hash_canonical_key_image(pixels)