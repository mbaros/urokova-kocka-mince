// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  reporter: 'line',
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:8765',
    trace: 'retain-on-failure',
    actionTimeout: 8_000,
    navigationTimeout: 10_000,
    locale: 'cs-CZ',
    // Environments with a preinstalled Chromium can point here instead of downloading one.
    launchOptions: process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {},
  },
  projects: [
    { name: 'mobile-chromium', use: { ...devices['Pixel 7'] } },
  ],
});
