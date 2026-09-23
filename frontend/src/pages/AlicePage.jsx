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
  const [showEncryptionStages, setShowEncryptionStages] = useState(false);
  const [encryptionStageIndex, setEncryptionStageIndex] = useState(0);
  const [showTextDiagnostics, setShowTextDiagnostics] = useState(false);
  const [privateMorse, setPrivateMorse] = useState("");
  const [privateSymbols, setPrivateSymbols] = useState([]);
  const [privateEnergyLevels, setPrivateEnergyLevels] = useState([]);

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
        stages: res.data.stages || [],
      };

      setEncryptionStageIndex(0);
      setShowEncryptionStages(false);
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
    const morse = textToMorseLocal(secretText);
    setPrivateMorse(morse);
    setPrivateSymbols(symbolsFromMorse(morse));

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
    const morse = textToMorseLocal(secretText);
    setPrivateMorse(morse);
    setPrivateSymbols(symbolsFromMorse(morse));

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
        thresholds: res.data.thresholds || [],
        energyLevels: res.data.energy_levels || [],
        baseImageShape: res.data.base_image_shape,
        previews: res.data.previews || [],
        image: res.data.previews?.[0]?.image || null,
      };

      setFrameIndex(0);
      setPrivateEnergyLevels(res.data.energy_levels || []);
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

        {mode === "image" && packet?.messageType === "image" && packet.stages?.length > 0 && (
          <button
            type="button"
            onClick={() => setShowEncryptionStages((visible) => !visible)}
            style={processToggleStyle}
          >
            {showEncryptionStages ? "Hide Under the hood" : "Under the hood"}
          </button>
        )}

        {showEncryptionStages && packet?.stages?.length > 0 && (
          <ProcessStageViewer
            stages={packet.stages}
            index={encryptionStageIndex}
            onChange={setEncryptionStageIndex}
          />
        )}

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

        {(mode === "text" || mode === "basic-energy") && privateMorse && (
          <>
            <button
              type="button"
              onClick={() => setShowTextDiagnostics((visible) => !visible)}
              style={processToggleStyle}
            >
              {showTextDiagnostics ? "Hide behind the scenes" : "Behind the scenes"}
            </button>
            {showTextDiagnostics && (
              <div style={processViewerStyle}>
                {(() => {
                  const stateIndex = privateSymbols[frameIndex] === "DOT" ? 0 : privateSymbols[frameIndex] === "DASH" ? 1 : privateSymbols[frameIndex] === "LETTER_GAP" ? 2 : 3;
                  const firstDifference = [16, 16, -16, -16][stateIndex];
                  const secondDifference = [16, -16, 16, -16][stateIndex];
                  return (
                    <>
                      <div style={processHeaderStyle}>
                        <span style={processKickerStyle}>Private sender diagnostics</span>
                        <span style={processCounterStyle}>{frameIndex + 1} / {privateSymbols.length}</span>
                      </div>
                      <div style={diagnosticLabelStyle}>Whole Morse sequence</div>
                      <MorseSequenceHighlight morse={privateMorse} activeIndex={frameIndex} />
                      <div style={{ marginTop: 12, color: "#f4f8ff", fontWeight: 700 }}>
                        Current state: {privateSymbols[frameIndex] || "pending"}
                      </div>
                      <div style={{ marginTop: 8, color: "#dceaf7", fontFamily: "monospace", fontSize: 12 }}>
                        {mode === "text"
                          ? `A-B energy difference: ${firstDifference > 0 ? "+" : ""}${firstDifference} | C-D energy difference: ${secondDifference > 0 ? "+" : ""}${secondDifference}`
                          : `Expected total Parseval energy: ${privateEnergyLevels[stateIndex]?.toFixed?.(2) || "pending"}`}
                      </div>
                      <div style={{ marginTop: 8, color: "#aebbd0", fontSize: 12 }}>
                        {mode === "text"
                          ? "Differential encoding applies equal and opposite changes to the block pairs, preserving the intended net energy balance."
                          : "Basic Morse changes the whole-image brightness level, producing a distinct Parseval energy level."}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </>
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

function MorseSequenceHighlight({ morse, activeIndex }) {
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: 2,
        marginTop: 4,
        padding: "9px 10px",
        borderRadius: 8,
        background: "rgba(0,0,0,0.28)",
        border: "1px solid rgba(255,255,255,0.08)",
        fontFamily: "monospace",
        fontSize: 17,
        lineHeight: 1.5,
        whiteSpace: "pre-wrap",
      }}
      aria-label={`Morse sequence, active symbol ${activeIndex + 1}`}
    >
      {[...morse].map((character, index) => (
        <span
          key={`${character}-${index}`}
          style={{
            minWidth: character === " " ? 11 : "auto",
            padding: character === " " ? "0 2px" : "1px 4px",
            borderRadius: 5,
            color: index === activeIndex ? "#111923" : "#f4f8ff",
            background: index === activeIndex
              ? "linear-gradient(135deg, #ffffff 0%, #eaf2ff 55%, #cbd9ed 100%)"
              : "transparent",
            boxShadow: index === activeIndex
              ? "0 0 8px rgba(255,255,255,0.95), 0 0 18px rgba(202,220,255,0.7)"
              : "none",
            transform: index === activeIndex ? "translateY(-1px)" : "none",
            transition: "all 0.2s ease",
          }}
        >
          {character === " " ? "·" : character}
        </span>
      ))}
    </div>
  );
}

const ITU_MORSE = {
  A: ".-", B: "-...", C: "-.-.", D: "-..", E: ".", F: "..-.", G: "--.", H: "....",
  I: "..", J: ".---", K: "-.-", L: ".-..", M: "--", N: "-.", O: "---", P: ".--.",
  Q: "--.-", R: ".-.", S: "...", T: "-", U: "..-", V: "...-", W: ".--", X: "-..-",
  Y: "-.--", Z: "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--",
  "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
  ".": ".-.-.-", ",": "--..--", "?": "..--..",
};

function textToMorseLocal(text) {
  return text.trim().toUpperCase().split(/\s+/).map((word) => (
    [...word].map((character) => ITU_MORSE[character] || "").filter(Boolean).join(" ")
  )).join("/");
}

function symbolsFromMorse(morse) {
  return [...morse].map((character) => ({ ".": "DOT", "-": "DASH", " ": "LETTER_GAP", "/": "WORD_GAP" }[character]));
}

const diagnosticLabelStyle = { color: "#8ec5ff", fontSize: 10, letterSpacing: 1, textTransform: "uppercase" };
const diagnosticValueStyle = { color: "#f4f8ff", fontFamily: "monospace", wordBreak: "break-all", marginTop: 4 };

function ProcessStageViewer({ stages, index, onChange }) {
  const stage = stages[index];
  if (!stage) return null;

  return (
    <div style={processViewerStyle}>
      <div style={processHeaderStyle}>
        <span style={processKickerStyle}>Encryption sequence</span>
        <span style={processCounterStyle}>{index + 1} / {stages.length}</span>
      </div>
      <div style={{ color: "#f4f8ff", fontWeight: 700, marginBottom: 10 }}>{formatStageName(stage.name)}</div>
      <img
        src={`data:image/png;base64,${stage.image}`}
        alt={formatStageName(stage.name)}
        style={{ width: "100%", maxHeight: 240, objectFit: "contain", borderRadius: 10, background: "rgba(0,0,0,0.35)" }}
      />
      <input
        type="range"
        min="0"
        max={stages.length - 1}
        value={index}
        onChange={(event) => onChange(Number(event.target.value))}
        aria-label="Encryption stage"
        style={{ width: "100%", marginTop: 12, accentColor: "#e7edf5" }}
      />
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, marginTop: 8 }}>
        <button type="button" onClick={() => onChange(Math.max(0, index - 1))} disabled={index === 0} style={processButtonStyle}>Previous</button>
        <button type="button" onClick={() => onChange(Math.min(stages.length - 1, index + 1))} disabled={index === stages.length - 1} style={processButtonStyle}>Next</button>
      </div>
    </div>
  );
}

function formatStageName(name) {
  return name.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

const processToggleStyle = {
  width: "100%",
  marginTop: 12,
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "#e7edf5",
  cursor: "pointer",
  fontWeight: 700,
};

const processViewerStyle = {
  marginTop: 12,
  padding: 14,
  borderRadius: 12,
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.035)",
};

const processHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: 10,
};

const processKickerStyle = {
  color: "#aebbd0",
  fontSize: 11,
  letterSpacing: 1.4,
  textTransform: "uppercase",
};

const processCounterStyle = {
  color: "#f4f8ff",
  fontSize: 13,
  fontVariantNumeric: "tabular-nums",
};

const processButtonStyle = {
  border: "1px solid rgba(255,255,255,0.16)",
  borderRadius: 8,
  background: "rgba(255,255,255,0.07)",
  color: "#f4f8ff",
  padding: "7px 12px",
  cursor: "pointer",
};

