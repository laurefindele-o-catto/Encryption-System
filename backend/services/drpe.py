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


# --- Mask generation -------------------------------------------------------

def mask_seed(material: bytes) -> int:
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:16], "big")


def generate_phase_masks(
    shape: tuple[int, ...],
    p1_material: bytes,
    p2_material: bytes,
) -> tuple[np.ndarray, np.ndarray]:
    rng_p1 = np.random.default_rng(mask_seed(p1_material))
    rng_p2 = np.random.default_rng(mask_seed(p2_material))

    p1 = rng_p1.uniform(
        0.0,
        2.0 * np.pi,
        size=shape,
    ).astype(np.float64)

    p2 = rng_p2.uniform(
        0.0,
        2.0 * np.pi,
        size=shape,
    ).astype(np.float64)

    return p1, p2
    

# --- Encrypt / decrypt -----------------------------------------------------

def drpe_encrypt(
    cover_image: np.ndarray,
    p1_material: bytes,
    p2_material: bytes,
) -> dict:
    """
    Returns:
        dict with keys:
            "complex"     — complex128 ndarray, the full complex ciphertext.
            "amplitude"   — float64 ndarray, |complex|, the exact magnitude image
                            |DRPE(cover)| produced after complex rotation.
            "p1", "p2"    — float64 ndarrays, the phase masks used.
    """
    p1, p2 = generate_phase_masks(
        cover_image.shape,
        p1_material,
        p2_material,
    )

    # 1. Apply spatial phase mask P1 to cover image (complex rotation in spatial domain)
    cover_spatial = cover_image * np.exp(1j * p1)
    # 2. 2D Fourier transform to frequency domain across spatial dimensions
    g = np.fft.fft2(cover_spatial, axes=(0, 1))
    # 3. Apply frequency phase mask P2 (complex rotation in Fourier plane)
    g_prime = g * np.exp(1j * p2)
    # 4. 2D Inverse Fourier transform back to spatial domain -> complex ciphertext c
    c = np.fft.ifft2(g_prime, axes=(0, 1))

    return {
        "complex": c.astype(np.complex128),
        "amplitude": np.abs(c).astype(np.float64),
        "p1": p1,
        "p2": p2,
    }


def drpe_decrypt(
    ciphertext_complex: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
) -> np.ndarray:
    """
    Reverse drpe_encrypt() given the COMPLEX ciphertext and the phase masks (p1, p2).

    P1 and P2 come directly from the caller (frontend) as float64 arrays without
    being regenerated inside drpe.py.

    Args:
        ciphertext_complex: complex128 ndarray from drpe_encrypt()["complex"].
        p1: float64 ndarray — spatial domain phase mask P1.
        p2: float64 ndarray — frequency domain phase mask P2.

    Returns:
        float64 ndarray — the recovered cover image.
    """
    # 1. 2D Fourier transform of complex ciphertext (spatial -> frequency)
    g_prime = np.fft.fft2(ciphertext_complex, axes=(0, 1))
    # 2. Remove frequency phase mask P2
    g = g_prime * np.exp(-1j * p2)
    # 3. 2D Inverse Fourier transform to spatial domain
    cover_spatial = np.fft.ifft2(g, axes=(0, 1))
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

