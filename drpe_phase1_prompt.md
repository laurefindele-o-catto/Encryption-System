# Implementation Prompt: DRPE Encryption Demo (Phase 1) — React Frontend + API Backend

## Context / Goal

Build a **working demo of Double Random Phase Encryption (DRPE)** as a standalone, presentable system with a **React frontend** and a **backend API**, to be shown to a supervisor as a milestone deliverable.

This is explicitly **Phase 1** of a larger project. The larger project (covert Morse-code text transmission over DRPE-encrypted images, using differential two-block brightness encoding) will be layered on top of this in Phase 2. **This phase must be built with clear extension points so the Morse/text-encoding layer can be added later without re-architecting the DRPE core.**

Do not implement Morse code, text-to-symbol conversion, or differential block encoding in this phase. Only implement: image upload → DRPE encrypt → DRPE decrypt → visual verification, end-to-end, working, and demoable.

---

## 1. Scope of Phase 1 (What to Build Now)

1. **DRPE Encryption/Decryption Engine (Backend)**
   - Implement DRPE as a backend service/API (image in → encrypted image out; encrypted image + key/seed in → decrypted image out).
   - Core DRPE steps to implement:
     1. Take input image (grayscale or RGB — decide and document which, see Section 4).
     2. Generate/derive two random phase masks (P1, P2) from a **key**, where the key is derived from a **predetermined base/reference image + a seed value** (per the project's existing key-management scheme — seed N → key N).
     3. Apply FFT → multiply by P1 → IFFT → multiply by P2 (or the specific DRPE variant chosen — document exactly which mathematical formulation is implemented).
     4. Output the encrypted (ciphertext) image — store/represent it in a form suitable for transmission and re-display (e.g., normalized amplitude image, or store real/imaginary parts if complex-valued).
   - Implement the inverse operation for decryption using the same base image + seed to regenerate the identical key/masks.

2. **API Layer**
   - Expose clean REST (or equivalent) endpoints, e.g.:
     - `POST /api/encrypt` — accepts an image + seed, returns the encrypted image (and/or a reference/ID to retrieve it).
     - `POST /api/decrypt` — accepts an encrypted image (or reference/ID) + seed, returns the decrypted image.
     - `GET /api/base-image` — returns/confirms the predetermined base image being used for key derivation (for demo transparency).
   - Design the API so **future endpoints can be added** for symbol-level/Morse-level operations (e.g., a future `POST /api/encode-symbol` or `POST /api/decode-message`) without breaking these core endpoints. Keep DRPE logic isolated in its own service/module, decoupled from any future encoding logic.

3. **React Frontend**
   - Simple, clean, demo-friendly UI:
     - Upload/select an image.
     - Input or auto-generate a seed.
     - Button: **Encrypt** → calls `/api/encrypt`, displays the resulting (visually noise-like) ciphertext image.
     - Button: **Decrypt** → calls `/api/decrypt` using the same seed, displays the recovered image side-by-side with the original for visual proof of correctness.
     - Display the seed/key index being used, and clearly show that a **wrong seed produces garbage output** (important for the demo — supervisor should see that decryption fails without the correct key).
   - Keep the UI modular (component-level separation) so a future "Morse/Text Transmission" tab or view can be added later without reworking the DRPE demo view.

4. **Demo Flow (what the supervisor should see)**
   - Upload an image.
   - Show the encrypted output (visually random/noise-like — proving encryption occurred).
   - Decrypt with correct seed → recovers original image (pixel-perfect or near-identical, document expected fidelity/loss if any).
   - Attempt decrypt with wrong seed → show garbled/incorrect output, to demonstrate the key dependency is real and functioning.
   - (Optional, if time permits) Show a simple energy/statistics readout (e.g., Σ(pixel²) before/after encryption) to visually reinforce the Parseval-invariant property discussed in the project's security analysis — useful context-setting for Phase 2's problem statement, without needing to explain the Morse layer yet.

---

## 2. Explicit Extension Points for Phase 2 (Morse Code Layer) — Do Not Build Yet, But Design For

Structure the code so the following can be added later **without breaking or rewriting the DRPE core**:

1. **Backend:**
   - A future `encoding/` module (or service) that sits *before* encryption (sender side) and *after* decryption (receiver side), structured as follows:

   **Sender-side (text → images ready for DRPE encryption):**
   - `text_to_morse(text)` — converts raw input text into a flat sequence of Morse symbols (dots, dashes, inter-symbol gaps, inter-letter gaps, inter-word gaps), using a standard Morse code table.
   - `morse_to_symbol_sequence(morse)` — maps each Morse symbol type to a discrete integer state (e.g., dot → state 0, dash → state 1, space variants → state 2/3 etc.), producing an ordered list of states, one per image to be generated.
   - `generate_symbol_image(state, base_image, block_A_coords, block_B_coords, delta)` — for each state in the sequence, takes the shared base/template image and applies the **differential two-block brightness encoding**: if state maps to symbol-type-1, Block A gets +Δ brightness and Block B gets −Δ; if state maps to symbol-type-2, Block A gets −Δ and Block B gets +Δ. The net energy change across the full image is always exactly zero (+Δ and −Δ cancel), closing the Parseval side-channel described in the project's security analysis. This function outputs one modified image per symbol, ready to be passed into the DRPE encryption pipeline.
   - The full sender pipeline chains as: `text → morse → symbol_sequence → [image_0, image_1, ..., image_N]` — one image per symbol — each then individually encrypted via the existing `/api/encrypt` endpoint (seed index incremented per image), and transmitted in order.

   **Receiver-side (decrypted images → text):**
   - `read_differential_brightness(image, block_A_coords, block_B_coords)` — after each image is decrypted via the existing `/api/decrypt` endpoint, reads the brightness at the two predetermined pixel block coordinates and computes `sign(Brightness(A) − Brightness(B))` to recover the encoded symbol state.
   - `symbol_sequence_to_morse(states)` — maps the recovered sequence of integer states back to Morse symbols (dots, dashes, spaces).
   - `morse_to_text(morse)` — decodes the reconstructed Morse stream back into the original plaintext message.
   - The full receiver pipeline chains as: `[encrypted_image_0, ..., encrypted_image_N] → decrypt each → read_differential_brightness per image → symbol_sequence → morse → text`.

   - **Key design constraint for Phase 2:** Both `block_A_coords`, `block_B_coords`, and `delta` must be agreed upon and fixed between sender and receiver **out-of-band** (pre-shared, same as the base image and seed scheme). These values must be stored/configured in one place in the codebase (e.g., a shared `config.py` or `constants.js`) so they are never hardcoded separately on each side and can be updated without touching business logic.
   - The current `/api/encrypt` and `/api/decrypt` endpoints should remain usable as-is by this future module — i.e., the future module should be able to call them per-image in a loop/sequence, rather than requiring changes to the DRPE endpoints themselves.
   - Reserve a place (e.g., a `symbols/` or `sequences/` folder, or a `message_id` concept) for grouping multiple images together as one transmitted message, even though this phase only handles single images.

2. **Frontend:**
   - Keep the current encrypt/decrypt demo as one self-contained view/component (e.g., `DRPEDemo.jsx` or similar).
   - Leave a placeholder route/tab (can literally say "Coming in Phase 2: Text Transmission" for today's demo) so the supervisor can see the intended direction without it needing to function yet.

3. **Key/Seed scheme:**
   - Keep the seed-per-image indexing scheme (seed N → key N) generic enough that Phase 2 can assign one seed per Morse symbol/image in a sequence, incrementing automatically, without changing how keys are derived.

---

## 3. Non-Goals for This Phase (Explicitly Out of Scope)

- Text input, Morse code conversion, or any symbol encoding.
- Two-block differential brightness encoding.
- Multi-image sequencing/transmission logic.
- Any side-channel/statistical security hardening beyond what's naturally demonstrated by DRPE itself (energy-invariance discussion is optional/illustrative only in this phase, not something to defend against yet).

---

## 4. Technical Decisions to Make Explicit (document these in the implementation)

- Image format/color handling: grayscale vs RGB, and how DRPE is applied per-channel if RGB.
- How the complex-valued ciphertext is represented/stored/displayed (since DRPE output is generally complex — decide: store amplitude + phase separately, store as two real images, or use a specific normalization for display purposes).
- FFT library/implementation used on the backend (e.g., numpy/scipy `fft2`, or equivalent in the chosen backend language).
- Exact random phase mask generation method (e.g., uniform random phase in [0, 2π), seeded via a PRNG keyed by the seed + base image hash/derivation).
- Precision/rounding behavior and expected fidelity loss (if any) between original and decrypted image.

---

## 5. Suggested Tech Stack (adjust as needed to your existing setup)

- **Frontend:** React (Vite or CRA), plain fetch/axios for API calls, basic CSS or a lightweight component library — prioritize clarity and demo-readiness over polish.
- **Backend:** Python (FastAPI or Flask) recommended for FFT/image-processing convenience via numpy/scipy/PIL — but keep language choice flexible if the team already has a preferred stack.
- **Image handling:** PIL/OpenCV (Python) or equivalent for load/save/normalize operations.

---

## 6. Deliverable for Supervisor Demo

A working local (or deployed) instance where:
1. An image can be uploaded via the React UI.
2. It gets encrypted via the API (DRPE), and the visually-random ciphertext is shown.
3. It gets decrypted via the API using the correct seed, recovering the original image.
4. A wrong-seed attempt visibly fails to recover the image, demonstrating the encryption is functioning correctly and is key-dependent.
5. A clearly labeled "Phase 2: Text/Morse Transmission — Coming Next" placeholder is visible in the UI, to communicate the project roadmap.
