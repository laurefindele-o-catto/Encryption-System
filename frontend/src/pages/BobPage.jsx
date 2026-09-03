import { useState } from "react";
import api from "../api.js";

export default function BobPage({ packet, onSuccessfulDecrypt, revealActive, setRevealActive }) {
  const [keyFile, setKeyFile] = useState(null);
  const [password, setPassword] = useState("phase1-demo");
  const [status, setStatus] = useState("Waiting for Alice packet.");
  const [busy, setBusy] = useState(false);
  const [decryptedImage, setDecryptedImage] = useState(null);

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
              style={{ maxWidth: "100%", maxHeight: 300, borderRadius: 10 }}
            />
          ) : (
            <div style={{ color: "#859ab1", fontSize: 14 }}>Decrypted image will appear here.</div>
          )}
        </div>

        <div style={{ marginTop: 18, color: "#dceaf7", lineHeight: 1.6 }}>
          <div><strong>Packet received:</strong> {packet ? "yes" : "no"}</div>
          <div><strong>Message ID:</strong> {packet?.messageId || "—"}</div>
          <div><strong>Reveal active:</strong> {revealActive ? "yes" : "no"}</div>
        </div>
      </div>
    </div>
  );
}
