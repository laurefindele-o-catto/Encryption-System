import { useState } from "react";
import AlicePage from "./pages/AlicePage.jsx";
import BobPage from "./pages/BobPage.jsx";
import NoiseReveal from "./components/NoiseReveal.jsx";

export default function App() {
  const [role, setRole] = useState("alice");
  const [packet, setPacket] = useState(null);
  const [revealActive, setRevealActive] = useState(false);

  const handlePacketReady = (payload) => {
    setPacket(payload);
    setRevealActive(true);
  };

  const handleSuccessfulBobDecrypt = () => {
    setRevealActive(false);
  };

  return (
    <>
      <style>{`
        @keyframes starTwinkle {
          0%, 100% {
            opacity: 0.2;
            transform: scale(0.75) rotate(0deg);
            filter: brightness(0.8);
          }
          20% {
            opacity: 0.7;
            transform: scale(1) rotate(12deg);
            filter: brightness(1.15);
          }
          50% {
            opacity: 1;
            transform: scale(1.25) rotate(0deg);
            filter: brightness(1.5);
          }
          75% {
            opacity: 0.8;
            transform: scale(1.08) rotate(-10deg);
            filter: brightness(1.2);
          }
        }
      `}</style>

      <div
        style={{
          minHeight: "100vh",
          background: "#000000",
          color: "#f5f7fa",
          fontFamily: "Segoe UI, sans-serif",
          padding: "28px 20px 48px",
        }}
      >
        <NoiseReveal active={revealActive} />

        <div style={{ maxWidth: 1180, margin: "0 auto", position: "relative", zIndex: 1 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            marginBottom: 24,
            borderBottom: "1px solid rgba(255,255,255,0.18)",
            paddingBottom: 18,
          }}
        >
          <div style={{ position: "relative", paddingLeft: 18 }}>
            <div
              aria-hidden="true"
              style={{
                position: "absolute",
                left: -2,
                top: -2,
                width: 18,
                height: 18,
                pointerEvents: "none",
                opacity: revealActive ? 0 : 1,
                transition: "opacity 0.4s ease",
              }}
            >
              <div
                style={{
                  width: 18,
                  height: 18,
                  background: "linear-gradient(135deg, #ffffff 0%, #edf2ff 35%, #cfd9ec 100%)",
                  clipPath: "polygon(50% 0%, 61% 35%, 100% 35%, 68% 57%, 79% 100%, 50% 71%, 21% 100%, 32% 57%, 0% 35%, 39% 35%)",
                  boxShadow: "0 0 12px rgba(255, 255, 255, 0.9), 0 0 26px rgba(215, 224, 255, 0.7), 0 0 40px rgba(190, 202, 240, 0.45)",
                  animation: "starTwinkle 3.8s ease-in-out infinite",
                  transformOrigin: "center",
                }}
              />
            </div>
            <div style={{ letterSpacing: 3, fontSize: 12, color: "#9aa4b2", textTransform: "uppercase" }}>
              H.-.-laand Encryption
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "2.3rem", fontWeight: 700 }}>- -.-. .- - - ---</h1>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              onClick={() => setRole("alice")}
              style={{
                border: role === "alice" ? "1px solid #5ab7ff" : "1px solid rgba(255,255,255,0.18)",
                background: role === "alice" ? "rgba(90,183,255,0.18)" : "rgba(255,255,255,0.03)",
                color: "#f4f8ff",
                padding: "10px 18px",
                borderRadius: 999,
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Enter as Alice
            </button>
            <button
              onClick={() => setRole("bob")}
              style={{
                border: role === "bob" ? "1px solid #9fe7ad" : "1px solid rgba(255,255,255,0.18)",
                background: role === "bob" ? "rgba(159,231,173,0.12)" : "rgba(255,255,255,0.03)",
                color: "#f4f8ff",
                padding: "10px 18px",
                borderRadius: 999,
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Enter as Bob
            </button>
          </div>
        </div>

        {role === "alice" ? (
          <AlicePage
            packet={packet}
            onPacketReady={handlePacketReady}
            revealActive={revealActive}
            setRevealActive={setRevealActive}
          />
        ) : (
          <BobPage
            packet={packet}
            onSuccessfulDecrypt={handleSuccessfulBobDecrypt}
            revealActive={revealActive}
            setRevealActive={setRevealActive}
          />
        )}
        </div>
      </div>
    </>
  );
}
