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

from config import BASE_IMAGE_PATH, DEFAULT_BASE_IMAGE_SIZE

# Fixed seed for the fallback synthesis. Stable, arbitrary, memorable.
# Change it ONLY if you also rotate the on-disk base_image.png, so
# sender and receiver still agree.
_SYNTH_SEED = 20240801

_cached: np.ndarray | None = None


def _load_or_synthesize() -> np.ndarray:
    if os.path.exists(BASE_IMAGE_PATH):
        img = Image.open(BASE_IMAGE_PATH).convert("RGB")
        return np.array(img, dtype=np.float64)

    # Synthesize a deterministic noise pattern; write it to disk so the
    # next process boot sees the same bytes.
    rng = np.random.default_rng(_SYNTH_SEED)
    arr = rng.uniform(0, 255, size=(DEFAULT_BASE_IMAGE_SIZE, DEFAULT_BASE_IMAGE_SIZE, 3))
    os.makedirs(os.path.dirname(BASE_IMAGE_PATH), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8)).save(BASE_IMAGE_PATH, format="PNG")
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

