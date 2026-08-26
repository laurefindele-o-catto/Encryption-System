# Implementation Prompt: DRPE Encryption Demo (Phase 1) — React Frontend + API Backend

## Context / Goal

Build a **working demo of Double Random Phase Encryption (DRPE)** as a standalone, presentable system with a **React frontend** and a **backend API**, to be shown to a supervisor as a milestone deliverable.

This is explicitly **Phase 1** of a larger project. The larger project (covert Morse-code text transmission over DRPE-encrypted images, using a differential two-block brightness encoding technique where symbol duration is encoded by the magnitude of the brightness delta) will be layered on top of this in Phase 2. **This phase must be built with clear extension points so the Morse/text-encoding layer can be added later without re-architecting the DRPE core.**

Do not implement Morse code, text-to-symbol conversion, or differential block encoding in this phase. Only implement: image upload → DRPE encrypt → DRPE decrypt → visual verification, end-to-end, working, and demoable.

---

## 1. Scope of Phase 1 (What to Build Now)

1. **DRPE Encryption/Decryption Engine (Backend)**

   - Implement DRPE as a backend service/API (image in → encrypted image out; encrypted image + key/seed in → decrypted image out).
   - Core DRPE steps to implement:
     1. Take input image (**RGB — three channels, shape `(H, W, 3)`**, see Section 4). All uploaded images are converted to RGB by the upload pipeline; the DRPE engine then operates per-channel on the phase masks `P1`, `P2`. In Phase 1, the same 2D $(H, W)$ masks $P_1, P_2$ are reused across all three color channels (the classical multichannel optical DRPE formulation, minimizing payload size). The extension point `derive_key(seed, frame_index, channel_idx)` is reserved for strict per-channel cryptographic isolation.
     2. Generate/derive two random phase masks (P1, P2) from a **dual-seed + base-image key scheme**:
        - P1 lives in the **spatial domain** (input plane) and is derived from `seed_p1`.
        - P2 lives in the **frequency domain** (Fourier plane) and is derived from `seed_p2`.
        - Both seeds are mixed with a hash of the **predetermined base/reference image** (per the project's existing key-management scheme), so two different base images with the same seeds produce completely different masks.
        - A per-frame `frame_index: int = 0` is mixed in via SHA-256 (`derive_key(seed, frame_index)`), so that Phase 2 can transmit a sequence of independently-keyed images without recovering one key revealing another.
     3. Apply, per channel: `cover · exp(j·P1)` → `FFT2` → `· exp(j·P2)` → `IFFT2`. This is the classical 4-f DRPE formulation.
     4. Output the encrypted (ciphertext) image — store/represent it in a form suitable for transmission and re-display. The amplitude `|ciphertext|` is the noise-like display PNG; the full complex128 array is losslessly base64-encoded and sent back to the client so decryption can be re-run by the receiver without trusting any server-side state.
   - Implement the inverse operation for decryption using the same base image + seeds (or directly-supplied P1/P2 masks) to regenerate or accept the identical key/masks.

2. **API Layer**

   - Expose clean REST (or equivalent) endpoints:
     - `POST /api/encrypt` — accepts `cover_image: UploadFile`, `seed_p1: str`, `seed_p2: str`, and optional `frame_index: int = 0` (multipart form). Returns `EncryptResponse`: full complex ciphertext as `ciphertext_b64` (lossless base64 of a complex128 ndarray), `ciphertext_shape`, phase masks (`p1_b64`, `p2_b64`), display PNG (`image`), raw unclipped Parseval energy readouts (`energy`, `cover_energy`), and `cover_hash` (SHA-256 of raw cover pixels). Phase 1 is **strictly stateless** — the client holds the ciphertext and verification hashes; the server persists no global session state.
     - `POST /api/decrypt` — accepts JSON `DecryptRequest`: `{ciphertext_b64, ciphertext_shape, frame_index: int = 0, cover_hash: str | None = None}` plus EITHER `(seed_p1, seed_p2)` OR `(p1_b64, p2_b64)`. Re-derives or directly uses the phase masks and runs the inverse. Returns `DecryptResponse`: recovered image (`image`), raw energy (`energy`), and `match_with_cover` boolean (computed statelessly against `cover_hash` if supplied, or verified client-side).
     - `GET /api/base-image` — returns the predetermined base image and its shape (for demo transparency).
     - `GET /api/health` — liveness check.
   - Design the API so **future endpoints can be added** for symbol-level/Morse-level operations (e.g., a future `POST /api/encode-message` or `POST /api/decode-message`) without breaking these core endpoints. Keep DRPE logic isolated in its own service/module, decoupled from any future encoding logic.

3. **React Frontend**

   - Simple, clean, demo-friendly UI with two tabs:
     - **Tab 1: DRPE Demo** (`DRPEDemo.jsx`):
       - Upload/select an image. Uploaded files are auto-resized client-side to a max of 2048 px on the longest edge (BICUBIC) so the demo can handle arbitrarily large photos.
       - Input or auto-generate two seeds: `seed_p1` (spatial mask) and `seed_p2` (frequency mask). There are "Random P1 Seed" / "Random P2 Seed" buttons.
       - Button: **Encrypt** → calls `POST /api/encrypt` (passing `frame_index: 0`), displays the resulting (visually noise-like) ciphertext amplitude image.
       - Two decryption input boxes (`P1` and `P2`) start empty after encryption — the user must type or paste values. Quick-action buttons:
         - "📋 Paste Matching Keys" — fills the boxes with the original `seed_p1` and `seed_p2` (correct decryption).
         - "⚡ Wrong P1 Key" / "⚡ Wrong P2 Key" — fill the boxes with intentionally-wrong seeds so the demo visibly fails.
         - "🗑️ Clear" — empties both inputs.
       - Button: **Decrypt** → calls `POST /api/decrypt` (passing `frame_index: 0` and `cover_hash`), displays the recovered image side-by-side with the original. The client-side status banner verifies exact pixel equality / hash match ("Decryption Successful" with `match_with_cover = true`) or "Uncorrelated phase noise" (with `match_with_cover = false`).
       - Display the seed/key index being used, and clearly show that a **wrong seed produces garbage output** (important for the demo — supervisor should see that decryption fails without the correct key).
       - A collapsible "Show the predetermined base image" panel displays the reference base image with shape and channel count.
       - A workflow explanation block at the bottom of the panel walks through the math (`FFT₂D(Ciphertext) · e^(-jP₂) → IFFT₂D → · e^(-jP₁)`) and what success vs. failure looks like.
     - **Tab 2: Phase 2 (Coming Next)** (`Phase2Placeholder.jsx`): a clearly labeled "Coming Next" placeholder showing the planned sender/receiver pipeline as static text, so the supervisor can see the intended direction without it needing to function yet.
   - Keep the UI modular (component-level separation, e.g. `<ImagePanel />`) so a future "Morse/Text Transmission" tab/view can be added later without reworking the DRPE demo view.

4. **Demo Flow (what the supervisor should see)**
   - Upload an RGB image.
   - Show the encrypted output (visually random/noise-like — proving encryption occurred).
   - Decrypt with correct seeds → recovers original image (pixel-perfect; round-trip is lossless to within ~1e-13 floating-point round-off, so the PNG round-trip is bit-identical).
   - Attempt decrypt with wrong `seed_p1` or wrong `seed_p2` → show garbled/incorrect output, to demonstrate the key dependency is real and functioning for **both** phase masks independently.
   - Show a simple energy readout (Σ(pixel²)) computed from raw floating-point data for cover vs. ciphertext, which are equal up to numerical precision — this is the Parseval-invariant property from the project's security analysis. It is also useful context-setting for Phase 2's problem statement (the side-channel we are closing), without needing to explain the Morse layer yet.

---

## 2. Explicit Extension Points for Phase 2 (Morse Code Layer) — Do Not Build Yet, But Design For

Structure the code so the following can be added later **without breaking or rewriting the DRPE core**.

### 2.1 Morse code timing model (the new five-symbol alphabet)

Phase 2 does not encode Morse using a single discrete state per dot/dash. Instead, the **duration** of each symbol in time units is encoded by **the magnitude of the brightness delta** applied to the differential two-block pattern. The full set of Morse primitives is exactly five:

| #   | Symbol                                       | Duration (time units) | Δ magnitude (multiples of `DELTA`)         |
| --- | -------------------------------------------- | --------------------- | ------------------------------------------ |
| 1   | Dot (·)                                      | 1                     | `1·DELTA`                                  |
| 2   | Dash (–)                                     | 3                     | `3·DELTA`                                  |
| 3   | Intra-symbol gap (parts of the same letter)  | 1                     | `1·DELTA` (inverse / "no-signal" polarity) |
| 4   | Inter-letter gap (between letters in a word) | 3                     | `3·DELTA` (inverse / "no-signal" polarity) |
| 5   | Inter-word gap (between words)               | 7                     | `7·DELTA` (inverse / "no-signal" polarity) |

**The differential-two-block technique adopts this timing by encoding each symbol as `±k·DELTA`** on the two pre-agreed blocks, where `k` is the symbol's time-unit count (1, 3, or 7) and the sign depends on whether the symbol is a "tone" (dot/dash) or a "silence" (the three gap types). Concretely:

- **Tones** (dot, dash): Block A gets `+k·DELTA` brightness, Block B gets `−k·DELTA`. So a dot writes `+DELTA`/`−DELTA` and a dash writes `+3·DELTA`/`−3·DELTA` — the magnitude of the modulation directly encodes the symbol's duration.
- **Silences** (the three gap types): the polarity is inverted so the receiver can distinguish "no symbol" from "this is the dash slot" using only one image per time slot — Block A gets `−k·DELTA` and Block B gets `+k·DELTA`, where `k` is again the gap's time-unit count. So an intra-letter gap writes `−DELTA`/`+DELTA`, an inter-letter gap writes `−3·DELTA`/`+3·DELTA`, and an inter-word gap writes `−7·DELTA`/`+7·DELTA`.
- **Parseval safety (honest version)**: Σpixel² is quadratic, so writing `(x + k·Δ)² + (x − k·Δ)²` does **not** yield exact energy invariance. With `mean(A) = mean(B)` in the base image, the **linear** brightness cross-term `2·k·Δ·(S_A − S_B)` cancels exactly. A residual quadratic term of `2·N·(k·Δ)²` remains (where `N = BLOCK_SIZE²` is the number of pixels per block); this is small, bounded, and predictable for reasonable `Δ`. The full analysis (and the bound's numerical evaluation against natural image-energy variance) is documented in `SECURITY_NOTES.md`. **Precondition (guaranteed at synthesis time, see §4):** the two block regions must have equal mean brightness in the base image (`|mean(A) − mean(B)| < 0.01`). This kills the linear cross-term and is what makes the residual small enough to plausibly hide below the natural-energy noise floor of the cover. We do **not** claim the side-channel is closed absolutely — we claim it is reduced to a bounded residual that is analyzed numerically.

This collapses the legacy 5-state-per-Morse-character design (dot/dash/intra/inter/inter-word each as one integer state) into a single differential-brightness primitive whose magnitude carries the timing information. There is therefore no longer a need for "placeholder images" for gaps; every transmitted image is one time slot, and the receiver decodes each image's `sign` and `magnitude` to recover the symbol type and duration.

### 2.2 Sender-side pipeline (text → images ready for DRPE encryption)

1. `text_to_morse(text)` — converts raw input text into a **timed Morse sequence** (a flat stream where each character is annotated with its time-unit duration). Implementation uses a standard ITU Morse code table; non-alphanumerics are uppercased or skipped per the standard.
2. `morse_to_symbol_sequence(timed_morse)` — expands the timed Morse stream into **one entry per symbol** (one Morse primitive: dot, dash, or one of the three gap types), **not** one entry per literal time unit. A dash, for example, produces a **single** entry with `k = 3`; it does not produce three separate images. Each entry is a small struct: `{"polarity": "tone" | "silence", "k": 1 | 3 | 7, "kind": "dot" | "dash" | "intra_letter" | "inter_letter" | "inter_word"}`. The length of this list is the number of images the sender will transmit, and each entry's `k` value is what gets encoded into the Δ-magnitude of that one image, per §2.1.
3. `generate_symbol_image(entry, base_image)` — for each entry in the sequence, takes the shared base/template image and applies the **differential two-block brightness encoding** at the magnitude determined by `entry.k`:
   - if `entry.polarity == "tone"`: Block A gets `+k·DELTA` brightness, Block B gets `−k·DELTA` (uniformly applied across all R, G, B channels).
   - if `entry.polarity == "silence"`: Block A gets `−k·DELTA` brightness, Block B gets `+k·DELTA` (uniformly applied across all R, G, B channels).
   - The linear brightness cross-term across the two blocks cancels (`+` and `−`), leaving only the small, bounded quadratic residual $2\cdot N\cdot (k\cdot\Delta)^2$ documented in §2.1 and `SECURITY_NOTES.md`.
   - Block coordinates come from `BLOCK_A_COORDS` and `BLOCK_B_COORDS`, edge length from `BLOCK_SIZE`, and the per-unit step from `DELTA` in `backend/config.py`. This function outputs one modified image per time-unit slot, ready to be passed into the DRPE encryption pipeline.
4. The full sender pipeline chains as:
   `text → morse → timed_symbol_sequence → [image_0, image_1, ..., image_N]`
   Each image is individually encrypted via the existing `/api/encrypt` endpoint with explicit `frame_index = 0, 1, ..., N-1` (and transmitted with sequence metadata `{"frame_index": i, "total_frames": N, "message_id": id}` so dropped or reordered frames can be detected deterministically by the receiver).

### 2.3 Receiver-side pipeline (decrypted images → text)

1. `read_differential_brightness(image, base_image)` — after each image is decrypted via the existing `/api/decrypt` endpoint (using the matching `frame_index`), executes a **Two-Tier Authentication & Demodulation Pipeline**:

   - **Tier 1 (Background Template Authenticity Gate):**
     Before measuring block differences, the receiver compares the decrypted image *outside* the two blocks ($\Omega_{\text{bg}} = \text{All Pixels} \setminus (\text{Block A} \cup \text{Block B})$) against the known reference `base_image`:
     $$\text{MSE}_{\text{bg}} = \frac{1}{3 \cdot |\Omega_{\text{bg}}|} \sum_{p \in \Omega_{\text{bg}}} \sum_{C \in \{R,G,B\}} (I_{\text{dec}}(p, C) - I_{\text{base}}(p, C))^2$$
     If $\text{MSE}_{\text{bg}} > \tau_{\text{bg}}$ (e.g. threshold $\tau_{\text{bg}} = 5.0$, whereas decryption with a wrong key produces un-correlated phase noise with $\text{MSE}_{\text{bg}} > 1000$), the frame is immediately rejected as `corrupted` (wrong key / noise). **This prevents a wrong key that generates random noise from "getting lucky" and producing a coincidental in-alphabet block difference.**

   - **Tier 2 (Differential Delta Demodulation):**
     If Tier 1 passes, reads the mean luma brightness in Block A and Block B (using the luma formula defined in §4) and extracts polarity and duration magnitude:
     - `sign = sign(mean_luma(A) − mean_luma(B))` → polarity (`+` = tone, `−` = silence).
     - `k = round(|mean_luma(A) − mean_luma(B)| / (2 · DELTA))` → duration in time units.
     - Validation: `k` must strictly land in `{1, 3, 7}`, and the combination `(+7)` is illegal.
     - The returned entry is `{"polarity": "tone" | "silence", "k": int, "kind": ...}` — matching the sender's struct:

       | sign | k   | kind             |
       | ---- | --- | ---------------- |
       | +    | 1   | dot              |
       | +    | 3   | dash             |
       | −    | 1   | intra-letter gap |
       | −    | 3   | inter-letter gap |
       | −    | 7   | inter-word gap   |

2. `symbol_sequence_to_morse(entries)` — groups consecutive time-unit entries back into Morse characters using the timing rules.
3. `morse_to_text(morse)` — decodes the reconstructed Morse stream back into plaintext ASCII.
4. The full receiver pipeline chains as:
   `[encrypted_image_0, ..., encrypted_image_N] → decrypt each (with frame_index) → read_differential_brightness per image → entries → morse → text`.

**Corrupted-frame handling.** If a frame fails the Tier 1 authenticity gate or Tier 2 returns an invalid `k` (or the illegal `+7`), the frame is marked `corrupted` and **not** silently coerced. `symbol_sequence_to_morse` skips corrupted frames and inserts a placeholder (e.g. `?`) in the recovered text, making decode failures visible rather than producing silent substitutions.

### 2.4 Key design constraints for Phase 2

- **All shared parameters in one place**: `BLOCK_A_COORDS`, `BLOCK_B_COORDS`, `BLOCK_SIZE`, and `DELTA` are pre-agreed between sender and receiver **out-of-band** and live in `backend/config.py` as the single source of truth. With the timing model, `DELTA` is the _unit step_ of the brightness scale (legal magnitudes: `1·DELTA`, `3·DELTA`, `7·DELTA`).
- **No DRPE endpoint breaking changes**: the Phase 1 `/api/encrypt` and `/api/decrypt` endpoints already accept `frame_index: int = 0` (default 0). Phase 2 calls them per-image in a loop passing `frame_index = 0, 1, 2, ...` with zero API schema modifications.
- **Message grouping & Packet framing**: a logical transmission is a `Message` containing $N$ `Frame`s (`services/messages.py`). Phase 2 groups an entire timed Morse stream under one `message_id`, carrying frame sequence numbers `{"frame_index": i, "total_frames": N, "message_id": id}` to ensure reliable reconstruction and drop detection.
- **Statelessness & Verification**: Server-side mutable global state (like `_last_cover`) is eliminated. Per-frame verification is performed statelessly via client-side pixel comparison or optional `cover_hash` in `DecryptRequest`.
- **Per-frame key independence**: the SHA-256-based `derive_key(seed, frame_index)` in `services/keys.py` guarantees cryptographic independence across frames.
- **Symbol-stream bookkeeping**: keep the timed-symbol sequence alongside encrypted frames in `Message` for timing auditability.

### 2.5 Frontend extension points

- Keep the current encrypt/decrypt demo as one self-contained view/component (`DRPEDemo.jsx`).
- The `Phase2Placeholder.jsx` tab stays as the "Coming in Phase 2: Text Transmission" placeholder for today's demo, and is the home for the future live text-transmission view.
- The frontend's `api.js` (axios instance pointing at `/api`) is the single place to add new endpoints — no need to touch per-component base URLs.

### 2.6 Key/Seed scheme

- Keep the dual-seed scheme (`seed_p1` for the spatial mask, `seed_p2` for the frequency mask) generic. Phase 2 assigns a fixed per-slot `frame_index` to every time-unit image in the Morse stream, and `derive_key(seed, frame_index)` produces a unique per-frame key without changing the API.
- The base image is part of the key (as it is in Phase 1); it does not change per slot.

---

## 3. Non-Goals for This Phase (Explicitly Out of Scope)

- Text input, Morse code conversion, or any symbol encoding.
- Differential two-block brightness encoding (the new timing-based Δ-magnitude variant described in §2.1 is also out of scope for Phase 1).
- Multi-image sequencing/transmission logic over a `message_id`.
- Any side-channel/statistical security hardening beyond what's naturally demonstrated by DRPE itself (energy-invariance discussion is optional/illustrative only in this phase, not something to defend against yet).

---

## 4. Technical Decisions Made Explicit (documented in the implementation)

- **Image format/color handling: RGB only.** All uploaded images are converted to RGB by `services/image_utils.file_to_array()` (`.convert("RGB")` in PIL). The DRPE engine operates on the array as shape `(H, W, 3)` and applies the same P1 and P2 masks to all three color channels in Phase 1 (classical optical color formulation). For strict cryptographic channel isolation, `derive_key(seed, frame_index, channel_idx)` provides per-channel mask derivation.
- **Brightness metric & Per-Channel Encoding (Phase 2).**
  - `generate_symbol_image` applies a **uniform per-channel additive offset** to all three color channels: $(R \pm k\Delta, G \pm k\Delta, B \pm k\Delta)$.
  - The receiver reads the mean brightness in Block A and Block B using the ITU-R BT.601 luma formula:
    ```
    brightness(block) = mean over all pixels in the block of (0.299·R + 0.587·G + 0.114·B)
    ```
    Because $0.299(k\Delta) + 0.587(k\Delta) + 0.114(k\Delta) = 1.0 \cdot k\Delta$, the sender's uniform RGB offset matches the receiver's luma read-back exactly, provided no individual channel clips.
- **Config-time invariants for Phase 2 block parameters** (loud-fail at Phase 2 initialization, before any symbol is encoded). In Phase 1, `backend/config.py` contains `BLOCK_A_COORDS`, `BLOCK_B_COORDS`, `BLOCK_SIZE`, and `DELTA` as static, inert constants/placeholders. In Phase 2, when `backend/services/encoding/symbol_image.py` is initialized (or upon first call to `generate_symbol_image`), all four invariants run against `services/base_image.get_base_image()`. Failing any of these refuses to proceed with a clear error:
  1. **Block-in-bounds**: each of `BLOCK_A_COORDS` and `BLOCK_B_COORDS`, expanded by `BLOCK_SIZE` in both dimensions, must fit entirely within the base image's `(H, W)`.
  2. **No overlap**: the two block rectangles must be disjoint (no shared pixels).
  3. **Independent RGB Clipping safeguard for maximum magnitude:** every pixel in both block regions of the base image must satisfy:
     $$\forall p \in (\text{Block A} \cup \text{Block B}), \quad \forall C \in \{R, G, B\}, \quad C(p) \in [7\cdot\text{DELTA}, 255 - 7\cdot\text{DELTA}]$$
     *Checking the luma aggregate alone is forbidden*, because an individual color channel (e.g. $R=250$) could clip at 255 upon adding $+k\Delta$, silently corrupting the differential signal while luma appears within bounds.
  4. **Near-equal mean brightness (energy-invariance precondition):** `|mean_luma(BLOCK_A) − mean_luma(BLOCK_B)| < 0.01`. This cancels the linear `2·k·Δ·(S_A − S_B)` cross-term in the energy analysis (§2.1).
- **Deterministic Base Image Synthesis & Block Equalization:**
  To guarantee that Invariant #4 holds automatically without random trial-and-error, `services/base_image._load_or_synthesize()` performs a deterministic equalization step during base image generation:
  1. Generates the initial pseudo-random RGB noise field from seed `20240801`.
  2. Computes the per-channel mean difference between Block A and Block B: $\delta C = \text{mean}(A_C) - \text{mean}(B_C)$ for $C \in \{R, G, B\}$.
  3. Applies a uniform correction $-\delta C / 2$ to Block A and $+\delta C / 2$ to Block B (or shifts Block B by $+\delta C$) so that $\text{mean}(A) \equiv \text{mean}(B)$ to $< 0.01$ luma precision.
  4. Validates that Invariant #3 ($[7\Delta, 255 - 7\Delta]$) holds for all equalized pixels before writing `backend/data/base_image.png`.
- **Ciphertext representation:** the full complex128 ciphertext is losslessly base64-encoded and sent to the client in `EncryptResponse` (`ciphertext_b64`, `ciphertext_shape`). The API also returns `image` — a base64 PNG of spatial-domain amplitude `|ciphertext|`, the phase masks (`p1_b64`, `p2_b64`), and raw unclipped Parseval energies (`energy`, `cover_energy`).
- **Stateless Server Architecture:** The FastAPI server is 100% stateless across encryption/decryption requests. The mutable `_last_cover` global is eliminated. Decryption verification is performed by matching against the client's transmitted `cover_hash` or comparing images directly client-side, eliminating race conditions under concurrent requests or React dev mode double-mounts.
- **FFT library:** `numpy.fft.fft2` / `numpy.fft.ifft2` (no new dependencies; numpy was already in the venv).
- **Key and Phase Mask Derivation:**
  1. **Scalar seed derivation:** `derive_key(base_seed, frame_index) = int(SHA-256(f"{base_seed}:{frame_index}").hexdigest()[:16], 16)` produces a 64-bit integer (`uint64`).
  2. **Base image & shape context mixing (`_shape_seed`):** SHA-256 is computed over the raw bytes of `base_image` concatenated with the target shape dimensions `(H, W)`. The top 8 bytes are extracted as a 64-bit unsigned integer `blob_int`.
  3. **Full 64-bit Domain separation:** Bitwise XOR combines `mixed = base_seed ^ blob_int ^ DOMAIN_TAG` using 64-bit domain constants (`0x50314D3150314D31` for $P_1$ and `0x50324D3250324D32` for $P_2$) ensuring complete domain separation across all 64 bits.
  4. **PRNG sampling for full $(H, W)$ array:** NumPy's default bit generator (`np.random.default_rng(mixed)`) is seeded with the 64-bit integer, sampling an $(H, W)$ array of uniform float64 phases in $[0, 2\pi)$: `rng.uniform(0.0, 2.0 * np.pi, size=shape).astype(np.float64)`.
  5. **Fixed base image (256×256) vs arbitrarily-sized covers (up to 2048×2048):** The 256×256 base image acts as cryptographic key material (salt/pepper). Its SHA-256 digest provides key material, while the target cover image shape $(H, W)$ is passed to the PRNG to generate full shape-matched $(H, W)$ phase masks.
- **Base image:** auto-synthesized as a 256×256 RGB equalized PNG on first boot, written to `backend/data/base_image.png`, and cached in memory.
- **Precision / fidelity & Real-part reconstruction:** float64 throughout. Decryption strictly extracts the **real part** $\text{Re}(s \cdot e^{-j P_1})$, rounding and clipping to $[0, 255]$ for display. Reconstructing from $\text{Re}(\dots)$ rather than $\text{abs}(\dots)$ is mathematically mandatory for DRPE: if $\text{abs}()$ were used, an incorrect spatial mask $P_1$ would not garble the amplitude output because $|f \cdot e^{j \Delta}| = |f|$, compromising $P_1$'s security role. Round-trip is lossless to within ~1e-13 (FFT numerical round-off), producing bit-identical recovered images when correctly keyed.
- **Frontend image pre-processing:** uploaded files are resized client-side to a max of 2048 px on the longest edge (`utils/imageResizer.js`, BICUBIC) before being sent to the API. This keeps the demo responsive for arbitrarily large photos without changing the protocol.

---

## 5. Suggested Tech Stack (current implementation)

- **Frontend:** React (Vite, plain JavaScript), `axios` for API calls, hand-rolled inline-styles for components (no component library — prioritize clarity and demo-readiness over polish). Two views: `DRPEDemo.jsx` and `Phase2Placeholder.jsx`, switched via a tab in `App.jsx`.
- **Backend:** Python 3 + FastAPI + uvicorn. numpy for FFT; PIL for image I/O; pydantic for schemas. The layer split is `routers/ → controllers/ → services/`, with the pure-function DRPE engine isolated in `services/drpe.py`.
- **Image handling:** PIL (via `services/image_utils.py`) for load/convert, numpy for all math, `io.BytesIO` + base64 for in-memory transport between server and client.

---

## 6. Deliverable for Supervisor Demo

A working local instance where:

1. An RGB image can be uploaded via the React UI.
2. It gets encrypted via the API (DRPE), and the visually-random ciphertext is shown. The full complex ciphertext + phase masks are returned losslessly so the receiver can decrypt offline.
3. It gets decrypted via the API using the correct `seed_p1` and `seed_p2`, recovering the original image pixel-perfectly (the `match_with_cover` boolean is `true`).
4. A wrong `seed_p1` or wrong `seed_p2` visibly fails to recover the image (the `match_with_cover` boolean is `false` and the output is un-correlated phase noise), demonstrating the encryption is functioning correctly and is key-dependent for both phase masks independently.
5. A Parseval energy readout (Σ(pixel²)) for cover and ciphertext is shown side-by-side, illustrating DRPE's energy-preservation property and foreshadowing the side-channel mitigation (canceling the linear energy cross-term) that Phase 2 builds upon.
6. A clearly labeled "Phase 2: Text/Morse Transmission — Coming Next" tab is visible in the UI, to communicate the project roadmap. (For the future Phase 2, the placeholder will be replaced with a live text-transmission view whose timing is encoded in the magnitude of the differential two-block brightness modulation per §2.1.)
