"""
Single source of truth for shared constants.

Both sender-side and receiver-side code MUST import from here, never
hardcode these values inline. This is the contract between endpoints.

Phase 2 placeholders (BLOCK_A_COORDS, BLOCK_B_COORDS, DELTA) are listed
here now so the differential-brightness module can drop in later without
touching business logic.
"""

import os

# --- Path / filesystem -----------------------------------------------------

# backend/ is the project root for the Python package; this file is at
# backend/config.py, so the data directory lives at backend/data/.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_BACKEND_DIR, "data")

# --- Demo defaults ---------------------------------------------------------

DEFAULT_SEED = "phase1-demo"

# --- Phase 2 placeholders (intentionally unused in Phase 1) ----------------
# The future module services/encoding/symbol_image.py will use these.
# Both sender and receiver must agree on the same values; config.py is the
# only place they should be defined.

# Top-left pixel of block A (row, col) on the base image.
BLOCK_A_COORDS = (10, 10)
# Top-left pixel of block B (row, col) on the base image.
BLOCK_B_COORDS = (10, 50)
# Per-block edge length in pixels.
BLOCK_SIZE = 16
# Brightness delta applied to each block (net change across both blocks = 0).
DELTA = 8
