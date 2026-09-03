import { useEffect, useState } from "react";
import api from "../api.js";

export default function BobPage({ packet, onSuccessfulDecrypt, revealActive, setRevealActive }) {
  const [keyFile, setKeyFile] = useState(null);
  const [password, setPassword] = useState("phase1-demo");
  const [status, setStatus] = useState("Waiting for Alice packet.");
  const [busy, setBusy] = useState(false);
  const [decryptedImage, setDecryptedImage] = useState(null);
  const [packageSeen, setPackageSeen] = useState(false);
  const [imageVisible, setImageVisible] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);
  const [frameIndex, setFrameIndex] = useState(0);

  const isTextPacket = packet?.messageType === "text";
  const framePreviews = packet?.previews || packet?.frames || [];
  const currentFrame = framePreviews[frameIndex];
  const currentFrameImage = currentFrame?.image || currentFrame?.preview;

  const handlePackageSeen = () => {
    setPackageSeen(true);
    setImageVisible(true);
  };

  useEffect(() => {
    setPackageSeen(false);
    setImageVisible(false);
    setLightboxImage(null);
    setFrameIndex(0);
    setDecryptedImage(null);
  }, [packet?.messageId]);

  const previousFrame = () => {
    setFrameIndex((index) => Math.max(0, index - 1));
  };

  const nextFrame = () => {
    setFrameIndex((index) => Math.min(framePreviews.length - 1, index + 1));
  };

  const handleDecrypt = async () => {
    if (!packet) {
      setStatus("Alice has not sent a packet yet.");
      return;
    }

    if (!keyFile) {
      setStatus("Upload Bob's secret key image before decrypting.");
      return;
    }

    if (!password.trim()) {
      setStatus("Enter the password before decrypting.");
      return;
    }

    setBusy(true);
    setRevealActive(true);
    setStatus("Decrypting signal...");

    try {
      const form = new FormData();
      form.append("secret_key_image", keyFile);
      form.append("secret_password", password);
      form.append("message_id", packet.messageId || "");
      form.append("salt_b64", packet.saltB64 || "");
      form.append("frame_index", "0");

      const res = await api.post("/decrypt-with-key-images", form);
      setDecryptedImage(res.data.image);

      if (res.data.match_with_cover) {
        setStatus("Successful decryption. The reveal fades away.");
        setRevealActive(false);
        onSuccessfulDecrypt();
      } else {
        setStatus("Decryption did not match the original cover. The reveal remains active.");
        setRevealActive(true);
      }
    } catch (error) {
      console.error(error);
      setStatus(error.response?.data?.detail || error.message || "Decryption failed.");
      setRevealActive(true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 1100,
        margin: "0 auto",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 24,
      }}
    >
      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.02)",
          borderRadius: 20,
          padding: 20,
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: "#a0ebba" }}>
          Bob receiver
        </div>

        <h2 style={{ margin: "12px 0 18px" }}>Decrypt packet</h2>

        <div style={{ display: "grid", gap: 14 }}>
          <div>
            <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Receiver key image</label>
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setKeyFile(event.target.files[0] || null)}
              style={{ width: "100%", color: "#dfeaf8" }}
            />
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              style={{
                width: "100%",
                boxSizing: "border-box",
                borderRadius: 10,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(0,0,0,0.35)",
                color: "#f6fbff",
                padding: "12px 14px",
              }}
            />
          </div>
        </div>

        <button
          onClick={handleDecrypt}
          disabled={busy}
          style={{
            marginTop: 22,
            width: "100%",
            border: "1px solid rgba(255,255,255,0.18)",
            background: busy
              ? "linear-gradient(135deg, #dfe5ec 0%, #a6b0bb 100%)"
              : "linear-gradient(135deg, #f0f3f7 0%, #a7afb9 30%, #dfe6ee 100%)",
            color: "#1b2430",
            padding: "14px 18px",
            borderRadius: 12,
            cursor: busy ? "not-allowed" : "pointer",
            fontWeight: 700,
            fontSize: 15,
            boxShadow: "0 0 17px rgba(186, 195, 208, 0.55), inset 0 1px 0 rgba(255,255,255,0.7)",
            transition: "filter 0.2s ease",
          }}
        >
          {busy ? "Decrypting..." : "Decrypt packet"}
        </button>

        <div style={{ marginTop: 18, color: "#dff9ea", minHeight: 22 }}>{status}</div>
      </div>

      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.02)",
          borderRadius: 20,
          padding: 20,
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: "#8ec5ff" }}>
          Recovered output
        </div>

        <div
          style={{
            marginTop: 18,
            minHeight: 300,
            background: "rgba(0,0,0,0.38)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {decryptedImage ? (
            <img
              src={`data:image/png;base64,${decryptedImage}`}
              alt="Decrypted image"
              onClick={() => setLightboxImage(`data:image/png;base64,${decryptedImage}`)}
              style={{ width: "min(100%, 500px)", maxHeight: 420, objectFit: "contain", borderRadius: 10, cursor: "zoom-in" }}
            />
          ) : !packet ? (
            <div style={{ color: "#859ab1", fontSize: 14 }}>Waiting for Alice's package.</div>
          ) : !packageSeen ? (
            <div style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}>
              <strong style={{ display: "block", marginBottom: 10 }}>Got a new package!</strong>
              <button
                type="button"
                onClick={handlePackageSeen}
                style={{
                  border: "1px solid rgba(255,255,255,0.2)",
                  background: "linear-gradient(135deg, #edf1f5, #9da8b5, #e7ecf2)",
                  color: "#1b2430",
                  padding: "9px 14px",
                  borderRadius: 9,
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                {isTextPacket ? "View frames" : "View image"}
              </button>
            </div>
          ) : isTextPacket ? (
            framePreviews.length > 0 && imageVisible && currentFrameImage ? (
              <img
                src={`data:image/png;base64,${currentFrameImage}`}
                alt={`Encrypted frame ${frameIndex + 1}`}
                onClick={() => setLightboxImage(`data:image/png;base64,${currentFrameImage}`)}
                style={{ width: "min(100%, 500px)", maxHeight: 420, objectFit: "contain", borderRadius: 10, cursor: "zoom-in", imageRendering: "auto" }}
              />
            ) : (
              <div style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}>
                {framePreviews.length > 0 ? "Click View frames to inspect the encrypted sequence." : "Encrypted frames are ready for Bob."}
              </div>
            )
          ) : imageVisible && packet.image ? (
            <img
              src={`data:image/png;base64,${packet.image}`}
              alt="Encrypted package"
              onClick={() => setLightboxImage(`data:image/png;base64,${packet.image}`)}
              style={{ width: "min(100%, 500px)", maxHeight: 420, objectFit: "contain", borderRadius: 10, cursor: "zoom-in" }}
            />
          ) : (
            <div style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}>
              Encrypted package is visible above.
            </div>
          )}
        </div>

        {isTextPacket && framePreviews.length > 0 && imageVisible && (
          <div
            style={{
              marginTop: 16,
              padding: "14px 16px",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12,
              background: "rgba(255,255,255,0.035)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 10 }}>
              <span style={{ color: "#aebbd0", fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase" }}>
                Frame navigator
              </span>
              <output style={{ color: "#f4f8ff", fontVariantNumeric: "tabular-nums", fontSize: 14 }}>
                {String(frameIndex + 1).padStart(2, "0")} <span style={{ color: "#748198" }}>/ {String(framePreviews.length).padStart(2, "0")}</span>
              </output>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button type="button" onClick={previousFrame} disabled={frameIndex === 0} aria-label="Previous frame" style={frameButtonStyle}>
              &#8592;
            </button>
            <input
              type="range"
              min="0"
              max={framePreviews.length - 1}
              value={frameIndex}
              onChange={(event) => setFrameIndex(Number(event.target.value))}
              aria-label="Encrypted frame index"
              style={{ flex: 1, accentColor: "#e7edf5", cursor: "pointer" }}
            />
            <button type="button" onClick={nextFrame} disabled={frameIndex === framePreviews.length - 1} aria-label="Next frame" style={frameButtonStyle}>
              &#8594;
            </button>
            </div>
            <input
              type="number"
              min="1"
              max={framePreviews.length}
              value={frameIndex + 1}
              onChange={(event) => {
                const requestedFrame = Number(event.target.value);
                if (Number.isInteger(requestedFrame)) {
                  setFrameIndex(Math.min(framePreviews.length - 1, Math.max(0, requestedFrame - 1)));
                }
              }}
              aria-label="Selected frame number"
              style={{
                width: 72,
                marginTop: 10,
                boxSizing: "border-box",
                border: "1px solid rgba(255,255,255,0.14)",
                borderRadius: 8,
                background: "rgba(0,0,0,0.32)",
                color: "#f4f8ff",
                padding: "7px 8px",
                textAlign: "center",
              }}
            />
          </div>
        )}

        <div style={{ marginTop: 18, color: "#dceaf7", lineHeight: 1.6 }}>
          <div><strong>Packet received:</strong> {packet ? "yes" : "no"}</div>
          <div><strong>Message ID:</strong> {packet?.messageId || "—"}</div>
          <div><strong>Reveal active:</strong> {revealActive ? "yes" : "no"}</div>
        </div>
      </div>

      {lightboxImage && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Expanded package image"
          onClick={() => setLightboxImage(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            background: "rgba(0,0,0,0.86)",
            cursor: "zoom-out",
          }}
        >
          <img
            src={lightboxImage}
            alt="Expanded encrypted package"
            style={{ maxWidth: "min(92vw, 1100px)", maxHeight: "90vh", objectFit: "contain", borderRadius: 12 }}
          />
        </div>
      )}
    </div>
  );
}

const frameButtonStyle = {
  width: 36,
  height: 36,
  border: "1px solid rgba(255,255,255,0.18)",
  borderRadius: 9,
  background: "rgba(255,255,255,0.08)",
  color: "#f4f8ff",
  cursor: "pointer",
};
