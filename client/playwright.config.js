const { defineConfig } = require('@playwright/test');

// Snapshot policy: never auto-regenerate in CI. Local intentional updates
// require PLAYWRIGHT_UPDATE_SNAPSHOTS=1 plus an explicit --update-snapshots flag.
const allowSnapshotUpdate = process.env.PLAYWRIGHT_UPDATE_SNAPSHOTS === '1' && process.env.CI !== 'true';

module.exports = defineConfig({
  testDir: './tests/e2e',
  // The local E2E server uses one SQLite workspace. Serial execution keeps
  // lifecycle mutations deterministic and avoids cross-test data races.
  workers: 1,
  timeout: 30000,
  updateSnapshots: allowSnapshotUpdate ? 'changed' : 'none',
  expect: {
    timeout: 5000,
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: 'sh ../scripts/start_e2e_server.sh',
        url: 'http://127.0.0.1:8010/login/',
        reuseExistingServer: true,
        timeout: 120000,
      },
  use: {
    headless: true,
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:8010',
  },
  reporter: 'list',
});
