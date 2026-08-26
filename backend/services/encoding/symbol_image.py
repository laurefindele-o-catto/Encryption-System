"""
Phase 2 stub: per-state differential two-block brightness encoding.

NOT IMPLEMENTED in Phase 1. The signatures are the planned Phase 2 contract.

The encoding uses BLOCK_A_COORDS, BLOCK_B_COORDS, BLOCK_SIZE, and DELTA
from backend/config.py as the single source of truth.
"""

from __future__ import annotations

import numpy as np


def generate_symbol_image(
    state: dict,
    base_image: np.ndarray,
) -> np.ndarray:
    """
    Build a single image ready to be DRPE-encrypted, encoding a timed Morse
    symbol `state` via differential brightness on two predetermined blocks.

    From the spec:
        if state["polarity"] == "tone": Block A +k·DELTA, Block B -k·DELTA
        if state["polarity"] == "silence": Block A -k·DELTA, Block B +k·DELTA
        linear cross-term cancels (2kΔ(S_A - S_B) = 0), leaving only the
        small bounded quadratic residual 2·N·(k·DELTA)^2.

    Args:
        state: dict from morse_to_symbol_sequence() containing 'polarity', 'k', and 'kind'.
        base_image: float64 ndarray — the shared template image.

    Returns:
        float64 ndarray — a copy of base_image with the block modifications
                          applied, ready to be passed into drpe_encrypt().

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("generate_symbol_image is a Phase 2 feature")


def read_differential_brightness(
    image: np.ndarray,
) -> dict:
    """
    Inverse of generate_symbol_image(). After a DRPE-decrypted image
    comes back, read the mean brightness in Block A and Block B, and extract:
        sign = sign(mean(A) - mean(B))
        k = round(|mean(A) - mean(B)| / (2 * DELTA))

    Args:
        image: float64 ndarray — a DRPE-decrypted image (the output of
               drpe_decrypt()).

    Returns:
        dict — recovered symbol descriptor: {"polarity": "tone" | "silence", "k": int, "kind": str}

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("read_differential_brightness is a Phase 2 feature")

