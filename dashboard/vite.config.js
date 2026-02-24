import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    // Injected at build time — visible in console as BUILD_VERSION global
    BUILD_VERSION: JSON.stringify(new Date().toISOString()),
  },
  server: {
    port: 3000,
    proxy: { "/api": "http://localhost:5001" },
  },
});
