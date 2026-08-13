from fastapi import HTTPException, UploadFile

from schemas.image_schema import ImageResponse
from services.crypto import decrypt_image, encrypt_image
from services.image_utils import array_to_base64, file_to_array
from services.state import state


async def encrypt_controller(cover_image: UploadFile, key_image: UploadFile, x: int, y: int) -> ImageResponse:
    """
    Sender side. Reads the two uploaded images, stores everything in
    state, runs encrypt_image(), and returns the encrypted image.
    """
    cover_arr = await file_to_array(cover_image)
    key_arr = await file_to_array(key_image)
    coord = (x, y)

    state["cover_image"] = cover_arr
    state["key_image"] = key_arr
    state["coord"] = coord

    try:
        encrypted = encrypt_image(cover_arr, key_arr, coord)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    state["encrypted_image"] = encrypted
    return ImageResponse(image=array_to_base64(encrypted))


def get_encrypted_image_controller() -> ImageResponse:
    """
    Receiver side. Returns whatever encrypted image is currently sitting
    in state, as if it had just arrived over the wire.
    """
    if state["encrypted_image"] is None:
        raise HTTPException(status_code=404, detail="No encrypted image available yet")
    return ImageResponse(image=array_to_base64(state["encrypted_image"]))


async def decrypt_controller(key_image: UploadFile) -> ImageResponse:
    """
    Receiver side. Combines the uploaded key image with whatever
    encrypted image + coord is currently in state, and returns the
    recovered original image.
    """
    if state["encrypted_image"] is None or state["coord"] is None:
        raise HTTPException(status_code=400, detail="No encrypted image to decrypt yet")

    key_arr = await file_to_array(key_image)

    try:
        decrypted = decrypt_image(state["encrypted_image"], key_arr, state["coord"])
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

    state["decrypted_image"] = decrypted
    return ImageResponse(image=array_to_base64(decrypted))
