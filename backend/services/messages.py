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


IMAGE_MESSAGE = "image"
TEXT_MESSAGE = "text"


@dataclass
class Frame:
    """One encrypted image within a message."""
    frame_index: int
    ciphertext_complex: np.ndarray  # complex128
    amplitude: np.ndarray          # float64, the noise-like display image


@dataclass
class Message:
    """A logical image or text transmission containing ordered frames."""
    message_id: str
    message_type: str = IMAGE_MESSAGE
    secret_key_image: bytes | None = None
    secret_password: str | None = None
    salt: bytes | None = None
    base_image: np.ndarray | None = None
    total_frames: int | None = None
    metadata: dict = field(default_factory=dict)
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
    message_type: str = IMAGE_MESSAGE,
    base_image: np.ndarray | None = None,
    total_frames: int | None = None,
    metadata: dict | None = None,
) -> Message:
    if message_type not in {IMAGE_MESSAGE, TEXT_MESSAGE}:
        raise ValueError(f"unsupported message_type: {message_type}")

    msg_id = message_id or new_message_id()
    if msg_id in _messages:
        raise ValueError(f"message_id already exists: {msg_id}")

    msg = Message(
        message_id=msg_id,
        message_type=message_type,
        secret_key_image=secret_key_image,
        secret_password=secret_password,
        salt=salt,
        base_image=base_image,
        total_frames=total_frames,
        metadata=metadata or {},
    )
    _messages[msg_id] = msg
    return msg


def get_message(message_id: str) -> Message:
    if message_id not in _messages:
        raise KeyError(f"unknown message_id: {message_id}")
    return _messages[message_id]


def add_frame(message: Message, frame: Frame) -> None:
    if frame.frame_index < 0:
        raise ValueError("frame_index must be non-negative")
    if any(existing.frame_index == frame.frame_index for existing in message.frames):
        raise ValueError(f"duplicate frame_index: {frame.frame_index}")
    if message.total_frames is not None and frame.frame_index >= message.total_frames:
        raise ValueError(f"frame_index exceeds total_frames: {frame.frame_index}")
    message.frames.append(frame)


def get_frame(message: Message, frame_index: int) -> Frame:
    for frame in message.frames:
        if frame.frame_index == frame_index:
            return frame
    raise KeyError(f"unknown frame_index: {frame_index}")


def get_ordered_frames(message: Message, require_complete: bool = False) -> list[Frame]:
    """Return frames in frame-index order, optionally requiring 0..N-1."""
    ordered = sorted(message.frames, key=lambda frame: frame.frame_index)
    if require_complete:
        expected = message.total_frames
        if expected is None:
            expected = len(ordered)
        actual_indices = [frame.frame_index for frame in ordered]
        if actual_indices != list(range(expected)):
            raise ValueError("message frames are missing or out of order")
    return ordered


def get_messages(message_type: str | None = None) -> list[Message]:
    """Return stored messages, optionally filtered by image or text type."""
    messages = list(_messages.values())
    if message_type is None:
        return messages
    if message_type not in {IMAGE_MESSAGE, TEXT_MESSAGE}:
        raise ValueError(f"unsupported message_type: {message_type}")
    return [message for message in messages if message.message_type == message_type]
