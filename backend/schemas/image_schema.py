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
    p1_b64: str          # Lossless base64-encoded float64 P1 mask
    p2_b64: str          # Lossless base64-encoded float64 P2 mask
    image: str          # base64-encoded PNG of |ciphertext| (display image)
    energy: float       # Σ(pixel²) over the displayed amplitude
    cover_energy: float  # Σ(pixel²) over the original cover (for Parseval readout)
    cover_hash: str | None = None  # SHA-256 hash of original cover pixels for stateless verification
    frame_index: int = 0  # Sequence index within a transmission


class DecryptRequest(BaseModel):
    """Payload sent to POST /api/decrypt."""
    ciphertext_b64: str
    ciphertext_shape: list[int]
    frame_index: int = 0
    seed_p1: str | None = None
    seed_p2: str | None = None
    p1_b64: str | None = None
    p2_b64: str | None = None
    cover_hash: str | None = None  # Optional client-provided hash for stateless verification



class DecryptResponse(BaseModel):
    """Returned by POST /api/decrypt."""
    image: str          # base64-encoded PNG of the recovered cover
    energy: float       # Σ(pixel²) over the recovered image
    match_with_cover: bool  # True iff the server still has the original and they match


class BaseImageResponse(BaseModel):
    """Returned by GET /api/base-image."""
    image: str          # base64-encoded PNG of the predetermined base image
    shape: list[int]    # [height, width, channels]

