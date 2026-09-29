# 🛡️ Double Random Phase Encryption (DRPE) Optical Cryptosystem & Steganographic Transmission

An end-to-end optical cryptography and signal transmission system implementing classical **4-f Double Random Phase Encoding (DRPE)** in the Fourier domain. The platform features modern cryptographic key derivation (**Scrypt**, **HMAC-SHA256**), client-side image processing, and steganographic text transmission over multi-frame image sequences using **Morse code** with **differential brightness modulation** and side-channel energy analysis.

---

## 📌 Table of Contents

- [Overview & Architecture](#-overview--architecture)
- [Theoretical & Mathematical Foundations](#-theoretical--mathematical-foundations)
  - [4-f DRPE Optical Pipeline](#1-4-f-drpe-optical-pipeline)
  - [Parseval's Energy Invariance](#2-parsevals-energy-invariance)
  - [Cryptographic Key Derivation (KDF)](#3-cryptographic-key-derivation-kdf)
  - [Phase 2: Morse Code & Differential Modulation](#4-phase-2-morse-code--differential-modulation)
  - [The Side-Channel Energy Vulnerability](#5-the-side-channel-energy-vulnerability)
- [System Features](#-system-features)
  - [Backend Features](#backend-features)
  - [Frontend Features](#frontend-features)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Backend API Reference](#-backend-api-reference)
- [Installation & Getting Started](#-installation--getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Running Automated Tests](#-running-automated-tests)
- [Security & Signal Processing Insights](#-security--signal-processing-insights)

---

## 🔬 Overview & Architecture

The repository simulates a physical 4-f optical encryption architecture combined with an Alice-and-Bob communications protocol:

```text
       ALICE (Sender)                                              BOB (Receiver)
┌──────────────────────────┐                               ┌──────────────────────────┐
│  • Cover Image / Text    │                               │  • Secret Key Image      │
│  • Secret Key Image      │                               │  • Password Material     │
│  • Password String       │                               └────────────┬─────────────┘
└────────────┬─────────────┘                                            │
             │ HTTP POST                                                │ HTTP POST
             ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND SYSTEM                                │
│                                                                                     │
│  1. Key Normalization & Scrypt KDF -> Master Key                                    │
│  2. HMAC Frame Derivation -> Phase Masks (P1 in spatial, P2 in Fourier domain)      │
│  3. DRPE Optical Fourier Pipeline:                                                  │
│     Spatial Rotation -> 2D-FFT -> Fourier Phase Rotation -> 2D-IFFT -> Ciphertext   │
│  4. Steganographic Modulation (Differential Brightness or Basic Energy Morse)       │
│  5. In-Memory Multi-Frame Message Store                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Theoretical & Mathematical Foundations

### 1. 4-f DRPE Optical Pipeline

The core mathematical engine in `backend/services/drpe.py` models an optical 4-f Fourier transform processor:

1. **Spatial Plane Modulation**: The 2D input image $f(x, y)$ is phase-modulated by an independent random phase mask $P_1(x, y) \in [0, 2\pi)$:
   $$s(x, y) = f(x, y) \cdot \exp\left(j \cdot P_1(x, y)\right)$$

2. **Optical Fourier Transform (First Lens)**: The wave propagates to the frequency plane via a 2D Discrete Fourier Transform:
   $$G(u, v) = \mathcal{F}_{2D}\left\{s(x, y)\right\}$$

3. **Fourier Plane Modulation**: The spectral distribution is modulated by a second independent random phase mask $P_2(u, v) \in [0, 2\pi)$:
   $$G'(u, v) = G(u, v) \cdot \exp\left(j \cdot P_2(u, v)\right)$$

4. **Inverse Fourier Transform (Second Lens)**: The signal propagates to the output spatial plane:
   $$c(x, y) = \mathcal{F}_{2D}^{-1}\left\{G'(u, v)\right\}$$
   The resulting complex array $c(x, y)$ constitutes the stationary white-noise-like ciphertext. The displayable preview corresponds to the amplitude $|c(x, y)|$.

5. **Decryption**: Using the exact conjugate phase masks $\exp(-j P_2)$ and $\exp(-j P_1)$ on the complex ciphertext $c(x, y)$:
   $$G'(u, v) = \mathcal{F}_{2D}\left\{c(x, y)\right\}$$
   $$G(u, v) = G'(u, v) \cdot \exp\left(-j \cdot P_2(u, v)\right)$$
   $$s(x, y) = \mathcal{F}_{2D}^{-1}\left\{G(u, v)\right\}$$
   $$f_{\text{recovered}}(x, y) = \text{Re}\left(s(x, y) \cdot \exp\left(-j \cdot P_1(x, y)\right)\right)$$

### 2. Parseval's Energy Invariance

By Parseval's theorem, unitary Fourier transformations preserve the total signal energy $\sum |x|^2$:
$$\sum_{x, y} |f(x, y)|^2 = \sum_{x, y} |c(x, y)|^2$$
The system computes and verifies the Parseval energy invariant:
$$E = \sum_{i, j} (\text{pixel}_{i, j})^2$$

### 3. Cryptographic Key Derivation (KDF)

Rather than relying on raw seeds or sequential offsets, the system enforces a cryptographically hardened key derivation hierarchy (`backend/services/keys.py`):
- **Image Canonicalization**: The uploaded key image is normalized into raw pixel bytes and hashed using `SHA-256` to produce a fixed 32-byte image digest.
- **Password KDF**: The password material is expanded with a 16-byte random salt using `scrypt` ($N=16384, r=8, p=1, \text{dklen}=32$).
- **Master Key**:
  $$\text{MasterKey} = \text{SHA-256}\left(\text{"DRPE-MASTER-v1"} \parallel \text{PasswordKey} \parallel \text{KeyImageDigest}\right)$$
- **Frame-Index-Bound Mask Generation**: Each frame $k$ derives independent, non-correlated phase seeds via HMAC:
  $$\text{Seed}_{P_1} = \text{HMAC-SHA-256}\left(\text{MasterKey}, \text{"DRPE-v1"} \parallel \text{"DRPE/P1"} \parallel \text{MessageID} \parallel k\right)$$
  $$\text{Seed}_{P_2} = \text{HMAC-SHA-256}\left(\text{MasterKey}, \text{"DRPE-v1"} \parallel \text{"DRPE/P2"} \parallel \text{MessageID} \parallel k\right)$$
  This guarantees that compromising frame $k$ leaks zero information about frame $k+1$.

---

### 4. Phase 2: Morse Code & Differential Modulation

Text transmission breaks down messages into international Morse code and assigns each character to a discrete symbol state:
- `DOT = 0` (`.`)
- `DASH = 1` (`-`)
- `LETTER_GAP = 2` (single space)
- `WORD_GAP = 3` (`/`)

#### Differential Two-Block-Pair Brightness Modulation (Secure)
To prevent energy leakage, `backend/services/encoding/symbol_image.py` implements a 4-block differential modulation scheme using two orthogonal block pairs:
- **Pair 1**: Block A $(10, 10)$ and Block B $(10, 50)$
- **Pair 2**: Block C $(50, 10)$ and Block D $(50, 50)$

Each symbol state maps to a 2-bit sign pattern $(\text{bit}_1, \text{bit}_2)$ with a fixed delta $\Delta = 8$:
- **DOT** $(0) \to (+1, +1)$: Pair 1 $(+\Delta, -\Delta)$, Pair 2 $(+\Delta, -\Delta)$
- **DASH** $(1) \to (+1, -1)$: Pair 1 $(+\Delta, -\Delta)$, Pair 2 $(-\Delta, +\Delta)$
- **LETTER_GAP** $(2) \to (-1, +1)$: Pair 1 $(-\Delta, +\Delta)$, Pair 2 $(+\Delta, -\Delta)$
- **WORD_GAP** $(3) \to (-1, -1)$: Pair 1 $(-\Delta, +\Delta)$, Pair 2 $(-\Delta, +\Delta)$

**Energy Cancellation Proof**:
Because every pair adds $+\Delta$ to one block and subtracts $-\Delta$ from the other:
$$\Delta \mu = \sum \Delta \text{pixel} = 0$$
The global Parseval energy of the frame remains completely constant across all symbols, neutralizing side-channel energy leakage.

---

### 5. The Side-Channel Energy Vulnerability (Educational Demonstration)

In `backend/services/basic_energy_service.py`, the system implements an uncancelled brightness modulation scheme:
$$\text{Offset} = \text{symbol} \times 20.0 \quad (\text{symbol} \in \{0, 1, 2, 3\})$$
Because the brightness offset is added without cancellation, the total frame energy increases monotonically:
$$E(\text{DOT}) < E(\text{DASH}) < E(\text{LETTER\_GAP}) < E(\text{WORD\_GAP})$$

By Parseval's theorem, this energy difference is preserved through the DRPE Fourier transformation. Consequently, an observer can **predict the Morse code and plaintext directly from the ciphertext amplitude without decrypting and without knowing the secret keys or password** via `POST /api/text/basic-energy/predict`!

---

## ✨ System Features

### Backend Features
- **Pure Functional Optical Engine (`backend/services/drpe.py`)**: Stateless, vectorized NumPy DRPE pipeline executing 2D FFT/IFFT, phase mask rotation, and energy verification.
- **Process Stages Visualizer**: Exports intermediate visual states:
  - Spatial Input Plane ($s$)
  - Shifted Fourier Spectrum ($G$)
  - Frequency Phase Mask ($P_2$)
  - Modulated Fourier Spectrum ($G'$)
  - Spatial Ciphertext Amplitude ($|c|$)
- **Dual Text Transmission Schemes**:
  1. *Differential Brightness Encoding*: Cryptographically secure 2-bit differential cancellation with zero energy leakage.
  2. *Basic Energy Modulation*: Demonstrator of Parseval energy leakage and side-channel classification.
- **Side-Channel Energy Predictor (`backend/services/basic_energy_service.py`)**: Automatic decision boundary calculation and threshold classification recovering Morse code with zero decryption.
- **Canonical Key Image Processor (`backend/services/image_utils.py`)**: Deterministic key image reading, mode normalization (RGB/L), base64 serializations, and SHA-256 fingerprinting.
- **In-Memory Message Registry (`backend/services/messages.py`)**: Concurrent, thread-safe store for multi-frame transmissions, complex NumPy arrays, and frame metadata.
- **FastAPI Modular Design**: RESTful architecture separating routers, controllers, validation schemas (Pydantic), and mathematical services.

### Frontend Features
- **Dynamic Role-Based Interface (`App.jsx`)**:
  - **Alice Terminal (`AlicePage.jsx`)**:
    - **Send Image Mode**: Upload cover image, key image, and password; view intermediate optical stages in real time.
    - **Send Text Mode**: Encrypt secret messages into differential Morse frames with live symbol breakdowns.
    - **Send Basic Energy Mode**: Transmit text with intentional energy signatures for side-channel vulnerability testing.
  - **Bob Terminal (`BobPage.jsx`)**:
    - Automatic detection of transmitted message packets.
    - DRPE Decryption: Input matching key image and password to recover images or plaintext.
    - Interactive Multi-Frame Stepper / Carousel for multi-frame Morse transmissions.
    - **"Extract Morse via Ciphertext Energy"**: One-click side-channel attack tool extracting text directly from Parseval energy levels.
    - Diagnostic Inspectors: Per-frame differential metrics, brightness deltas, energy deviation plots, and decision thresholds.
  - **Supervisor DRPE Laboratory (`DRPEDemo.jsx`)**:
    - Standalone single-page testbed for rapid side-by-side DRPE parameter exploration and Parseval energy verification.
- **Client-Side Image Resizer (`imageResizer.js`)**:
  - High-performance HTML5 Canvas resizer supporting arbitrary aspect ratios and scaling images larger than 2048px without distortion.
- **Atmospheric Visuals (`NoiseReveal.jsx`)**:
  - SVG-based procedural glass-shard noise reveal overlay with dynamic keyframe twinkle animations reflecting encryption and optical phase dispersion.

---

## 🛠️ Technology Stack

### Backend
| Technology | Version / Spec | Purpose |
| :--- | :--- | :--- |
| **Python** | 3.9+ / 3.13 | Core backend programming language |
| **FastAPI** | Latest | High-performance asynchronous REST API framework |
| **Uvicorn** | Standard | ASGI production web server |
| **NumPy** | Latest | High-speed FFT2, IFFT2, complex array manipulation, matrix math |
| **Pillow (PIL)** | Latest | Image decoding, canonicalization, and format conversion |
| **Pydantic** | v2 | Request/response data validation and serialization |
| **Python-Multipart** | Latest | Streaming multipart/form-data upload handling |
| **Standard Cryptography** | `hashlib`, `hmac`, `secrets` | Scrypt KDF, HMAC-SHA256, secure salt generation |
| **Pytest** | Latest | Automated testing framework for unit & integration suites |

### Frontend
| Technology | Version / Spec | Purpose |
| :--- | :--- | :--- |
| **React** | 18.2.0 | Reactive UI library with hooks |
| **Vite** | 5.0.0 | Next-generation frontend build tool and dev server |
| **Axios** | 1.6.0 | HTTP client communicating with FastAPI endpoints |
| **HTML5 Canvas API** | Native | Client-side proportional image resizing and thumbnailing |
| **SVG / CSS3** | Custom | Shard-based procedural noise overlay and dark theme styling |

---

## 📂 Project Directory Structure

```text
Encryption-System/
├── README.md                      # Comprehensive project documentation
├── Text-Encryption.md             # Specification for Phase 2 Morse transmission
├── backend/
│   ├── main.py                    # FastAPI entrypoint and CORS configuration
│   ├── config.py                  # Single source of truth for coordinates and constants
│   ├── requirements.txt           # Python dependency manifest
│   ├── routers/
│   │   ├── image_router.py        # Phase 1 image encryption/decryption routes
│   │   └── text_router.py         # Phase 2 differential and basic energy text routes
│   ├── controllers/
│   │   ├── image_controller.py    # Request handling for image operations
│   │   └── text_controller.py     # Request handling for text operations
│   ├── schemas/
│   │   └── image_schema.py        # Pydantic models for API request/response validation
│   ├── services/
│   │   ├── drpe.py                # Pure 4-f optical DRPE encryption and decryption math
│   │   ├── keys.py                # Scrypt KDF and HMAC-SHA256 per-frame key derivation
│   │   ├── image_utils.py         # Image canonicalization and base64 conversions
│   │   ├── messages.py            # In-memory transmission registry for multi-frame packets
│   │   ├── basic_energy_service.py# Basic Morse encryption and side-channel prediction
│   │   ├── text_encryption.py     # Differential brightness text encryption service
│   │   ├── text_decryption.py     # Differential brightness text decryption service
│   │   └── encoding/
│   │       ├── text_to_morse.py   # Text to ITU Morse converter
│   │       ├── morse_to_text.py   # ITU Morse to plaintext converter
│   │       ├── morse_to_symbol_sequence.py # Morse to 4-state symbol mapper
│   │       ├── symbol_image.py    # 4-block differential brightness image generator
│   │       └── basic_energy_morse.py       # Single-block energy modulation generator
│   └── tests/
│       ├── test_drpe.py           # Unit tests for DRPE math and roundtrip fidelity
│       ├── test_phase2_decryption.py # End-to-end tests for differential text transmission
│       └── test_basic_energy_morse.py# Tests for energy separation and side-channel extraction
└── frontend/
    ├── package.json               # Frontend dependency manifest
    ├── vite.config.js             # Vite configuration
    ├── index.html                 # Single-page application root
    └── src/
        ├── main.jsx               # React DOM entrypoint
        ├── App.jsx                # Main application component & role router (Alice/Bob)
        ├── api.js                 # Axios API client configured for backend baseURL
        ├── pages/
        │   ├── AlicePage.jsx      # Sender interface (Image, Text, Basic Energy modes)
        │   ├── BobPage.jsx        # Receiver interface (DRPE Decrypt & Energy Predictor)
        │   └── DRPEDemo.jsx       # Supervisor laboratory for standalone DRPE evaluation
        ├── components/
        │   ├── NoiseReveal.jsx    # Animated SVG glass-shard optical overlay
        │   └── drpe/
        │       └── ImagePanel.jsx # Reusable image preview component
        └── utils/
            └── imageResizer.js    # Client-side canvas image processor
```

---

## 📡 Backend API Reference

### 1. General
- **`GET /api/health`**
  - **Returns**: `{"status": "ok"}`
  - **Purpose**: System health and liveness check.

---

### 2. Phase 1: Image Encryption & Decryption
- **`POST /api/encrypt`**
  - **Payload (`multipart/form-data`)**:
    - `cover_image`: Original image file (JPEG/PNG).
    - `secret_key_image`: Key image file for mask derivation.
    - `secret_password`: Password string.
    - `message_id`: (Optional) Unique transmission identifier.
    - `frame_index`: (Optional, default `0`).
  - **Returns**: `EncryptResponse` (contains display magnitude image, Parseval cover and ciphertext energies, `message_id`, salt, and intermediate stages).

- **`POST /api/decrypt-with-key-images`**
  - **Payload (`multipart/form-data`)**:
    - `message_id`: ID of the stored transmission.
    - `secret_key_image`: Receiver's key image.
    - `secret_password`: Receiver's password.
    - `frame_index`: (Optional, default `0`).
  - **Returns**: `DecryptResponse` (recovered image base64, energy, `match_with_cover` boolean, and intermediate decryption stages).

---

### 3. Phase 2: Differential Brightness Text Transmission (Secure)
- **`POST /api/text/encrypt`**
  - **Payload (`multipart/form-data`)**:
    - `secret_text`: Plaintext message to encrypt.
    - `base_image`: Base RGB carrier image.
    - `secret_key_image`: Key image file.
    - `secret_password`: Password string.
  - **Returns**: `TextEncryptResponse` (`message_id`, `morse`, `symbols`, `frame_count`, `previews`).

- **`POST /api/text/decrypt`**
  - **Payload (`multipart/form-data`)**:
    - `message_id`: ID of the stored text packet.
    - `secret_key_image`: Bob's key image.
    - `secret_password`: Bob's password.
  - **Returns**: `TextDecryptResponse` (`text`, `morse`, `symbols`, `success`, `frames` diagnostics).

---

### 4. Phase 2: Basic Energy Text Transmission & Side-Channel Analysis
- **`POST /api/text/basic-energy/encrypt`**
  - **Payload (`multipart/form-data`)**:
    - `secret_text`: Plaintext string.
    - `base_image`: Base image file.
    - `secret_key_image`: Key image file.
    - `secret_password`: Password string.
  - **Returns**: `BasicEnergyEncryptResponse` (`thresholds`, `energy_levels`, `previews`, `symbols`).

- **`POST /api/text/basic-energy/decrypt`**
  - **Payload (`multipart/form-data`)**:
    - `message_id`: ID of the message.
    - `secret_key_image`: Key image file.
    - `secret_password`: Password string.
  - **Returns**: `BasicEnergyDecryptResponse` (normal DRPE decryption of basic energy frames).

- **`POST /api/text/basic-energy/predict`**
  - **Payload (`multipart/form-data`)**:
    - `message_id`: ID of the message.
  - **Returns**: `BasicEnergyPredictResponse` (**Zero-Decryption** recovery containing `predicted_text`, `predicted_morse`, `frame_energies`, and `thresholds`).

---

## 🚀 Installation & Getting Started

### Prerequisites
- **Python**: Version `3.9` or higher (tested up to `3.13`)
- **Node.js**: Version `18.x` or higher
- **npm**: Version `9.x` or higher

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the FastAPI application**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend will be live at `http://127.0.0.1:8000` with interactive API docs at `http://127.0.0.1:8000/docs`.

---

### Frontend Setup

1. **Open a new terminal and navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   Open your browser and navigate to `http://localhost:5173`.

---

## 🧪 Running Automated Tests

The backend includes a comprehensive automated test suite covering mathematical accuracy, roundtrip fidelity, key derivation uniqueness, and side-channel classification:

```bash
cd backend
# Run all tests
pytest -v

# Run individual test modules
pytest tests/test_drpe.py -v
pytest tests/test_phase2_decryption.py -v
pytest tests/test_basic_energy_morse.py -v
```

### Key Assertions Tested:
- **Mathematical Roundtrip Precision**: $\text{max error} < 10^{-15}$ when decrypting with identical dual keys.
- **Partial/Wrong Key Rejection**: Decryption with incorrect $P_1$ or $P_2$ yields unrecognizable noise ($\text{error} > 10.0$).
- **Parseval Energy Conservation**: Invariance of total energy across spatial and Fourier transformations.
- **Side-Channel Separation**: Rigorous monotonic ordering of $E(\text{DOT}) < E(\text{DASH}) < E(\text{LETTER\_GAP}) < E(\text{WORD\_GAP})$.
- **Zero-Decryption Prediction**: 100% accurate Morse and text extraction directly from ciphertext energy.

---

## 💡 Security & Signal Processing Insights

1. **Why Naive Sequential Seeds Failed**:
   Earlier designs used linear seed sequences ($S_k = S_0 + k$). Recovering one frame's key compromised all subsequent frames. The current architecture replaces this with **HMAC-SHA256 frame-index binding**, ensuring forward secrecy across frames.
2. **Why Energy Cancellation is Critical in Steganography**:
   Modulating intensity without differential cancellation creates an energy fingerprint that survives Fourier-domain phase scrambling due to Parseval's theorem. The **4-block differential technique** ensures that for every block receiving $+\Delta$, a counterpart receives $-\Delta$, making the ciphertext mathematically indistinguishable from random noise across all energy analyses.
