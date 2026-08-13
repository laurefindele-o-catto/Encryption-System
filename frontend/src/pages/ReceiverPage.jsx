import { useEffect, useState } from "react";
import api from "../api.js";

export default function ReceiverPage() {
  const [encryptedImage, setEncryptedImage] = useState(null);
  const [keyImage, setKeyImage] = useState(null);
  const [decryptedImage, setDecryptedImage] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // On load (and whenever this tab is shown), fetch whatever encrypted
  // image is currently sitting on the backend, as if it had just arrived.
  useEffect(() => {
    api
      .get("/encrypted-image")
      .then((res) => setEncryptedImage(res.data.image))
      .catch(() => setEncryptedImage(null));
  }, []);

  const handleDecrypt = async (e) => {
    e.preventDefault();
    setError(null);
    setDecryptedImage(null);
    setLoading(true);

    const formData = new FormData();
    formData.append("key_image", keyImage);

    try {
      const res = await api.post("/decrypt", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setDecryptedImage(res.data.image);
    } catch (err) {
      // 501 here just means decrypt_image() isn't implemented yet — expected
      // until you fill in services/crypto.py.
      setError(err.response?.data?.detail || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Receiver</h2>

      <p>Encrypted image (from sender):</p>
      {encryptedImage ? (
        <img src={`data:image/png;base64,${encryptedImage}`} alt="encrypted" width={200} />
      ) : (
        <p>No encrypted image yet — encrypt one on the Sender tab first.</p>
      )}

      <form onSubmit={handleDecrypt} style={{ marginTop: 16 }}>
        <label>Key image: </label>
        <input type="file" accept="image/*" onChange={(e) => setKeyImage(e.target.files[0])} required />
        <button type="submit" disabled={loading} style={{ marginLeft: 8 }}>
          {loading ? "Decrypting..." : "Decrypt"}
        </button>
      </form>

      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}

      {decryptedImage && (
        <div style={{ marginTop: 16 }}>
          <p>Decrypted image:</p>
          <img src={`data:image/png;base64,${decryptedImage}`} alt="decrypted" width={200} />
        </div>
      )}
    </div>
  );
}
