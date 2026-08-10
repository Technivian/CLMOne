/**
 * Default-off browser proof for the OC/PO technical activation mechanism.
 *
 * These scenarios boot disposable, explicitly configured Django E2E servers.
 * They never alter the shared browser fixture database and remove their own
 * SQLite files after the server exits.
 */
const { test, expect } = require('@playwright/test');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');

const rootDir = path.resolve(__dirname, '../../..');

function reservePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close((error) => (error ? reject(error) : resolve(port)));
    });
  });
}

function waitForServer(baseUrl) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + 120000;
    const check = () => {
      const request = http.get(`${baseUrl}/login/`, (response) => {
        response.resume();
        if (response.statusCode && response.statusCode < 500) {
          resolve();
        } else if (Date.now() >= deadline) {
          reject(new Error(`Activation E2E server failed to start: ${baseUrl}`));
        } else {
          setTimeout(check, 500);
        }
      });
      request.once('error', () => {
        if (Date.now() >= deadline) {
          reject(new Error(`Activation E2E server failed to start: ${baseUrl}`));
        } else {
          setTimeout(check, 500);
        }
      });
    };
    check();
  });
}

async function startActivationServer(enabledTypes) {
  const port = await reservePort();
  const token = `${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const database = path.join(os.tmpdir(), `clmone-oc-po-activation-${token}.sqlite3`);
  const baseUrl = `http://127.0.0.1:${port}`;
  const processHandle = spawn('sh', ['scripts/start_e2e_server.sh'], {
    cwd: rootDir,
    env: {
      ...process.env,
      E2E_PORT: String(port),
      E2E_DATABASE_URL: `sqlite:///${database}`,
      CONTROLLED_PILOT_ENABLED: 'true',
      PAYROLLMINDS_ENABLED_CONTRACT_TYPES: enabledTypes.join(','),
      GEMINI_AI_ENABLED: 'false',
      GEMINI_API_KEY: '',
    },
    stdio: 'ignore',
  });
  try {
    await waitForServer(baseUrl);
  } catch (error) {
    processHandle.kill('SIGTERM');
    fs.rmSync(database, { force: true });
    throw error;
  }
  return { baseUrl, database, processHandle };
}

function stopActivationServer(server) {
  if (server && server.processHandle && !server.processHandle.killed) {
    server.processHandle.kill('SIGTERM');
  }
  if (server) fs.rmSync(server.database, { force: true });
}

async function login(page, baseUrl, username = 'e2e_owner', password = 'e2e_pass_123') {
  await page.goto(`${baseUrl}/login/`);
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

async function createType(page, baseUrl, code, label) {
  const title = `Synthetic ${label} ${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  await page.goto(`${baseUrl}/contracts/new/start/`);
  await page.getByRole('link', { name: `Start ${label} request` }).click();
  await expect(page).toHaveURL(new RegExp(`/contracts/new/standard/${code}/`));
  await page.fill('input[name="title"]', title);
  await page.fill('input[name="counterparty"]', 'Synthetic browser counterparty');
  await page.fill('input[name="governing_law"]', 'Netherlands');
  await page.fill('input[name="jurisdiction"]', 'Amsterdam');
  await page.fill('input[name="start_date"]', '2026-01-01');
  await page.fill('input[name="end_date"]', '2027-01-01');
  await page.selectOption('select[name="currency"]', 'EUR');
  await page.click('#submit-contract-btn');
  await expect(page).toHaveURL(/\/contracts\/repository\//);
  const row = page.locator('tr.contract-row', { hasText: title });
  await expect(row).toBeVisible();
  const detailPath = await row.getAttribute('data-href');
  await row.click();
  await expect(page).toHaveURL(/\/contracts\/\d+\/?$/);
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  return { detailPath, title };
}

test.describe.serial('OC/PO activation readiness — default OFF', () => {
  // Each suite provisions an isolated Django database before starting its
  // disposable server. CI runners can take longer than Playwright's default
  // 30 seconds to migrate and seed that database.
  test.describe.configure({ timeout: 150000 });
  let server;

  test.beforeAll(async () => {
    // Playwright gives beforeAll its own timeout; describe configuration does
    // not extend it. The isolated Django setup includes migrations and seed
    // data, which can exceed the CI default on a cold runner.
    test.setTimeout(150000);
    server = await startActivationServer(['MSA', 'NDA', 'DPA']);
  });
  test.afterAll(() => stopActivationServer(server));

  test('Order Confirmation and Purchase Order are absent and direct intake is blocked', async ({ page }) => {
    test.setTimeout(150000);
    await login(page, server.baseUrl);
    await page.goto(`${server.baseUrl}/contracts/new/start/`);
    await expect(page.locator('[data-ctp-card][data-contract-type="ORDER_CONFIRMATION"]')).toHaveCount(0);
    await expect(page.locator('[data-ctp-card][data-contract-type="PURCHASE_ORDER"]')).toHaveCount(0);

    for (const code of ['ORDER_CONFIRMATION', 'PURCHASE_ORDER', 'SOW', 'VENDOR', 'EMPLOYMENT', 'SAAS', 'LEASE', 'OTHER']) {
      await page.goto(`${server.baseUrl}/contracts/new/standard/${code}/`);
      await expect(page).toHaveURL(/\/dashboard\//);
    }
  });
});

test.describe.serial('OC/PO activation readiness — test-only ON', () => {
  test.describe.configure({ timeout: 150000 });
  let server;

  test.beforeAll(async () => {
    test.setTimeout(150000);
    server = await startActivationServer(['MSA', 'NDA', 'DPA', 'ORDER_CONFIRMATION', 'PURCHASE_ORDER']);
  });
  test.afterAll(() => stopActivationServer(server));

  for (const [code, label] of [
    ['ORDER_CONFIRMATION', 'Order Confirmation'],
    ['PURCHASE_ORDER', 'Purchase Order'],
  ]) {
    test(`${label} follows the real browser intake and remains private`, async ({ browser, page }) => {
      test.setTimeout(150000);
      await login(page, server.baseUrl);
      const { detailPath, title } = await createType(page, server.baseUrl, code, label);

      const memberContext = await browser.newContext();
      const memberPage = await memberContext.newPage();
      try {
        await login(memberPage, server.baseUrl, 'e2e_legal', 'e2e_legal_pass_123');
        await memberPage.goto(`${server.baseUrl}${detailPath}`);
        await expect(memberPage).toHaveTitle(/Page not found|Not Found/i);
        await memberPage.goto(`${server.baseUrl}/contracts/repository/`);
        await expect(memberPage.locator('tr.contract-row', { hasText: title })).toHaveCount(0);
      } finally {
        await memberContext.close();
      }
    });
  }
});
