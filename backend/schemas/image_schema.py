from pydantic import BaseModel


class ImageResponse(BaseModel):
    image: str  # base64-encoded PNG
