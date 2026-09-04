"""
Phase 2: differential two-block-pair brightness encoding.

Every SymbolState is encoded as 2 bits, each from an independent block
pair swapping a FIXED +/-DELTA (never scaled by the state's numeric
value -- see design discussion for why that would leak state
information through total image energy).

    bit1 <- sign(mean(BLOCK_A) - mean(BLOCK_B))   pair swaps +/-DELTA
    bit2 <- sign(mean(BLOCK_C) - mean(BLOCK_D))   pair swaps +/-DELTA

    (+,+) -> DOT   (+,-) -> DASH   (-,+) -> LETTER_GAP   (-,-) -> WORD_GAP
"""

from __future__ import annotations

import numpy as np

from services.encoding.morse_to_symbol_sequence import SymbolState
from config import (
    BLOCK_A_COORDS, BLOCK_B_COORDS, BLOCK_C_COORDS, BLOCK_D_COORDS, BLOCK_SIZE, DELTA
)


# Fixed direction pattern per state -- magnitude is always DELTA, only
# which block goes up vs. down changes
STATE_TO_BITS = {
    SymbolState.DOT: (1,1),
    SymbolState.DASH: (1,-1),
    SymbolState.LETTER_GAP: (-1, 1),
    SymbolState.WORD_GAP: (-1, -1)
}

BITS_TO_STATE = {bits: state for state, bits in STATE_TO_BITS.items()}


# Extract Block A from a 2D base image array
# slices = _block_slice(BLOCK_A_COORDS)
# block_a_data = base_image[slices] 
# This is exactly equivalent to: base_image[10:26, 10:26]


def _block_slice(coords:tuple[int, int]) -> tuple[slice, slice]:
    row, col = coords
    return slice(row, row + BLOCK_SIZE), slice(col, col+BLOCK_SIZE)

def generate_symbol_image(
    state: SymbolState,
    base_image: np.ndarray,
) -> np.ndarray:
    """
    Overwrites (not offsets) the four block regions to BLOCK_BASE_VALUE
    +/- DELTA, so the encoded signal never depends on what the base
    image originally looked like at those coordinates.
    
    Args:
        state: one of the 4 SymbolState values from morse_to_symbol_sequence().
        base_image: 2D float64 -- the shared template image.

    Returns:
        2D float64 -- a copy of base_image with both block pairs
                      modified, ready to be passed into drpe_encrypt().

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    frame = base_image.copy()
    bit1, bit2 = STATE_TO_BITS[state]
    
    a_rows, a_cols = _block_slice(BLOCK_A_COORDS)
    b_rows, b_cols = _block_slice(BLOCK_B_COORDS)
    c_rows, c_cols = _block_slice(BLOCK_C_COORDS)
    d_rows, d_cols = _block_slice(BLOCK_D_COORDS)
    
    block_base_value = int(base_image.mean())
    
    frame[a_rows, a_cols] = block_base_value + bit1 * DELTA
    frame[b_rows, b_cols] = block_base_value - bit1 * DELTA
    frame[c_rows, c_cols] = block_base_value + bit2 * DELTA
    frame[d_rows, d_cols] = block_base_value - bit2 * DELTA
    
    return frame

def read_differential_brightness(
    image: np.ndarray,
) -> SymbolState:
    """
    Inverse of generate_symbol_image(). Reads mean brightness in both
    block pairs and recovers the SymbolState from the sign pattern.
    Args:
        image: 2D float64 — a DRPE-decrypted image (the output of
               drpe_decrypt()).

    Returns:
        int — the recovered symbol state.

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    
    a_rows, a_cols = _block_slice(BLOCK_A_COORDS)
    b_rows, b_cols = _block_slice(BLOCK_B_COORDS)
    c_rows, c_cols = _block_slice(BLOCK_C_COORDS)
    d_rows, d_cols = _block_slice(BLOCK_D_COORDS)
    
    bit1 = 1 if image[a_rows, a_cols].mean() > image[b_rows, b_cols].mean() else -1
    bit2 = 1 if image[c_rows, c_cols].mean() > image[d_rows, d_cols].mean() else -1

    return BITS_TO_STATE[(bit1, bit2)]
