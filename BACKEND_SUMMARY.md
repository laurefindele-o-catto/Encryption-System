# Backend Technical Architecture & Method Reference Summary

This document provides a comprehensive, detailed breakdown of every module, class, method, function, data schema, and configuration parameter in the backend of the **Optical DRPE Encryption System**.

---

## 1. Overview & Architecture

The backend is built with **FastAPI** and **NumPy**, structured according to a modular architecture:
- **API & Routing Layer** (`routers/`, `main.py`): Receives HTTP requests, validates payloads, and routes actions.
- **Orchestration Layer** (`controllers/`): Bridges API endpoints with domain logic, manages ephemeral memory state, and handles file transformations.
- **Domain & Cryptographic Engine** (`services/drpe.py`, `services/keys.py`): Pure, deterministic implementation of 4-f Double Random Phase Encryption (DRPE) and SHA-256 key derivation.
- **Utility & Storage Layer** (`services/base_image.py`, `services/image_utils.py`, `services/messages.py`): Handles PIL/NumPy array conversions, lossless Base64 encoding/decoding, base image synthesis, and message frame storage.
- **Phase 2 Modular Extension Stubs** (`services/encoding/`): Interface specifications for future Morse code conversion and differential brightness block modulation.
- **Test Suite** (`tests/test_drpe.py`): Automated integration and unit test coverage.

```
                  ┌───────────────────────────────┐
                  │    HTTP Client / Frontend     │
                  └───────────────┬───────────────┘
                                  │
                          GET / POST requests
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │     backend/main.py     │
                     └────────────┬────────────┘
                                  │
                                  ▼
                   ┌─────────────────────────────┐
                   │ routers/image_router.py     │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │ controllers/image_controller.py │
                 └────────────────┬────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ services/drpe.py │    │services/base_img │    │services/img_utils│
└────────┬─────────┘    └──────────────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐
│ services/keys.py │
└──────────────────┘
```

---

## 2. File-by-File Detailed Summary

### 2.1 [`backend/main.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/main.py)
**Purpose**: Application entry point for the FastAPI web framework. Configures CORS middleware and registers application routes.

* **Variables / Application Instances**:
  * `app`: `FastAPI` instance initialized with title `"DRPE Phase 1 Demo API"`.
* **Middlewares & Routers**:
  * `CORSMiddleware`: Configured with `allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"]` to allow web frontend clients to connect.
  * `app.include_router(image_router)`: Mounts `/api` routes defined in `routers/image_router.py`.
* **Functions / Handlers**:
  * [`health()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/main.py#L34-L36)
    * **HTTP Route**: `GET /api/health`
    * **Parameters**: None
    * **Return Type**: `dict` (`{"status": "ok"}`)
    * **Purpose**: Provides a lightweight liveness check for monitoring and frontend sanity checks.

---

### 2.2 [`backend/config.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/config.py)
**Purpose**: Single source of truth for global constants, file paths, and Phase 2 differential-brightness parameters.

* **Constants**:
  * `_BACKEND_DIR` (`str`): Absolute directory path of the `backend` module directory.
  * `DATA_DIR` (`str`): Absolute path to the data storage folder (`backend/data`).
  * `BASE_IMAGE_PATH` (`str`): Path to the base reference image file (`backend/data/base_image.png`).
  * `DEFAULT_SEED` (`str`): Default seed string (`"phase1-demo"`).
  * `DEFAULT_BASE_IMAGE_SIZE` (`int`): Default dimension (`256`) for synthesized fallback grayscale images.
  * `BLOCK_A_COORDS` (`tuple[int, int]`): Top-left pixel coordinate `(10, 10)` for Block A in Phase 2 encoding.
  * `BLOCK_B_COORDS` (`tuple[int, int]`): Top-left pixel coordinate `(10, 50)` for Block B in Phase 2 encoding.
  * `BLOCK_SIZE` (`int`): Edge length in pixels (`16`) for modulation blocks.
  * `DELTA` (`int`): Brightness modulation delta (`8`) applied across differential blocks.

---

### 2.3 [`backend/routers/image_router.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/image_router.py)
**Purpose**: Defines HTTP endpoint routes, specifying request parameters and Pydantic response schemas.

* **Variables**:
  * `router`: `APIRouter` instance with prefix `/api`.
* **Functions / Handlers**:
  * [`encrypt(cover_image: UploadFile, seed_p1: str, seed_p2: str)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/image_router.py#L24-L34)
    * **HTTP Route**: `POST /api/encrypt` (Form Data)
    * **Parameters**:
      * `cover_image`: `UploadFile` — User uploaded image file.
      * `seed_p1`: `str` — Spatial domain key seed.
      * `seed_p2`: `str` — Frequency domain key seed.
    * **Return Type**: `EncryptResponse`
    * **Purpose**: Receives uploaded cover image file and dual seeds, invoking `encrypt_controller` to generate DRPE ciphertext payload and display amplitude image.
  * [`decrypt(req: DecryptRequest)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/image_router.py#L37-L45)
    * **HTTP Route**: `POST /api/decrypt` (JSON Payload)
    * **Parameters**:
      * `req`: `DecryptRequest` Pydantic model containing `ciphertext_b64`, `ciphertext_height`, `ciphertext_width`, `seed_p1`, and `seed_p2`.
    * **Return Type**: `DecryptResponse`
    * **Purpose**: Accepts base64-encoded complex ciphertext and decryption seeds, delegating to `decrypt_controller`.
  * [`base_image()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/image_router.py#L48-L51)
    * **HTTP Route**: `GET /api/base-image`
    * **Parameters**: None
    * **Return Type**: `BaseImageResponse`
    * **Purpose**: Returns base reference image metadata and Base64 representation for frontend visualization.

---

### 2.4 [`backend/controllers/image_controller.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/image_controller.py)
**Purpose**: Controller layer handling file conversions, exception wrapping, state management, and orchestrating operations between services and routers.

* **State**:
  * `_last_cover`: Module-level global variable (`np.ndarray | None`) retaining the last encrypted cover image array to perform exact match verification upon decryption.
* **Functions**:
  * [`encrypt_controller(cover_image: UploadFile, seed_p1: str, seed_p2: str)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/image_controller.py#L38-L70)
    * **Parameters**: `cover_image: UploadFile`, `seed_p1: str`, `seed_p2: str`
    * **Return Type**: `EncryptResponse`
    * **Purpose**:
      1. Loads base image array via `get_base_image()`.
      2. Converts uploaded file into 2D float64 grayscale array using `file_to_array()`.
      3. Executes `drpe_encrypt()`.
      4. Stores cover image array in `_last_cover`.
      5. Serializes complex array to Base64 string via `complex_to_b64()`.
      6. Converts amplitude image to Base64 PNG via `array_to_base64()`.
      7. Computes Parseval energy metrics using `energy()`.
  * [`decrypt_controller(ciphertext_b64: str, ciphertext_height: int, ciphertext_width: int, seed_p1: str, seed_p2: str)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/image_controller.py#L73-L113)
    * **Parameters**: `ciphertext_b64: str`, `ciphertext_height: int`, `ciphertext_width: int`, `seed_p1: str`, `seed_p2: str`
    * **Return Type**: `DecryptResponse`
    * **Purpose**:
      1. Reconstructs 2D complex128 array using `b64_to_complex()`.
      2. Retrieves base image using `get_base_image()`.
      3. Runs `drpe_decrypt()`.
      4. Checks exact array equality with `_last_cover` using `np.allclose(atol=1e-15)` if dimensions match.
      5. Formats Base64 PNG image and returns response payload.
  * [`get_base_image_controller()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/image_controller.py#L116-L122)
    * **Parameters**: None
    * **Return Type**: `BaseImageResponse`
    * **Purpose**: Encodes cached base image array into Base64 PNG string and returns shape metadata.

---

### 2.5 [`backend/schemas/image_schema.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/schemas/image_schema.py)
**Purpose**: Pydantic models for strict data structure definition and input validation.

* **Classes**:
  * `ImageResponse`: Standard image response containing Base64 encoded PNG (`image: str`).
  * `EncryptResponse`: Response payload for POST `/api/encrypt`.
    * `ciphertext_b64`: `str` (Base64 string of complex128 ciphertext).
    * `ciphertext_shape`: `list[int]` (`[height, width]`).
    * `image`: `str` (Base64 PNG of spatial amplitude display image).
    * `energy`: `float` (Parseval energy sum of display image).
    * `cover_energy`: `float` (Parseval energy sum of original cover image).
  * `DecryptRequest`: Input payload for POST `/api/decrypt`.
    * `ciphertext_b64`: `str`
    * `ciphertext_height`: `int`
    * `ciphertext_width`: `int`
    * `seed_p1`: `str`
    * `seed_p2`: `str`
  * `DecryptResponse`: Response payload for POST `/api/decrypt`.
    * `image`: `str` (Base64 PNG of recovered image).
    * `energy`: `float` (Parseval energy sum of recovered image).
    * `match_with_cover`: `bool` (Indicates exact bitwise match with stored cover image).
  * `BaseImageResponse`: Response payload for GET `/api/base-image`.
    * `image`: `str` (Base64 PNG of base reference image).
    * `shape`: `list[int]` (`[height, width]`).

---

### 2.6 [`backend/services/drpe.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py)
**Purpose**: Pure mathematical implementation of 4-f Double Random Phase Encryption (DRPE) and decryption using Fast Fourier Transforms (FFT).

* **Mathematical Model**:
  $$\text{Encrypt: } c = \mathcal{F}^{-1}\left\{ \mathcal{F}\left\{ I_{\text{cover}} \cdot e^{j P_1} \right\} \cdot e^{j P_2} \right\}$$
  $$\text{Decrypt: } I_{\text{recovered}} = \text{Re}\left( \mathcal{F}^{-1}\left\{ \mathcal{F}\{c\} \cdot e^{-j P_2} \right\} \cdot e^{-j P_1} \right)$$

* **Functions**:
  * [`_shape_seed(base_image: np.ndarray, frame_index: int, shape: tuple[int, int] | None = None)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py#L34-L41)
    * **Parameters**: `base_image: np.ndarray`, `frame_index: int`, `shape: tuple[int, int] | None`
    * **Return Type**: `bytes`
    * **Purpose**: Hashes base image bytes and target shape via SHA-256 (taking top 8 bytes) combined with 8-byte big-endian `frame_index`. Ensures distinct base images or canvas sizes yield unique phase distribution parameters.
  * [`generate_phase_masks(shape: tuple[int, int], base_image: np.ndarray, seed_p1: str, seed_p2: str, frame_index: int = 0)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py#L44-L76)
    * **Parameters**: `shape: tuple[int, int]`, `base_image: np.ndarray`, `seed_p1: str`, `seed_p2: str`, `frame_index: int`
    * **Return Type**: `tuple[np.ndarray, np.ndarray]`
    * **Purpose**: Deterministically derives spatial phase mask $P_1$ and frequency phase mask $P_2$. Derives initial seeds using `derive_key()`, mixes with domain tags (`0x50314D31` for $P_1$ and `0x50324D32` for $P_2$), and samples uniform distributions over $[0, 2\pi)$.
  * [`drpe_encrypt(cover_image: np.ndarray, base_image: np.ndarray, seed_p1: str, seed_p2: str, frame_index: int = 0)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py#L81-L122)
    * **Parameters**: `cover_image: np.ndarray`, `base_image: np.ndarray`, `seed_p1: str`, `seed_p2: str`, `frame_index: int`
    * **Return Type**: `dict` (`{"complex": c, "amplitude": |c|, "p1": p1, "p2": p2}`)
    * **Purpose**: Performs spatial phase rotation $P_1$, 2D FFT, frequency phase rotation $P_2$, and 2D IFFT to yield full complex ciphertext $c$ and display amplitude $|c|$.
  * [`drpe_decrypt(ciphertext_complex: np.ndarray, base_image: np.ndarray, seed_p1: str, seed_p2: str, frame_index: int = 0)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py#L125-L157)
    * **Parameters**: `ciphertext_complex: np.ndarray`, `base_image: np.ndarray`, `seed_p1: str`, `seed_p2: str`, `frame_index: int`
    * **Return Type**: `np.ndarray` (2D float64 recovered image matrix)
    * **Purpose**: Performs 2D FFT of complex ciphertext, subtracts phase mask $P_2$, computes 2D IFFT, subtracts spatial phase mask $P_1$, extracts real part, and clips output to $[0, 255]$.
  * [`energy(image: np.ndarray)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py#L159-L165)
    * **Parameters**: `image: np.ndarray`
    * **Return Type**: `float`
    * **Purpose**: Computes $\sum (\text{pixel}^2)$ over 2D array to quantify total optical energy (Parseval theorem conservation metric).

---

### 2.7 [`backend/services/base_image.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/base_image.py)
**Purpose**: Manages reference/base image loading, memory caching, and fallback synthetic generation.

* **State**:
  * `_SYNTH_SEED` (`int = 20240801`): Constant random seed for deterministic synthetic pattern creation.
  * `_cached` (`np.ndarray | None`): Global in-memory array cache.
* **Functions**:
  * [`_load_or_synthesize()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/base_image.py#L35-L46)
    * **Parameters**: None
    * **Return Type**: `np.ndarray`
    * **Purpose**: Checks if `BASE_IMAGE_PATH` exists on disk and loads it. If absent, generates deterministic uniform noise of size $256 \times 256$, writes to disk as PNG, and returns float64 array.
  * [`get_base_image()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/base_image.py#L49-L56)
    * **Parameters**: None
    * **Return Type**: `np.ndarray`
    * **Purpose**: Accessor returning cached base image array (loads on initial call).
  * [`base_image_shape()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/base_image.py#L59-L60)
    * **Parameters**: None
    * **Return Type**: `tuple[int, int]`
    * **Purpose**: Helper returning `(height, width)` shape of cached base image.

---

### 2.8 [`backend/services/image_utils.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py)
**Purpose**: Data format conversion helpers (PIL images, byte arrays, complex arrays, Base64 strings).

* **Functions**:
  * [`file_to_array(upload: UploadFile, target_shape: tuple[int, int] | None = None)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py#L9-L28)
    * **Parameters**: `upload: UploadFile`, `target_shape: tuple[int, int] | None`
    * **Return Type**: `np.ndarray`
    * **Purpose**: Asynchronously reads upload bytes, converts image to grayscale PIL Image, resizes via bicubic interpolation if `target_shape` is specified, and returns 2D float64 NumPy array.
  * [`array_to_base64(arr: np.ndarray)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py#L31-L37)
    * **Parameters**: `arr: np.ndarray`
    * **Return Type**: `str`
    * **Purpose**: Clips array values to $[0, 255]$, casts to uint8, converts to PNG bytes buffer, and encodes as Base64 string.
  * [`complex_to_b64(c: np.ndarray)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py#L40-L42)
    * **Parameters**: `c: np.ndarray` (complex128)
    * **Return Type**: `str`
    * **Purpose**: Encodes raw bytes of complex128 array to Base64 string for lossless transmission.
  * [`b64_to_complex(b64_str: str, shape: tuple[int, int])`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py#L45-L48)
    * **Parameters**: `b64_str: str`, `shape: tuple[int, int]`
    * **Return Type**: `np.ndarray`
    * **Purpose**: Decodes Base64 string into complex128 byte buffer and reshapes into 2D matrix matching `shape`.

---

### 2.9 [`backend/services/keys.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/keys.py)
**Purpose**: Derives independent, non-sequential per-frame seeds using cryptographic hashing.

* **Functions**:
  * [`derive_key(base_seed: str, frame_index: int)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/keys.py#L13-L21)
    * **Parameters**: `base_seed: str`, `frame_index: int`
    * **Return Type**: `int`
    * **Purpose**: Hashes formatted string `"{base_seed}:{frame_index}"` using SHA-256 and converts the first 16 hex characters into a 64-bit integer seed for random generator initialization.

---

### 2.10 [`backend/services/messages.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py)
**Purpose**: In-memory data store for multi-frame message transmission sequences.

* **Data Classes**:
  * `Frame`: Container for an individual encrypted frame (`frame_index: int`, `ciphertext_complex: np.ndarray`, `amplitude: np.ndarray`).
  * `Message`: Container for an overall transmission (`message_id: str`, `base_image: np.ndarray`, `seed_p1: str`, `seed_p2: str`, `frames: list[Frame]`).
* **State & Counters**:
  * `_messages`: Dictionary mapping `message_id` string to `Message` object.
  * `_id_counter`: Thread-safe monotonic sequence counter (`itertools.count(1)`).
* **Functions**:
  * [`new_message_id()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py#L48-L49): Generates sequential message identifiers (`"msg-000001"`).
  * [`create_message(seed_p1: str, seed_p2: str, base_image: np.ndarray)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py#L52-L56): Instantiates new `Message` object and registers it in `_messages`.
  * [`get_message(message_id: str)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py#L59-L62): Fetches `Message` object by ID or raises `KeyError`.
  * [`add_frame(message: Message, frame: Frame)`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py#L65-L66): Appends `Frame` instance to message's frame list.

---

### 2.11 Phase 2 Stubs Package ([`backend/services/encoding/`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/))
**Purpose**: Placeholder package defining interface specifications for Phase 2 differential brightness and Morse transmission. All methods raise `NotImplementedError` in Phase 1.

* **`text_to_morse.py`**:
  * [`text_to_morse(text: str) -> str`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/text_to_morse.py#L9-L26): Planned conversion of ASCII string into flat Morse string.
* **`morse_to_symbol_sequence.py`**:
  * [`morse_to_symbol_sequence(morse: str) -> list[int]`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/morse_to_symbol_sequence.py#L8-L30): Planned mapping of Morse characters to symbol integer states ($0$ through $4$).
* **`symbol_image.py`**:
  * [`generate_symbol_image(state: int, base_image: np.ndarray) -> np.ndarray`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/symbol_image.py#L15-L39): Planned differential brightness modulation on Block A (+Δ) and Block B (-Δ).
  * [`read_differential_brightness(image: np.ndarray) -> int`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/symbol_image.py#L42-L60): Planned extraction of mean block brightness difference $\text{sign}(\text{Mean}(A) - \text{Mean}(B))$ from decrypted image.
* **`morse_to_text.py`**:
  * [`morse_to_text(morse: str) -> str`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/morse_to_text.py#L8-L22): Planned conversion of flat Morse string back to plaintext ASCII.

---

### 2.12 Test Suite ([`backend/tests/test_drpe.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py))
**Purpose**: Automated test suite executing unit tests on key derivation and mathematical DRPE fidelity, alongside integration tests via `fastapi.testclient.TestClient`.

* **Test Functions**:
  * [`test_key_derivation()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L27-L37): Asserts key determinism and uniqueness across different seeds and frame indices.
  * [`test_drpe_roundtrip_fidelity()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L39-L51): Verifies that encrypting and decrypting with identical dual seeds yields exact original cover array ($\text{max error} < 10^{-15}$).
  * [`test_drpe_partial_and_wrong_seed_rejection()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L54-L74): Verifies that using incorrect $P_1$, incorrect $P_2$, or both incorrect results in garbled noise ($\text{max error} > 10.0$).
  * [`test_parseval_energy_invariance()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L76-L80): Asserts accuracy of `energy()` on known matrix.
  * [`test_api_health()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L83-L87): Asserts status 200 and response payload of `GET /api/health`.
  * [`test_api_base_image()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L90-L98): Asserts response format of `GET /api/base-image`.
  * [`test_api_encrypt_decrypt_flow()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L100-L165): Integration test running full HTTP encryption and decryption flow, checking `match_with_cover` boolean behavior.
  * [`test_variable_size_image_encryption()`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py#L167-L205): Tests handling of non-square rectangular images (e.g. $384 \times 512$) end-to-end.

---

## 3. Summary Map of Backend API Endpoints

| Endpoint | Method | Input Payload | Controller Handler | Response Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | None | `health()` in `main.py` | `{"status": "ok"}` | Liveness check |
| `/api/base-image` | `GET` | None | `get_base_image_controller()` | `BaseImageResponse` | Fetch reference base image & shape |
| `/api/encrypt` | `POST` | Multipart Form: `cover_image`, `seed_p1`, `seed_p2` | `encrypt_controller()` | `EncryptResponse` | Perform DRPE encryption & return complex ciphertext + display PNG |
| `/api/decrypt` | `POST` | JSON: `ciphertext_b64`, `ciphertext_height`, `ciphertext_width`, `seed_p1`, `seed_p2` | `decrypt_controller()` | `DecryptResponse` | Decrypt complex ciphertext & return recovered image + match indicator |
