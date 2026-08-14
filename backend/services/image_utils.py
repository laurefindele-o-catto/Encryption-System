import base64
import io

import numpy as np
from fastapi import UploadFile
from PIL import Image


async def file_to_array(
    upload: UploadFile,
    target_shape: tuple[int, int] | None = None,
) -> np.ndarray:
    """
    Read an uploaded image file into a 2D grayscale numpy array.
    If target_shape (height, width) is provided, resize the image to match.
    """
    raw = await upload.read()
    if not raw or len(raw) < 8:
        raise ValueError("Uploaded file is empty or corrupted.")
    try:
        img = Image.open(io.BytesIO(raw)).convert("L") # if wanna use RGB instead of grayscale, change "L" to "RGB"
    except Exception as e:
        raise ValueError(f"Invalid image format: {e}")

    if target_shape is not None and img.size != (target_shape[1], target_shape[0]):
        # PIL size is (width, height), target_shape is (height, width)
        img = img.resize((target_shape[1], target_shape[0]), Image.Resampling.BICUBIC)
    return np.array(img, dtype=np.float64)


def array_to_base64(arr: np.ndarray) -> str:
    """Turn a 2D numpy array back into a base64-encoded PNG string."""
    clipped = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    img = Image.fromarray(clipped)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def complex_to_b64(c: np.ndarray) -> str:
    """Losslessly encode a complex128 numpy array to a base64 string."""
    return base64.b64encode(c.astype(np.complex128).tobytes()).decode("utf-8")


def b64_to_complex(b64_str: str, shape: tuple[int, int]) -> np.ndarray:
    """Losslessly decode a base64 string back into a 2D complex128 numpy array."""
    raw_bytes = base64.b64decode(b64_str)
    return np.frombuffer(raw_bytes, dtype=np.complex128).reshape(shape)

