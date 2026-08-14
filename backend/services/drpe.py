"""
Double Random Phase Encryption (DRPE) — classical 4-f optical system.

All functions are pure: no I/O, no global state. They take ndarrays
(grayscale, float64, shape (H, W)) and return ndarrays. Test from a
shell without involving FastAPI.

Math (4-f DRPE, classical):
    Encrypt:
        s  = cover * exp(j * P1)         # P1 in spatial domain (input plane)
        G  = FFT2(s)
        G' = G * exp(j * P2)             # P2 in frequency domain (Fourier plane)
        c  = IFFT2(G')                   # complex ciphertext
        amplitude = |c|                  # spatial magnitude image (|DRPE(cover)|)

    Decrypt (given the same P1, P2 + the COMPLEX ciphertext):
        G' = FFT2(ciphertext_complex)
        G  = G' * exp(-j * P2)           # remove frequency phase mask
        s  = IFFT2(G)
        cover_recovered = real(s * exp(-j * P1))  # remove spatial phase mask
"""

from __future__ import annotations

import hashlib

import numpy as np

from services.keys import derive_key


# --- Mask generation -------------------------------------------------------

def _shape_seed(base_image: np.ndarray, frame_index: int, shape: tuple[int, int] | None = None) -> bytes:
    """
    A base-image-aware seed blob. We hash the base image and target shape so that two
    different base images or shapes with the same input seed produce different phase masks.
    """
    shape_bytes = (shape[0].to_bytes(4, "big") + shape[1].to_bytes(4, "big")) if shape else b""
    digest = hashlib.sha256(base_image.tobytes() + shape_bytes).digest()[:8]
    return digest + int(frame_index).to_bytes(8, "big", signed=False)


def generate_phase_masks(
    shape: tuple[int, int],
    base_image: np.ndarray,
    seed_p1: str,
    seed_p2: str,
    frame_index: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Deterministically generate P1 and P2 given a (base image, seed_p1, seed_p2, frame index).

    Both masks are uniform in [0, 2π) and shape-matched to the cover image.
    P1 is derived from seed_p1 (applied in spatial domain before FFT).
    P2 is derived from seed_p2 (applied in frequency domain after FFT).

    Returns:
        (P1, P2) — both shape `shape`, float64, values in [0, 2π).
    """
    blob = _shape_seed(base_image, frame_index, shape)
    blob_int = int.from_bytes(blob[:8], "big")

    # Generate P1 from seed_p1
    base_seed_1 = derive_key(seed_p1, frame_index)
    mixed_1 = base_seed_1 ^ blob_int ^ 0x50314D31  # XOR tag for P1
    rng_1 = np.random.default_rng(mixed_1)
    p1 = rng_1.uniform(0.0, 2.0 * np.pi, size=shape).astype(np.float64)

    # Generate P2 from seed_p2
    base_seed_2 = derive_key(seed_p2, frame_index)
    mixed_2 = base_seed_2 ^ blob_int ^ 0x50324D32  # XOR tag for P2
    rng_2 = np.random.default_rng(mixed_2)
    p2 = rng_2.uniform(0.0, 2.0 * np.pi, size=shape).astype(np.float64)

    return p1, p2


# --- Encrypt / decrypt -----------------------------------------------------

def drpe_encrypt(
    cover_image: np.ndarray,
    base_image: np.ndarray,
    seed_p1: str,
    seed_p2: str,
    frame_index: int = 0,
) -> dict:
    """
    Encrypt a grayscale cover image using DRPE with dual seeds (seed_p1, seed_p2).

    Args:
        cover_image: 2D float64 ndarray — the image to encrypt.
        base_image:  2D float64 ndarray — the predetermined base/reference image
                     (used as part of key derivation).
        seed_p1:     str — seed for spatial domain phase mask P1.
        seed_p2:     str — seed for frequency domain phase mask P2.
        frame_index: int — index of this image within a multi-image message.

    Returns:
        dict with keys:
            "complex"     — complex128 ndarray, the full complex ciphertext.
            "amplitude"   — float64 ndarray, |complex|, the exact magnitude image
                            |DRPE(cover)| produced after complex rotation.
            "p1", "p2"    — float64 ndarrays, the phase masks used.
    """
    p1, p2 = generate_phase_masks(cover_image.shape, base_image, seed_p1, seed_p2, frame_index)

    # 1. Apply spatial phase mask P1 to cover image (complex rotation in spatial domain)
    cover_spatial = cover_image * np.exp(1j * p1)
    # 2. Fourier transform to frequency domain
    g = np.fft.fft2(cover_spatial)
    # 3. Apply frequency phase mask P2 (complex rotation in Fourier plane)
    g_prime = g * np.exp(1j * p2)
    # 4. Inverse Fourier transform back to spatial domain -> complex ciphertext c
    c = np.fft.ifft2(g_prime)

    return {
        "complex": c.astype(np.complex128),
        "amplitude": np.abs(c).astype(np.float64),
        "p1": p1,
        "p2": p2,
    }


def drpe_decrypt(
    ciphertext_complex: np.ndarray,
    base_image: np.ndarray,
    seed_p1: str,
    seed_p2: str,
    frame_index: int = 0,
) -> np.ndarray:
    """
    Reverse drpe_encrypt() given the COMPLEX ciphertext and the dual keys (seed_p1, seed_p2).

    Args:
        ciphertext_complex: complex128 ndarray from drpe_encrypt()["complex"].
        base_image:  2D float64 — the same base image used at encryption.
        seed_p1:     str — seed for phase mask P1.
        seed_p2:     str — seed for phase mask P2.
        frame_index: int — same frame index.

    Returns:
        2D float64 — the recovered cover image.
    """
    p1, p2 = generate_phase_masks(ciphertext_complex.shape, base_image, seed_p1, seed_p2, frame_index)

    # 1. Fourier transform of complex ciphertext
    g_prime = np.fft.fft2(ciphertext_complex)
    # 2. Remove frequency phase mask P2
    g = g_prime * np.exp(-1j * p2)
    # 3. Inverse Fourier transform to spatial domain
    cover_spatial = np.fft.ifft2(g)
    # 4. Remove spatial phase mask P1 and extract real component
    cover = cover_spatial * np.exp(-1j * p1)

    return np.clip(np.round(cover.real), 0, 255)


def energy(image: np.ndarray) -> float:
    """
    Σ(pixel²) over the image — the Parseval-relevant quantity. Theoretically
    invariant between cover and DRPE ciphertext (up to display-side clipping).
    Useful as a sanity-check readout in the demo.
    """
    return float(np.sum(image.astype(np.float64) ** 2))
