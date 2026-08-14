"""
Phase 2 stub: text -> Morse string (dots, dashes, intra/inter-letter
and inter-word gaps as a single flat string using sentinel characters).

NOT IMPLEMENTED in Phase 1. The signature is the planned Phase 2 contract.
"""


def text_to_morse(text: str) -> str:
    """
    Convert a plaintext string into a flat Morse sequence.

    Phase 2 will use a standard ITU Morse table, with intra-symbol gaps
    (e.g. ''), inter-letter gaps (e.g. ' '), and inter-word gaps
    (e.g. '/ ') as distinct separator characters.

    Args:
        text: any ASCII text (will be uppercased, non-alphanumerics skipped).

    Returns:
        A single string of '.' (dot), '-' (dash), and separator characters.

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("text_to_morse is a Phase 2 feature")
