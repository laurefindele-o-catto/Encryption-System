"""
Phase 2 stub: Morse string -> ordered list of integer symbol states.
"""

from enum import IntEnum

class SymbolState(IntEnum):
    DOT = 0
    DASH = 1
    LETTER_GAP = 2
    WORD_GAP = 3
    
SYMBOL_MAP = {
    '.': SymbolState.DOT,
    '-': SymbolState.DASH,
    ' ': SymbolState.LETTER_GAP,
    '/': SymbolState.WORD_GAP,
}


def morse_to_symbol_sequence(morse: str) -> list[SymbolState]:
    """
    Direct character-by-character mapping of a Morse string (from
    text_to_morse) into SymbolState values, one per frame.
    """
    return [SYMBOL_MAP[ch] for ch in morse]