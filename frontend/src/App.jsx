import { useState } from "react";
import SenderPage from "./pages/SenderPage.jsx";
import ReceiverPage from "./pages/ReceiverPage.jsx";

export default function App() {
  const [tab, setTab] = useState("sender");

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Two-Factor Image Encryption</h1>

      <div style={{ marginBottom: 24 }}>
        <button onClick={() => setTab("sender")} disabled={tab === "sender"}>
          Sender
        </button>
        <button onClick={() => setTab("receiver")} disabled={tab === "receiver"} style={{ marginLeft: 8 }}>
          Receiver
        </button>
      </div>

      {tab === "sender" ? <SenderPage /> : <ReceiverPage />}
    </div>
  );
}
