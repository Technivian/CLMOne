/**
 * Baseline evidence screenshots for controlled-pilot launch.
 * Run against e2e server (CONTROLLED_PILOT not required for honesty screens;
 * blocked-route checks use Django unit tests + optional live server with flags).
 */
const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';
const outDir = path.resolve(
  __dirname,
  '../../../docs/audits/evidence/2026-07-20-controlled-pilot-baseline/screenshots'
);

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.goto('/dashboard/');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

test.describe('Pilot baseline screenshots', () => {
  test.beforeAll(() => {
    fs.mkdirSync(outDir, { recursive: true });
  });

  test('capture allowed surfaces', async ({ page }) => {
    test.slow();
    await login(page);
    await page.screenshot({ path: path.join(outDir, '01-dashboard.png'), fullPage: true });

    await page.goto('/contracts/new/start/');
    await page.screenshot({ path: path.join(outDir, '02-new-contract-picker.png'), fullPage: true });

    await page.goto('/contracts/new/msa/');
    await page.screenshot({ path: path.join(outDir, '03-msa-builder.png'), fullPage: true });

    await page.goto('/contracts/new/nda/');
    await page.screenshot({ path: path.join(outDir, '04-nda-builder.png'), fullPage: true });

    await page.goto('/contracts/new/dpa/');
    await page.screenshot({ path: path.join(outDir, '05-dpa-builder.png'), fullPage: true });

    await page.goto('/contracts/repository/');
    await page.screenshot({ path: path.join(outDir, '06-repository.png'), fullPage: true });

    await page.goto('/contracts/workflows/');
    await page.screenshot({ path: path.join(outDir, '07-workflow-operations.png'), fullPage: true });

    // Honesty: NDA unsupported CTAs absent after generate is covered by e2e suite;
    // capture login for auth surface.
    await page.goto('/login/');
    await page.screenshot({ path: path.join(outDir, '08-login.png'), fullPage: true });
  });
});
