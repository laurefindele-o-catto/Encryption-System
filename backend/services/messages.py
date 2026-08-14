"""
Ephemeral server-side state for in-flight encrypted messages.

Phase 1: a single /api/encrypt call creates one entry here. The
/api/decrypt endpoint looks the entry up by message_id, re-derives
the same phase masks from the (seed, base_image, frame_index) triple,
and inverts the complex ciphertext that we couldn't safely send
through a PNG.

Phase 2 will group multiple encrypted images under one message_id
(a whole Morse sequence = one transmission). The structure below
already supports that — each message holds a list of frames.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Frame:
    """One encrypted image within a message."""
    frame_index: int
    ciphertext_complex: np.ndarray  # complex128
    amplitude: np.ndarray          # float64, the noise-like display image


@dataclass
class Message:
    """A logical transmission. Phase 1 always has exactly one frame."""
    message_id: str
    base_image: np.ndarray
    seed_p1: str
    seed_p2: str
    frames: list[Frame] = field(default_factory=list)


# In-memory store. Restarting the server clears it (intentional for the demo).
_messages: dict[str, Message] = {}

# Monotonic counter for unique message IDs.
_id_counter = itertools.count(1)


def new_message_id() -> str:
    return f"msg-{next(_id_counter):06d}"


def create_message(seed_p1: str, seed_p2: str, base_image: np.ndarray) -> Message:
    msg_id = new_message_id()
    msg = Message(message_id=msg_id, base_image=base_image, seed_p1=seed_p1, seed_p2=seed_p2)
    _messages[msg_id] = msg
    return msg


def get_message(message_id: str) -> Message:
    if message_id not in _messages:
        raise KeyError(f"unknown message_id: {message_id}")
    return _messages[message_id]


def add_frame(message: Message, frame: Frame) -> None:
    message.frames.append(frame)
