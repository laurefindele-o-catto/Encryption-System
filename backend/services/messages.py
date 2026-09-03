"""
Ephemeral server-side state for in-flight encrypted messages.

A single /api/encrypt call creates one entry here. The decrypt endpoint
looks the entry up by message_id, re-derives the same phase masks from the
(secret image digest, password, salt, message_id, frame_index) tuple, and
inverts the stored complex ciphertext.

Phase 2 will group multiple encrypted images under one message_id.
The structure below already supports that — each message holds a list of frames.
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
    secret_key_image: bytes | None = None
    secret_password: str | None = None
    salt: bytes | None = None
    receiver_secret_key_image: bytes | None = None
    receiver_password: str | None = None
    frames: list[Frame] = field(default_factory=list)


# In-memory store. Restarting the server clears it (intentional for the demo).
_messages: dict[str, Message] = {}

# Monotonic counter for unique message IDs.
_id_counter = itertools.count(1)


def new_message_id() -> str:
    return f"msg-{next(_id_counter):06d}"


def create_message(
    secret_key_image: bytes,
    secret_password: str,
    salt: bytes,
    message_id: str | None = None,
) -> Message:
    msg_id = message_id or new_message_id()
    msg = Message(
        message_id=msg_id,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        salt=salt,
    )
    _messages[msg_id] = msg
    return msg


def get_message(message_id: str) -> Message:
    if message_id not in _messages:
        raise KeyError(f"unknown message_id: {message_id}")
    return _messages[message_id]


def add_frame(message: Message, frame: Frame) -> None:
    message.frames.append(frame)


def get_frame(message: Message, frame_index: int) -> Frame:
    for frame in message.frames:
        if frame.frame_index == frame_index:
            return frame
    raise KeyError(f"unknown frame_index: {frame_index}")
