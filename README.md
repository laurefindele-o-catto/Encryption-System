# Encryption-System

This project is a DRPE-based image encryption demo using the real sender/receiver model: the sender uploads the original image, a key image, and a password; the receiver uploads the key image and the matching password to decrypt.

## Current architecture

The active backend contract is:

- `cover_image`: the original image being encrypted
- `secret_key_image`: Alice/Bob key image used to derive the DRPE masks
- `secret_password`: shared password material used for the decryption key derivation

This means the real flow is:

1. Sender uploads the original image
2. Sender uploads a key image
3. Sender enters the password
4. The backend derives `scrypt(password, salt)` and then the DRPE phase masks from that material
5. Receiver uploads the same key image and the same password
6. Bob decrypts the ciphertext and verifies it against the original cover image

This is the current implementation in `backend/services/keys.py` and `backend/controllers/image_controller.py`.

---

## What is implemented today

The project currently implements a working DRPE pipeline for image encryption and decryption:

- encrypt a cover image with a key image + password-derived material
- store the ciphertext in memory associated with a `message_id`
- decrypt the ciphertext with the receiving key image + matching password-derived material
- verify whether the recovered image matches the original cover image

This is the phase-1 functionality. The Morse / symbol / differential-brightness layer is not part of the live implementation yet.

---

## Core project behavior

The backend uses a DRPE design based on two phase masks, `P1` and `P2`, derived from image-based key material:

- `secret_key_image` is canonicalized and hashed
- `secret_password` is treated as a derived secret string, not a typed free-form password
- the project then runs `derive_image_password_keys(...)` to produce the P1 and P2 mask materials
- the actual encryption/decryption math is implemented in `backend/services/drpe.py`

The current route contract is already defined in `backend/routers/image_router.py` and should be treated as the source of truth.

---

## How to run

```bash
# backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Then open the Vite app in the browser and use the Alice/Bob interface.

---

## Frontend expectations

The UI should ask for the actual project inputs:

- sender original cover image
- sender key image
- sender password
- receiver key image
- receiver password

The backend API contract remains the same: `cover_image` is sent only by Alice, while Bob only sends the data needed to reproduce the same `secret_key_image` + `secret_password` pair.

---

## Important note on the old docs

The older README and earlier phase-1 prompt were written around a simplified DRPE demo that assumed a text password and a more generic demo flow. That is no longer the correct project description. The real active project is the image-key protocol described here.

The code in the repository is the authority:

- `backend/services/keys.py`
- `backend/controllers/image_controller.py`
- `backend/routers/image_router.py`
- `frontend/src/pages/AlicePage.jsx`
- `frontend/src/pages/BobPage.jsx`

Those files define the active implementation and should be treated as the canonical design.

---

## Project layout

```text
backend/
  main.py
  routers/
    image_router.py
  controllers/
    image_controller.py
  services/
    drpe.py
    keys.py
    image_utils.py
    messages.py
    encoding/
  schemas/
    image_schema.py

frontend/
  src/
    App.jsx
    api.js
    pages/
      AlicePage.jsx
      BobPage.jsx
    components/
      NoiseReveal.jsx
```

---

## Phase 2 status

Morse-code and differential-brightness encoding remain future work. The repository should not describe them as deployed functionality unless they are explicitly implemented and validated.

The current scope is: DRPE encryption/decryption using image-derived secret material.
