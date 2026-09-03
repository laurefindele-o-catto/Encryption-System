# Phase 1 implementation brief

This project is a DRPE image encryption system built around image-derived secret material. The key requirement is that the security material is not a typed text password; it is derived from image files, both for the sender and for the receiver.

## 1. Objectives

Build a working encrypted-image workflow where:

- Alice uploads a cover image
- Alice uploads a secret key image
- Alice uploads a second password image
- the frontend derives a deterministic password string from the password image
- the backend derives the DRPE masks using that password plus the key image digest
- Bob uploads the same key-image pattern and the corresponding password image
- Bob decrypts the image and verifies the recovered result against the original cover

This is the actual active system architecture used by the codebase today.

## 2. Active contract

The system currently uses these form fields:

- `cover_image`
- `secret_key_image`
- `secret_password`
- optional `message_id`
- optional `frame_index`

The `secret_password` value is not a human-entered password in the UI. It is generated from a second uploaded image by hashing it using SHA-256 and sending the resulting hex string to the backend.

This model is already implemented in:

- `backend/services/keys.py`
- `backend/controllers/image_controller.py`
- `backend/routers/image_router.py`

## 3. Correct design decisions

### Image-derived key material

The key image is canonicalized and hashed before being used in the KDF. The password image is also reduced to a deterministic digest. These image-derived values are mixed with the message ID, salt, and frame index before the P1/P2 masks are generated.

### DRPE core

`backend/services/drpe.py` performs the actual Fourier-domain encryption/decryption. The project uses the standard 4-f DRPE pattern:

- multiply cover by `exp(j * P1)`
- FFT2
- multiply by `exp(j * P2)`
- IFFT2
- reverse the process during decryption

### Data model

The encrypted ciphertext is stored as a complex array and sent as Base64 metadata. The visual preview is the magnitude image created from the complex ciphertext.

## 4. Frontend requirements

The UI should not expose a free-form text password field. Instead, the interface should require:

- sender key image
- sender password image
- receiver key image
- receiver password image

The frontend derives `secret_password` internally from the password image before calling the backend API.

This is the correct behavior for the real project state and matches the backend contract.

## 5. Phase-2 status

Morse text encoding, symbol sequencing, and differential brightness modulation are not part of the current live implementation and should not be described as finished functionality. The repository remains in phase 1: encrypted image transport using image-derived secrets.

## 6. Final note

Any earlier prompt or summary that treats the project as a generic DRPE demo with a typed password is outdated. The repository's active logic and route contract are the source of truth.
