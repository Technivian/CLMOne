const { expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

// Shared by pilot-verification.spec.js and browser-isolation-regression.spec.js.
// See docs/pilots/payrollminds/BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md.
//
// This is the exact creation path that used to leak a persistent "Life NDA"
// contract into every later test in the shard (list, workspace, dashboard,
// and — because it sorted first — the "detail" test's record selection).
// Any test using createLifecycleNda() owns cleaning up what it creates via
// deleteE2eLifecycleContract(); nothing here mutates shared/seeded fixtures.

/**
 * Submit the real NDA creation wizard as a synthetic "Life NDA" lifecycle
 * fixture and return its contract id. Leaves the workflow ACTIVE / contract
 * DRAFTING, matching the original leaking test's behavior.
 */
async function createLifecycleNda(page, suffix) {
  await page.goto('/contracts/new/nda/');
  await page.fill('[data-field-key="counterparty"]', `Life NDA ${suffix}`);
  await page.fill('[data-field-key="start_date"]', '2026-10-01');
  await page.fill('[data-field-key="contract_owner"]', 'Avery Brooks');
  await page.fill('[data-field-key="business_unit"]', 'Revenue Operations');
  await page.fill('[data-field-key="internal_reference"]', `NDA-L-${suffix}`);
  await page.selectOption('[data-field-key="nda_type"]', 'Mutual');
  await page.fill('[data-field-key="confidentiality_purpose"]', 'product diligence');
  await page.fill('[data-field-key="confidentiality_period"]', '2');
  await page.fill('[data-field-key="disclosure_scope"]', 'technical architecture');
  await page.fill('[data-field-key="permitted_recipients"]', 'employees');
  await page.fill('[data-field-key="governing_law"]', 'Netherlands');
  await page.fill('[data-field-key="jurisdiction"]', 'Amsterdam');
  await page.check('[data-field-key="injunctive_relief_included"]');
  await page.click('#submit-nda-btn');
  await expect(page).toHaveURL(/\/contracts\/workflows\/\d+/);
  await page.locator('details.dc-ds-workspace__actions-menu summary').click();
  await page.getByRole('menuitem', { name: 'View contract record' }).click();
  await expect(page).toHaveURL(/\/contracts\/\d+\/?$/);
  return page.url().match(/\/contracts\/(\d+)/)[1];
}

/** Test-only ownership cleanup: delete exactly the contract this test created. */
function deleteE2eLifecycleContract(contractId) {
  const rootDir = path.resolve(__dirname, '../../../..');
  const venvPython = path.join(rootDir, '.venv', 'bin', 'python');
  const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python';
  execFileSync(
    pythonBin,
    ['manage.py', 'delete_e2e_lifecycle_fixture', '--contract-id', String(contractId)],
    {
      cwd: rootDir,
      env: {
        ...process.env,
        DJANGO_E2E: '1',
        DJANGO_SETTINGS_MODULE: process.env.DJANGO_SETTINGS_MODULE || 'config.settings_development',
        DATABASE_URL: process.env.E2E_DATABASE_URL || `sqlite:///${rootDir}/e2e.sqlite3`,
      },
      stdio: 'pipe',
    },
  );
}

module.exports = { createLifecycleNda, deleteE2eLifecycleContract };
