# Encryption-System
Morse code encoded in the pixels of a series of DRPE-encrypted images, for CSE 220 project of Epshita Jahan and Tafsir Al Nafin.

## What's in this repo

This is **Phase 1** of the larger project. Phase 1 = a working **Double Random Phase Encryption (DRPE)** demo. Phase 2 = the covert Morse/text transmission pipeline that will be layered on top. The Phase 2 logic is **out of scope for this phase** — only DRPE encrypt/decrypt works end-to-end today — but the architecture leaves a clean home for it.

---

## Phase 1 demo flow (what the supervisor should see)

1. Open the React UI at `http://localhost:5173` (after running the steps below).
2. **Tab 1: DRPE Demo** — upload an image, choose dual seeds (`seed_p1` for P1 frequency mask, `seed_p2` for P2 spatial mask).
3. **Encrypt** → the UI shows a noise-like ciphertext image, plus a Parseval energy readout (Σ·pixel²) that's identical for cover and ciphertext, illustrating that DRPE is energy-preserving.
4. **Decrypt (correct seeds)** → the original image comes back, pixel-identical to the cover (within float round-off, ≤ 1e-12).
5. **Decrypt (wrong P1 or P2 seed)** → the recovered image is noise — showing independent key dependency for both phase masks.
6. **Tab 2: Phase 2 (Coming Next)** — a clearly labeled placeholder showing the planned sender/receiver pipeline.

---

## How to run

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the FastAPI server on `:8000`, so the React code never hardcodes the backend host.

---

## Technical decisions (Phase 1)

These are the choices the spec asked us to make explicit. They're all implemented in the code; this section is the high-level summary.

- **Image format:** grayscale (single-channel 2D float64 ndarray). RGB can be added per-channel later; not needed for the demo.
- **DRPE variant:** classical 4-f system. `cover → FFT2 → ·exp(jP₁) → IFFT2 → ·exp(jP₂)`; decrypt is the exact inverse with the same P₁, P₂. Implemented in `backend/services/drpe.py`.
- **FFT library:** `numpy.fft.fft2` / `numpy.fft.ifft2` (no new dependencies; numpy was already in the existing venv).
- **Phase mask generation:** both P₁ and P₂ are uniform in `[0, 2π)`. $P_1$ is derived from `seed_p1` and $P_2$ is derived from `seed_p2` (SHA-256 of `"<seed>:<frame_index>"`, truncated to 128 bits — see `backend/services/keys.py`) XORed with a SHA-256 of the base image. The base image is therefore part of the key: same seeds + different base image → completely different masks.
- **Key scheme:** "predetermined base image + dual seeds → keys". The base image is auto-synthesized as a 256×256 noise PNG on first boot and saved to `backend/data/base_image.png`, so a fresh checkout "just works" without shipping the base image in the repo.
- **Ciphertext representation:** DRPE produces a complex field. For the **browser display** we send the amplitude `|ciphertext|` (visually noise-like, satisfying the supervisor demo). The complex ciphertext is kept server-side keyed by `message_id`; the decrypt endpoint accepts `(message_id, seed_p1, seed_p2)` and re-derives the phase masks from the seeds, then inverts. This is the "store real/imaginary parts if complex-valued" option from the spec.
- **Precision / fidelity:** float64 throughout. Round-trip is lossless to within ~1e-13 (FFT numerical round-off), so when clipped to 0–255 for PNG, the recovered image is **pixel-identical** to the original.
- **Energy readout (Parseval):** the `Σ(pixel²)` over the cover equals the same quantity over the ciphertext (ratio 1.000000 in our test). The demo UI shows both side-by-side as a sanity check, and as forward-context for Phase 2's covert-channel story.

---

## Project layout

```
backend/
  config.py                      Single source of truth (base image path, defaults,
                                 Phase 2 block coordinates + delta).
  main.py                        FastAPI entry point.
  data/
    base_image.png               (auto-created on first boot) the predetermined
                                 base image used as part of the key.
  routers/
    image_router.py              Thin route handlers — unpack request, call
                                 controller, return schema.
  controllers/
    image_controller.py          Orchestration: file I/O → DRPE service →
                                 message store → response shape.
  services/
    drpe.py                      The DRPE engine (pure functions, no I/O).
    base_image.py                Lazy-load / synthesize the predetermined base image.
    keys.py                      derive_key(seed, frame_index) — SHA-256 per-frame key.
    messages.py                  In-memory message_id → {complex, amplitude, masks}.
    image_utils.py               file_to_array / array_to_base64 (unchanged).
    encoding/                    Phase 2 extension point. Each module is a
      __init__.py                NotImplementedError stub with the planned
      text_to_morse.py           signature documented, so the rest of the
      morse_to_symbol_sequence.py codebase can refer to them as known
      symbol_image.py            future imports.
      morse_to_text.py
  schemas/
    image_schema.py              Pydantic request/response shapes.

frontend/
  index.html                     <title>DRPE Phase 1 Demo</title>
  src/
    App.jsx                      Tabbed shell: DRPE Demo + Phase 2 placeholder.
    api.js                       axios instance with /api base.
    main.jsx                     React entry.
    pages/
      DRPEDemo.jsx               The full supervisor demo in one view.
      Phase2Placeholder.jsx      "Coming Next" roadmap view.
    components/
      drpe/
        ImagePanel.jsx           Reusable labeled image preview.
```

The layered pattern (`routers/` → `controllers/` → `services/`) is the same one the previous skeleton used, so anyone who's already read the prior code will find the structure familiar.

---

## How to add new stuff (re-stated for the new endpoints)

- **Schema first** — define request/response shapes in `schemas/image_schema.py`.
- **Service next** — pure functions, no FastAPI imports, testable from a Python shell. New `services/encoding/*.py` modules go here for Phase 2.
- **Controller** — orchestration + error handling. The controller's only HTTP-specific concern is `HTTPException`.
- **Router** — the thinnest possible route handler. Just unpacks the request, calls the controller, returns the schema object.
- **Register** — `routers/image_router.py` is already wired into `main.py`. If you add a brand-new router file, `app.include_router(...)` it in `main.py`.
- **Frontend last** — once the endpoint is smoke-tested, wire up the React side.

---

## Phase 2 extension points (designed-for, not implemented)

The following are intentionally stubbed today. They are import-safe and reachable from the rest of the codebase:

- `services/encoding/text_to_morse(text) → str`
- `services/encoding/morse_to_symbol_sequence(morse) → list[int]`
- `services/encoding/symbol_image.generate_symbol_image(state, base_image) → ndarray`
- `services/encoding/symbol_image.read_differential_brightness(image) → int`
- `services/encoding/morse_to_text(morse) → str`

All shared constants for Phase 2 (`BLOCK_A_COORDS`, `BLOCK_B_COORDS`, `BLOCK_SIZE`, `DELTA`) live in `backend/config.py`. The existing `POST /api/encrypt` and `POST /api/decrypt` endpoints will be reused as-is by the Phase 2 module — it will call them per-image in a loop, incrementing `frame_index` for each symbol. The `messages.py` store is already structured so a whole Morse sequence can sit under one `message_id`.
