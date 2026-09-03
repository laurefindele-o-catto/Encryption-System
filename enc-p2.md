# Phase 2: Text Transmission Plan

## Scope

Add a separate text-transmission mode to Alice's page while preserving the existing Phase 1 image-encryption workflow. This implementation covers the Alice/frontend side only. Bob's decryption implementation will be completed separately by a teammate.

## Alice frontend

Modify `frontend/src/pages/AlicePage.jsx` to:

1. Add tabs for `Send Image` and `Send Text`.
2. Keep the current Phase 1 image form available under `Send Image`.
3. Add a Phase 2 text form under `Send Text` with:
   - secret text
   - base RGB image
   - secret key image
   - password
4. Initialize text and password state with empty strings rather than `null`.
5. Add a separate `handleSendText()` function.
6. Submit text-mode data as multipart form data to `POST /api/text/encrypt` using:
   - `secret_text`
   - `base_image`
   - `secret_key_image`
   - `secret_password`
7. Store the returned message metadata in the shared packet state without sending complex ciphertext through the browser.
8. Keep Phase 1's `handleSend()` and `/api/encrypt` request unchanged.
9. Provide validation, loading, success, and error states for the text form.

## Backend work to follow

The frontend expects a future sender endpoint:

`POST /api/text/encrypt`

The endpoint should:

1. Validate the text, base image, key image, and password.
2. Convert plaintext to Morse.
3. Convert Morse characters to ordered symbol states.
4. Generate one RGB symbol image per state from the uploaded base image.
5. Derive per-frame DRPE key material using the key image, password, message ID, and frame index.
6. Encrypt each frame and store all complex ciphertext frames under one message ID.
7. Return compact metadata such as:
   - `message_id`
   - `salt_b64`
   - `frame_count`
   - `morse`
   - `symbols`
   - `base_image_shape`
   - optional display previews

Complex ciphertext should remain server-side to avoid oversized multipart requests.

## Backend files for the later implementation

- `backend/services/encoding/text_to_morse.py`
  - validate and normalize plaintext
  - define unsupported-character behavior
- `backend/services/encoding/morse_to_symbol_sequence.py`
  - define symbol states
  - add forward and reverse mappings
- `backend/services/encoding/symbol_image.py`
  - implement RGB block modulation and bounds checks
- `backend/services/encoding/morse_to_text.py`
  - implement reverse Morse decoding for Bob
- `backend/services/text_encryption.py`
  - implement the Alice text-to-encrypted-frame pipeline
- `backend/services/messages.py`
  - support one message containing multiple ordered frames
  - reject duplicate, negative, or incomplete frame indices
- `backend/schemas/image_schema.py`
  - add text-encryption response schemas
- `backend/controllers/text_controller.py`
  - orchestrate the sender request
- `backend/routers/text_router.py`
  - add `POST /api/text/encrypt`
- `backend/main.py`
  - register the text router
- `backend/tests/test_phase2_encryption.py`
  - add Morse, symbol, frame, endpoint, and integration tests
- `README.md` or `PHASE2_API.md`
  - document the sender response and future Bob decryption contract

## Future Bob endpoint

The teammate can implement:

`POST /api/text/decrypt`

Request fields:

- `message_id`
- `secret_key_image`
- `secret_password`

The receiver should retrieve ordered frames, decrypt each frame, read the symbol, rebuild Morse, convert Morse to plaintext, and return recovered text plus frame diagnostics.

## Verification

1. Confirm Image and Text tabs render correctly.
2. Confirm Phase 1 image sending still uses `/api/encrypt`.
3. Confirm Text mode validates all required inputs.
4. Confirm Text mode sends only the expected multipart fields to `/api/text/encrypt`.
5. Confirm text-mode response metadata is stored in the shared packet state.
6. Run `npm run build` in `frontend`.
7. After backend implementation, add a real Alice-to-Bob integration test and retain the Phase 1 image regression test.
