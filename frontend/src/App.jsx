import { useState } from "react";
import DRPEDemo from "./pages/DRPEDemo.jsx";
import Phase2Placeholder from "./pages/Phase2Placeholder.jsx";

export default function App() {
  const [tab, setTab] = useState("drpe");

  const buttonStyle = (active) => ({
    padding: "8px 16px",
    marginRight: 8,
    border: "1px solid #444",
    background: active ? "#1f6feb" : "#f4f4f4",
    color: active ? "#fff" : "#222",
    cursor: "pointer",
    borderRadius: 4,
  });

  return (
    <div style={{ maxWidth: 1100, margin: "32px auto", fontFamily: "sans-serif", color: "#222" }}>
      <h1 style={{ marginBottom: 4 }}>DRPE Phase 1 Demo</h1>
      <p style={{ marginTop: 0, color: "#666" }}>
        Double Random Phase Encryption — image upload → encrypt → decrypt (correct &amp; wrong seed).
      </p>

      <div style={{ marginBottom: 24, marginTop: 16 }}>
        <button style={buttonStyle(tab === "drpe")} onClick={() => setTab("drpe")}>
          DRPE Demo
        </button>
        <button style={buttonStyle(tab === "phase2")} onClick={() => setTab("phase2")}>
          Phase 2 (Coming Next)
        </button>
      </div>

      {tab === "drpe" ? <DRPEDemo /> : <Phase2Placeholder />}
    </div>
  );
}
