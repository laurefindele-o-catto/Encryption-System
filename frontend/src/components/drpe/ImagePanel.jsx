/**
 * Reusable image-preview panel: a labeled thumbnail with optional body text.
 */
export default function ImagePanel({ title, src, caption, height = 200 }) {
  const imgSrc = src
    ? src.startsWith("data:")
      ? src
      : `data:image/png;base64,${src}`
    : null;

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 4,
        padding: 8,
        background: "#fafafa",
        minWidth: 220,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{title}</div>
      {imgSrc ? (
        <img
          src={imgSrc}
          alt={title}
          style={{ width: "100%", height, objectFit: "contain", background: "#fff" }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#999",
            background: "#fff",
            fontSize: 13,
          }}
        >
          (empty)
        </div>
      )}
      {caption && (
        <div style={{ marginTop: 6, fontSize: 12, color: "#555" }}>{caption}</div>
      )}
    </div>
  );
}
