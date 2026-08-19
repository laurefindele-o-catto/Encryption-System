import axios from "axios";

// Target FastAPI backend directly during development to avoid Node proxy socket restrictions.
const baseURL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" && window.location.port === "5173"
    ? "http://127.0.0.1:8000/api"
    : "/api");

const api = axios.create({ baseURL });

export default api;
