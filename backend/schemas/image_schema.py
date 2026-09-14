"""
Pydantic request/response shapes for the image encryption API.
"""

from pydantic import BaseModel


class ImageResponse(BaseModel):
    """Base64-encoded PNG of a single 2D image."""
    image: str  # base64-encoded PNG


class EncryptResponse(BaseModel):
    """Returned by POST /api/encrypt."""
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


class TextFramePreview(BaseModel):
    """Optional display-only preview for one encrypted text frame."""
    frame_index: int
    image: str
    energy: float


class TextEncryptResponse(BaseModel):
    """Returned by POST /api/text/encrypt."""
    message_id: str
    salt_b64: str
    morse: str
    symbols: list[int]
    frame_count: int
    base_image_shape: list[int]
    previews: list[TextFramePreview] = []


class TextDecryptedFrame(BaseModel):
    """Per-frame diagnostic information returned during text decryption."""
    frame_index: int
    symbol: int
    symbol_name: str


class TextDecryptResponse(BaseModel):
    """Returned by POST /api/text/decrypt."""
    message_id: str
    text: str
    morse: str
    symbols: list[int]
    frame_count: int
    success: bool
    image: str | None = None
    frames: list[TextDecryptedFrame] = []


class BasicEnergyFramePreview(BaseModel):
    """Preview info for basic energy encrypted frame."""
    frame_index: int
    image: str
    energy: float
    symbol: int
    symbol_name: str


class BasicEnergyEncryptResponse(BaseModel):
    """Returned by POST /api/text/basic-energy/encrypt."""
    message_id: str
    salt_b64: str
    morse: str
    symbols: list[int]
    frame_count: int
    base_image_shape: list[int]
    thresholds: list[float] = []
    energy_levels: list[float] = []
    previews: list[BasicEnergyFramePreview] = []


class BasicEnergyDecryptedFrame(BaseModel):
    """Per-frame diagnostic returned during normal DRPE decryption."""
    frame_index: int
    symbol: int
    symbol_name: str


class BasicEnergyDecryptResponse(BaseModel):
    """Returned by POST /api/text/basic-energy/decrypt."""
    message_id: str
    text: str
    morse: str
    symbols: list[int]
    frame_count: int
    success: bool
    image: str | None = None
    frames: list[BasicEnergyDecryptedFrame] = []


class BasicEnergyPredictedFrame(BaseModel):
    """Per-frame energy prediction detail."""
    frame_index: int
    energy: float
    predicted_symbol: int
    symbol_name: str


class BasicEnergyPredictResponse(BaseModel):
    """Returned by POST /api/text/basic-energy/predict (Zero Decryption)."""
    message_id: str
    predicted_text: str
    predicted_morse: str
    predicted_symbols: list[int]
    frame_count: int
    thresholds: list[float] = []
    energy_levels: list[float] = []
    frame_energies: list[float] = []
    frames: list[BasicEnergyPredictedFrame] = []
    success: bool
    bypassed_decryption: bool = True



