"""
Pydantic request/response shapes for the image encryption API.
"""

from pydantic import BaseModel


class ImageResponse(BaseModel):
    """Base64-encoded PNG of a single 2D image."""
    image: str  # base64-encoded PNG


class EncryptResponse(BaseModel):
    """Returned by POST /api/encrypt."""
    ciphertext_b64: str  # Lossless base64-encoded complex128 array
    ciphertext_shape: list[int]  # [height, width, channels] or [height, width]
    image: str          # base64-encoded PNG of |ciphertext| (display image)
    energy: float       # Σ(pixel²) over the displayed amplitude
    cover_energy: float  # Σ(pixel²) over the original cover (for Parseval readout)
    message_id: str
    salt_b64: str


class DecryptResponse(BaseModel):
    """Returned by POST /api/decrypt."""
    image: str          # base64-encoded PNG of the recovered cover
    energy: float       # Σ(pixel²) over the recovered image
    match_with_cover: bool  # True iff the server still has the original and they match


