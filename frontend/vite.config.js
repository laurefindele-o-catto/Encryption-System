import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Any request to /api/* from React gets forwarded to FastAPI,
      // so the frontend code never needs to hardcode localhost:8000.
      "/api": "http://localhost:8000",
    },
  },
});
