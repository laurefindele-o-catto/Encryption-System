"""
Basic Morse code image encoding without differential block cancellation.

Encodes Morse symbols directly into image frames with an uncancelled brightness
offset, causing the total Parseval energy to vary monotonically with the symbol.
This provides:
1. Normal decryption: Decrypt with DRPE -> extract symbol from recovered brightness.
2. Energy bug side-channel: Predict symbol directly from ciphertext total energy
   without decrypting and without requiring keys or passwords.

Morse formatting conventions:
- Letters within a word are separated by a single space (' ').
- Words are separated by a slash ('/').
- Unrecognized codes are mapped to '?'.
"""

from __future__ import annotations

import numpy as np

from services.encoding.morse_to_symbol_sequence import (
    SymbolState,
    morse_to_symbol_sequence,
    symbol_sequence_to_morse,
)
from services.encoding.morse_to_text import is_valid_morse, morse_to_text
from services.encoding.text_to_morse import text_to_morse

# Default brightness offset step between symbol levels (0, 1, 2, 3)
ENERGY_OFFSET_STEP = 20.0

SYMBOL_NAMES = {
    SymbolState.DOT: "DOT",
    SymbolState.DASH: "DASH",
    SymbolState.LETTER_GAP: "LETTER_GAP",
    SymbolState.WORD_GAP: "WORD_GAP",
}


def encode_text_to_symbols(text: str) -> tuple[str, list[SymbolState]]:
    """Convert plaintext into standard ITU Morse code and symbol states."""
    morse = text_to_morse(text)
    symbols = morse_to_symbol_sequence(morse)
    return morse, symbols


def prepare_base_image_for_offset(
    base_image: np.ndarray,
    offset_step: float = ENERGY_OFFSET_STEP,
) -> np.ndarray:
    """Safely clamp the base image so adding up to 3*offset_step does not clip at 255."""
    max_headroom = 3.0 * offset_step
    return np.clip(np.asarray(base_image, dtype=np.float64), 0.0, 255.0 - max_headroom)


def generate_basic_symbol_image(
    symbol: int | SymbolState,
    base_image: np.ndarray,
    offset_step: float = ENERGY_OFFSET_STEP,
) -> np.ndarray:
    """
    Modulate base image with an uncancelled global intensity offset.
    State 0 (DOT)        -> offset 0
    State 1 (DASH)       -> offset +1 * offset_step
    State 2 (LETTER_GAP) -> offset +2 * offset_step
    State 3 (WORD_GAP)   -> offset +3 * offset_step
    """
    clamped_base = prepare_base_image_for_offset(base_image, offset_step)
    offset = float(symbol) * offset_step
    return np.clip(clamped_base + offset, 0.0, 255.0)


def compute_expected_energy_levels(
    base_image: np.ndarray,
    offset_step: float = ENERGY_OFFSET_STEP,
) -> tuple[list[float], list[float]]:
    """
    Compute the theoretical total energy for each symbol state (0..3)
    and the mid-point decision thresholds between consecutive levels.

    Returns:
        (energies, thresholds):
            energies: [E_dot, E_dash, E_letter_gap, E_word_gap]
            thresholds: 3 decision boundaries separating the 4 energy levels
    """
    clamped_base = prepare_base_image_for_offset(base_image, offset_step)
    energies = []
    for s in [SymbolState.DOT, SymbolState.DASH, SymbolState.LETTER_GAP, SymbolState.WORD_GAP]:
        frame = clamped_base + float(s) * offset_step
        energies.append(float(np.sum(frame ** 2)))

    thresholds = [
        (energies[i] + energies[i + 1]) / 2.0
        for i in range(len(energies) - 1)
    ]
    return energies, thresholds


def predict_symbol_from_energy(
    energy_val: float,
    thresholds: list[float],
) -> int:
    """Classify a ciphertext's Parseval energy into a symbol state (0, 1, 2, 3)."""
    if len(thresholds) < 3:
        raise ValueError("Expected 3 thresholds for 4 symbol states")
    if energy_val < thresholds[0]:
        return int(SymbolState.DOT)
    elif energy_val < thresholds[1]:
        return int(SymbolState.DASH)
    elif energy_val < thresholds[2]:
        return int(SymbolState.LETTER_GAP)
    else:
        return int(SymbolState.WORD_GAP)


def extract_symbol_from_decrypted_image(
    decrypted_image: np.ndarray,
    base_image: np.ndarray,
    offset_step: float = ENERGY_OFFSET_STEP,
) -> SymbolState:
    """
    Extract symbol state from a DRPE-decrypted image.
    Calculates brightness difference from baseline and quantizes to nearest SymbolState.
    """
    clamped_base = prepare_base_image_for_offset(base_image, offset_step)
    diff = float(decrypted_image.mean() - clamped_base.mean())
    estimated_k = diff / offset_step
    symbol_int = int(np.clip(np.round(estimated_k), 0, 3))
    return SymbolState(symbol_int)


def decode_symbols_to_morse_and_text(
    symbols: list[int | SymbolState],
) -> tuple[str, str, bool]:
    """
    Convert a list of symbol integers into Morse string and plaintext,
    matching the two-block differential technique implementation.
    The Morse string is reconstructed directly, and unrecognized codes
    are mapped to '?' by morse_to_text() via the ITU Morse table.
    """
    morse = symbol_sequence_to_morse([SymbolState(s) for s in symbols])
    text = morse_to_text(morse)
    success = is_valid_morse(morse)
    return morse, text, success
