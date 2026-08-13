"""
Fill these in yourself. The API layer (main.py) already calls these with
the right arguments and knows how to handle NotImplementedError, so you
can build/test the rest of the app before writing any encryption logic.

Both functions work on grayscale images as float numpy arrays.
"""

import numpy as np


def encrypt_image(cover_image: np.ndarray, key_image: np.ndarray, coord: tuple[int, int]) -> np.ndarray:
    """
    Encrypt `cover_image` using `key_image` as the key, and (optionally)
    `coord` as the secret hiding location.

    Args:
        cover_image: 2D numpy array (grayscale), the image to encrypt.
        key_image:   2D numpy array (grayscale), same shape as cover_image.
        coord:       (x, y) tuple, the secret coordinate.

    Returns:
        2D numpy array, the encrypted ("noise-like") image, same shape as input.
    """
    raise NotImplementedError("encrypt_image is not implemented yet")


def decrypt_image(encrypted_image: np.ndarray, key_image: np.ndarray, coord: tuple[int, int]) -> np.ndarray:
    """
    Decrypt `encrypted_image` using `key_image` as the key. Should exactly
    reverse encrypt_image() when given the same key_image and coord.

    Args:
        encrypted_image: 2D numpy array (grayscale), output of encrypt_image().
        key_image:       2D numpy array (grayscale), same shape as encrypted_image.
        coord:           (x, y) tuple, the secret coordinate.

    Returns:
        2D numpy array, the recovered original image.
    """
    raise NotImplementedError("decrypt_image is not implemented yet")
