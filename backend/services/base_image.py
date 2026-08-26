"""
Predetermined base/reference image used as part of the key scheme.

The project contract: "seed N -> key N" is implemented as
    derive_key(base_seed, frame_index)
which in turn is mixed with a hash of this base image (see drpe.py).
So both sender and receiver MUST use the same base image.

We cache the loaded image in memory; on first call we either:
  1. Load from BASE_IMAGE_PATH if a PNG exists on disk, OR
  2. Synthesize a deterministic 2D pattern (seeded noise) of the
     configured size, save it to disk for the next process, and return it.

Option 2 means the demo "just works" on a fresh checkout without anyone
having to ship a base image in the repo.
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image

from config import (
    BASE_IMAGE_PATH,
    BLOCK_A_COORDS,
    BLOCK_B_COORDS,
    BLOCK_SIZE,
    DEFAULT_BASE_IMAGE_SIZE,
    DELTA,
)

# Fixed seed for the fallback synthesis. Stable, arbitrary, memorable.
# Change it ONLY if you also rotate the on-disk base_image.png, so
# sender and receiver still agree.
_SYNTH_SEED = 20240801

_cached: np.ndarray | None = None


def _load_or_synthesize() -> np.ndarray:
    if os.path.exists(BASE_IMAGE_PATH):
        img = Image.open(BASE_IMAGE_PATH).convert("RGB")
        return np.array(img, dtype=np.float64)

    # Synthesize a deterministic noise pattern with equalized block means.
    rng = np.random.default_rng(_SYNTH_SEED)
    arr = rng.uniform(60.0, 195.0, size=(DEFAULT_BASE_IMAGE_SIZE, DEFAULT_BASE_IMAGE_SIZE, 3)).astype(np.float64)

    # Deterministic block mean equalization for Phase 2 energy-invariance precondition:
    ra, ca = BLOCK_A_COORDS
    rb, cb = BLOCK_B_COORDS
    sz = BLOCK_SIZE

    block_a = arr[ra : ra + sz, ca : ca + sz, :]
    block_b = arr[rb : rb + sz, cb : cb + sz, :]

    # Calculate per-channel difference: mean(A) - mean(B)
    diff = np.mean(block_a, axis=(0, 1)) - np.mean(block_b, axis=(0, 1))
    # Adjust Block B to equalize means across all channels exactly
    arr[rb : rb + sz, cb : cb + sz, :] += diff

    # Ensure clipping headroom [7*DELTA, 255 - 7*DELTA] is preserved for all pixels
    margin = 7 * DELTA
    arr = np.clip(arr, margin, 255.0 - margin)

    os.makedirs(os.path.dirname(BASE_IMAGE_PATH), exist_ok=True)
    Image.fromarray(np.round(arr).astype(np.uint8)).save(BASE_IMAGE_PATH, format="PNG")
    return arr



def get_base_image() -> np.ndarray:
    """
    Return the cached float64 RGB base image.
    """
    global _cached
    if _cached is None:
        _cached = _load_or_synthesize()
    return _cached


def base_image_shape() -> tuple[int, ...]:
    return get_base_image().shape

