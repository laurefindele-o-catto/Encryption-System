"""
Phase 2 stub: Morse string -> ordered list of integer symbol states.

NOT IMPLEMENTED in Phase 1. The signature is the planned Phase 2 contract.
"""


def morse_to_symbol_sequence(morse: str) -> list[int]:
    """
    Map a flat Morse string into an ordered list of integer states,
    one per image to be generated. The integer values correspond to
    the differential-brightness patterns the encoder will apply.

    Planned mapping (from the spec):
        dot (.)         -> state 0  (Block A +Δ, Block B -Δ)
        dash (-)        -> state 1  (Block A -Δ, Block B +Δ)
        intra-letter '' -> state 2  (no change; placeholder image)
        inter-letter ' '-> state 3  (no change; placeholder image)
        inter-word '/'  -> state 4  (no change; placeholder image)

    Args:
        morse: output of text_to_morse().

    Returns:
        List[int] of length == number of images to be transmitted.

    Raises:
        NotImplementedError: always, in Phase 1.
    """
    raise NotImplementedError("morse_to_symbol_sequence is a Phase 2 feature")
