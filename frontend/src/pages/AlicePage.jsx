import { useState } from "react";
import api from "../api.js";

export default function AlicePage({ packet, onPacketReady, revealActive, setRevealActive }) {
  const [mode, setMode] = useState("image");
  const [coverImage, setCoverImage] = useState(null);
  const [baseImage, setBaseImage] = useState(null);
  const [keyFile, setKeyFile] = useState(null);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Ready to send.");
  const [busy, setBusy] = useState(false);
  const [secretText, setSecretText] = useState("");

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
        ciphertextB64: res.data.ciphertext_b64,
        ciphertextShape: res.data.ciphertext_shape,
        messageId: res.data.message_id,
        saltB64: res.data.salt_b64,
        image: res.data.image,
      };

      onPacketReady(payload);
      setStatus("Signal encrypted and ready for Bob to receive.");
    } catch (error) {
      console.error(error);
      setStatus(error.response?.data?.detail || error.message || "Encryption failed.");
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
      };

      onPacketReady(textPacket);
      setStatus("Secret text encrypted and ready for Bob to receive.");
    } catch (error) {
      console.error(error);
      setStatus(error.response?.data?.detail || error.message || "Text encryption failed.");
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
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: "#8ec5ff" }}>
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
              border: mode === "image" ? "1px solid #dfe6ee" : "1px solid rgba(255,255,255,0.16)",
              background: mode === "image" ? "rgba(223,230,238,0.18)" : "rgba(255,255,255,0.03)",
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
              border: mode === "text" ? "1px solid #dfe6ee" : "1px solid rgba(255,255,255,0.16)",
              background: mode === "text" ? "rgba(223,230,238,0.18)" : "rgba(255,255,255,0.03)",
              color: "#f4f8ff",
              padding: "9px 14px",
              borderRadius: 10,
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Send text
          </button>
        </div>

        <h2 style={{ margin: "12px 0 16px" }}>
          {mode === "image" ? "Send encrypted image" : "Send encrypted text"}
        </h2>

        <div style={{ marginTop: 22, display: "grid", gap: 14 }}>
          {mode === "text" ? (
            <div>
              <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Secret text</label>
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
              <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Original image to send</label>
              <input
                type="file"
                accept="image/*"
                onChange={(event) => setCoverImage(event.target.files[0] || null)}
                style={{ width: "100%", color: "#dfeaf8" }}
              />
            </div>
          )}

          {mode === "text" && (
            <div>
              <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Base image</label>
              <input
                type="file"
                accept="image/*"
                onChange={(event) => setBaseImage(event.target.files[0] || null)}
                style={{ width: "100%", color: "#dfeaf8" }}
              />
            </div>
          )}

          <div>
            <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Secret key image</label>
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
          onClick={mode === "image" ? handleSend : handleSendText}
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
            boxShadow: "0 0 18px rgba(188, 196, 209, 0.55), inset 0 1px 0 rgba(255,255,255,0.75)",
            transition: "filter 0.2s ease",
          }}
        >
          {busy ? "Encrypting..." : mode === "image" ? "Send encrypted packet" : "Send encrypted text"}
        </button>

        <div style={{ marginTop: 18, color: "#cfe3ff", minHeight: 22 }}>{status}</div>
      </div>

      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.02)",
          borderRadius: 20,
          padding: 20,
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: "#9fe7ad" }}>
          Packet preview
        </div>

        <div
          style={{
            marginTop: 18,
            minHeight: 260,
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
          {packet?.image ? (
            <img
              src={`data:image/png;base64,${packet.image}`}
              alt="Encrypted packet preview"
              style={{ maxWidth: "100%", maxHeight: 260, borderRadius: 10 }}
            />
          ) : (
            <div style={{ color: "#859ab1", fontSize: 14 }}>No packet ready yet.</div>
          )}
        </div>

        <div style={{ marginTop: 18, color: "#dceaf7", lineHeight: 1.6 }}>
          <div><strong>Message ID:</strong> {packet?.messageId || "—"}</div>
          <div><strong>Original image:</strong> {coverImage ? "ready" : "waiting"}</div>
          <div><strong>Key material:</strong> {keyFile ? "ready" : "waiting"}</div>
          <div><strong>Reveal state:</strong> {revealActive ? "active" : "clear"}</div>
        </div>
      </div>
    </div>
  );
}
