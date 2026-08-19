import base64
import io

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


def complex_to_b64(c: np.ndarray) -> str:
    """Losslessly encode a complex128 numpy array to a base64 string."""
    return base64.b64encode(c.astype(np.complex128).tobytes()).decode("utf-8")


def b64_to_complex(b64_str: str, shape: tuple[int, ...]) -> np.ndarray:
    """Losslessly decode a base64 string back into a complex128 numpy array."""
    raw_bytes = base64.b64decode(b64_str)
    return np.frombuffer(raw_bytes, dtype=np.complex128).reshape(tuple(shape))


def float_to_b64(arr: np.ndarray) -> str:
    """Losslessly encode a float64 numpy array (e.g., P1 or P2 mask) to a base64 string."""
    return base64.b64encode(arr.astype(np.float64).tobytes()).decode("utf-8")


def b64_to_float(b64_str: str, shape: tuple[int, ...]) -> np.ndarray:
    """Losslessly decode a base64 string back into a float64 numpy array."""
    raw_bytes = base64.b64decode(b64_str)
    return np.frombuffer(raw_bytes, dtype=np.float64).reshape(tuple(shape))


