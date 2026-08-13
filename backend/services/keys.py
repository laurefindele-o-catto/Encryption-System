"""
Per-frame key derivation.

The analysis report flagged sequential seeds (base_seed + N) as a
vulnerability: recovering one frame's key reveals every other key via a
fixed linear offset. This replaces that with a one-way hash, so knowing
key_5 reveals nothing about key_6.
"""

import hashlib


def derive_key(base_seed: str, frame_index: int) -> int:
    """
    Deterministically derive a per-frame integer seed from a shared base
    secret and the frame's position in the sequence. Both sender and
    receiver call this the same way, so they always agree on the seed
    without ever transmitting it.
    """
    raw = f"{base_seed}:{frame_index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)
