# Comprehensive Backend Documentation: Signal Project Encryption System

## Table of Contents
1. [Overview & Mathematical Foundations](#1-overview--mathematical-foundations)
   - [1.1 4-f Optical Double Random Phase Encryption (DRPE)](#11-4-f-optical-double-random-phase-encryption-drpe)
   - [1.2 Parseval's Energy Invariance Theorem](#12-parsevals-energy-invariance-theorem)
   - [1.3 Differential Two-Block-Pair Steganography (Zero-Energy Leakage)](#13-differential-two-block-pair-steganography-zero-energy-leakage)
   - [1.4 Basic Energy Bug Side-Channel (Parseval Leakage Vulnerability)](#14-basic-energy-bug-side-channel-parseval-leakage-vulnerability)
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
    - [`services/encoding/morse_to_symbol_sequence.py`](#servicesencodingmorse_to_symbol_sequencepy)
    - [`services/encoding/text_to_morse.py`](#servicesencodingtext_to_morsepy)
    - [`services/encoding/morse_to_text.py`](#servicesencodingmorse_to_textpy)
    - [`services/encoding/symbol_image.py`](#servicesencodingsymbol_imagepy)
    - [`services/encoding/basic_energy_morse.py`](#servicesencodingbasic_energy_morsepy)
12. [High-Level Transmission Pipelines](#12-high-level-transmission-pipelines)
    - [`services/image_encryption.py`](#servicesimage_encryptionpy)
    - [`services/image_decryption.py`](#servicesimage_decryptionpy)
    - [`services/text_encryption.py`](#servicestext_encryptionpy)
    - [`services/text_decryption.py`](#servicestext_decryptionpy)
    - [`services/basic_energy_service.py`](#servicesbasic_energy_servicepy)
13. [Test Suite Architecture & Verification](#13-test-suite-architecture--verification)
    - [`tests/test_drpe.py`](#teststest_drpepy)
    - [`tests/test_phase2_decryption.py`](#teststest_phase2_decryptionpy)
    - [`tests/test_basic_energy_morse.py`](#teststest_basic_energy_morsepy)
14. [Complete API Endpoint Specification](#14-complete-api-endpoint-specification)

---

## 1. Overview & Mathematical Foundations

The backend provides a complete simulation and dual-channel implementation of **Double Random Phase Encryption (DRPE)** operating within a classical 4-f optical Fourier processor. It supports:
1. **Single Image Encryption & Decryption**: High-fidelity optical encryption of 2D/3D images with visual step-by-step 4-f intermediate transformation stages.
2. **Differential Morse Text Steganography**: Zero-energy-leakage covert text transmission using 2-bit differential spatial block pairs.
3. **Basic Energy Morse Modulation & Side-Channel Attack**: Demonstration of optical Parseval energy leakage (the "Energy Bug"), showing how uncancelled amplitude modulation allows eavesdroppers to recover covert text with zero decryption and without keys or passwords.

```
+-----------------------------------------------------------------------------------------------+
|                                  OPTICAL 4-f SYSTEM SIMULATION                                |
|                                                                                               |
|  Input Plane           Spatial Phase      Fourier Plane          Freq Phase     Output Plane  |
|  [f(x, y)] ---------> [* exp(j*P1)] ----> [ Lens 1: FFT2 ] ----> [* exp(j*P2)] -> [ Lens 2:  |
|  Amplitude             Input Mask          G(u, v)                Filter Mask       IFFT2 ]   |
|                                                                                       |       |
|                                                                                       v       |
|                                                                                 Complex c(x,y)|
+-----------------------------------------------------------------------------------------------+
```

### 1.1 4-f Optical Double Random Phase Encryption (DRPE)

DRPE encrypts a spatial amplitude signal $f(x, y)$ (where $f(x, y) \in [0, 255]$) into stationary, complex white Gaussian-like noise $c(x, y)$ using two statistically independent random phase masks $P_1(x, y)$ and $P_2(u, v)$ uniformly distributed over $[0, 2\pi)$.

#### Forward Encryption Transformation:
1. **Spatial Domain Phase Modulation (Input Plane)**:
   $$s(x, y) = f(x, y) \cdot \exp(j \cdot P_1(x, y))$$
2. **First Lens (2D Optical Discrete Fourier Transform)**:
   $$G(u, v) = \mathcal{F}_{2D}\{s(x, y)\} = \iint_{-\infty}^{\infty} s(x, y) \exp(-j 2\pi (ux + vy)) \, dx \, dy$$
3. **Fourier Plane Phase Modulation (Spatial Frequency Plane)**:
   $$G'(u, v) = G(u, v) \cdot \exp(j \cdot P_2(u, v))$$
4. **Second Lens (2D Optical Inverse Discrete Fourier Transform)**:
   $$c(x, y) = \mathcal{F}_{2D}^{-1}\{G'(u, v)\} = \iint_{-\infty}^{\infty} G'(u, v) \exp(j 2\pi (ux + vy)) \, du \, dv$$
   The output $c(x, y) \in \mathbb{C}$ is a complex-valued array with zero mean and uniform phase distribution.
5. **Magnitude / Amplitude Display Representation**:
   $$A(x, y) = |c(x, y)| = \sqrt{\text{Re}(c(x, y))^2 + \text{Im}(c(x, y))^2}$$

#### Inverse Decryption Transformation:
Given complex ciphertext $c(x, y)$ and identical phase distributions $P_1(x, y)$ and $P_2(u, v)$:
1. **2D Fourier Transform of Complex Ciphertext**:
   $$G'(u, v) = \mathcal{F}_{2D}\{c(x, y)\}$$
2. **Frequency Mask Demodulation**:
   $$G(u, v) = G'(u, v) \cdot \exp(-j \cdot P_2(u, v))$$
3. **2D Inverse Fourier Transform to Spatial Domain**:
   $$s(x, y) = \mathcal{F}_{2D}^{-1}\{G(u, v)\}$$
4. **Spatial Mask Demodulation & Amplitude Reconstruction**:
   $$f(x, y) = \text{round}\left(\text{clip}\left(\text{Re}\{s(x, y) \cdot \exp(-j \cdot P_1(x, y))\}, 0, 255\right)\right)$$

### 1.2 Parseval's Energy Invariance Theorem

Under the unitary discrete Fourier transform, total signal energy is strictly conserved between the spatial domain and the frequency domain:
$$\sum_{x, y} |f(x, y)|^2 = \sum_{x, y} |s(x, y)|^2 = \sum_{u, v} |G(u, v)|^2 = \sum_{u, v} |G'(u, v)|^2 = \sum_{x, y} |c(x, y)|^2$$

In this codebase, energy is quantified by the Frobenius energy metric:
$$E = \sum_{x, y, c} I(x, y, c)^2$$
For lossless complex transmission, $\text{energy}(|c|) \approx \text{energy}(f)$ to machine precision ($< 10^{-15}$).

### 1.3 Differential Two-Block-Pair Steganography (Zero-Energy Leakage)

To transmit covert text through a sequence of image frames without revealing Morse symbols through ciphertext energy fluctuations, the system implements differential 2-block-pair brightness modulation.

Each Morse token is mapped to one of four states in `SymbolState`:
- `DOT = 0` $\rightarrow$ bits `(+1, +1)`
- `DASH = 1` $\rightarrow$ bits `(+1, -1)`
- `LETTER_GAP = 2` $\rightarrow$ bits `(-1, +1)`
- `WORD_GAP = 3` $\rightarrow$ bits `(-1, -1)`

Four non-overlapping spatial blocks of dimension $16 \times 16$ pixels (`BLOCK_SIZE = 16`, $N = 256$ pixels per block) are modulated with differential step `DELTA = 8` around the base image mean $\mu$:
$$\text{Block } A = \mu + \text{bit}_1 \cdot \Delta, \quad \text{Block } B = \mu - \text{bit}_1 \cdot \Delta$$
$$\text{Block } C = \mu + \text{bit}_2 \cdot \Delta, \quad \text{Block } D = \mu - \text{bit}_2 \cdot \Delta$$

#### Zero-Sum Energy & Mean Invariant:
$$\Delta \mu = \frac{1}{4N}\left[(\text{bit}_1 \Delta) + (-\text{bit}_1 \Delta) + (\text{bit}_2 \Delta) + (-\text{bit}_2 \Delta)\right] = 0$$
$$\Delta E = N \left[ (\mu + \Delta)^2 + (\mu - \Delta)^2 \right] = 2N(\mu^2 + \Delta^2)$$
Because $(\text{bit}_1)^2 = 1$ and $(\text{bit}_2)^2 = 1$ for all four states, the energy delta is identical across every symbol! An attacker observing ciphertext energy $|c|^2$ observes identical values for DOT, DASH, LETTER_GAP, and WORD_GAP.

### 1.4 Basic Energy Bug Side-Channel (Parseval Leakage Vulnerability)

In contrast to differential modulation, naive Morse encoding modifies the global frame brightness:
$$f_k(x, y) = f_{\text{base}}(x, y) + k \cdot \Delta_{\text{offset}}, \quad k \in \{0, 1, 2, 3\}$$
where $\Delta_{\text{offset}} = 20.0$.

Under Parseval's theorem:
$$E(k) = \sum_{x, y} (f_{\text{base}}(x, y) + k \cdot \Delta_{\text{offset}})^2 = \sum f_{\text{base}}^2 + 2 k \Delta_{\text{offset}} \sum f_{\text{base}} + M N (k \Delta_{\text{offset}})^2$$
Since $f_{\text{base}} \ge 0$ and $\Delta_{\text{offset}} > 0$:
$$E(0) < E(1) < E(2) < E(3)$$
$E_{\text{DOT}} < E_{\text{DASH}} < E_{\text{LETTER\_GAP}} < E_{\text{WORD\_GAP}}$ is strictly monotonic.

An eavesdropper intercepting the DRPE ciphertext amplitude $A(x, y) = |c(x, y)|$ calculates:
$$E_{\text{cipher}} = \sum A(x, y)^2$$
By comparing $E_{\text{cipher}}$ against precomputed decision thresholds:
$$\tau_0 = \frac{E(0) + E(1)}{2}, \quad \tau_1 = \frac{E(1) + E(2)}{2}, \quad \tau_2 = \frac{E(2) + E(3)}{2}$$
the eavesdropper classifies every symbol with 100% accuracy **without decrypting the ciphertext, without knowing the key image, and without knowing the password**.

---

## 2. Project Architecture & Directory Layout

```text
backend/
├── main.py                             # FastAPI app initialization, CORS, routers mount, healthcheck
├── config.py                           # Central configuration, block coordinates, constants
├── requirements.txt                    # Python dependencies
├── run_code.txt                        # Local runtime instructions
│
├── routers/                            # API HTTP endpoint controllers
│   ├── __init__.py
│   ├── image_router.py                 # POST /api/encrypt, POST /api/decrypt-with-key-images
│   └── text_router.py                  # POST /api/text/encrypt, POST /api/text/decrypt,
│                                       # POST /api/text/basic-energy/* (encrypt, decrypt, predict)
│
├── controllers/                        # HTTP request orchestration & model serialization
│   ├── __init__.py
│   ├── image_controller.py             # Single-image encryption & decryption orchestration
│   └── text_controller.py              # Differential & basic-energy text sequence controllers
│
├── schemas/                            # Pydantic contract models
│   ├── __init__.py
│   └── image_schema.py                 # Request/response validation models & walkthrough stages
│
├── services/                           # Pure domain logic & cryptographic processing
│   ├── __init__.py
│   ├── drpe.py                         # 2D FFT/IFFT 4-f optical encryption engine & stage extraction
│   ├── keys.py                         # RFC 7914 Scrypt + SHA-256 + HMAC-SHA256 key derivation
│   ├── messages.py                     # In-memory ephemeral message and frame repository
│   ├── image_utils.py                  # Base64, PIL, canonicalization, and SHA-256 hashing
│   ├── image_encryption.py             # Single-frame image encryption pipeline
│   ├── image_decryption.py             # Single-frame image decryption pipeline
│   ├── text_encryption.py              # Differential text -> Morse -> symbol frames -> DRPE
│   ├── text_decryption.py              # DRPE -> differential extraction -> Morse -> text
│   ├── basic_energy_service.py         # Basic energy pipeline (encryption, normal decrypt, prediction)
│   │
│   └── encoding/                       # Morse & steganographic encoding primitives
│       ├── __init__.py
│       ├── morse_to_symbol_sequence.py # SymbolState enum & char <-> symbol translation
│       ├── text_to_morse.py            # ITU Morse code translation
│       ├── morse_to_text.py            # Morse to plaintext string decoding & validation
│       ├── symbol_image.py             # Differential 2-block-pair patch generation & detection
│       └── basic_energy_morse.py       # Global brightness offset modulation & energy classification
│
└── tests/                              # Automated test suites
    ├── test_drpe.py                    # Unit tests for DRPE math, keys, and image endpoints
    ├── test_phase2_decryption.py       # Unit & integration tests for differential Morse pipeline
    └── test_basic_energy_morse.py      # Unit & integration tests for basic energy & side-channel
```

---

## 3. Configuration Layer

### `config.py`
Path: [`backend/config.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/config.py)

Acts as the single source of truth for sender and receiver parameters. Inline hardcoding is strictly forbidden.

#### Constants:
- `_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))`: Absolute path to `backend/`.
- `DATA_DIR = os.path.join(_BACKEND_DIR, "data")`: Local data directory path.
- `DEFAULT_SEED = "phase1-demo"`: Fallback entropy seed.
- `BLOCK_A_COORDS = (10, 10)`: Top-left pixel `(row, col)` for differential block $A$.
- `BLOCK_B_COORDS = (10, 50)`: Top-left pixel `(row, col)` for differential block $B$.
- `BLOCK_C_COORDS = (50, 10)`: Top-left pixel `(row, col)` for differential block $C$.
- `BLOCK_D_COORDS = (50, 50)`: Top-left pixel `(row, col)` for differential block $D$.
- `BLOCK_SIZE = 16`: Edge length in pixels for each square block ($16 \times 16 = 256$ pixels).
- `DELTA = 8`: Pixel intensity shift applied to each block ($\pm 8$).

---

## 4. FastAPI Server Entry Point

### `main.py`
Path: [`backend/main.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/main.py)

Initializes the ASGI FastAPI application, configures CORS middleware, mounts routing controllers, and registers the health check probe.

#### Core Configuration:
- `app = FastAPI(title="DRPE Phase 1 Demo API")`
- `CORSMiddleware`:
  - `allow_origins`: Configured for `["http://localhost:5173", "http://127.0.0.1:5173", "*"]` to permit Vite dev servers and local testing.
  - `allow_credentials`: `True`
  - `allow_methods`: `["*"]`
  - `allow_headers`: `["*"]`
- Mounted Subrouters:
  - `app.include_router(image_router)`: Mounts routes under `/api`.
  - `app.include_router(text_router)`: Mounts routes under `/api/text`.

#### Endpoints:
- `GET /api/health`:
  - Returns `{"status": "ok"}`.

---

## 5. API Routing Layer

### `routers/image_router.py`
Path: [`backend/routers/image_router.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/image_router.py)
Router Prefix: `/api`

Exposes multipart form endpoints for single-image encryption and decryption.

#### Endpoints:
1. `POST /api/encrypt`
   - **Signature**:
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
   - **Behavior**: Unpacks multipart form fields, invokes `encrypt_controller`, and returns `EncryptResponse`.

2. `POST /api/decrypt-with-key-images`
   - **Signature**:
     ```python
     @router.post("/decrypt-with-key-images", response_model=DecryptResponse)
     async def decrypt_with_key_images(
         message_id: str = Form(...),
         secret_key_image: UploadFile = File(...),
         secret_password: str = Form(...),
         frame_index: int = Form(0),
         salt_b64: str | None = Form(None),
         ciphertext_b64: str | None = Form(None),
         ciphertext_shape: str | None = Form(None),
     ) -> DecryptResponse
     ```
   - **Behavior**: Delegates `message_id`, Bob's `secret_key_image`, `secret_password`, and `frame_index` to `decrypt_controller`. Optional fallback fields are accepted for legacy compatibility.

---

### `routers/text_router.py`
Path: [`backend/routers/text_router.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/routers/text_router.py)
Router Prefix: `/api/text`

Exposes endpoints for both Differential Morse transmission and Basic Energy side-channel demonstration.

#### Endpoints:
1. `POST /api/text/encrypt`
   - **Input**: `secret_text: str`, `base_image: UploadFile`, `secret_key_image: UploadFile`, `secret_password: str`.
   - **Response Model**: `TextEncryptResponse`.
   - **Description**: Converts text to Morse sequence and encrypts each symbol into a zero-sum differential brightness frame.

2. `POST /api/text/decrypt`
   - **Input**: `message_id: str`, `secret_key_image: UploadFile`, `secret_password: str`.
   - **Response Model**: `TextDecryptResponse`.
   - **Description**: Recovers complex frames from in-memory store, inverts DRPE with Bob's credentials, reads differential block pairs, and reconstructs Morse and plaintext.

3. `POST /api/text/basic-energy/encrypt`
   - **Input**: `secret_text: str`, `base_image: UploadFile`, `secret_key_image: UploadFile`, `secret_password: str`.
   - **Response Model**: `BasicEnergyEncryptResponse`.
   - **Description**: Encrypts text using uncancelled global brightness offsets ($\Delta = 20.0$), computing energy levels and classification thresholds.

4. `POST /api/text/basic-energy/decrypt`
   - **Input**: `message_id: str`, `secret_key_image: UploadFile`, `secret_password: str`.
   - **Response Model**: `BasicEnergyDecryptResponse`.
   - **Description**: Normal DRPE decryption path for basic energy frames requiring correct credentials.

5. `POST /api/text/basic-energy/predict`
   - **Input**: `message_id: str = Form(...)`.
   - **Response Model**: `BasicEnergyPredictResponse`.
   - **Description**: Exploits Parseval energy leakage. Reads ciphertext Parseval energy directly from stored frames without decryption and without requiring any key image or password.

---

## 6. Controller & Orchestration Layer

### `controllers/image_controller.py`
Path: [`backend/controllers/image_controller.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/image_controller.py)

Orchestrates file reading, byte parsing, error translation, and response creation for image endpoints.

#### Functions:
- `async def encrypt_controller(...) -> EncryptResponse`:
  1. Calls `await file_to_array(cover_image)`.
  2. Reads raw bytes: `await secret_key_image.read()`.
  3. Executes `encrypt_image_message(...)`.
  4. Encodes 16-byte cryptographic salt as Base64.
  5. Packages 5 visual transformation stages into `ProcessStage` models.
  6. Catches `ValueError` and general exceptions, raising HTTP 400 `HTTPException`.

- `async def decrypt_controller(...) -> DecryptResponse`:
  1. Reads Bob's key image bytes: `await secret_key_image.read()`.
  2. Executes `decrypt_image_message(...)`.
  3. Packages reconstructed image Base64, Parseval energy, `match_with_cover` boolean, and 5 reverse process stages.
  4. Catches `KeyError` (raising HTTP 404) and `ValueError` (raising HTTP 400).

---

### `controllers/text_controller.py`
Path: [`backend/controllers/text_controller.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/controllers/text_controller.py)

Manages request execution for differential and basic-energy Morse pipelines.

#### Functions:
- `async def encrypt_text_controller(...) -> TextEncryptResponse`:
  - Parses uploaded base image array and secret key bytes.
  - Calls `services.text_encryption.encrypt_text_message(..., include_previews=True)`.
  - Serializes `previews` as `TextFramePreview` objects and returns `TextEncryptResponse`.

- `async def decrypt_text_controller(...) -> TextDecryptResponse`:
  - Calls `services.text_decryption.decrypt_text_message(...)`.
  - Maps frame diagnostics (including `block_a_minus_b` and `block_c_minus_d`) to `TextDecryptedFrame` instances.
  - Returns reconstructed text, Morse string, symbol integer array, and status.

- `async def encrypt_basic_energy_controller(...) -> BasicEnergyEncryptResponse`:
  - Invokes `encrypt_basic_morse_message(...)`.
  - Returns `BasicEnergyEncryptResponse` containing frame count, thresholds, expected energy levels, and frame previews.

- `async def decrypt_basic_energy_controller(...) -> BasicEnergyDecryptResponse`:
  - Invokes `decrypt_basic_morse_normal(...)`.
  - Returns `BasicEnergyDecryptResponse` with mean brightness, delta, and energy diagnostics per frame.

- `async def predict_basic_energy_controller(message_id: str) -> BasicEnergyPredictResponse`:
  - Invokes `predict_basic_morse_from_energy(message_id)`.
  - Constructs `BasicEnergyPredictResponse` with predicted plaintext, Morse, symbols, frame energies, decision thresholds, and `bypassed_decryption=True`.

---

## 7. Pydantic Validation Schemas

### `schemas/image_schema.py`
Path: [`backend/schemas/image_schema.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/schemas/image_schema.py)

All data structures are typed using Pydantic `BaseModel`:

```python
class ImageResponse(BaseModel):
    image: str

class ProcessStage(BaseModel):
    name: str
    image: str

class EncryptResponse(BaseModel):
    image: str
    energy: float
    cover_energy: float
    message_id: str
    salt_b64: str
    stages: list[ProcessStage] = []

class DecryptResponse(BaseModel):
    image: str
    energy: float
    match_with_cover: bool
    stages: list[ProcessStage] = []

class TextFramePreview(BaseModel):
    frame_index: int
    image: str
    energy: float

class TextEncryptResponse(BaseModel):
    message_id: str
    salt_b64: str
    frame_count: int
    base_image_shape: list[int]
    previews: list[TextFramePreview] = []

class TextDecryptedFrame(BaseModel):
    frame_index: int
    symbol: int
    symbol_name: str
    block_a_minus_b: float | None = None
    block_c_minus_d: float | None = None

class TextDecryptResponse(BaseModel):
    message_id: str
    text: str
    morse: str
    symbols: list[int]
    frame_count: int
    success: bool
    image: str | None = None
    frames: list[TextDecryptedFrame] = []

class BasicEnergyFramePreview(BaseModel):
    frame_index: int
    image: str
    energy: float

class BasicEnergyEncryptResponse(BaseModel):
    message_id: str
    salt_b64: str
    frame_count: int
    base_image_shape: list[int]
    thresholds: list[float] = []
    energy_levels: list[float] = []
    previews: list[BasicEnergyFramePreview] = []

class BasicEnergyDecryptedFrame(BaseModel):
    frame_index: int
    symbol: int
    symbol_name: str
    mean_brightness: float | None = None
    brightness_delta: float | None = None
    total_energy: float | None = None

class BasicEnergyDecryptResponse(BaseModel):
    message_id: str
    text: str
    morse: str
    symbols: list[int]
    frame_count: int
    success: bool
    image: str | None = None
    frames: list[BasicEnergyDecryptedFrame] = []

class BasicEnergyPredictedFrame(BaseModel):
    frame_index: int
    energy: float
    predicted_symbol: int
    symbol_name: str

class BasicEnergyPredictResponse(BaseModel):
    message_id: str
    predicted_text: str
    predicted_morse: str
    predicted_symbols: list[int]
    frame_count: int
    thresholds: list[float] = []
    energy_levels: list[float] = []
    frame_energies: list[float] = []
    frames: list[BasicEnergyPredictedFrame] = []
    success: bool
    bypassed_decryption: bool = True
```

---

## 8. Core Cryptographic Engine

### `services/drpe.py`
Path: [`backend/services/drpe.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/drpe.py)

Contains pure mathematical functions with no I/O or state.

#### Functions:
- `mask_seed(material: bytes) -> int`:
  Takes key material bytes, computes SHA-256, and extracts the first 16 bytes as an unsigned 128-bit big-endian integer for PRNG seeding.

- `generate_phase_masks(shape: tuple[int, ...], p1_material: bytes, p2_material: bytes) -> tuple[np.ndarray, np.ndarray]`:
  Instantiates two independent `np.random.default_rng` generators with `mask_seed(p1_material)` and `mask_seed(p2_material)`. Generates uniform float64 continuous distributions over $[0, 2\pi)$ matching `shape`.

- `drpe_encrypt(cover_image: np.ndarray, p1_material: bytes, p2_material: bytes, include_stages: bool = False) -> dict`:
  1. Generates phase masks $P_1$ and $P_2$.
  2. Spatial phase rotation: $s = \text{cover} \cdot \exp(j \cdot P_1)$.
  3. Spatial 2D FFT: $G = \text{fft2}(s, \text{axes}=(0, 1))$.
  4. Frequency phase rotation: $G' = G \cdot \exp(j \cdot P_2)$.
  5. Spatial 2D IFFT: $c = \text{ifft2}(G', \text{axes}=(0, 1))$.
  6. If `include_stages=True`, extracts normalized intermediate stages:
     - `"original"`: `cover_image`
     - `"spatial_rotation"`: $|s|$
     - `"frequency_spectrum"`: $\log(1 + |G|)$ preview
     - `"frequency_rotation"`: $\log(1 + |G'|)$ preview
     - `"ciphertext"`: $|c|$
  7. Returns `{"complex": c, "amplitude": np.abs(c), "p1": p1, "p2": p2, ["stages": ...]}`.

- `drpe_decrypt(ciphertext_complex: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> np.ndarray`:
  1. $G' = \text{fft2}(c, \text{axes}=(0, 1))$
  2. $G = G' \cdot \exp(-j \cdot P_2)$
  3. $s = \text{ifft2}(G, \text{axes}=(0, 1))$
  4. $\text{cover} = s \cdot \exp(-j \cdot P_1)$
  5. Returns $\text{clip}(\text{round}(\text{Re}\{\text{cover}\}), 0, 255)$.

- `drpe_decrypt_with_stages(ciphertext_complex: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> tuple[np.ndarray, dict]`:
  Performs decryption while retaining five displayable visual stages:
  `"ciphertext"`, `"frequency_spectrum"`, `"frequency_phase_removed"`, `"spatial_phase_removed"`, and `"recovered"`.

- `_magnitude_preview(values: np.ndarray) -> np.ndarray`:
  Computes log-normalized visual preview: $\frac{\log(1 + |v|)}{\max(\log(1 + |v|))} \times 255.0$.

- `energy(image: np.ndarray) -> float`:
  Computes Parseval Frobenius energy: $\sum I(x, y)^2$.

---

### `services/keys.py`
Path: [`backend/services/keys.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/keys.py)

Implements RFC 7914 compliant key derivation and HMAC-based frame separation to prevent key reuse vulnerabilities.

```
+-----------------------------------------------------------------------------------+
|                            KEY DERIVATION HIERARCHY                               |
|                                                                                   |
|  secret_password + salt                                   secret_key_image        |
|          |                                                       |                |
|          v (hashlib.scrypt, N=16384, r=8, p=1)                   v (SHA-256)      |
|     password_key (32 bytes)                             secret_image_digest       |
|          \                                                     /                  |
|           \                                                   /                   |
|            +---> SHA-256(b"DRPE-MASTER-v1" + pwd_key + digest)                    |
|                                    |                                              |
|                                    v                                              |
|                               master_key                                          |
|                                    |                                              |
|             +----------------------+----------------------+                       |
|             |                                             |                       |
|             v (HMAC-SHA256, purpose=b"DRPE/P1")           v (HMAC-SHA256, P2)     |
|      p1_material (32 bytes)                        p2_material (32 bytes)         |
+-----------------------------------------------------------------------------------+
```

#### Functions:
- `derive_password_key(password: str, salt: bytes) -> bytes`:
  Executes `hashlib.scrypt` with $N = 16384, r = 8, p = 1, \text{dklen} = 32$.
- `derive_master_key(password_key: bytes, secret_image_digest: bytes) -> bytes`:
  Computes $\text{SHA-256}(\text{b"DRPE-MASTER-v1"} \parallel \text{password\_key} \parallel \text{secret\_image\_digest})$.
- `derive_frame_key(master_key: bytes, message_id: str, frame_index: int, purpose: bytes) -> bytes`:
  Computes $\text{HMAC-SHA256}(\text{master\_key}, \text{b"DRPE-v1"} \parallel \text{purpose} \parallel \text{message\_id} \parallel \text{frame\_index}_{8\text{-byte big-endian}})$.
- `derive_image_password_keys(password: str, salt: bytes, secret_image_digest: bytes, message_id: str, frame_index: int) -> tuple[bytes, bytes]`:
  Executes the full pipeline, returning `(p1_material, p2_material)`.
- `derive_key(seed: str, frame_index: int = 0) -> bytes`:
  Legacy single-seed derivation function.

---

## 9. In-Memory State & Messaging Store

### `services/messages.py`
Path: [`backend/services/messages.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/messages.py)

Manages thread-safe in-memory storage of transmissions.

#### Constants & Data Classes:
- `IMAGE_MESSAGE = "image"`
- `TEXT_MESSAGE = "text"`
- `BASIC_ENERGY_MESSAGE = "basic_energy_morse"`

```python
@dataclass
class Frame:
    frame_index: int
    ciphertext_complex: np.ndarray  # complex128
    amplitude: np.ndarray          # float64

@dataclass
class Message:
    message_id: str
    message_type: str = IMAGE_MESSAGE
    secret_key_image: bytes | None = None
    secret_password: str | None = None
    salt: bytes | None = None
    base_image: np.ndarray | None = None
    total_frames: int | None = None
    metadata: dict = field(default_factory=dict)
    receiver_secret_key_image: bytes | None = None
    receiver_password: str | None = None
    frames: list[Frame] = field(default_factory=list)
```

#### Functions:
- `new_message_id() -> str`: Monotonic formatting `"msg-%06d"`.
- `create_message(...) -> Message`: Validates message type against `{IMAGE_MESSAGE, TEXT_MESSAGE, BASIC_ENERGY_MESSAGE}`, checks ID uniqueness, and inserts into `_messages`.
- `get_message(message_id: str) -> Message`: Looks up message or raises `KeyError`.
- `add_frame(message: Message, frame: Frame) -> None`: Validates non-negative index, avoids duplicates, verifies total frame bounds, and appends frame.
- `get_frame(message: Message, frame_index: int) -> Frame`: Finds frame by index or raises `KeyError`.
- `get_ordered_frames(message: Message, require_complete: bool = False) -> list[Frame]`: Returns frames sorted by index; asserts contiguous sequence $[0 \dots N-1]$ if `require_complete=True`.
- `get_messages(message_type: str | None = None) -> list[Message]`: Returns all stored messages or filters by type.

---

## 10. Image Processing & Serialization Utilities

### `services/image_utils.py`
Path: [`backend/services/image_utils.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_utils.py)

#### Functions:
- `async def file_to_array(upload: UploadFile, target_shape=None) -> np.ndarray`:
  Reads bytes asynchronously (verifies $\ge 8$ bytes), decodes image via PIL, converts to RGB float64, and optionally resizes via `BICUBIC`.
- `def array_to_base64(arr: np.ndarray) -> str`:
  Clips array to $[0, 255]$, casts to `uint8`, saves as PNG into `io.BytesIO()`, and encodes as a UTF-8 Base64 string.
- `def array_to_base64_preview(arr: np.ndarray, max_size: int = 512) -> str`:
  Clips to $[0, 255]$, applies `thumbnail((max_size, max_size), LANCZOS)`, and returns Base64 PNG.
- `def canonicalize_key_image(raw: bytes) -> np.ndarray`:
  Opens key image bytes, converts to RGB, and resizes to standardized $256 \times 256$ pixels using `LANCZOS` resampling. Returns `(256, 256, 3)` `uint8` array.
- `def hash_canonical_key_image(pixels: np.ndarray) -> bytes`:
  Hashes canonical pixels with domain prefix:
  $$\text{SHA-256}(\text{b"DRPE-KEY-IMAGE-v1"} \parallel \text{pixels.shape} \parallel \text{pixels.tobytes()})$$
- `async def key_image_digest(upload: UploadFile) -> bytes`:
  Asynchronously reads upload, canonicalizes, and returns the 32-byte SHA-256 digest.

---

## 11. Steganographic & Optical Morse Encoding Layer

### `services/encoding/morse_to_symbol_sequence.py`
Path: [`backend/services/encoding/morse_to_symbol_sequence.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/morse_to_symbol_sequence.py)

Defines the 4-state symbol enumeration and character translations:
```python
class SymbolState(IntEnum):
    DOT = 0
    DASH = 1
    LETTER_GAP = 2
    WORD_GAP = 3

SYMBOL_MAP = {'.': SymbolState.DOT, '-': SymbolState.DASH, ' ': SymbolState.LETTER_GAP, '/': SymbolState.WORD_GAP}
REVERSE_SYMBOL_MAP = {state: ch for ch, state in SYMBOL_MAP.items()}
```
- `morse_to_symbol_sequence(morse: str) -> list[SymbolState]`: Maps characters to enum values.
- `symbol_sequence_to_morse(symbols: list[SymbolState | int]) -> str`: Reconstructs Morse string.

---

### `services/encoding/text_to_morse.py`
Path: [`backend/services/encoding/text_to_morse.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/text_to_morse.py)

Contains `ITU_MORSE_TABLE` covering `'A'-'Z'`, `'0'-'9'`, and punctuation (`.`, `,`, `?`).
- `text_to_morse(text: str) -> str`: Converts text to uppercase. Words are split on `' '`. Letters are joined with `' '`, and words are joined with `'/'`.

---

### `services/encoding/morse_to_text.py`
Path: [`backend/services/encoding/morse_to_text.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/morse_to_text.py)

- `REVERSE_ITU_MORSE_TABLE`: Inverted dictionary mapping Morse strings to characters.
- `morse_to_text(morse: str) -> str`: Splits on `'/'` for words, then `' '` for letters. Unrecognized codes map to `'?'`.
- `is_valid_morse(morse: str) -> bool`: Validates that every token exists in `REVERSE_ITU_MORSE_TABLE`.

---

### `services/encoding/symbol_image.py`
Path: [`backend/services/encoding/symbol_image.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/symbol_image.py)

Implements the zero-energy-leakage differential encoding.

#### Block Coordinates and Mappings:
```python
STATE_TO_BITS = {
    SymbolState.DOT: (1, 1),
    SymbolState.DASH: (1, -1),
    SymbolState.LETTER_GAP: (-1, 1),
    SymbolState.WORD_GAP: (-1, -1),
}
```

#### Functions:
- `_block_slice(coords: tuple[int, int]) -> tuple[slice, slice]`: Returns `slice(row, row + 16), slice(col, col + 16)`.
- `generate_symbol_image(state: SymbolState, base_image: np.ndarray) -> np.ndarray`:
  Sets block pixels to $\mu_{\text{base}} \pm \Delta$:
  - `Block A` = $\mu + \text{bit}_1 \cdot \Delta$
  - `Block B` = $\mu - \text{bit}_1 \cdot \Delta$
  - `Block C` = $\mu + \text{bit}_2 \cdot \Delta$
  - `Block D` = $\mu - \text{bit}_2 \cdot \Delta$
- `read_differential_brightness(image: np.ndarray) -> SymbolState`:
  Calculates sign of differences:
  - $\text{bit}_1 = 1$ if $\text{mean}(A) > \text{mean}(B)$ else $-1$
  - $\text{bit}_2 = 1$ if $\text{mean}(C) > \text{mean}(D)$ else $-1$
  - Maps `(bit1, bit2)` back to `SymbolState`.
- `differential_brightness_metrics(image: np.ndarray) -> dict[str, float]`:
  Returns `{"block_a_minus_b": mean(A) - mean(B), "block_c_minus_d": mean(C) - mean(D)}`.

---

### `services/encoding/basic_energy_morse.py`
Path: [`backend/services/encoding/basic_energy_morse.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/encoding/basic_energy_morse.py)

Implements naive global intensity modulation and side-channel classification.

#### Constants:
- `ENERGY_OFFSET_STEP = 20.0`: The brightness offset step between symbol levels.

#### Functions:
- `encode_text_to_symbols(text: str) -> tuple[str, list[SymbolState]]`:
  Encodes plaintext into Morse string and symbol states.
- `prepare_base_image_for_offset(base_image: np.ndarray, offset_step: float = 20.0) -> np.ndarray`:
  Clamps base image to $[0.0, 255.0 - 3 \cdot \Delta_{\text{offset}}]$ (default max 195.0) to prevent overflow clipping.
- `generate_basic_symbol_image(symbol: int | SymbolState, base_image: np.ndarray, offset_step: float = 20.0) -> np.ndarray`:
  Applies uncancelled offset: $\text{frame} = \text{base}_{\text{clamped}} + \text{symbol} \times \Delta_{\text{offset}}$.
- `compute_expected_energy_levels(base_image: np.ndarray, offset_step: float = 20.0) -> tuple[list[float], list[float]]`:
  Computes the 4 theoretical frame energies:
  $$E_s = \sum (\text{base}_{\text{clamped}} + s \cdot \Delta_{\text{offset}})^2, \quad s \in \{0, 1, 2, 3\}$$
  and the 3 decision boundaries:
  $$\tau_i = \frac{E_i + E_{i+1}}{2}, \quad i \in \{0, 1, 2\}$$
- `predict_symbol_from_energy(energy_val: float, thresholds: list[float]) -> int`:
  Classifies an observed Parseval energy value into state 0, 1, 2, or 3 based on $\tau$.
- `extract_symbol_from_decrypted_image(decrypted_image: np.ndarray, base_image: np.ndarray, offset_step: float = 20.0) -> SymbolState`:
  Extracts symbol from decrypted image by calculating global mean shift:
  $$k = \text{clip}\left(\text{round}\left(\frac{\text{mean}(\text{decrypted}) - \text{mean}(\text{base}_{\text{clamped}})}{\Delta_{\text{offset}}}\right), 0, 3\right)$$
- `decode_symbols_to_morse_and_text(symbols: list[int | SymbolState]) -> tuple[str, str, bool]`:
  Reconstructs Morse string, decodes to text, and validates ITU conformance.

---

## 12. High-Level Transmission Pipelines

### `services/image_encryption.py`
Path: [`backend/services/image_encryption.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_encryption.py)

#### Function: `encrypt_image_message(...)`
- Inputs: `cover_image: np.ndarray`, `secret_key_image: bytes`, `secret_password: str`, `message_id: str | None`.
- Pipeline:
  1. Generates 16-byte cryptographically secure random salt (`secrets.token_bytes(16)`).
  2. Canonicalizes sender's key image to $256 \times 256$ RGB and hashes via SHA-256.
  3. Derives `p1_material` and `p2_material` for frame index 0.
  4. Encrypts cover array via `drpe_encrypt(..., include_stages=True)`.
  5. Creates `Message` (`type="image"`) and attaches `Frame(0, ciphertext_complex, amplitude)`.
  6. Formats visual stages (`"original"`, `"spatial_rotation"`, `"frequency_spectrum"`, `"frequency_rotation"`, `"ciphertext"`).
  7. Returns dictionary with `message_id`, `salt`, `image`, `energy`, `cover_energy`, and `stages`.

---

### `services/image_decryption.py`
Path: [`backend/services/image_decryption.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/image_decryption.py)

#### Function: `decrypt_image_message(...)`
- Inputs: `message_id: str`, `secret_key_image: bytes`, `secret_password: str`, `frame_index: int = 0`.
- Pipeline:
  1. Retrieves stored `Message` and `Frame(frame_index)`.
  2. Canonicalizes and hashes Bob's key image.
  3. Derives `p1_material` and `p2_material` using Bob's credentials and `message.salt`.
  4. Generates phase masks $P_1$ and $P_2$.
  5. Decrypts complex ciphertext via `drpe_decrypt_with_stages(...)`.
  6. Evaluates ground-truth fidelity: `np.allclose(message.base_image, recovered, atol=1e-15)`.
  7. Formats 5 reverse visual stages.
  8. Returns dictionary with `image`, `energy`, `match_with_cover`, and `stages`.

---

### `services/text_encryption.py`
Path: [`backend/services/text_encryption.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/text_encryption.py)

#### Function: `encrypt_text_message(...)`
- Inputs: `secret_text: str`, `base_image: np.ndarray`, `secret_key_image: bytes`, `secret_password: str`, `include_previews: bool = False`.
- Pipeline:
  1. Translates text to Morse string via `text_to_morse()`.
  2. Maps Morse string to `list[SymbolState]` via `morse_to_symbol_sequence()`.
  3. Derives master secret: Scrypt(`secret_password`, salt) $\rightarrow$ SHA-256 with key image digest.
  4. Creates `Message` with `total_frames = len(symbols)` and `message_type = "text"`.
  5. For each `(frame_index, symbol)`:
     - Modulates base image: `symbol_image = generate_symbol_image(symbol, base_image)`.
     - Derives per-frame keys: `p1_material` and `p2_material`.
     - Encrypts via `drpe_encrypt(symbol_image, p1_material, p2_material)`.
     - Appends `Frame(frame_index, complex, amplitude)` to message.
     - Optionally appends Base64 thumbnail preview.
  6. Returns dictionary with `message_id`, `salt`, `morse`, `symbols`, `frame_count`, `base_image_shape`, and `previews`.

---

### `services/text_decryption.py`
Path: [`backend/services/text_decryption.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/text_decryption.py)

#### Function: `decrypt_text_message(...)`
- Inputs: `message_id: str`, `secret_key_image: bytes`, `secret_password: str`.
- Pipeline:
  1. Retrieves `Message` and ordered frames from in-memory store.
  2. Derives master key using Bob's credentials and stored salt.
  3. For each frame in `ordered_frames`:
     - Derives frame phase keys and generates $P_1, P_2$.
     - Decrypts complex array: `drpe_decrypt(frame.ciphertext_complex, p1, p2)`.
     - Extracts symbol: `read_differential_brightness(recovered_image)`.
     - Records diagnostics: `symbol`, `symbol_name`, `block_a_minus_b`, `block_c_minus_d`.
  4. Converts symbols back to Morse: `symbol_sequence_to_morse()`.
  5. Decodes Morse to plaintext: `morse_to_text()`.
  6. Returns dictionary with `text`, `morse`, `symbols`, `frame_count`, `success`, first recovered frame preview `image`, and `frames`.

---

### `services/basic_energy_service.py`
Path: [`backend/services/basic_energy_service.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/services/basic_energy_service.py)

Implements the basic Morse image encryption and dual-extraction routes.

#### Functions:
1. `encrypt_basic_morse_message(...) -> dict`:
   - Prepares clamped base image and computes theoretical energy levels & decision thresholds.
   - Encodes text into Morse and symbol states.
   - For each symbol, generates uncancelled offset image: `generate_basic_symbol_image(symbol, base)`.
   - Encrypts each frame via DRPE and stores `Frame` with `c_complex` and `amplitude`.
   - Stores `thresholds` and `energy_levels` in message metadata.
   - Returns dictionary with `message_id`, `salt_b64`, `thresholds`, `energy_levels`, `frame_count`, and `previews`.

2. `decrypt_basic_morse_normal(message_id, secret_key_image, secret_password) -> dict`:
   - Normal credentialed decryption path.
   - Decrypts each complex frame using DRPE and Bob's keys.
   - Quantizes recovered global image brightness: `extract_symbol_from_decrypted_image(...)`.
   - Decodes symbols to Morse and text.
   - Returns dictionary with `text`, `morse`, `symbols`, `frames` (including `mean_brightness`, `brightness_delta`, and `total_energy`).

3. `predict_basic_morse_from_energy(message_id: str) -> dict`:
   - **Zero-Decryption Side-Channel Path**:
   - Accesses stored complex frames without Bob's key image and without password.
   - Reads Parseval energy of each frame: `c_energy = energy(frame.amplitude)`.
   - Classifies energy against stored decision thresholds: `predict_symbol_from_energy(c_energy, thresholds)`.
   - Reconstructs Morse string and plaintext directly from predicted symbols.
   - Returns dictionary with `predicted_text`, `predicted_morse`, `predicted_symbols`, `frame_energies`, `thresholds`, `frames`, and `bypassed_decryption=True`.

---

## 13. Test Suite Architecture & Verification

The test suite is written with `pytest` and uses FastAPI's `TestClient` for HTTP testing.

### `tests/test_drpe.py`
Path: [`backend/tests/test_drpe.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_drpe.py)
- `test_key_derivation()`: Asserts key derivation determinism and uniqueness across different seeds and frame indices.
- `test_drpe_roundtrip_fidelity()`: Verifies exact reconstruction of cover image ($\text{max error} < 10^{-15}$).
- `test_drpe_partial_and_wrong_mask_rejection()`: Verifies that wrong $P_1$, wrong $P_2$, or both wrong produce garbled noise ($\text{error} > 10.0$).
- `test_parseval_energy_invariance()`: Verifies $\sum I^2$ calculation on a known matrix.
- `test_api_health()`: Tests `GET /api/health`.
- `test_api_encrypt_decrypt_flow()`: Tests full HTTP encryption/decryption flow and validates `match_with_cover` boolean.
- `test_variable_size_image_encryption()`: Verifies handling of non-square rectangular RGB images (e.g. $384 \times 512 \times 3$).

### `tests/test_phase2_decryption.py`
Path: [`backend/tests/test_phase2_decryption.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_phase2_decryption.py)
- `test_morse_roundtrip()`: Verifies that text $\rightarrow$ Morse $\rightarrow$ text roundtrips accurately for standard phrases, punctuation, and numerals.
- `test_symbol_sequence_roundtrip()`: Verifies that Morse string $\rightarrow$ symbol sequence $\rightarrow$ Morse string is identical.
- `test_text_encryption_decryption_service()`: Tests end-to-end differential text encryption and decryption service logic.
- `test_text_decryption_wrong_password_or_key()`: Verifies that wrong password or wrong key image fails to recover plaintext.
- `test_api_text_encrypt_and_decrypt_flow()`: Integration test for `POST /api/text/encrypt` and `POST /api/text/decrypt`.

### `tests/test_basic_energy_morse.py`
Path: [`backend/tests/test_basic_energy_morse.py`](file:///Users/tafsiralnafin/Documents/Signal_Project/Encryption-System/backend/tests/test_basic_energy_morse.py)
- `test_basic_morse_encoding_and_decoding()`: Verifies Morse formatting (words separated by `'/'`, letters by `' '`).
- `test_unrecognized_codes_mapped_to_question_mark()`: Verifies invalid tokens map to `'?'`.
- `test_energy_monotonic_separation()`: Asserts $E(\text{DOT}) < E(\text{DASH}) < E(\text{LETTER\_GAP}) < E(\text{WORD\_GAP})$ and confirms decision threshold classification.
- `test_drpe_parseval_conservation_on_basic_frames()`: Verifies that DRPE ciphertext energy matches spatial frame energy ($rtol \le 10^{-5}$).
- `test_end_to_end_service_encryption_and_prediction()`: Verifies that `predict_basic_morse_from_energy` recovers plaintext without keys, while normal decryption succeeds with correct credentials and fails with wrong credentials.
- `test_api_basic_energy_endpoints_flow()`: Tests HTTP endpoints `/api/text/basic-energy/encrypt`, `/api/text/basic-energy/predict` (zero credentials provided), and `/api/text/basic-energy/decrypt`.

---

## 14. Complete API Endpoint Specification

| Endpoint | Method | Content-Type | Parameters / Body | Response Schema | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | `application/json` | None | `{"status": "ok"}` | Service health probe |
| `/api/encrypt` | `POST` | `multipart/form-data` | `cover_image` (file), `secret_key_image` (file), `secret_password` (str), `message_id` (opt str), `frame_index` (opt int) | `EncryptResponse` | Encrypts cover image via DRPE; returns display PNG, Parseval energy, and 5 process stages |
| `/api/decrypt-with-key-images` | `POST` | `multipart/form-data` | `message_id` (str), `secret_key_image` (file), `secret_password` (str), `frame_index` (opt int) | `DecryptResponse` | Decrypts complex ciphertext via DRPE; returns recovered image, energy, match boolean, and 5 reverse stages |
| `/api/text/encrypt` | `POST` | `multipart/form-data` | `secret_text` (str), `base_image` (file), `secret_key_image` (file), `secret_password` (str) | `TextEncryptResponse` | Encrypts text using 2-bit differential brightness blocks (zero energy leakage) |
| `/api/text/decrypt` | `POST` | `multipart/form-data` | `message_id` (str), `secret_key_image` (file), `secret_password` (str) | `TextDecryptResponse` | Recovers frames with credentials, detects block brightness differentials, decodes Morse and text |
| `/api/text/basic-energy/encrypt` | `POST` | `multipart/form-data` | `secret_text` (str), `base_image` (file), `secret_key_image` (file), `secret_password` (str) | `BasicEnergyEncryptResponse` | Encrypts text using uncancelled global brightness offsets; calculates energy levels and thresholds |
| `/api/text/basic-energy/decrypt` | `POST` | `multipart/form-data` | `message_id` (str), `secret_key_image` (file), `secret_password` (str) | `BasicEnergyDecryptResponse` | Normal DRPE decryption of basic energy frames using Bob's credentials |
| `/api/text/basic-energy/predict` | `POST` | `multipart/form-data` | `message_id` (str) | `BasicEnergyPredictResponse` | **Side-channel prediction**: Recovers Morse and text directly from Parseval energy with zero decryption and no keys |
