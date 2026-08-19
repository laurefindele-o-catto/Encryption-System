/**
 * Phase 2 placeholder. The future "Text/Morse Transmission" view will
 * live behind this tab — for the supervisor demo, the intent is
 * visible even though no logic is wired up yet.
 */
export default function Phase2Placeholder() {
  return (
    <div
      style={{
        border: "2px dashed #aaa",
        borderRadius: 8,
        padding: 24,
        background: "#f9f9f9",
      }}
    >
      <h2 style={{ marginTop: 0 }}>Phase 2: Text/Morse Transmission — Coming Next</h2>
      <p style={{ color: "#444" }}>
        This tab will host the covert Morse-code text pipeline layered on top of
        the DRPE core you see in the DRPE Demo tab.
      </p>

      <h3>Planned sender pipeline</h3>
      <ol>
        <li>text → Morse (standard ITU table)</li>
        <li>Morse → ordered symbol states (dot/dash/gap types as integers)</li>
        <li>
          For each state, generate one image by applying a differential
          two-block brightness encoding on the shared base image
          (Block A ±Δ, Block B ∓Δ; net energy change = 0)
        </li>
        <li>
          Encrypt each generated image with the existing DRPE pipeline
          (one seed per symbol, auto-incremented)
        </li>
        <li>Transmit the resulting sequence of encrypted images</li>
      </ol>

      <h3>Planned receiver pipeline</h3>
      <ol>
        <li>Decrypt each image with the existing DRPE pipeline</li>
        <li>Read the differential brightness at the two pre-agreed block coordinates</li>
        <li>Symbol states → Morse → original text</li>
      </ol>

      <p style={{ color: "#666", fontSize: 13, marginTop: 16 }}>
        Phase 1 deliberately does <strong>not</strong> implement this. The
        architecture leaves the <code>services/encoding/</code> package as
        the single home for the new logic, and a shared <code>config.py</code>
        for the pre-agreed block coordinates and Δ.
      </p>
    </div>
  );
}
