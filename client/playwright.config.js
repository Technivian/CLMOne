const { defineConfig } = require('@playwright/test');

// Snapshot policy: never auto-regenerate in CI. Local intentional updates
// require PLAYWRIGHT_UPDATE_SNAPSHOTS=1 plus an explicit --update-snapshots flag.
const allowSnapshotUpdate = process.env.PLAYWRIGHT_UPDATE_SNAPSHOTS === '1' && process.env.CI !== 'true';
const testTimeout = Number(process.env.PLAYWRIGHT_TEST_TIMEOUT_MS || 60000);
const shardAcrossTests = process.env.PLAYWRIGHT_SHARD_ACROSS_TESTS === '1';

if (!Number.isFinite(testTimeout) || testTimeout < 1000) {
  throw new Error('PLAYWRIGHT_TEST_TIMEOUT_MS must be a number of at least 1000 milliseconds');
}

module.exports = defineConfig({
  testDir: './tests/e2e',
  // Every CI shard owns an isolated SQLite database. Test-level sharding may
  // distribute files across those databases, while one worker per shard keeps
  // lifecycle mutations serial and deterministic inside each workspace.
  fullyParallel: shardAcrossTests,
  workers: 1,
  timeout: testTimeout,
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
