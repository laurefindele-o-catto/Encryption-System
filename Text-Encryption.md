# Phase 2 Text Encryption

## Status

The Alice-side text-encryption path is implemented. Bob's text decryption path is still pending and can be implemented independently against the contract below.

Phase 1 image encryption remains available through the existing image endpoint and UI flow.

## What Has Been Implemented

### Alice frontend

`frontend/src/pages/AlicePage.jsx` provides two transmission tabs:

- **Send image** keeps the Phase 1 workflow.
- **Send text** accepts secret text, a base RGB image, a secret key image, and a password.

The text form validates required inputs and sends one multipart request to:

```text
POST /api/text/encrypt
```

The frontend stores the returned message metadata in shared packet state. It does not send complex ciphertext through the browser.

### Message storage

`backend/services/messages.py` supports typed image and text messages in one in-memory registry:

- `message_type` is either `image` or `text`.
- A text message stores one base image and multiple ordered frames.
- Duplicate, negative, and out-of-range frame indices are rejected.
- `get_ordered_frames()` returns frames in index order and can require a complete sequence.
- Image and text messages use distinct message IDs and do not overwrite one another.

The store is process-local. Restarting the backend removes stored messages.

### Text encryption service

`backend/services/text_encryption.py` implements:

```text
secret text
  -> text_to_morse()
  -> morse_to_symbol_sequence()
  -> generate_symbol_image() for each symbol
  -> per-frame DRPE key derivation
  -> drpe_encrypt() for each frame
  -> ordered server-side frame storage
```

The password KDF runs once per message. Each frame receives distinct P1/P2 material through frame-index-bound HMAC derivation.

The current symbol states are:

- `DOT = 0`
- `DASH = 1`
- `LETTER_GAP = 2`
- `WORD_GAP = 3`

The symbol-image implementation uses four RGB block regions and encodes each state as a two-bit brightness pattern. The same base RGB image is copied for every frame.

### API files

- `backend/routers/text_router.py` defines `POST /api/text/encrypt`.
- `backend/controllers/text_controller.py` reads Alice's uploads and calls the service.
- `backend/schemas/image_schema.py` defines `TextEncryptResponse` and `TextFramePreview`.
- `backend/main.py` registers the text router.

## Sender API Contract

### Request

Multipart form fields:

```text
secret_text: string
base_image: image file
secret_key_image: image file
secret_password: string
```

### Response

```json
{
  "message_id": "msg-000001",
  "salt_b64": "...",
  "morse": ".-",
  "symbols": [0, 1],
  "frame_count": 2,
  "base_image_shape": [64, 64, 3],
  "previews": [
    {
      "frame_index": 0,
      "image": "...",
      "energy": 123.0
    }
  ]
}
```

`previews` contains small display-only PNGs. The actual complex ciphertext is stored in `Message.frames` and is not returned in the response.

## Bob Decryption Work Remaining

Add this endpoint:

```text
POST /api/text/decrypt
```

### Request fields

```text
message_id: string
secret_key_image: image file
secret_password: string
```

Bob does not upload the base image. Alice's base image is stored with the message as `message.base_image`.

### Required pipeline

1. Look up the message with `get_message(message_id)`.
2. Confirm `message.message_type == "text"`.
3. Retrieve frames using `get_ordered_frames(message, require_complete=True)`.
4. Read and canonicalize Bob's key image using the same `key_image_digest()` policy.
5. Derive the password key once with `derive_password_key(message_password, message.salt)`.
6. Derive the master key once with `derive_master_key(password_key, image_digest)`.
7. For every frame index, derive P1/P2 with:

   ```python
   derive_frame_key(master_key, message_id, frame_index, b"DRPE/P1")
   derive_frame_key(master_key, message_id, frame_index, b"DRPE/P2")
   ```

8. Generate phase masks with the stored frame ciphertext shape.
9. Call `drpe_decrypt()` on the stored complex ciphertext.
10. Call `read_differential_brightness()` on the recovered RGB image.
11. Convert ordered symbol states back to Morse.
12. Convert Morse to plaintext with `morse_to_text()`.

Wrong passwords or key images should result in an invalid/failed sequence, not silently accepted plaintext.

## Recommended Bob Response

```json
{
  "message_id": "msg-000001",
  "text": "A",
  "morse": ".-",
  "symbols": [0, 1],
  "frame_count": 2,
  "frames": [
    {
      "frame_index": 0,
      "symbol": 0,
      "valid": true
    }
  ]
}
```

Per-frame diagnostics may report invalid, ambiguous, missing, or corrupted frames. The response should not return complex ciphertext.

## Bob Files To Create Or Modify

- `backend/services/text_decryption.py`
  - decrypt frames and reconstruct the text sequence
- `backend/controllers/text_controller.py`
  - add a receiver controller, or create a separate decryption controller
- `backend/routers/text_router.py`
  - add `POST /api/text/decrypt`
- `backend/schemas/image_schema.py`
  - add decryption response and per-frame result schemas
- `backend/services/encoding/morse_to_symbol_sequence.py`
  - add reverse symbol-to-Morse conversion if needed
- `backend/services/encoding/morse_to_text.py`
  - implement Morse-to-plaintext conversion
- `backend/tests/test_phase2_decryption.py`
  - add receiver and end-to-end tests
- `frontend/src/pages/BobPage.jsx`
  - submit the text decryption request and display recovered plaintext

## Verification Checklist

### Sender

- Plaintext converts deterministically to Morse.
- Every Morse character produces one frame.
- All frames share one message ID and salt.
- Frame indices are `0..frame_count-1`.
- Different frame indices derive different masks.
- Image and text messages do not overwrite one another.
- Text encryption completes without repeated password-KDF delays.
- Preview responses remain compact.

### Receiver

- Correct key image and password recover the original text.
- Wrong key image or password fails validation or produces an invalid sequence.
- Missing or duplicate frames are rejected.
- Swapped frame indices do not silently decode as the original message.
- The receiver uses stored complex ciphertext, not amplitude PNG previews.

### Regression

- Existing Phase 1 image encryption/decryption continues to work.
- Frontend build succeeds with `npm run build`.
- Backend tests run in the project virtual environment.
