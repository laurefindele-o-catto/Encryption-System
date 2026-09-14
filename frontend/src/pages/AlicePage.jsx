import { useState } from "react";
import api from "../api.js";

export default function AlicePage({
  packet,
  onPacketReady,
  revealActive,
  setRevealActive,
}) {
  const [mode, setMode] = useState("image");
  const [coverImage, setCoverImage] = useState(null);
  const [baseImage, setBaseImage] = useState(null);
  const [keyFile, setKeyFile] = useState(null);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Ready to send.");
  const [busy, setBusy] = useState(false);
  const [secretText, setSecretText] = useState("");
  const [frameIndex, setFrameIndex] = useState(0);
  const [lightboxImage, setLightboxImage] = useState(null);

  const isTextPacket =
    packet?.messageType === "text" ||
    packet?.messageType === "basic_energy_morse";
  const framePreviews = packet?.previews || [];
  const currentFrame = isTextPacket ? framePreviews[frameIndex] : null;
  const previewImage = isTextPacket
    ? currentFrame?.image || packet?.image || null
    : packet?.image;

  const handleSend = async () => {
    if (!coverImage) {
      setStatus("Upload the original cover image before sending.");
      return;
    }

    if (!keyFile) {
      setStatus("Upload the sender key image before sending.");
      return;
    }

    if (!password.trim()) {
      setStatus("Enter the password before sending.");
      return;
    }

    setBusy(true);
    setStatus("Encrypting signal...");
    setRevealActive(true);

    try {
      const form = new FormData();
      form.append("cover_image", coverImage);
      form.append("secret_key_image", keyFile);
      form.append("secret_password", password);
      form.append("message_id", `alice-${Date.now()}`);
      form.append("frame_index", "0");

      const res = await api.post("/encrypt", form);

      const payload = {
        messageType: "image",
        messageId: res.data.message_id,
        image: res.data.image,
      };

      onPacketReady(payload);
      setStatus("Signal encrypted and ready for Bob to receive.");
    } catch (error) {
      console.error(error);
      setStatus(
        error.response?.data?.detail || error.message || "Encryption failed."
      );
      setRevealActive(false);
    } finally {
      setBusy(false);
    }
  };

  const handleSendText = async () => {
    if (!secretText.trim()) {
      setStatus("Enter the secret text before sending.");
      return;
    }

    if (!baseImage) {
      setStatus("Upload a base image before sending text.");
      return;
    }

    if (!keyFile) {
      setStatus("Upload the sender key image before sending.");
      return;
    }

    if (!password.trim()) {
      setStatus("Enter the password before sending.");
      return;
    }

    setBusy(true);
    setStatus("Converting text and encrypting frames...");
    setRevealActive(true);

    try {
      const form = new FormData();
      form.append("secret_text", secretText);
      form.append("base_image", baseImage);
      form.append("secret_key_image", keyFile);
      form.append("secret_password", password);

      const res = await api.post("/text/encrypt", form);
      const textPacket = {
        messageType: "text",
        messageId: res.data.message_id,
        saltB64: res.data.salt_b64,
        frameCount: res.data.frame_count,
        morse: res.data.morse,
        symbols: res.data.symbols,
        baseImageShape: res.data.base_image_shape,
        previews: res.data.previews || [],
        image: res.data.previews?.[0]?.image || null,
      };

      setFrameIndex(0);
      onPacketReady(textPacket);
      setStatus("Secret text encrypted and ready for Bob to receive.");
    } catch (error) {
      console.error(error);
      setStatus(
        error.response?.data?.detail ||
          error.message ||
          "Text encryption failed."
      );
      setRevealActive(false);
    } finally {
      setBusy(false);
    }
  };

  const handleSendBasicEnergy = async () => {
    if (!secretText.trim()) {
      setStatus("Enter the secret text before sending.");
      return;
    }

    if (!baseImage) {
      setStatus("Upload a base image before sending Morse.");
      return;
    }

    if (!keyFile) {
      setStatus("Upload the sender key image before sending.");
      return;
    }

    if (!password.trim()) {
      setStatus("Enter the password before sending.");
      return;
    }

    setBusy(true);
    setStatus("Converting text and encrypting Basic Morse frames...");
    setRevealActive(true);

    try {
      const form = new FormData();
      form.append("secret_text", secretText);
      form.append("base_image", baseImage);
      form.append("secret_key_image", keyFile);
      form.append("secret_password", password);

      const res = await api.post("/text/basic-energy/encrypt", form);
      const energyPacket = {
        messageType: "basic_energy_morse",
        messageId: res.data.message_id,
        saltB64: res.data.salt_b64,
        frameCount: res.data.frame_count,
        morse: res.data.morse,
        symbols: res.data.symbols,
        thresholds: res.data.thresholds || [],
        energyLevels: res.data.energy_levels || [],
        baseImageShape: res.data.base_image_shape,
        previews: res.data.previews || [],
        image: res.data.previews?.[0]?.image || null,
      };

      setFrameIndex(0);
      onPacketReady(energyPacket);
      setStatus("Basic Morse encrypted and ready for transmission.");
    } catch (error) {
      console.error(error);
      setStatus(
        error.response?.data?.detail ||
          error.message ||
          "Basic Morse encryption failed."
      );
      setRevealActive(false);
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
        gridTemplateColumns: "1.2fr 1fr",
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
        <div
          style={{
            fontSize: 12,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: "#8ec5ff",
          }}
        >
          Alice terminal
        </div>

        <div
          role="tablist"
          aria-label="Alice transmission type"
          style={{ display: "flex", gap: 8, marginTop: 18, marginBottom: 20 }}
        >
          <button
            type="button"
            role="tab"
            aria-selected={mode === "image"}
            onClick={() => setMode("image")}
            style={{
              border:
                mode === "image"
                  ? "1px solid #dfe6ee"
                  : "1px solid rgba(255,255,255,0.16)",
              background:
                mode === "image"
                  ? "rgba(223,230,238,0.18)"
                  : "rgba(255,255,255,0.03)",
              color: "#f4f8ff",
              padding: "9px 14px",
              borderRadius: 10,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Send image
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "text"}
            onClick={() => setMode("text")}
            style={{
              border:
                mode === "text"
                  ? "1px solid #dfe6ee"
                  : "1px solid rgba(255,255,255,0.16)",
              background:
                mode === "text"
                  ? "rgba(223,230,238,0.18)"
                  : "rgba(255,255,255,0.03)",
              color: "#f4f8ff",
              padding: "9px 14px",
              borderRadius: 10,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Send text
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "basic-energy"}
            onClick={() => setMode("basic-energy")}
            style={{
              border:
                mode === "basic-energy"
                  ? "1px solid #ffd166"
                  : "1px solid rgba(255,255,255,0.16)",
              background:
                mode === "basic-energy"
                  ? "rgba(255,209,102,0.18)"
                  : "rgba(255,255,255,0.03)",
              color: mode === "basic-energy" ? "#ffd166" : "#f4f8ff",
              padding: "9px 14px",
              borderRadius: 10,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Basic Morse
          </button>
        </div>

        <h2 style={{ margin: "12px 0 16px" }}>
          {mode === "image"
            ? "Send encrypted image"
            : mode === "text"
            ? "Send encrypted text"
            : "Send basic Morse"}
        </h2>

        <div style={{ marginTop: 22, display: "grid", gap: 14 }}>
          {mode === "text" || mode === "basic-energy" ? (
            <div>
              <label
                style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
              >
                Secret text
              </label>
              <textarea
                value={secretText}
                onChange={(event) => setSecretText(event.target.value)}
                placeholder="Enter the message to transmit"
                rows={5}
                style={{
                  width: "100%",
                  boxSizing: "border-box",
                  resize: "vertical",
                  borderRadius: 10,
                  border: "1px solid rgba(255,255,255,0.1)",
                  background: "rgba(0,0,0,0.35)",
                  color: "#f6fbff",
                  padding: "12px 14px",
                  font: "inherit",
                }}
              />
            </div>
          ) : (
            <div>
              <label
                style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
              >
                Original image to send
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(event) =>
                  setCoverImage(event.target.files[0] || null)
                }
                style={{ width: "100%", color: "#dfeaf8" }}
              />
            </div>
          )}

          {(mode === "text" || mode === "basic-energy") && (
            <div>
              <label
                style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
              >
                Base image
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(event) =>
                  setBaseImage(event.target.files[0] || null)
                }
                style={{ width: "100%", color: "#dfeaf8" }}
              />
            </div>
          )}

          <div>
            <label
              style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
            >
              Secret key image
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setKeyFile(event.target.files[0] || null)}
              style={{ width: "100%", color: "#dfeaf8" }}
            />
          </div>

          <div>
            <label
              style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
            >
              Password
            </label>
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
          onClick={
            mode === "image"
              ? handleSend
              : mode === "text"
              ? handleSendText
              : handleSendBasicEnergy
          }
          disabled={busy}
          style={{
            marginTop: 22,
            width: "100%",
            border: "1px solid rgba(255,255,255,0.16)",
            background: busy
              ? "linear-gradient(135deg, #dfe5ec 0%, #a6b0bb 100%)"
              : "linear-gradient(135deg, #edf1f5 0%, #adb7c3 28%, #e8edf3 100%)",
            color: "#1b2430",
            padding: "14px 18px",
            borderRadius: 12,
            cursor: busy ? "not-allowed" : "pointer",
            fontWeight: 700,
            fontSize: 15,
            boxShadow:
              "0 0 18px rgba(188, 196, 209, 0.55), inset 0 1px 0 rgba(255,255,255,0.75)",
            transition: "filter 0.2s ease",
          }}
        >
          {busy
            ? "Encrypting..."
            : mode === "image"
            ? "Send encrypted packet"
            : mode === "text"
            ? "Send encrypted text"
            : "Send basic Morse"}
        </button>

        <div style={{ marginTop: 18, color: "#cfe3ff", minHeight: 22 }}>
          {status}
        </div>
      </div>

      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.02)",
          borderRadius: 20,
          padding: 20,
        }}
      >
        <div
          style={{
            fontSize: 12,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: "#9fe7ad",
          }}
        >
          Packet preview
        </div>

        <div
          style={{
            marginTop: 18,
            minHeight: 320,
            background: "rgba(0,0,0,0.38)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
            overflow: "hidden",
            padding: 8,
            boxSizing: "border-box",
          }}
        >
          {previewImage ? (
            <img
              src={`data:image/png;base64,${previewImage}`}
              alt="Encrypted packet preview"
              onClick={() =>
                setLightboxImage(`data:image/png;base64,${previewImage}`)
              }
              style={{
                width: "min(100%, 500px)",
                maxHeight: 420,
                objectFit: "contain",
                borderRadius: 10,
                cursor: "zoom-in",
                display: "block",
              }}
            />
          ) : (
            <div style={{ color: "#859ab1", fontSize: 14 }}>
              No packet ready yet.
            </div>
          )}
        </div>

        {isTextPacket && framePreviews.length > 1 && (
          <div
            style={{
              marginTop: 14,
              padding: "10px 14px",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 10,
              background: "rgba(255,255,255,0.03)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 10,
            }}
          >
            <span style={{ fontSize: 12, color: "#aebbd0" }}>
              Frame {frameIndex + 1} / {framePreviews.length}
            </span>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                type="button"
                onClick={() => setFrameIndex((i) => Math.max(0, i - 1))}
                disabled={frameIndex === 0}
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.18)",
                  background: "rgba(255,255,255,0.08)",
                  color: "#f4f8ff",
                  cursor: frameIndex === 0 ? "not-allowed" : "pointer",
                }}
              >
                &#8592;
              </button>
              <button
                type="button"
                onClick={() =>
                  setFrameIndex((i) =>
                    Math.min(framePreviews.length - 1, i + 1)
                  )
                }
                disabled={frameIndex === framePreviews.length - 1}
                style={{
                  padding: "4px 10px",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.18)",
                  background: "rgba(255,255,255,0.08)",
                  color: "#f4f8ff",
                  cursor:
                    frameIndex === framePreviews.length - 1
                      ? "not-allowed"
                      : "pointer",
                }}
              >
                &#8594;
              </button>
            </div>
          </div>
        )}

        <div style={{ marginTop: 18, color: "#dceaf7", lineHeight: 1.6 }}>
          <div>
            <strong>Message ID:</strong> {packet?.messageId || "—"}
          </div>
          <div>
            <strong>Original image:</strong>{" "}
            {(
              mode === "text" || mode === "basic-energy"
                ? baseImage
                : coverImage
            )
              ? "ready"
              : "waiting"}
          </div>
          <div>
            <strong>Key material:</strong> {keyFile ? "ready" : "waiting"}
          </div>
          {isTextPacket && packet && (
            <div>
              <strong>Frames:</strong>{" "}
              {packet.frameCount || framePreviews.length}
            </div>
          )}
          <div>
            <strong>Reveal state:</strong> {revealActive ? "active" : "clear"}
          </div>
        </div>
      </div>

      {lightboxImage && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Expanded packet preview"
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
            alt="Expanded packet preview"
            style={{
              maxWidth: "min(92vw, 1100px)",
              maxHeight: "90vh",
              objectFit: "contain",
              borderRadius: 12,
            }}
          />
        </div>
      )}
    </div>
  );
}
