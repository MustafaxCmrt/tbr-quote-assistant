import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/health": "http://api:8000",
      "/api": "http://api:8000",
    },
  },
});
