import { defineConfig, devices } from "@playwright/test";

const python =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: `${python} -m uvicorn pulso.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
    },
    {
      command: "node scripts/next.mjs dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
});
