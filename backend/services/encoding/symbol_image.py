"""
Phase 2 stub: per-state differential two-block brightness encoding.

NOT IMPLEMENTED in Phase 1. The signatures are the planned Phase 2 contract.

The encoding uses BLOCK_A_COORDS, BLOCK_B_COORDS, BLOCK_SIZE, and DELTA
from backend/config.py as the single source of truth.
"""

from __future__ import annotations

import numpy as np


def generate_symbol_image(
    state: int,
    base_image: np.ndarray,
) -> np.ndarray:
    """
    Build a single image ready to be DRPE-encrypted, encoding `state`
    via differential brightness on two predetermined blocks.

    From the spec:
        if state maps to symbol-type-1: Block A +Δ, Block B -Δ
        if state maps to symbol-type-2: Block A -Δ, Block B +Δ
        net energy change across the full image = 0 (Parseval-safe)

    Args:
        state: integer from morse_to_symbol_sequence().
        base_image: 2D float64 — the shared template image.

    Returns:
        2D float64 — a copy of base_image with the block modifications
                     applied, ready to be passed into drpe_encrypt().

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("generate_symbol_image is a Phase 2 feature")


def read_differential_brightness(
    image: np.ndarray,
) -> int:
    """
    Inverse of generate_symbol_image(). After a DRPE-decrypted image
    comes back, read the mean brightness in Block A and Block B and
    return sign(Brightness(A) - Brightness(B)) as the recovered state.

    Args:
        image: 2D float64 — a DRPE-decrypted image (the output of
               drpe_decrypt()).

    Returns:
        int — the recovered symbol state.

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("read_differential_brightness is a Phase 2 feature")
