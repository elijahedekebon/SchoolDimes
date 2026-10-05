import { defineConfig } from "@playwright/test";

/**
 * End-to-end tests against the REAL backend with seed data:
 *   docker compose up -d && docker compose exec web python manage.py seed_demo
 *   (optionally simulate_pos), then `npm run e2e` (starts `next dev` if needed).
 */
export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  use: { baseURL: process.env.E2E_BASE_URL || "http://localhost:3000", trace: "retain-on-failure" },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/login",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
