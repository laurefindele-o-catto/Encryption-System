"""Morse string -> plaintext decoder."""

from __future__ import annotations

from services.encoding.text_to_morse import ITU_MORSE_TABLE

REVERSE_ITU_MORSE_TABLE = {v: k for k, v in ITU_MORSE_TABLE.items()}


def morse_to_text(morse: str) -> str:
    """
    Decode a flat Morse string back into plaintext, using the same
    separator conventions as text_to_morse().

    Letters within a word are separated by a single space (' ').
    Words are separated by a slash ('/').
    Unrecognized codes are mapped to '?'.

    Args:
        morse: output of text_to_morse() or reconstructed from symbol sequence.

    Returns:
        The decoded plaintext string in uppercase.
    """
    if not morse:
        return ""

    words = morse.split('/')
    decoded_words = []

    for word in words:
        if not word:
            continue
        letters = []
        for code in word.split(' '):
            if not code:
                continue
            letters.append(REVERSE_ITU_MORSE_TABLE.get(code, '?'))
        decoded_words.append(''.join(letters))

    return ' '.join(decoded_words)


def is_valid_morse(morse: str) -> bool:
    """Check if all tokens in a Morse string are recognized ITU Morse codes."""
    if not morse:
        return False
    words = morse.split('/')
    for word in words:
        if not word:
            continue
        for code in word.split(' '):
            if not code:
                continue
            if code not in REVERSE_ITU_MORSE_TABLE:
                return False
    return True

