import { useEffect, useState } from "react";
import api from "../api.js";

export default function BobPage({
  packet,
  onSuccessfulDecrypt,
  revealActive,
  setRevealActive,
}) {
  const [keyFile, setKeyFile] = useState(null);
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Waiting for Alice packet.");
  const [busy, setBusy] = useState(false);
  const [decryptedImage, setDecryptedImage] = useState(null);
  const [decryptedText, setDecryptedText] = useState(null);
  const [decryptedMorse, setDecryptedMorse] = useState(null);
  const [decryptedSuccess, setDecryptedSuccess] = useState(null);
  const [decryptionFrames, setDecryptionFrames] = useState([]);
  const [decryptionStages, setDecryptionStages] = useState([]);
  const [showDecryptionStages, setShowDecryptionStages] = useState(false);
  const [decryptionStageIndex, setDecryptionStageIndex] = useState(0);
  const [packageSeen, setPackageSeen] = useState(false);
  const [imageVisible, setImageVisible] = useState(false);
  const [lightboxImage, setLightboxImage] = useState(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [outputView, setOutputView] = useState("recovered");
  const [decryptionMethod, setDecryptionMethod] = useState(null);
  const [predictedEnergies, setPredictedEnergies] = useState(null);
  const [predictedFrames, setPredictedFrames] = useState([]);
  const [predictedThresholds, setPredictedThresholds] = useState([]);
  const [extractHovered, setExtractHovered] = useState(false);
  const [showFrameInspector, setShowFrameInspector] = useState(false);
  const [showEnergyInspector, setShowEnergyInspector] = useState(false);

  const isBasicEnergyPacket = packet?.messageType === "basic_energy_morse";
  const isTextPacket = packet?.messageType === "text" || isBasicEnergyPacket;
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
    setDecryptedText(null);
    setDecryptedMorse(null);
    setDecryptedSuccess(null);
    setDecryptionFrames([]);
    setDecryptionStages([]);
    setShowDecryptionStages(false);
    setDecryptionStageIndex(0);
    setDecryptionMethod(null);
    setPredictedEnergies(null);
    setPredictedFrames([]);
    setPredictedThresholds([]);
    setOutputView("recovered");
    setShowFrameInspector(false);
    setShowEnergyInspector(false);
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
      if (isBasicEnergyPacket) {
        const form = new FormData();
        form.append("secret_key_image", keyFile);
        form.append("secret_password", password);
        form.append("message_id", packet.messageId || "");

        const res = await api.post("/text/basic-energy/decrypt", form);
        setDecryptedText(res.data.text);
        setDecryptedMorse(res.data.morse);
        setDecryptedSuccess(res.data.success);
        setDecryptionFrames(res.data.frames || []);
        setDecryptionMethod("normal");
        setImageVisible(true);

        if (res.data.success) {
          setStatus(
            "Successful DRPE decryption! Secret message recovered. The reveal fades away."
          );
          setRevealActive(false);
          onSuccessfulDecrypt();
        } else {
          setStatus(
            "Decryption completed with unrecognized Morse patterns. Key or password mismatch."
          );
          setRevealActive(true);
        }
      } else if (isTextPacket) {
        const form = new FormData();
        form.append("secret_key_image", keyFile);
        form.append("secret_password", password);
        form.append("message_id", packet.messageId || "");

        const res = await api.post("/text/decrypt", form);
        setDecryptedText(res.data.text);
        setDecryptedMorse(res.data.morse);
        setDecryptedSuccess(res.data.success);
        setDecryptionFrames(res.data.frames || []);
        setDecryptionMethod("normal");
        setImageVisible(true);

        if (res.data.success) {
          setStatus(
            "Successful decryption! Secret message recovered. The reveal fades away."
          );
          setRevealActive(false);
          onSuccessfulDecrypt();
        } else {
          setStatus(
            "Decryption completed with unrecognized Morse patterns. Key or password mismatch."
          );
          setRevealActive(true);
        }
      } else {
        const form = new FormData();
        form.append("secret_key_image", keyFile);
        form.append("secret_password", password);
        form.append("message_id", packet.messageId || "");

        const res = await api.post("/decrypt-with-key-images", form);
        setDecryptedImage(res.data.image);
        setDecryptionStages(res.data.stages || []);
        setDecryptionStageIndex(0);
        setShowDecryptionStages(false);
        setDecryptionMethod("normal");
        setOutputView("recovered");
        setImageVisible(true);

        if (res.data.match_with_cover) {
          setStatus("Successful decryption. The reveal fades away.");
          setRevealActive(false);
          onSuccessfulDecrypt();
        } else {
          setStatus(
            "Decryption did not match the original cover. The reveal remains active."
          );
          setRevealActive(true);
        }
      }
    } catch (error) {
      console.error(error);
      setStatus(
        error.response?.data?.detail || error.message || "Decryption failed."
      );
      setRevealActive(true);
    } finally {
      setBusy(false);
    }
  };

  const handlePredictEnergy = async () => {
    if (!packet) {
      setStatus("Alice has not sent a packet yet.");
      return;
    }

    setBusy(true);
    setStatus("Extracting Morse sequence from ciphertext...");

    try {
      const form = new FormData();
      form.append("message_id", packet.messageId || "");

      const res = await api.post("/text/basic-energy/predict", form);
      const frames = res.data.frames || [];
      setDecryptedText(res.data.predicted_text);
      setDecryptedMorse(res.data.predicted_morse);
      setDecryptedSuccess(res.data.success);
      setDecryptionMethod("energy_prediction");
      setPredictedEnergies(res.data.frame_energies || []);
      setPredictedFrames(frames);
      setDecryptionFrames(frames);
      setPredictedThresholds(res.data.thresholds || []);
      setImageVisible(true);

      if (res.data.success) {
        setStatus("Success! Morse sequence extracted directly.");
        setRevealActive(false);
        onSuccessfulDecrypt();
      } else {
        setStatus("Extraction completed with unrecognized patterns.");
        setRevealActive(true);
      }
    } catch (error) {
      console.error(error);
      setStatus(
        error.response?.data?.detail || error.message || "Extraction failed."
      );
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
        <div
          style={{
            fontSize: 12,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: "#a0ebba",
          }}
        >
          Bob receiver
        </div>

        <h2 style={{ margin: "12px 0 18px" }}>Decrypt packet</h2>

        <div style={{ display: "grid", gap: 14 }}>
          <div>
            <label
              style={{ display: "block", marginBottom: 8, fontWeight: 600 }}
            >
              Receiver key image
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
            boxShadow:
              "0 0 17px rgba(186, 195, 208, 0.55), inset 0 1px 0 rgba(255,255,255,0.7)",
            transition: "filter 0.2s ease",
          }}
        >
          {busy
            ? "Decrypting..."
            : isTextPacket
            ? "Decrypt frames"
            : "Decrypt packet"}
        </button>

        {isBasicEnergyPacket && (
          <button
            type="button"
            onClick={handlePredictEnergy}
            onMouseEnter={() => setExtractHovered(true)}
            onMouseLeave={() => setExtractHovered(false)}
            disabled={busy}
            style={{
              marginTop: 12,
              width: "100%",
              boxSizing: "border-box",
              border:
                extractHovered && !busy
                  ? "1px solid rgba(251, 191, 36, 0.45)"
                  : "1px solid rgba(255, 255, 255, 0.12)",
              background:
                extractHovered && !busy
                  ? "linear-gradient(180deg, rgba(251, 191, 36, 0.12) 0%, rgba(251, 191, 36, 0.04) 100%)"
                  : "linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)",
              padding: "12px 16px",
              borderRadius: 12,
              cursor: busy ? "not-allowed" : "pointer",
              transition: "all 0.2s ease",
              boxShadow:
                extractHovered && !busy
                  ? "0 4px 14px rgba(0, 0, 0, 0.35), 0 0 12px rgba(251, 191, 36, 0.12)"
                  : "0 2px 6px rgba(0, 0, 0, 0.2)",
              transform: extractHovered && !busy ? "translateY(-1px)" : "none",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 4,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                color: extractHovered && !busy ? "#fef3c7" : "#f1f5f9",
                fontSize: 14,
                fontWeight: 600,
                letterSpacing: 0.2,
                transition: "color 0.2s ease",
              }}
            >
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke={extractHovered && !busy ? "#fbbf24" : "#cbd5e1"}
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ transition: "stroke 0.2s ease" }}
              >
                <path d="M2 12h3l3-7 4 14 3-7h3l2-4 2 4h2" />
              </svg>
              <span>Extract Morse from total energy</span>
            </div>
            <span
              style={{
                fontSize: 11,
                color:
                  extractHovered && !busy
                    ? "rgba(254, 243, 199, 0.75)"
                    : "rgba(148, 163, 184, 0.8)",
                fontWeight: 400,
                letterSpacing: 0.1,
                transition: "color 0.2s ease",
              }}
            >
              Direct extraction without receiver key
            </span>
          </button>
        )}

        <div style={{ marginTop: 18, color: "#dff9ea", minHeight: 22 }}>
          {status}
        </div>

        {!isTextPacket && decryptionStages.length > 0 && (
          <button
            type="button"
            onClick={() => setShowDecryptionStages((visible) => !visible)}
            style={processToggleStyle}
          >
            {showDecryptionStages
              ? "Hide Pulling back the curtain"
              : "Pulling back the curtain"}
          </button>
        )}

        {showDecryptionStages && decryptionStages.length > 0 && (
          <ProcessStageViewer
            stages={decryptionStages}
            index={decryptionStageIndex}
            onChange={setDecryptionStageIndex}
            kicker="Decryption sequence"
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
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
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
            {isTextPacket
              ? "Encrypted transmission"
              : !isTextPacket && decryptedImage
              ? "Recovered image"
              : "Received package"}
          </div>
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
          {!isTextPacket && decryptedImage ? (
            <img
              src={`data:image/png;base64,${decryptedImage}`}
              alt="Decrypted image"
              onClick={() =>
                setLightboxImage(`data:image/png;base64,${decryptedImage}`)
              }
              style={{
                width: "min(100%, 500px)",
                maxHeight: 420,
                objectFit: "contain",
                borderRadius: 10,
                cursor: "zoom-in",
              }}
            />
          ) : !packet ? (
            <div style={{ color: "#859ab1", fontSize: 14 }}>
              Waiting for Alice's package.
            </div>
          ) : !packageSeen ? (
            <div
              style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}
            >
              <strong style={{ display: "block", marginBottom: 10 }}>
                Got a new package!
              </strong>
              <button
                type="button"
                onClick={handlePackageSeen}
                style={{
                  border: "1px solid rgba(255,255,255,0.2)",
                  background:
                    "linear-gradient(135deg, #edf1f5, #9da8b5, #e7ecf2)",
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
                onClick={() =>
                  setLightboxImage(`data:image/png;base64,${currentFrameImage}`)
                }
                style={{
                  width: "min(100%, 500px)",
                  maxHeight: 420,
                  objectFit: "contain",
                  borderRadius: 10,
                  cursor: "zoom-in",
                  imageRendering: "auto",
                }}
              />
            ) : (
              <div
                style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}
              >
                {framePreviews.length > 0
                  ? "Click View frames to inspect the encrypted sequence."
                  : "Encrypted frames are ready for Bob."}
              </div>
            )
          ) : imageVisible && packet.image ? (
            <img
              src={`data:image/png;base64,${packet.image}`}
              alt="Encrypted package"
              onClick={() =>
                setLightboxImage(`data:image/png;base64,${packet.image}`)
              }
              style={{
                width: "min(100%, 500px)",
                maxHeight: 420,
                objectFit: "contain",
                borderRadius: 10,
                cursor: "zoom-in",
              }}
            />
          ) : (
            <div
              style={{ color: "#dceaf7", textAlign: "center", fontSize: 14 }}
            >
              Encrypted package is visible above.
            </div>
          )}
        </div>

        {isTextPacket && decryptedText !== null && (
          <div
            style={{
              marginTop: 18,
              padding: 20,
              background: "rgba(160, 235, 186, 0.05)",
              border: "1px solid rgba(160, 235, 186, 0.35)",
              borderRadius: 14,
              boxShadow: "0 0 24px rgba(160, 235, 186, 0.08)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 12,
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  letterSpacing: 1.5,
                  textTransform: "uppercase",
                  color: "#a0ebba",
                  fontWeight: 700,
                }}
              >
                Decrypted Plaintext
              </div>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: "4px 10px",
                  borderRadius: 999,
                  background:
                    decryptionMethod === "energy_prediction"
                      ? "rgba(255, 209, 102, 0.2)"
                      : decryptedSuccess
                      ? "rgba(160, 235, 186, 0.2)"
                      : "rgba(255, 107, 107, 0.2)",
                  color:
                    decryptionMethod === "energy_prediction"
                      ? "#ffd166"
                      : decryptedSuccess
                      ? "#a0ebba"
                      : "#ff8585",
                  border:
                    decryptionMethod === "energy_prediction"
                      ? "1px solid rgba(255, 209, 102, 0.5)"
                      : decryptedSuccess
                      ? "1px solid rgba(160, 235, 186, 0.4)"
                      : "1px solid rgba(255, 107, 107, 0.4)",
                }}
              >
                {decryptionMethod === "energy_prediction"
                  ? "DIRECT EXTRACTION (NO KEY)"
                  : decryptedSuccess
                  ? "VALID ITU MORSE"
                  : "CORRUPTED / UNRECOGNIZED"}
              </span>
            </div>

            <div
              style={{
                fontSize: "1.45rem",
                fontWeight: 700,
                color: "#f6fbff",
                wordBreak: "break-word",
                lineHeight: 1.4,
                padding: "12px 16px",
                background: "rgba(0, 0, 0, 0.45)",
                borderRadius: 10,
                border: "1px solid rgba(255, 255, 255, 0.12)",
                fontFamily: "monospace",
                letterSpacing: 1,
              }}
            >
              {decryptedText || "(empty message)"}
            </div>

            <div style={{ marginTop: 14 }}>
              <div
                style={{
                  fontSize: 11,
                  color: "#8ec5ff",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  marginBottom: 4,
                  fontWeight: 600,
                }}
              >
                Extracted Morse Sequence
              </div>
              <div
                style={{
                  fontSize: 13,
                  fontFamily: "monospace",
                  color: "#dceaf7",
                  background: "rgba(0, 0, 0, 0.3)",
                  padding: "8px 12px",
                  borderRadius: 8,
                  wordBreak: "break-all",
                  letterSpacing: 2,
                }}
              >
                {decryptedMorse || "—"}
              </div>
            </div>

            {decryptionFrames.length > 0 && (
              <button
                type="button"
                onClick={() => setShowFrameInspector(true)}
                style={{
                  ...inspectFrameButtonStyle,
                  marginTop: 14,
                  background:
                    decryptionMethod === "energy_prediction"
                      ? "rgba(255, 209, 102, 0.12)"
                      : "rgba(160, 235, 186, 0.12)",
                  border:
                    decryptionMethod === "energy_prediction"
                      ? "1px solid rgba(255, 209, 102, 0.35)"
                      : "1px solid rgba(160, 235, 186, 0.35)",
                  color:
                    decryptionMethod === "energy_prediction"
                      ? "#ffd166"
                      : "#a0ebba",
                }}
              >
                Inspect frame diagnostics ({decryptionFrames.length} frames)
              </button>
            )}
          </div>
        )}

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
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 12,
                marginBottom: 10,
              }}
            >
              <span
                style={{
                  color: "#aebbd0",
                  fontSize: 11,
                  letterSpacing: 1.5,
                  textTransform: "uppercase",
                }}
              >
                Frame navigator
              </span>
              <output
                style={{
                  color: "#f4f8ff",
                  fontVariantNumeric: "tabular-nums",
                  fontSize: 14,
                }}
              >
                {String(frameIndex + 1).padStart(2, "0")}{" "}
                <span style={{ color: "#748198" }}>
                  / {String(framePreviews.length).padStart(2, "0")}
                </span>
              </output>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                type="button"
                onClick={previousFrame}
                disabled={frameIndex === 0}
                aria-label="Previous frame"
                style={frameButtonStyle}
              >
                &#8592;
              </button>
              <input
                type="range"
                min="0"
                max={framePreviews.length - 1}
                value={frameIndex}
                onChange={(event) => {
                  setFrameIndex(Number(event.target.value));
                }}
                aria-label="Encrypted frame index"
                style={{ flex: 1, accentColor: "#e7edf5", cursor: "pointer" }}
              />
              <button
                type="button"
                onClick={nextFrame}
                disabled={frameIndex === framePreviews.length - 1}
                aria-label="Next frame"
                style={frameButtonStyle}
              >
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
                  setFrameIndex(
                    Math.min(
                      framePreviews.length - 1,
                      Math.max(0, requestedFrame - 1)
                    )
                  );
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
            {decryptionFrames.length > 0 && (
              <button
                type="button"
                onClick={() => setShowFrameInspector(true)}
                style={inspectFrameButtonStyle}
              >
                Inspect frame diagnostics
              </button>
            )}
          </div>
        )}

        <div style={{ marginTop: 18, color: "#dceaf7", lineHeight: 1.6 }}>
          <div>
            <strong>Packet received:</strong> {packet ? "yes" : "no"}
          </div>
          <div>
            <strong>Message ID:</strong> {packet?.messageId || "—"}
          </div>
          <div>
            <strong>Type:</strong>{" "}
            {packet?.messageType === "basic_energy_morse"
              ? "Basic Morse"
              : packet?.messageType || "image"}
          </div>
          <div>
            <strong>Reveal active:</strong> {revealActive ? "yes" : "no"}
          </div>
        </div>
      </div>

      {showFrameInspector && decryptionFrames.length > 0 && (
        <FrameInspector
          frame={decryptionFrames[frameIndex]}
          frameImage={currentFrameImage}
          frameIndex={frameIndex}
          frameCount={decryptionFrames.length}
          isBasicEnergyPacket={isBasicEnergyPacket}
          decryptionMethod={decryptionMethod}
          onPrevious={previousFrame}
          onNext={nextFrame}
          onSelectFrame={setFrameIndex}
          onClose={() => setShowFrameInspector(false)}
        />
      )}

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

function ProcessStageViewer({ stages, index, onChange, kicker }) {
  const stage = stages[index];
  if (!stage) return null;

  return (
    <div style={processViewerStyle}>
      <div style={processHeaderStyle}>
        <span style={processKickerStyle}>{kicker}</span>
        <span style={processCounterStyle}>
          {index + 1} / {stages.length}
        </span>
      </div>
      <div style={{ color: "#f4f8ff", fontWeight: 700, marginBottom: 10 }}>
        {formatStageName(stage.name)}
      </div>
      <img
        src={`data:image/png;base64,${stage.image}`}
        alt={formatStageName(stage.name)}
        style={{
          width: "100%",
          maxHeight: 240,
          objectFit: "contain",
          borderRadius: 10,
          background: "rgba(0,0,0,0.35)",
        }}
      />
      <input
        type="range"
        min="0"
        max={stages.length - 1}
        value={index}
        onChange={(event) => onChange(Number(event.target.value))}
        aria-label="Decryption stage"
        style={{ width: "100%", marginTop: 12, accentColor: "#e7edf5" }}
      />
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 8,
          marginTop: 8,
        }}
      >
        <button
          type="button"
          onClick={() => onChange(Math.max(0, index - 1))}
          disabled={index === 0}
          style={processButtonStyle}
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => onChange(Math.min(stages.length - 1, index + 1))}
          disabled={index === stages.length - 1}
          style={processButtonStyle}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function formatStageName(name) {
  return name
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatNumber(value) {
  return typeof value === "number" ? value.toFixed(2) : "-";
}

function FrameInspector({
  frame,
  frameImage,
  frameIndex,
  frameCount,
  isBasicEnergyPacket,
  decryptionMethod,
  onPrevious,
  onNext,
  onSelectFrame,
  onClose,
}) {
  const isEnergyPrediction = decryptionMethod === "energy_prediction";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Frame diagnostics"
      onClick={onClose}
      style={frameInspectorOverlayStyle}
    >
      <div
        onClick={(event) => event.stopPropagation()}
        style={frameInspectorBoxStyle}
      >
        <div style={processHeaderStyle}>
          <div>
            <div style={processKickerStyle}>
              {isEnergyPrediction
                ? "Energy side-channel diagnostics"
                : "Frame diagnostics"}
            </div>
            <div style={{ color: "#f4f8ff", fontWeight: 700, marginTop: 4 }}>
              Frame {frameIndex + 1} / {frameCount}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close frame diagnostics"
            style={closeInspectorButtonStyle}
          >
            &times;
          </button>
        </div>

        {frameImage && (
          <img
            src={`data:image/png;base64,${frameImage}`}
            alt={`Encrypted frame ${frameIndex + 1}`}
            style={frameInspectorImageStyle}
          />
        )}

        <div
          style={{
            marginTop: 14,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
          }}
        >
          <button
            type="button"
            onClick={onPrevious}
            disabled={frameIndex === 0}
            style={frameButtonStyle}
          >
            &#8592;
          </button>
          <input
            type="range"
            min="0"
            max={frameCount - 1}
            value={frameIndex}
            onChange={(event) => {
              const next = Number(event.target.value);
              if (onSelectFrame) {
                onSelectFrame(next);
              } else {
                if (next < frameIndex) onPrevious();
                if (next > frameIndex) onNext();
              }
            }}
            aria-label="Frame diagnostics index"
            style={{ flex: 1, accentColor: "#f4f8ff" }}
          />
          <button
            type="button"
            onClick={onNext}
            disabled={frameIndex === frameCount - 1}
            style={frameButtonStyle}
          >
            &#8594;
          </button>
        </div>

        <div style={diagnosticsPanelStyle}>
          <div style={diagnosticLabelStyle}>
            {isEnergyPrediction
              ? "Predicted Morse symbol (via Total Energy)"
              : "Recovered Morse symbol"}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginTop: 4,
            }}
          >
            <span
              style={{
                color: "#ffffff",
                fontSize: 20,
                fontFamily: "monospace",
                fontWeight: 700,
              }}
            >
              {frame?.symbol_name || "-"}
            </span>
            {(frame?.symbol != null || frame?.predicted_symbol != null) && (
              <span
                style={{
                  fontSize: 11,
                  fontFamily: "monospace",
                  color: isEnergyPrediction ? "#ffd166" : "#8ec5ff",
                  padding: "2px 8px",
                  borderRadius: 6,
                  background: isEnergyPrediction
                    ? "rgba(255, 209, 102, 0.15)"
                    : "rgba(142, 197, 255, 0.15)",
                  border: isEnergyPrediction
                    ? "1px solid rgba(255, 209, 102, 0.35)"
                    : "1px solid rgba(142, 197, 255, 0.3)",
                }}
              >
                State {frame?.symbol ?? frame?.predicted_symbol}
              </span>
            )}
          </div>
          <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
            {isBasicEnergyPacket ? (
              isEnergyPrediction ? (
                <>
                  <div style={diagnosticRowStyle}>
                    <span>Total Parseval energy</span>
                    <strong>
                      {formatNumber(frame?.total_energy ?? frame?.energy)}
                    </strong>
                  </div>
                  {frame?.expected_energy != null && (
                    <div style={diagnosticRowStyle}>
                      <span>Expected level energy</span>
                      <strong>{formatNumber(frame?.expected_energy)}</strong>
                    </div>
                  )}
                  {frame?.energy_deviation != null && (
                    <div style={diagnosticRowStyle}>
                      <span>Energy deviation</span>
                      <strong>{formatNumber(frame?.energy_deviation)}</strong>
                    </div>
                  )}
                  {frame?.decision_threshold && (
                    <div style={diagnosticRowStyle}>
                      <span>Threshold interval</span>
                      <strong>{frame.decision_threshold}</strong>
                    </div>
                  )}
                  <div style={diagnosticRowStyle}>
                    <span>Extraction mode</span>
                    <strong style={{ color: "#ffd166" }}>
                      Zero Decryption (Parseval)
                    </strong>
                  </div>
                </>
              ) : (
                <>
                  <div style={diagnosticRowStyle}>
                    <span>Mean brightness</span>
                    <strong>{formatNumber(frame?.mean_brightness)}</strong>
                  </div>
                  <div style={diagnosticRowStyle}>
                    <span>Brightness delta</span>
                    <strong>{formatNumber(frame?.brightness_delta)}</strong>
                  </div>
                  <div style={diagnosticRowStyle}>
                    <span>Total energy</span>
                    <strong>{formatNumber(frame?.total_energy)}</strong>
                  </div>
                </>
              )
            ) : (
              <>
                <div style={diagnosticRowStyle}>
                  <span>A-B difference</span>
                  <strong>{formatNumber(frame?.block_a_minus_b)}</strong>
                </div>
                <div style={diagnosticRowStyle}>
                  <span>C-D difference</span>
                  <strong>{formatNumber(frame?.block_c_minus_d)}</strong>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
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

const diagnosticsPanelStyle = {
  marginTop: 16,
  padding: 14,
  borderRadius: 12,
  border: "1px solid rgba(142, 197, 255, 0.18)",
  background: "rgba(142, 197, 255, 0.045)",
};

const inspectFrameButtonStyle = {
  width: "100%",
  marginTop: 10,
  padding: "9px 12px",
  borderRadius: 9,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.06)",
  color: "#e7edf5",
  cursor: "pointer",
  fontWeight: 700,
};

const frameInspectorOverlayStyle = {
  position: "fixed",
  inset: 0,
  zIndex: 20,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 20,
  background: "rgba(0,0,0,0.72)",
};

const frameInspectorBoxStyle = {
  width: "min(560px, 94vw)",
  maxHeight: "90vh",
  overflowY: "auto",
  padding: 20,
  borderRadius: 16,
  border: "1px solid rgba(255,255,255,0.18)",
  background:
    "linear-gradient(145deg, rgba(25,32,44,0.98), rgba(9,13,20,0.98))",
  boxShadow: "0 24px 80px rgba(0,0,0,0.6), 0 0 24px rgba(190,215,255,0.12)",
};

const frameInspectorImageStyle = {
  display: "block",
  width: "100%",
  maxHeight: 330,
  objectFit: "contain",
  borderRadius: 10,
  background: "rgba(0,0,0,0.35)",
};

const closeInspectorButtonStyle = {
  width: 32,
  height: 32,
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(255,255,255,0.08)",
  color: "#f4f8ff",
  fontSize: 20,
  lineHeight: 1,
  cursor: "pointer",
};

const diagnosticLabelStyle = {
  color: "#8ec5ff",
  fontSize: 10,
  letterSpacing: 1,
  textTransform: "uppercase",
};

const diagnosticValueStyle = {
  color: "#f4f8ff",
  fontFamily: "monospace",
  wordBreak: "break-all",
  marginTop: 4,
};

const diagnosticRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  color: "#dceaf7",
  fontSize: 12,
  fontFamily: "monospace",
  padding: "7px 8px",
  borderRadius: 7,
  background: "rgba(0,0,0,0.22)",
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

const frameButtonStyle = {
  width: 36,
  height: 36,
  border: "1px solid rgba(255,255,255,0.18)",
  borderRadius: 9,
  background: "rgba(255,255,255,0.08)",
  color: "#f4f8ff",
  cursor: "pointer",
};
