const { defineConfig } = require('@playwright/test');

// Snapshot policy: never auto-regenerate in CI. Local intentional updates
// require PLAYWRIGHT_UPDATE_SNAPSHOTS=1 plus an explicit --update-snapshots flag.
const allowSnapshotUpdate = process.env.PLAYWRIGHT_UPDATE_SNAPSHOTS === '1' && process.env.CI !== 'true';

module.exports = defineConfig({
  // CI captures on macos-14; keep a single committed darwin suffix on all hosts.
  snapshotPathTemplate: '{testDir}/{testFilePath}-snapshots/{arg}-darwin{ext}',
  testDir: './tests/e2e',
  // The local E2E server uses one SQLite workspace. Serial execution keeps
  // lifecycle mutations deterministic and avoids cross-test data races.
  workers: 1,
  timeout: 60000,
  updateSnapshots: allowSnapshotUpdate ? 'changed' : 'none',
  expect: {
    timeout: 8000,
  },
  retries: 0,
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
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  reporter: 'list',
});
