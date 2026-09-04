import { useState } from "react";
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

  const [secretKeyImage, setSecretKeyImage] = useState(null);
  const [secretPassword, setSecretPassword] = useState("");

  const [receiverSecretKeyImage, setReceiverSecretKeyImage] = useState(null);
  const [receiverPassword, setReceiverPassword] = useState("");
  const [messageId, setMessageId] = useState(null);
  const [saltB64, setSaltB64] = useState(null);

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
    if (!secretKeyImage || !secretPassword) {
      setError("Please provide the secret key image and password.");
      return;
    }
    setError(null);
    setBusy(true);
    setDecryptedResult(null);
    setDecryptedMatch(null);
    setDecryptStatusMessage("");
    const form = new FormData();
    form.append("cover_image", coverFile);
    form.append("secret_key_image", secretKeyImage);
    form.append("secret_password", secretPassword);
    try {
      const res = await api.post("/encrypt", form);
      setCiphertextB64(res.data.ciphertext_b64);
      setCiphertextShape(res.data.ciphertext_shape);
      setCiphertext(res.data.image);
      setCoverEnergy(res.data.cover_energy);
      setCipherEnergy(res.data.energy);
      setMessageId(res.data.message_id);
      setSaltB64(res.data.salt_b64);
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
    if (!receiverSecretKeyImage) {
      setError("Please upload the receiver secret key image before decrypting.");
      return;
    }
    if (!receiverPassword || !saltB64 || !messageId) {
      setError("Please provide the receiver password and encrypt an image first.");
      return;
    }
    setError(null);
    setBusy(true);
    setDecryptedResult(null);
    setDecryptedMatch(null);
    setDecryptStatusMessage("");

    const payload = new FormData();
    payload.append("secret_key_image", receiverSecretKeyImage);
    payload.append("secret_password", receiverPassword);
    payload.append("message_id", messageId || "");
    payload.append("salt_b64", saltB64);

    try {
      const res = await api.post("/decrypt-with-key-images", payload);
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

  const clearDecryptInputs = () => {
    setReceiverSecretKeyImage(null);
    setReceiverPassword("");
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

          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151" }}>
              Secret Key Image
            </label>
            <input type="file" accept="image/*" onChange={(e) => setSecretKeyImage(e.target.files[0] || null)} />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151" }}>
              Secret Password
            </label>
            <input
              type="password"
              value={secretPassword}
              onChange={(e) => setSecretPassword(e.target.value)}
              placeholder="Optional until KDF is implemented"
              style={{ width: "100%", padding: "6px 10px", boxSizing: "border-box" }}
            />
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

          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151" }}>
              Receiver Secret Key Image
            </label>
            <input type="file" accept="image/*" onChange={(e) => setReceiverSecretKeyImage(e.target.files[0] || null)} />
          </div>

          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#374151" }}>
              Receiver Secret Password
            </label>
            <input
              type="password"
              value={receiverPassword}
              onChange={(e) => setReceiverPassword(e.target.value)}
              placeholder="Must match sender password"
              style={{ width: "100%", padding: "6px 10px", boxSizing: "border-box" }}
            />
          </div>

          <button type="button" onClick={clearDecryptInputs}>
            Clear receiver inputs
          </button>

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
              The sender encrypts the RGB cover image using a secret key image and password. The backend derives independent spatial mask{" "}
              <code>P₁</code> and frequency mask <code>P₂</code> values for this message and frame.
            </li>
            <li>
              The receiver uploads the matching secret key image and enters the matching password. The message salt and frame metadata allow the same masks to be reproduced without transmitting the masks.
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
              If the image and password match, the phase rotations cancel out, producing the original RGB cover image. If either credential is wrong or modified, the output is unrecoverable phase noise.
            </li>
          </ol>
        </div>
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

