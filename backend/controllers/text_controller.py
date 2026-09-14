"""Controller for Alice's Phase 2 text-encryption request."""

from __future__ import annotations

import base64

from fastapi import HTTPException, UploadFile

from schemas.image_schema import (
    BasicEnergyDecryptResponse,
    BasicEnergyDecryptedFrame,
    BasicEnergyEncryptResponse,
    BasicEnergyFramePreview,
    BasicEnergyPredictResponse,
    BasicEnergyPredictedFrame,
    TextDecryptResponse,
    TextDecryptedFrame,
    TextEncryptResponse,
    TextFramePreview,
)
from services.basic_energy_service import (
    decrypt_basic_morse_normal,
    encrypt_basic_morse_message,
    predict_basic_morse_from_energy,
)
from services.image_utils import file_to_array
from services.text_decryption import decrypt_text_message
from services.text_encryption import encrypt_text_message


async def encrypt_text_controller(
    secret_text: str,
    base_image: UploadFile,
    secret_key_image: UploadFile,
    secret_password: str,
) -> TextEncryptResponse:
    """Read Alice's uploads and create a stored encrypted text message."""
    try:
        base_image_array = await file_to_array(base_image, target_shape=None)
        key_image_bytes = await secret_key_image.read()
        result = encrypt_text_message(
            secret_text=secret_text,
            base_image=base_image_array,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
            include_previews=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Text encryption failed: {exc}") from exc

    previews = [TextFramePreview(**preview) for preview in result["previews"]]
    return TextEncryptResponse(
        message_id=result["message_id"],
        salt_b64=base64.b64encode(result["salt"]).decode("ascii"),
        morse=result["morse"],
        symbols=result["symbols"],
        frame_count=result["frame_count"],
        base_image_shape=result["base_image_shape"],
        previews=previews,
    )


async def decrypt_text_controller(
    message_id: str,
    secret_key_image: UploadFile,
    secret_password: str,
) -> TextDecryptResponse:
    """Read Bob's uploads and decrypt the stored text message frames."""
    try:
        key_image_bytes = await secret_key_image.read()
        result = decrypt_text_message(
            message_id=message_id,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Text decryption failed: {exc}") from exc

    frames = [TextDecryptedFrame(**frame) for frame in result["frames"]]
    return TextDecryptResponse(
        message_id=result["message_id"],
        text=result["text"],
        morse=result["morse"],
        symbols=result["symbols"],
        frame_count=result["frame_count"],
        success=result["success"],
        image=result.get("image"),
        frames=frames,
    )


async def encrypt_basic_energy_controller(
    secret_text: str,
    base_image: UploadFile,
    secret_key_image: UploadFile,
    secret_password: str,
) -> BasicEnergyEncryptResponse:
    """Encrypt secret text using basic Morse image energy modulation."""
    try:
        base_image_array = await file_to_array(base_image, target_shape=None)
        key_image_bytes = await secret_key_image.read()
        result = encrypt_basic_morse_message(
            secret_text=secret_text,
            base_image=base_image_array,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
            include_previews=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Basic energy encryption failed: {exc}") from exc

    previews = [BasicEnergyFramePreview(**preview) for preview in result["previews"]]
    return BasicEnergyEncryptResponse(
        message_id=result["message_id"],
        salt_b64=result["salt_b64"],
        morse=result["morse"],
        symbols=result["symbols"],
        frame_count=result["frame_count"],
        base_image_shape=result["base_image_shape"],
        thresholds=result["thresholds"],
        energy_levels=result["energy_levels"],
        previews=previews,
    )


async def decrypt_basic_energy_controller(
    message_id: str,
    secret_key_image: UploadFile,
    secret_password: str,
) -> BasicEnergyDecryptResponse:
    """Normal DRPE decryption path with Bob's key image and password."""
    try:
        key_image_bytes = await secret_key_image.read()
        result = decrypt_basic_morse_normal(
            message_id=message_id,
            secret_key_image=key_image_bytes,
            secret_password=secret_password,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Basic energy normal decryption failed: {exc}") from exc

    frames = [BasicEnergyDecryptedFrame(**frame) for frame in result["frames"]]
    return BasicEnergyDecryptResponse(
        message_id=result["message_id"],
        text=result["text"],
        morse=result["morse"],
        symbols=result["symbols"],
        frame_count=result["frame_count"],
        success=result["success"],
        image=result.get("image"),
        frames=frames,
    )


async def predict_basic_energy_controller(
    message_id: str,
) -> BasicEnergyPredictResponse:
    """Zero-decryption side-channel path predicting Morse directly from ciphertext energy."""
    try:
        result = predict_basic_morse_from_energy(message_id=message_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Basic energy prediction failed: {exc}") from exc

    frames = [BasicEnergyPredictedFrame(**frame) for frame in result["frames"]]
    return BasicEnergyPredictResponse(
        message_id=result["message_id"],
        predicted_text=result["predicted_text"],
        predicted_morse=result["predicted_morse"],
        predicted_symbols=result["predicted_symbols"],
        frame_count=result["frame_count"],
        thresholds=result["thresholds"],
        energy_levels=result["energy_levels"],
        frame_energies=result["frame_energies"],
        frames=frames,
        success=result["success"],
        bypassed_decryption=result["bypassed_decryption"],
    )