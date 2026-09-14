# Comprehensive Backend Documentation: Signal Project Encryption System

## Table of Contents
1. [Overview & Mathematical Foundations](#1-overview--mathematical-foundations)
2. [Project Architecture & Directory Layout](#2-project-architecture--directory-layout)
3. [Configuration Layer](#3-configuration-layer)
   - [`config.py`](#configpy)
4. [FastAPI Server Entry Point](#4-fastapi-server-entry-point)
   - [`main.py`](#mainpy)
5. [API Routing Layer](#5-api-routing-layer)
   - [`routers/image_router.py`](#routersimage_routerpy)
   - [`routers/text_router.py`](#routerstext_routerpy)
6. [Controller & Orchestration Layer](#6-controller--orchestration-layer)
   - [`controllers/image_controller.py`](#controllersimage_controllerpy)
   - [`controllers/text_controller.py`](#controllerstext_controllerpy)
7. [Pydantic Validation Schemas](#7-pydantic-validation-schemas)
   - [`schemas/image_schema.py`](#schemasimage_schemapy)
8. [Core Cryptographic Engine](#8-core-cryptographic-engine)
   - [`services/drpe.py`](#servicesdrpepy)
   - [`services/keys.py`](#serviceskeyspy)
9. [In-Memory State & Messaging Store](#9-in-memory-state--messaging-store)
   - [`services/messages.py`](#servicesmessagespy)
10. [Image Processing & Serialization Utilities](#10-image-processing--serialization-utilities)
    - [`services/image_utils.py`](#servicesimage_utilspy)
11. [Steganographic & Optical Morse Encoding Layer](#11-steganographic--optical-morse-encoding-layer)
    - [`services/encoding/symbol_image.py`](#servicesencodingsymbol_imagepy)
    - [`services/encoding/morse_to_symbol_sequence.py`](#servicesencodingmorse_to_symbol_sequencepy)
    - [`services/encoding/text_to_morse.py`](#servicesencodingtext_to_morsepy)
    - [`services/encoding/morse_to_text.py`](#servicesencodingmorse_to_textpy)
12. [High-Level Transmission Pipelines](#12-high-level-transmission-pipelines)
    - [`services/text_encryption.py`](#servicestext_encryptionpy)
    - [`services/text_decryption.py`](#servicestext_decryptionpy)

---

## 1. Overview & Mathematical Foundations

This backend implements an optical encryption system based on **Double Random Phase Encryption (DRPE)** operating within a simulated 4-f optical Fourier processor, integrated with differential optical steganography for covert text transmission.

### 1.1 DRPE Mathematical Model
DRPE transforms an input spatial signal $f(x, y)$ (e.g. an image or encoded symbol image) into a complex stationary white-noise distribution $c(x, y)$ via two independent random phase distributions $P_1(x, y)$ and $P_2(u, v)$ defined uniformly over $[0, 2\pi)$.

#### Encryption Pipeline:
1. **Spatial Domain Phase Modulation**:
   $$s(x, y) = f(x, y) \cdot \exp(j \cdot P_1(x, y))$$
   Modulates the input image amplitude with the first random phase mask $P_1$.
2. **First Lens / 2D Fourier Transform**:
   $$G(u, v) = \mathcal{F}_{2D}\{s(x, y)\} = \iint_{-\infty}^{\infty} s(x, y) \exp(-j 2\pi (ux + vy)) \, dx \, dy$$
3. **Fourier Plane Phase Modulation**:
   $$G'(u, v) = G(u, v) \cdot \exp(j \cdot P_2(u, v))$$
   Rotates the frequency spectrum phases by the second random phase mask $P_2$.
4. **Second Lens / 2D Inverse Fourier Transform**:
   $$c(x, y) = \mathcal{F}_{2D}^{-1}\{G'(u, v)\} = \iint_{-\infty}^{\infty} G'(u, v) \exp(j 2\pi (ux + vy)) \, du \, dv$$
   The output $c(x, y)$ is a complex-valued array with uniform amplitude statistics and random phase.
5. **Amplitude Representation**:
   $$A(x, y) = |c(x, y)| = \sqrt{\text{Re}(c)^2 + \text{Im}(c)^2}$$

#### Decryption Pipeline:
Given the complex ciphertext $c(x, y)$ and identical phase distributions $P_1$ and $P_2$:
1. **Fourier Transform of Ciphertext**:
   $$G'(u, v) = \mathcal{F}_{2D}\{c(x, y)\}$$
2. **Frequency Mask Demodulation**:
   $$G(u, v) = G'(u, v) \cdot \exp(-j \cdot P_2(u, v))$$
3. **Inverse Fourier Transform to Spatial Domain**:
   $$s(x, y) = \mathcal{F}_{2D}^{-1}\{G(u, v)\}$$
4. **Spatial Mask Demodulation & Intensity Extraction**:
   $$f(x, y) = \text{Re}\{s(x, y) \cdot \exp(-j \cdot P_1(x, y))\}$$

#### Energy Invariance (Parseval's Theorem):
Under the unitary discrete Fourier transform:
$$\sum_{x, y} |f(x, y)|^2 = \sum_{x, y} |c(x, y)|^2$$
Total signal energy is strictly conserved between the input spatial domain and the encrypted domain.

---

## 2. Project Architecture & Directory Layout

```text
backend/
├── main.py                    # FastAPI entrypoint, middleware, route mounting, healthcheck
├── config.py                  # Single source of truth for coordinates, block dimensions, constants
├── routers/                   # HTTP endpoint definitions (unpacks payloads, validates schemas)
│   ├── image_router.py        # POST /api/encrypt, POST /api/decrypt-with-key-images
│   └── text_router.py         # POST /api/text/encrypt, POST /api/text/decrypt
├── controllers/               # Business orchestration (I/O, message lookup, service delegation)
│   ├── image_controller.py    # Image encryption/decryption controller
│   └── text_controller.py     # Text sequence encryption/decryption controller
├── schemas/                   # Pydantic data validation schemas
│   └── image_schema.py        # Request and response models
├── services/                  # Pure domain logic
│   ├── drpe.py                # Pure 2D FFT/IFFT DRPE math implementation
│   ├── keys.py                # Scrypt & HMAC-SHA256 hierarchical key derivation
│   ├── messages.py            # In-memory ephemeral storage for messages & frames
│   ├── image_utils.py         # Base64, complex128, PIL Image, and hash canonicalization
│   ├── text_encryption.py     # Pipeline: Text -> Morse -> Symbols -> Differential Images -> DRPE
│   ├── text_decryption.py     # Pipeline: DRPE -> Differential Extraction -> Morse -> Text
│   └── encoding/              # Steganographic primitives
│       ├── symbol_image.py    # Differential 2-bit pair patch modulation
│       ├── morse_to_symbol_sequence.py # Morse char to SymbolState enum mapping
│       ├── text_to_morse.py   # Plaintext string to ITU Morse code string
│       └── morse_to_text.py   # Morse string to plaintext string
```

---

## 3. Configuration Layer

### `config.py`
Defines shared immutable parameters across sender and receiver.

#### Line-by-Line Syntax & Details:
- `_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))`: Computes the absolute path of `config.py` and retrieves its parent folder directory (`backend/`).
- `DATA_DIR = os.path.join(_BACKEND_DIR, "data")`: Constructs path to file data storage.
- `DEFAULT_SEED = "phase1-demo"`: Fallback entropy seed for legacy routines.
- `BLOCK_A_COORDS = (10, 10)`: Top-left `(row, col)` coordinates for block $A$.
- `BLOCK_B_COORDS = (10, 50)`: Top-left `(row, col)` coordinates for block $B$.
- `BLOCK_C_COORDS = (50, 10)`: Top-left `(row, col)` coordinates for block $C$.
- `BLOCK_D_COORDS = (50, 50)`: Top-left `(row, col)` coordinates for block $D$.
- `BLOCK_SIZE = 16`: Height and width of each modulation block ($16 \times 16 = 256$ pixels).
- `DELTA = 8`: The differential brightness shift value ($\pm 8$ pixel values).

---

## 4. FastAPI Server Entry Point

### `main.py`
Initializes the ASGI server, configures CORS, mounts routers, and registers health check routes.

#### Line-by-Line Syntax & Details:
- `app = FastAPI(title="DRPE Phase 1 Demo API")`: Creates the core FastAPI application instance with OpenAPI metadata.
- `app.add_middleware(CORSMiddleware, ...)`: Configures Cross-Origin Resource Sharing:
  - `allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"]`: Permits client-side JavaScript from Vite dev ports and wildcard origins.
  - `allow_credentials=True`: Allows credentials (cookies, HTTP authorization headers).
  - `allow_methods=["*"]`: Permits all HTTP methods (`GET`, `POST`, `OPTIONS`, etc.).
  - `allow_headers=["*"]`: Permits arbitrary headers in client requests.
- `app.include_router(image_router)`: Mounts image encryption endpoints under `/api`.
- `app.include_router(text_router)`: Mounts text encryption endpoints under `/api/text`.
- `@app.get("/api/health")`: Route decorator binding HTTP `GET /api/health`.
- `def health() -> dict`:
  - **Syntax**: Standard synchronous endpoint handler.
  - **Execution**: Returns JSON `{"status": "ok"}` with default status code `200 OK`.

---

## 5. API Routing Layer

### `routers/image_router.py`
Handles multipart form uploads for image encryption and decryption.

#### Functions:
- `encrypt(...)`:
  - **Syntax**:
    ```python
    @router.post("/encrypt", response_model=EncryptResponse)
    async def encrypt(
        cover_image: UploadFile,
        secret_key_image: UploadFile = File(...),
        secret_password: str = Form(...),
        message_id: str | None = Form(None),
        frame_index: int = Form(0),
    ) -> EncryptResponse
    ```
  - **Line Analysis**:
    - `@router.post("/encrypt", response_model=EncryptResponse)`: Specifies POST endpoint and validates return type against `EncryptResponse`.
    - `cover_image: UploadFile`: The image to be encrypted, streamed as multipart file.
    - `secret_key_image: UploadFile = File(...)`: Required secret key image file.
    - `secret_password: str = Form(...)`: Form-data string containing the password or password image hash.
    - `message_id: str | None = Form(None)`: Optional pre-assigned message UUID.
    - `frame_index: int = Form(0)`: Sequence index of the frame (default `0`).
    - `return await encrypt_controller(...)`: Delegates asynchronously to controller logic.
- `decrypt_with_key_images(...)`:
  - **Syntax**:
    ```python
    @router.post("/decrypt-with-key-images", response_model=DecryptResponse)
    async def decrypt_with_key_images(
        ciphertext_b64: str | None = Form(None),
        ciphertext_shape: str | None = Form(None),
        secret_key_image: UploadFile = File(...),
        secret_password: str = Form(...),
        frame_index: int = Form(0),
        message_id: str = Form(...),
        salt_b64: str = Form(...),
    ) -> DecryptResponse
    ```
  - **Line Analysis**:
    - Unpacks form fields: Base64 ciphertext, shape string, secret key image, password string, frame index, message ID, and Base64 salt.
    - `shape = json.loads(ciphertext_shape) if ciphertext_shape else None`: Parses shape string (e.g. `"[512, 512, 3]"`) into integer list. Raises HTTP 400 `HTTPException` on JSON syntax errors.
    - Calls `decrypt_controller(...)` and returns `DecryptResponse`.

---

### `routers/text_router.py`
Handles text-to-image sequence operations.

#### Functions:
- `encrypt_text(...)`:
  - **Syntax**:
    ```python
    @router.post("/encrypt", response_model=TextEncryptResponse)
    async def encrypt_text(
        secret_text: str = Form(...),
        base_image: UploadFile = File(...),
        secret_key_image: UploadFile = File(...),
        secret_password: str = Form(...),
    ) -> TextEncryptResponse
    ```
  - **Line Analysis**:
    - Receives `secret_text`, `base_image` template, `secret_key_image`, and `secret_password`.
    - Returns `TextEncryptResponse` populated by `encrypt_text_controller`.
- `decrypt_text(...)`:
  - **Syntax**:
    ```python
    @router.post("/decrypt", response_model=TextDecryptResponse)
    async def decrypt_text(
        message_id: str = Form(...),
        secret_key_image: UploadFile = File(...),
        secret_password: str = Form(...),
    ) -> TextDecryptResponse
    ```
  - **Line Analysis**:
    - Takes `message_id`, receiver's `secret_key_image`, and `secret_password`.
    - Reconstructs text frames and returns `TextDecryptResponse`.

---

## 6. Controller & Orchestration Layer

### `controllers/image_controller.py`

#### Module Variables:
- `_last_cover: np.ndarray | None = None`: Module-level storage holding the most recently encrypted cover image for ground-truth verification during decryption.

#### Functions:
- `encrypt_controller(...)`:
  - **Syntax**:
    ```python
    async def encrypt_controller(
        cover_image: UploadFile,
        secret_key_image: UploadFile,
        secret_password: str,
        message_id: str | None = None,
        frame_index: int = 0,
    ) -> EncryptResponse
    ```
  - **Analysis**:
    - Reads `cover_image` into a `float64` array via `file_to_array`.
    - Reads raw bytes of `secret_key_image`.
    - Delegates core encryption to `services.image_encryption.encrypt_image_message(...)`.
    - Returns `EncryptResponse` containing amplitude display image PNG, energy metrics, message ID, and Base64 salt.

- `decrypt_controller(...)`:
  - **Syntax**:
    ```python
    async def decrypt_controller(
        message_id: str,
        secret_key_image: UploadFile,
        secret_password: str,
        frame_index: int = 0,
        **kwargs,
    ) -> DecryptResponse
    ```
  - **Analysis**:
    - Reads raw bytes of `secret_key_image`.
    - Delegates core decryption to `services.image_decryption.decrypt_image_message(...)`.
    - Retrieves stored ciphertext and salt from `Message` in `messages.py` by `message_id`.
    - Reconstructs original image via inverse DRPE and verifies exact element-wise fidelity against `message.base_image`.
    - Returns `DecryptResponse` containing reconstructed image Base64, energy, and `match_with_cover`.

---

### `controllers/text_controller.py`

#### Functions:
- `encrypt_text_controller(...)`:
  - **Syntax**:
    ```python
    async def encrypt_text_controller(
        secret_text: str,
        base_image: UploadFile,
        secret_key_image: UploadFile,
        secret_password: str,
    ) -> TextEncryptResponse
    ```
  - **Line Analysis**:
    - Converts `base_image` upload into NumPy array via `file_to_array(base_image)`.
    - Reads raw bytes of `secret_key_image`.
    - Delegates to `services.text_encryption.encrypt_text_message(...)`.
    - Converts preview dictionaries to `TextFramePreview` models.
    - Returns `TextEncryptResponse`.

- `decrypt_text_controller(...)`:
  - **Syntax**:
    ```python
    async def decrypt_text_controller(
        message_id: str,
        secret_key_image: UploadFile,
        secret_password: str,
    ) -> TextDecryptResponse
    ```
  - **Line Analysis**:
    - Reads binary data from `secret_key_image`.
    - Delegates to `services.text_decryption.decrypt_text_message(...)`.
    - Converts diagnostic dictionaries to `TextDecryptedFrame` models.
    - Returns `TextDecryptResponse`.

---

## 7. Pydantic Validation Schemas

### `schemas/image_schema.py`
Defines data contracts for HTTP requests and responses.

- `ImageResponse(BaseModel)`:
  - `image: str`: Base64-encoded PNG image string.
- `EncryptResponse(BaseModel)`:
  - `ciphertext_b64: str`: Losslessly serialized `complex128` binary payload.
  - `ciphertext_shape: list[int]`: Dimension list `[height, width, channels]` or `[height, width]`.
  - `image: str`: Displayable magnitude image ($|c|$) encoded as PNG Base64.
  - `energy: float`: Calculated Parseval energy $\sum |c|^2$.
  - `cover_energy: float`: Parseval energy of input cover image $\sum |f|^2$.
  - `message_id: str`: Unique transmission identifier.
  - `salt_b64: str`: Base64 representation of the 16-byte cryptographic salt.
- `DecryptResponse(BaseModel)`:
  - `image: str`: Base64 PNG of decrypted reconstructed image.
  - `energy: float`: Parseval energy of the recovered image.
  - `match_with_cover: bool`: True if identical to original cover within $10^{-15}$ tolerance.
- `TextFramePreview(BaseModel)`:
  - `frame_index: int`: Index of the frame in the sequence.
  - `image: str`: Base64 PNG preview of ciphertext amplitude.
  - `energy: float`: Frame energy value.
- `TextEncryptResponse(BaseModel)`:
  - `message_id: str`, `salt_b64: str`, `morse: str`, `symbols: list[int]`, `frame_count: int`, `base_image_shape: list[int]`, `previews: list[TextFramePreview]`.
- `TextDecryptedFrame(BaseModel)`:
  - `frame_index: int`, `symbol: int`, `symbol_name: str` (e.g. `"DOT"`).
- `TextDecryptResponse(BaseModel)`:
  - `message_id: str`, `text: str`, `morse: str`, `symbols: list[int]`, `frame_count: int`, `success: bool`, `image: str | None`, `frames: list[TextDecryptedFrame]`.

---

## 8. Core Cryptographic Engine

### `services/drpe.py`

#### Functions:
- `mask_seed(material: bytes) -> int`:
  ```python
  def mask_seed(material: bytes) -> int:
      digest = hashlib.sha256(material).digest()
      return int.from_bytes(digest[:16], "big")
  ```
  - Computes SHA-256 over key material bytes.
  - Extracts first 16 bytes (128 bits) and interprets as unsigned big-endian integer.
  - Returns integer seed for NumPy's PRNG.

- `generate_phase_masks(shape, p1_material, p2_material)`:
  ```python
  def generate_phase_masks(
      shape: tuple[int, ...],
      p1_material: bytes,
      p2_material: bytes,
  ) -> tuple[np.ndarray, np.ndarray]:
      rng_p1 = np.random.default_rng(mask_seed(p1_material))
      rng_p2 = np.random.default_rng(mask_seed(p2_material))
      p1 = rng_p1.uniform(0.0, 2.0 * np.pi, size=shape).astype(np.float64)
      p2 = rng_p2.uniform(0.0, 2.0 * np.pi, size=shape).astype(np.float64)
      return p1, p2
  ```
  - Initializes independent PCG-64 pseudorandom generators `rng_p1` and `rng_p2`.
  - Samples uniform continuous values over $[0, 2\pi)$ radians matching `shape`.
  - Returns `(p1, p2)` float64 arrays.

- `drpe_encrypt(cover_image, p1_material, p2_material) -> dict`:
  ```python
  def drpe_encrypt(cover_image: np.ndarray, p1_material: bytes, p2_material: bytes) -> dict:
      p1, p2 = generate_phase_masks(cover_image.shape, p1_material, p2_material)
      cover_spatial = cover_image * np.exp(1j * p1)
      g = np.fft.fft2(cover_spatial, axes=(0, 1))
      g_prime = g * np.exp(1j * p2)
      c = np.fft.ifft2(g_prime, axes=(0, 1))
      return {
          "complex": c.astype(np.complex128),
          "amplitude": np.abs(c).astype(np.float64),
          "p1": p1,
          "p2": p2,
      }
  ```
  - `cover_image * np.exp(1j * p1)`: Spatial phase modulation by Euler's identity $e^{j \theta} = \cos \theta + j \sin \theta$.
  - `np.fft.fft2(cover_spatial, axes=(0, 1))`: 2D Fast Fourier Transform along spatial axes (0 and 1).
  - `g * np.exp(1j * p2)`: Fourier domain phase rotation.
  - `np.fft.ifft2(g_prime, axes=(0, 1))`: 2D Inverse Fast Fourier Transform yielding complex ciphertext array $c$.
  - Returns dictionary with complex ciphertext, magnitude array (`np.abs(c)`), and generated masks.

- `drpe_decrypt(ciphertext_complex, p1, p2) -> np.ndarray`:
  ```python
  def drpe_decrypt(ciphertext_complex: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
      g_prime = np.fft.fft2(ciphertext_complex, axes=(0, 1))
      g = g_prime * np.exp(-1j * p2)
      cover_spatial = np.fft.ifft2(g, axes=(0, 1))
      cover = cover_spatial * np.exp(-1j * p1)
      return np.clip(np.round(cover.real), 0, 255)
  ```
  - Applies 2D FFT to complex ciphertext.
  - Demodulates frequency phase mask by multiplying with complex conjugate $\exp(-j P_2)$.
  - Applies 2D IFFT to return to spatial plane.
  - Demodulates spatial mask by multiplying with complex conjugate $\exp(-j P_1)$.
  - Extracts real part (`cover.real`), rounds to nearest integer, and clips values to dynamic range $[0, 255]$.

- `energy(image: np.ndarray) -> float`:
  ```python
  def energy(image: np.ndarray) -> float:
      return float(np.sum(image.astype(np.float64) ** 2))
  ```
  - Calculates the Frobenius energy $\sum |I(x, y)|^2$, used for Parseval conservation verification.

---

### `services/keys.py`

#### Functions:
- `derive_password_key(password: str, salt: bytes) -> bytes`:
  ```python
  return hashlib.scrypt(
      password.encode("utf-8"),
      salt=salt, 
      n=2**14,
      r=8,
      p=1,
      dklen=32,
  )
  ```
  - Implements RFC 7914 Scrypt password-based key derivation.
  - `n=16384` (CPU/memory cost), `r=8` (RAM block size), `p=1` (parallelization).
  - Produces 256-bit (32-byte) key resistant to ASIC/GPU brute-force attacks.

- `derive_master_key(password_key: bytes, secret_image_digest: bytes) -> bytes`:
  ```python
  material = (b"DRPE-MASTER-v1" + password_key + secret_image_digest)
  return hashlib.sha256(material).digest()
  ```
  - Combines domain separator, password key, and image digest using SHA-256 to produce master secret.

- `derive_frame_key(master_key: bytes, message_id: str, frame_index: int, purpose: bytes) -> bytes`:
  ```python
  context = (
      b"DRPE-v1"
      + purpose
      + message_id.encode("utf-8")
      + frame_index.to_bytes(8, "big")
  )
  return hmac.new(master_key, context, hashlib.sha256).digest()
  ```
  - Constructs unique context string per frame and per purpose (`b"DRPE/P1"` or `b"DRPE/P2"`).
  - Uses HMAC-SHA256 as a cryptographically strong pseudorandom function (PRF).
  - Guarantees forward and backward secrecy across frames: compromise of frame $k$ reveals zero information about frame $k+1$.

- `derive_image_password_keys(...) -> tuple[bytes, bytes]`:
  - Executes complete hierarchy: `derive_password_key` $\to$ `derive_master_key` $\to$ `derive_frame_key` for P1 and P2.
  - Returns `(p1_material, p2_material)`.

- `derive_key(seed: str, frame_index: int = 0) -> bytes`:
  - Legacy helper calculating SHA-256 of `f"{seed}:{frame_index}"`.

---

## 9. In-Memory State & Messaging Store

### `services/messages.py`

#### Data Classes:
- `@dataclass class Frame`:
  - `frame_index: int`: Zero-based frame position in the sequence.
  - `ciphertext_complex: np.ndarray`: Complex128 ciphertext array.
  - `amplitude: np.ndarray`: Float64 magnitude array.
- `@dataclass class Message`:
  - `message_id: str`: Unique transmission identifier.
  - `message_type: str`: `"image"` or `"text"`.
  - `secret_key_image: bytes | None`: Alice's sender key image bytes.
  - `secret_password: str | None`: Alice's password.
  - `salt: bytes | None`: 16-byte cryptographic salt.
  - `base_image: np.ndarray | None`: Base image array.
  - `total_frames: int | None`: Total expected frames.
  - `metadata: dict`: Transmission metadata (Morse string, symbol array).
  - `receiver_secret_key_image: bytes | None`: Bob's uploaded key image bytes.
  - `receiver_password: str | None`: Bob's supplied password.
  - `frames: list[Frame]`: List of received frames.

#### Functions:
- `new_message_id() -> str`: Formats monotonic counter `itertools.count(1)` into `"msg-XXXXXX"`.
- `create_message(...) -> Message`: Validates message type, checks uniqueness of `msg_id`, creates and saves `Message` in `_messages` dictionary.
- `get_message(message_id: str) -> Message`: Retrieves message or raises `KeyError`.
- `add_frame(message: Message, frame: Frame) -> None`: Validates non-negative index, verifies no duplicate `frame_index`, checks `frame_index < total_frames`, and appends frame.
- `get_frame(message: Message, frame_index: int) -> Frame`: Finds frame by index or raises `KeyError`.
- `get_ordered_frames(message: Message, require_complete: bool = False) -> list[Frame]`: Returns frames sorted by `frame_index`. If `require_complete=True`, verifies indices form contiguous sequence `0..N-1`.
- `get_messages(message_type: str | None = None) -> list[Message]`: Returns all messages, optionally filtered by type.

---

## 10. Image Processing & Serialization Utilities

### `services/image_utils.py`

#### Functions:
- `file_to_array(upload: UploadFile, target_shape=None) -> np.ndarray`:
  - Reads uploaded bytes and checks length $\ge 8$ bytes.
  - Opens image via `PIL.Image.open(...)` and converts to RGB.
  - Resizes to `target_shape` via bicubic interpolation if specified.
  - Returns `np.array(img, dtype=np.float64)`.
- `array_to_base64(arr: np.ndarray) -> str`:
  - Rounds array, clips to $[0, 255]$, and casts to `uint8`.
  - Encodes image into PNG format in memory buffer `io.BytesIO()`.
  - Returns UTF-8 Base64 string.
- `array_to_base64_preview(arr: np.ndarray, max_size: int = 512) -> str`:
  - Scales image to fit `max_size` bounding box via Lanczos resampling before encoding to Base64 PNG.

- `canonicalize_key_image(raw: bytes) -> np.ndarray`:
  - Opens raw image bytes, converts to RGB, and resizes to standard dimensions $256 \times 256$ pixels using Lanczos filtering.
  - Returns `uint8` array of shape `(256, 256, 3)`.
- `hash_canonical_key_image(pixels: np.ndarray) -> bytes`:
  - Appends header `b"DRPE-KEY-IMAGE-v1"`, shape buffer, and raw pixel bytes.
  - Computes and returns SHA-256 digest (32 bytes).
- `key_image_digest(upload: UploadFile) -> bytes`:
  - Asynchronously reads upload and delegates to `canonicalize_key_image` and `hash_canonical_key_image`.

---

## 11. Steganographic & Optical Morse Encoding Layer

### `services/encoding/symbol_image.py`

#### Module Constants & Mapping:
```python
STATE_TO_BITS = {
    SymbolState.DOT: (1, 1),
    SymbolState.DASH: (1, -1),
    SymbolState.LETTER_GAP: (-1, 1),
    SymbolState.WORD_GAP: (-1, -1),
}
BITS_TO_STATE = {bits: state for state, bits in STATE_TO_BITS.items()}
```

#### Functions:
- `_block_slice(coords: tuple[int, int]) -> tuple[slice, slice]`:
  ```python
  row, col = coords
  return slice(row, row + BLOCK_SIZE), slice(col, col + BLOCK_SIZE)
  ```
  - Generates 2D slice tuple spanning $[row, row + 16)$ and $[col, col + 16)$.
- `generate_symbol_image(state: SymbolState, base_image: np.ndarray) -> np.ndarray`:
  ```python
  frame = base_image.copy()
  bit1, bit2 = STATE_TO_BITS[state]
  block_base_value = int(base_image.mean())
  frame[a_rows, a_cols] = block_base_value + bit1 * DELTA
  frame[b_rows, b_cols] = block_base_value - bit1 * DELTA
  frame[c_rows, c_cols] = block_base_value + bit2 * DELTA
  frame[d_rows, d_cols] = block_base_value - bit2 * DELTA
  return frame
  ```
  - Clones base template image.
  - Retrieves `(bit1, bit2)` sign pair for requested symbol state.
  - Sets patch pixels to `block_base_value` modified by $\pm \text{DELTA}$.
  - **Zero-Sum Property**:
    $$\Delta_{\text{net}} = (\text{bit}_1 \cdot \Delta) + (-\text{bit}_1 \cdot \Delta) + (\text{bit}_2 \cdot \Delta) + (-\text{bit}_2 \cdot \Delta) = 0$$
    Total image mean and energy remain strictly constant regardless of the encoded symbol state, preventing ciphertext energy leakage.
- `read_differential_brightness(image: np.ndarray) -> SymbolState`:
  ```python
  bit1 = 1 if image[a_rows, a_cols].mean() > image[b_rows, b_cols].mean() else -1
  bit2 = 1 if image[c_rows, c_cols].mean() > image[d_rows, d_cols].mean() else -1
  return BITS_TO_STATE[(bit1, bit2)]
  ```
  - Computes mean intensity of block $A$ vs block $B$, and block $C$ vs block $D$.
  - Reconstructs bit signs and maps back to `SymbolState`.

---

### `services/encoding/morse_to_symbol_sequence.py`

#### Classes & Mappings:
- `SymbolState(IntEnum)`:
  - `DOT = 0`
  - `DASH = 1`
  - `LETTER_GAP = 2`
  - `WORD_GAP = 3`
- `SYMBOL_MAP = {'.': SymbolState.DOT, '-': SymbolState.DASH, ' ': SymbolState.LETTER_GAP, '/': SymbolState.WORD_GAP}`
- `REVERSE_SYMBOL_MAP = {state: ch for ch, state in SYMBOL_MAP.items()}`

#### Functions:
- `morse_to_symbol_sequence(morse: str) -> list[SymbolState]`:
  - List comprehension `[SYMBOL_MAP[ch] for ch in morse]`.
- `symbol_sequence_to_morse(symbols: list[SymbolState | int]) -> str`:
  - Reconstructs Morse string: `"".join(REVERSE_SYMBOL_MAP[SymbolState(s)] for s in symbols)`.

---

### `services/encoding/text_to_morse.py` & `morse_to_text.py`

- `ITU_MORSE_TABLE`: Dictionary mapping alphanumeric characters `A-Z`, `0-9`, and punctuation to ITU Morse patterns.
- `REVERSE_ITU_MORSE_TABLE`: Inverted dictionary mapping Morse patterns back to alphanumeric characters.
- `text_to_morse(text: str) -> str`:
  - Converts input string to uppercase and splits on spaces into words.
  - Translates characters to Morse codes separated by space `' '`.
  - Joins words using slash `'/'`.
- `morse_to_text(morse: str) -> str`:
  - Splits input on `'/'` to isolate words.
  - Splits each word on `' '` to isolate character codes.
  - Translates codes to letters via `REVERSE_ITU_MORSE_TABLE.get(code, '?')`.
  - Joins letters into words and words with spaces.
- `is_valid_morse(morse: str) -> bool`:
  - Iterates over all tokens and returns `True` if every non-empty token exists in `REVERSE_ITU_MORSE_TABLE`.

---

## 12. High-Level Transmission Pipelines

### `services/text_encryption.py`

#### Function: `encrypt_text_message(...)`
```python
def encrypt_text_message(
    secret_text: str,
    base_image: np.ndarray,
    secret_key_image: bytes,
    secret_password: str,
    message_id: str | None = None,
    salt: bytes | None = None,
    include_previews: bool = False,
) -> dict
```

#### Step-by-Step Execution:
1. **Validation**: Checks that `secret_text` is non-empty, `base_image` is an RGB float array with shape `(H, W, 3)`, and key image bytes are present.
2. **Morse & Symbol Mapping**:
   - `morse = text_to_morse(secret_text)`
   - `symbols = morse_to_symbol_sequence(morse)`
3. **Key Material Derivation**:
   - `image_digest = hash_canonical_key_image(canonicalize_key_image(secret_key_image))`
   - `password_key = derive_password_key(secret_password, generated_salt)`
   - `master_key = derive_master_key(password_key, image_digest)`
4. **Message Storage**:
   - Initializes `Message` object with type `TEXT_MESSAGE` and `total_frames=len(symbols)`.
5. **Frame Encryption Loop**:
   - For each `(frame_index, symbol)`:
     - Modulates base image: `symbol_image = generate_symbol_image(symbol, normalized_base)`.
     - Derives frame keys:
       - `p1_material = derive_frame_key(master_key, message_id, frame_index, b"DRPE/P1")`
       - `p2_material = derive_frame_key(master_key, message_id, frame_index, b"DRPE/P2")`
     - Runs DRPE encryption: `encrypted = drpe_encrypt(symbol_image, p1_material, p2_material)`.
     - Adds `Frame` containing `ciphertext_complex` and `amplitude` to message.
     - Optionally generates Base64 preview thumbnail.
6. **Return**: Returns dictionary with `message_id`, `salt`, `morse`, `symbols`, `frame_count`, `base_image_shape`, and `previews`.

---

### `services/text_decryption.py`

#### Function: `decrypt_text_message(...)`
```python
def decrypt_text_message(
    message_id: str,
    secret_key_image: bytes,
    secret_password: str,
) -> dict
```

#### Step-by-Step Execution:
1. **Retrieves Stored Transmission**:
   - Fetches `Message` from in-memory store by `message_id`.
   - Asserts `message.message_type == TEXT_MESSAGE`.
   - Calls `get_ordered_frames(message, require_complete=True)` to obtain all frames in order.
2. **Recomputes Key Material**:
   - Normalizes and hashes receiver's key image bytes.
   - Derives `password_key` from `secret_password` and stored `message.salt`.
   - Derives `master_key`.
3. **Frame Decryption & Symbol Recovery Loop**:
   - For each `frame` in `ordered_frames`:
     - Derives frame phase materials for `b"DRPE/P1"` and `b"DRPE/P2"`.
     - Reconstructs phase masks: `p1, p2 = generate_phase_masks(frame.ciphertext_complex.shape, p1_material, p2_material)`.
     - Decrypts complex array: `recovered_image = drpe_decrypt(frame.ciphertext_complex, p1=p1, p2=p2)`.
     - Extracts symbol: `symbol = read_differential_brightness(recovered_image)`.
     - Appends `symbol` to recovered sequence and collects frame diagnostics.
4. **Morse & Text Reconstruction**:
   - `morse = symbol_sequence_to_morse(recovered_symbols)`
   - `text = morse_to_text(morse)`
   - `valid_morse = is_valid_morse(morse)`
5. **Return**: Returns dictionary containing `message_id`, decoded `text`, `morse`, `symbols`, `frame_count`, `success`, and per-frame diagnostics.

---

### `services/image_encryption.py`

#### Function: `encrypt_image_message(...)`
```python
def encrypt_image_message(
    cover_image: np.ndarray,
    secret_key_image: bytes,
    secret_password: str,
    message_id: str | None = None,
) -> dict
```
- Normalizes `cover_image` to `float64` array.
- Generates 16-byte random salt.
- Hashes sender's normalized key image and executes full KDF hierarchy (`derive_image_password_keys`).
- Encrypts cover image via `drpe_encrypt`.
- Creates `Message` (`type="image"`, `base_image=cover_image.copy()`, `salt=salt`, `total_frames=1`).
- Appends `Frame(0, ciphertext_complex, amplitude)`.
- Returns dictionary containing `message_id`, `salt`, display `image` (Base64 PNG), `energy`, and `cover_energy`.

---

### `services/image_decryption.py`

#### Function: `decrypt_image_message(...)`
```python
def decrypt_image_message(
    message_id: str,
    secret_key_image: bytes,
    secret_password: str,
    frame_index: int = 0,
) -> dict
```
- Fetches `Message` and `Frame` from in-memory store by `message_id`.
- Re-derives phase masks using Bob's credentials and stored `message.salt`.
- Inverts stored complex ciphertext via `drpe_decrypt`.
- Checks floating-point fidelity against `message.base_image` for exact `match_with_cover`.
- Returns dictionary with recovered `image` (Base64 PNG), `energy`, and `match_with_cover` boolean.

