import { defineConfig } from "vite";

// Server-side only: the proxy adds the admin key to API requests. The value is
// not VITE_-prefixed, so it never reaches the browser bundle.
const adminKey = process.env.ADMIN_API_KEY;

export default defineConfig({
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/health": "http://api:8000",
      "/api": {
        target: "http://api:8000",
        headers: adminKey ? { "X-Admin-Key": adminKey } : {},
      },
    },
  },
});
