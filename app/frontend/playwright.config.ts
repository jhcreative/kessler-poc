import { defineConfig, devices } from "@playwright/test";

// Runs against the real stack (Caddy, backend, Postgres) at :9219: app/scripts/e2e.sh brings it up and seeds it.
export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: process.env.E2E_BASE ?? "http://localhost:9219", ...devices["Desktop Chrome"], deviceScaleFactor: 1 },
});
