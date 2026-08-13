import { useState } from "react";
import api from "../api.js";

export default function SenderPage() {
  const [coverImage, setCoverImage] = useState(null);
  const [keyImage, setKeyImage] = useState(null);
  const [x, setX] = useState(0);
  const [y, setY] = useState(0);

  const [encryptedImage, setEncryptedImage] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setEncryptedImage(null);
    setLoading(true);

    const formData = new FormData();
    formData.append("cover_image", coverImage);
    formData.append("key_image", keyImage);
    formData.append("x", x);
    formData.append("y", y);

    try {
      const res = await api.post("/encrypt", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setEncryptedImage(res.data.image);
    } catch (err) {
      // 501 here just means encrypt_image() isn't implemented yet — expected
      // until you fill in services/crypto.py.
      setError(err.response?.data?.detail || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Sender</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Cover image: </label>
          <input type="file" accept="image/*" onChange={(e) => setCoverImage(e.target.files[0])} required />
        </div>
        <div style={{ marginTop: 8 }}>
          <label>Key image: </label>
          <input type="file" accept="image/*" onChange={(e) => setKeyImage(e.target.files[0])} required />
        </div>
        <div style={{ marginTop: 8 }}>
          <label>Secret coordinate: </label>
          x <input type="number" value={x} onChange={(e) => setX(Number(e.target.value))} style={{ width: 60 }} />
          y <input type="number" value={y} onChange={(e) => setY(Number(e.target.value))} style={{ width: 60 }} />
        </div>
        <button type="submit" disabled={loading} style={{ marginTop: 12 }}>
          {loading ? "Encrypting..." : "Encrypt"}
        </button>
      </form>

      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}

      {encryptedImage && (
        <div style={{ marginTop: 16 }}>
          <p>Encrypted image:</p>
          <img src={`data:image/png;base64,${encryptedImage}`} alt="encrypted" width={200} />
        </div>
      )}
    </div>
  );
}
