/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev: `npm run dev` proxies /api (WebSocket included) to the Caddy at :9219, so the dev server sees the same origin
// rules as the box.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": { target: "http://localhost:9219", ws: true, changeOrigin: false } } },
  // The grid chunk is AG Grid Community (ADR-0014); the budget is checked by scripts/gate.sh, not by this warning.
  build: { sourcemap: false, target: "es2022", chunkSizeWarningLimit: 1200 },
  test: { include: ["src/**/*.test.ts"], environment: "node" },
});
