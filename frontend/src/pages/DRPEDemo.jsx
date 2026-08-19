import { useEffect, useState } from "react";
import api from "../api.js";
import ImagePanel from "../components/drpe/ImagePanel.jsx";
import { processImageFile } from "../utils/imageResizer.js";

/**
 * Supervisor-facing DRPE demo. One self-contained view that walks
 * through: upload → encrypt → decrypt with manual user inputs for P1 and P2.
 */
export default function DRPEDemo() {
  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null); // base64 string
  const [resizeInfo, setResizeInfo] = useState(null);

  // Dual seeds for Encryption (Sender)
  const [seedP1, setSeedP1] = useState("seed-p1-demo");
  const [seedP2, setSeedP2] = useState("seed-p2-demo");

  // Receiver decryption inputs (initially empty, only populated if user types or clicks helper)
  const [decryptP1, setDecryptP1] = useState("");
  const [decryptP2, setDecryptP2] = useState("");

  const [baseImage, setBaseImage] = useState(null);
  const [baseShape, setBaseShape] = useState(null);

  const [ciphertextB64, setCiphertextB64] = useState(null);
  const [ciphertextShape, setCiphertextShape] = useState(null);
  const [ciphertext, setCiphertext] = useState(null);
  const [coverEnergy, setCoverEnergy] = useState(null);
  const [cipherEnergy, setCipherEnergy] = useState(null);

  const [decryptedResult, setDecryptedResult] = useState(null);
  const [decryptedMatch, setDecryptedMatch] = useState(null);
  const [decryptStatusMessage, setDecryptStatusMessage] = useState("");

  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  // Fetch the predetermined base image once on mount.
  useEffect(() => {
    api
      .get("/base-image")
      .then((res) => {
        setBaseImage(res.data.image);
        setBaseShape(res.data.shape);
      })
      .catch((err) =>
        setError(err.response?.data?.detail || "Failed to load base image")
      );
  }, []);

  // Handle uploaded cover file with automatic variable image processor.
  const handleCoverFile = async (file) => {
    setError(null);
    setCiphertextB64(null);
    setCiphertextShape(null);
    setCiphertext(null);
    setDecryptedResult(null);
    setDecryptedMatch(null);
    setDecryptStatusMessage("");
    setCoverEnergy(null);
    setCipherEnergy(null);
    setDecryptP1("");
    setDecryptP2("");
    if (!file) {
      setCoverFile(null);
      setCoverPreview(null);
      setResizeInfo(null);
      return;
    }

    try {
      const res = await processImageFile(file, 2048);
      setCoverFile(res.processedFile);
      setCoverPreview(res.previewB64);
      setResizeInfo({
        isResized: res.isResized,
        width: res.width,
        height: res.height,
        originalWidth: res.originalWidth,
        originalHeight: res.originalHeight,
      });
    } catch (err) {
      console.error("Image processor error:", err);
      setCoverFile(file);
      setResizeInfo(null);
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result;
        const b64 = result.startsWith("data:") ? result.split(",")[1] : result;
        setCoverPreview(b64);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleEncrypt = async () => {
    if (!coverFile) return;
    setError(null);
    setBusy(true);
    setDecryptedResult(null);
    setDecryptedMatch(null);
    setDecryptStatusMessage("");
    const form = new FormData();
    form.append("cover_image", coverFile);
    form.append("seed_p1", seedP1);
    form.append("seed_p2", seedP2);
    try {
      const res = await api.post("/encrypt", form);
      setCiphertextB64(res.data.ciphertext_b64);
      setCiphertextShape(res.data.ciphertext_shape);
      setCiphertext(res.data.image);
      setCoverEnergy(res.data.cover_energy);
      setCipherEnergy(res.data.energy);
      // Keep decryption input boxes empty after encryption.
      // User must enter or choose P1 and P2 keys/seeds to decrypt.
    } catch (err) {
      console.error("Encrypt error:", err);
      const detail =
        err.response?.data?.detail || err.message || "Encrypt failed";
      setError(detail);
    } finally {
      setBusy(false);
    }
  };

  const handleUserDecrypt = async () => {
    if (!ciphertextB64 || !ciphertextShape) {
      setError("Please encrypt an image first.");
      return;
    }
    if (!decryptP1.trim() || !decryptP2.trim()) {
      setError("Please enter Decryption Key/Seed P₁ and P₂ in the boxes below before decrypting.");
      return;
    }
    setError(null);
    setBusy(true);
    setDecryptedResult(null);
    setDecryptedMatch(null);
    setDecryptStatusMessage("");

    // If user provided a base64 mask payload (> 100 chars), send as p1_b64/p2_b64; otherwise as seeds
    const isP1Base64 = decryptP1.length > 200;
    const isP2Base64 = decryptP2.length > 200;

    const payload = {
      ciphertext_b64: ciphertextB64,
      ciphertext_shape: ciphertextShape,
      ...(isP1Base64 && isP2Base64
        ? { p1_b64: decryptP1.trim(), p2_b64: decryptP2.trim() }
        : { seed_p1: decryptP1.trim(), seed_p2: decryptP2.trim() }),
    };

    try {
      const res = await api.post("/decrypt", payload);
      setDecryptedResult(res.data.image);
      setDecryptedMatch(res.data.match_with_cover);

      if (res.data.match_with_cover) {
        setDecryptStatusMessage(
          "✓ Decryption Successful! Keys P1 and P2 correctly matched and inverted the ciphertext back to the original RGB cover image."
        );
      } else {
        setDecryptStatusMessage(
          "⚠️ Decryption Output: Keys P1 or P2 do not match encryption keys. Showing exact phase noise generated by these keys."
        );
      }
    } catch (err) {
      console.error("Decrypt error:", err);
      const detail =
        err.response?.data?.detail || err.message || "Decrypt failed";
      setError(detail);
    } finally {
      setBusy(false);
    }
  };

  const randomP1 = () => setSeedP1(Math.random().toString(36).slice(2, 10));
  const randomP2 = () => setSeedP2(Math.random().toString(36).slice(2, 10));

  const pasteMatchingKeys = () => {
    setDecryptP1(seedP1);
    setDecryptP2(seedP2);
  };

  const pasteWrongP1 = () => {
    setDecryptP1(seedP1 + "_wrong");
    setDecryptP2(seedP2);
  };

  const pasteWrongP2 = () => {
    setDecryptP1(seedP1);
    setDecryptP2(seedP2 + "_wrong");
  };

  const clearDecryptInputs = () => {
    setDecryptP1("");
    setDecryptP2("");
  };

  return (
    <div>
      {/* Inputs Section */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
          marginBottom: 16,
        }}
      >
        {/* Step 1: Sender / Encryption setup */}
        <div
          style={{
            border: "1px solid #d9d9d9",
            borderRadius: 6,
            padding: 16,
            background: "#ffffff",
          }}
        >
          <h3
            style={{
              marginTop: 0,
              marginBottom: 12,
              fontSize: 16,
              color: "#1f2937",
            }}
          >
            1. Sender Setup (RGB Encryption)
          </h3>

          <div style={{ marginBottom: 12 }}>
            <label
              style={{
                display: "block",
                fontWeight: 600,
                fontSize: 13,
                marginBottom: 4,
              }}
            >
              RGB Cover Image Upload
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleCoverFile(e.target.files[0])}
            />
            <div style={{ marginTop: 4, color: "#666", fontSize: 12 }}>
              Upload any RGB resolution image (e.g. 256×256, 512×512, 1024×768).
            </div>
            {resizeInfo && (
              <div
                style={{
                  marginTop: 8,
                  padding: "6px 10px",
                  borderRadius: 4,
                  background: resizeInfo.isResized ? "#e6f4ff" : "#f6ffed",
                  border: `1px solid ${
                    resizeInfo.isResized ? "#91caff" : "#b7eb8f"
                  }`,
                  fontSize: 12,
                  color: resizeInfo.isResized ? "#0958d9" : "#389e0d",
                }}
              >
                🖼️ <strong>Image Specs:</strong> {resizeInfo.width}×
                {resizeInfo.height} px RGB{" "}
                {resizeInfo.isResized
                  ? `(scaled down from ${resizeInfo.originalWidth}×${resizeInfo.originalHeight} max 2048px limit)`
                  : "(native resolution maintained)"}
              </div>
            )}
          </div>

          {/* Encryption Seed P1 */}
          <div style={{ marginBottom: 8 }}>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: "#374151",
              }}
            >
              Encryption Seed P1 (Spatial Mask Seed)
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={seedP1}
                onChange={(e) => setSeedP1(e.target.value)}
                style={{ flex: 1, padding: "4px 8px" }}
              />
              <button onClick={randomP1} type="button">
                Random P1 Seed
              </button>
            </div>
          </div>

          {/* Encryption Seed P2 */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: "#374151",
              }}
            >
              Encryption Seed P2 (Frequency Mask Seed)
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={seedP2}
                onChange={(e) => setSeedP2(e.target.value)}
                style={{ flex: 1, padding: "4px 8px" }}
              />
              <button onClick={randomP2} type="button">
                Random P2 Seed
              </button>
            </div>
          </div>

          <button
            onClick={handleEncrypt}
            disabled={!coverFile || busy}
            style={{
              width: "100%",
              fontWeight: 600,
              padding: "8px 16px",
              background: "#1f6feb",
              color: "#ffffff",
              border: "none",
              borderRadius: 4,
              cursor: coverFile && !busy ? "pointer" : "not-allowed",
              opacity: coverFile && !busy ? 1 : 0.6,
            }}
          >
            {busy ? "Encrypting..." : "🔒 Encrypt Cover Image (RGB)"}
          </button>
        </div>

        {/* Step 2: Receiver / Decryption setup */}
        <div
          style={{
            border: "1px solid #d9d9d9",
            borderRadius: 6,
            padding: 16,
            background: "#fafafa",
          }}
        >
          <h3
            style={{
              marginTop: 0,
              marginBottom: 12,
              fontSize: 16,
              color: "#1f2937",
            }}
          >
            2. Receiver Setup (Decryption Keys P₁ & P₂)
          </h3>

          {/* Decryption Key P1 Input */}
          <div style={{ marginBottom: 12 }}>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: "#374151",
                marginBottom: 4,
              }}
            >
              Decryption Key / Seed P₁ (Spatial Domain)
            </label>
            <input
              type="text"
              placeholder="Enter P1 decryption key/seed..."
              value={decryptP1}
              onChange={(e) => setDecryptP1(e.target.value)}
              style={{
                width: "100%",
                padding: "6px 10px",
                fontSize: 13,
                boxSizing: "border-box",
                borderRadius: 4,
                border: "1px solid #ccc",
                background: "#ffffff",
              }}
            />
          </div>

          {/* Decryption Key P2 Input */}
          <div style={{ marginBottom: 14 }}>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: "#374151",
                marginBottom: 4,
              }}
            >
              Decryption Key / Seed P₂ (Frequency Domain)
            </label>
            <input
              type="text"
              placeholder="Enter P2 decryption key/seed..."
              value={decryptP2}
              onChange={(e) => setDecryptP2(e.target.value)}
              style={{
                width: "100%",
                padding: "6px 10px",
                fontSize: 13,
                boxSizing: "border-box",
                borderRadius: 4,
                border: "1px solid #ccc",
                background: "#ffffff",
              }}
            />
          </div>

          {/* Helper buttons for quick testing */}
          <div
            style={{
              marginBottom: 14,
              borderTop: "1px dashed #ccc",
              paddingTop: 10,
            }}
          >
            <div style={{ fontSize: 11, color: "#666", marginBottom: 6 }}>
              Quick Demo Actions:
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={pasteMatchingKeys}
                style={{ fontSize: 11, padding: "4px 8px", cursor: "pointer" }}
                title="Fill with sender's exact P1 and P2 keys"
              >
                📋 Paste Matching Keys
              </button>
              <button
                type="button"
                onClick={pasteWrongP1}
                style={{ fontSize: 11, padding: "4px 8px", cursor: "pointer" }}
                title="Test decryption failure with wrong P1"
              >
                ⚡ Wrong P1 Key
              </button>
              <button
                type="button"
                onClick={pasteWrongP2}
                style={{ fontSize: 11, padding: "4px 8px", cursor: "pointer" }}
                title="Test decryption failure with wrong P2"
              >
                ⚡ Wrong P2 Key
              </button>
              <button
                type="button"
                onClick={clearDecryptInputs}
                style={{ fontSize: 11, padding: "4px 8px", cursor: "pointer" }}
                title="Clear all decryption inputs"
              >
                🗑️ Clear
              </button>
            </div>
          </div>

          <button
            onClick={() => handleUserDecrypt()}
            disabled={!ciphertextB64 || busy}
            style={{
              width: "100%",
              fontWeight: 600,
              padding: "8px 16px",
              background: "#2da44e",
              color: "#ffffff",
              border: "none",
              borderRadius: 4,
              cursor: ciphertextB64 && !busy ? "pointer" : "not-allowed",
              opacity: ciphertextB64 && !busy ? 1 : 0.6,
            }}
          >
            {busy ? "Decrypting..." : "🔓 Decrypt Image"}
          </button>
        </div>
      </section>


      {error && (
        <div
          style={{
            padding: "8px 12px",
            background: "#ffebe9",
            border: "1px solid #ff8182",
            borderRadius: 4,
            color: "#cf222e",
            marginBottom: 16,
          }}
        >
          Error: {error}
        </div>
      )}

      {decryptStatusMessage && (
        <div
          style={{
            padding: "8px 12px",
            background: decryptedMatch ? "#dafbe1" : "#fff8c5",
            border: `1px solid ${decryptedMatch ? "#4ac26b" : "#d4a72c"}`,
            borderRadius: 4,
            color: decryptedMatch ? "#1a7f37" : "#9a6700",
            marginBottom: 16,
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          {decryptStatusMessage}
        </div>
      )}

      {/* Step 3: result grid */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <ImagePanel
          title="Original cover (RGB)"
          src={coverPreview}
          caption={
            coverFile
              ? resizeInfo
                ? `${coverFile.name} (${resizeInfo.width}×${resizeInfo.height} px RGB)`
                : coverFile.name
              : ""
          }
        />
        <ImagePanel
          title="Ciphertext (|DRPE(cover)|)"
          src={ciphertext}
          caption={
            ciphertext
              ? `Energy Σ·pixel² = ${formatEnergy(
                  cipherEnergy
                )} (vs cover ${formatEnergy(coverEnergy)})`
              : "noise-like, not viewable in plain form"
          }
        />
        <ImagePanel
          title="Decrypted Image Output (RGB)"
          src={decryptedResult}
          caption={
            decryptedResult
              ? decryptedMatch
                ? "✓ Matches original RGB image perfectly."
                : "⚠️ Uncorrelated noise output (incorrect P1 or P2 key used)."
              : "Enter P1 & P2 keys and click 'Decrypt Image'."
          }
        />
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "1fr",
          gap: 12,
        }}
      >
        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 4,
            padding: 12,
            background: "#fafafa",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>
            RGB DRPE Key-Based Decryption Workflow
          </div>
          <ol style={{ paddingLeft: 18, margin: 0 }}>
            <li>
              The sender encrypts the RGB cover image using spatial mask{" "}
              <code>P₁</code> and frequency mask <code>P₂</code> derived from sender seeds and the predetermined base image.
            </li>
            <li>
              The receiver enters decryption keys <code>P₁</code> and <code>P₂</code> (or uses quick action buttons). The input boxes remain clean and empty after encryption until typed into or filled.
            </li>
            <li>
              The backend computes the reverse complex rotation:
              <code
                style={{
                  display: "block",
                  margin: "4px 0",
                  background: "#f0f0f0",
                  padding: "4px 8px",
                }}
              >
                FFT₂D(Ciphertext) · e<sup>-jP₂</sup> → IFFT₂D → · e<sup>-jP₁</sup>
              </code>
            </li>
            <li>
              If $P_1$ and $P_2$ match the encryption keys, the phase rotations cancel out, producing the original RGB cover image. If either key is wrong or modified, the output is un-recoverable phase noise.
            </li>
          </ol>
        </div>
      </section>

      {/* Base image transparency */}
      <section style={{ marginTop: 16 }}>
        <details>
          <summary style={{ cursor: "pointer", color: "#1f6feb" }}>
            Show the predetermined base image
          </summary>
          <div
            style={{
              marginTop: 8,
              display: "flex",
              gap: 16,
              alignItems: "flex-start",
            }}
          >
            <ImagePanel
              title="Predetermined base image"
              src={baseImage}
              height={160}
              caption={
                baseShape ? `${baseShape[0]}×${baseShape[1]} px RGB (${baseShape[2]} channels)` : ""
              }
            />
            <p
              style={{ fontSize: 12, color: "#555", maxWidth: 480, margin: 0 }}
            >
              This image is part of key derivation. Both sender and receiver use the
              same base image; the seeds alone generate $P_1$ and $P_2$, which are then passed as-is into decryption.
            </p>
          </div>
        </details>
      </section>
    </div>
  );
}

function formatEnergy(e) {
  if (e == null) return "—";
  if (e > 1e9) return (e / 1e9).toFixed(3) + " B";
  if (e > 1e6) return (e / 1e6).toFixed(3) + " M";
  if (e > 1e3) return (e / 1e3).toFixed(3) + " k";
  return e.toFixed(2);
}

