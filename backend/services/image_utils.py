import base64
import io

import numpy as np
from fastapi import UploadFile
from PIL import Image


async def file_to_array(upload: UploadFile) -> np.ndarray:
    """Read an uploaded image file into a 2D grayscale numpy array."""
    raw = await upload.read()
    img = Image.open(io.BytesIO(raw)).convert("L")
    return np.array(img, dtype=np.float64)


def array_to_base64(arr: np.ndarray) -> str:
    """Turn a 2D numpy array back into a base64-encoded PNG string."""
    clipped = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(clipped)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
