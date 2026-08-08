/**
 * Order-independence regression coverage for the browser-isolation repair.
 * See docs/pilots/payrollminds/BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md.
 *
 * Proves the "Life NDA" lifecycle fixture (client/tests/e2e/pilot-verification.spec.js,
 * "Verification: lifecycle Stage vs Status") never survives into a later test's
 * view of the dashboard, repository list, or workflow workspace — regardless of
 * run order or repetition — because it now owns cleaning up what it creates.
 */
const { test, expect } = require('@playwright/test');
const { createLifecycleNda, deleteE2eLifecycleContract } = require('./helpers/lifecycle-fixtures');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.goto('/dashboard/');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

async function surfacesFreeOfLifeNda(page) {
  for (const path of ['/dashboard/', '/contracts/repository/', '/contracts/workflows/']) {
    await page.goto(path);
    await expect(page.locator('body')).not.toContainText('Life NDA');
  }
}

async function workflowLinkOrder(page) {
  await page.goto('/contracts/workflows/');
  return page.locator('a[href^="/contracts/workflows/"]').evaluateAll((links) => (
    Array.from(new Set(
      links
        .map((link) => link.getAttribute('href'))
        .filter((href) => /^\/contracts\/workflows\/\d+\/$/.test(href)),
    ))
  ));
}

test.describe('Browser isolation: lifecycle leak does not survive into later tests', () => {
  test('lifecycle scenario leaves no trace on dashboard, list, or workspace', async ({ page }) => {
    test.slow();
    await login(page);
    const suffix = `${Date.now()}`.slice(-6);
    const contractId = await createLifecycleNda(page, suffix);

    // Sanity: the fixture we're about to clean up really was live just now.
    await page.goto('/contracts/workflows/');
    await expect(page.locator('body')).toContainText('Life NDA');

    deleteE2eLifecycleContract(contractId);

    await surfacesFreeOfLifeNda(page);
  });

  test('reverse order: visual surfaces are clean before and after the lifecycle scenario runs', async ({ page }) => {
    test.slow();
    await login(page);

    const before = await workflowLinkOrder(page);
    await surfacesFreeOfLifeNda(page);

    const suffix = `${Date.now()}`.slice(-6);
    const contractId = await createLifecycleNda(page, suffix);
    deleteE2eLifecycleContract(contractId);

    const after = await workflowLinkOrder(page);
    await surfacesFreeOfLifeNda(page);

    // Same fixture set, same order — the lifecycle scenario is not observable
    // in the workflow list once its own test has finished with it.
    expect(after).toEqual(before);
  });

  test('repetition: running the lifecycle scenario twice leaves no accumulated records', async ({ page }) => {
    test.slow();
    await login(page);

    const baseline = await workflowLinkOrder(page);

    for (let i = 0; i < 2; i += 1) {
      const suffix = `${Date.now()}`.slice(-6);
      const contractId = await createLifecycleNda(page, suffix);
      deleteE2eLifecycleContract(contractId);
    }

    const final = await workflowLinkOrder(page);
    expect(final).toEqual(baseline);
    await surfacesFreeOfLifeNda(page);
  });

  test('search does not retain the lifecycle fixture after cleanup', async ({ page }) => {
    test.slow();
    await login(page);
    const suffix = `${Date.now()}`.slice(-6);
    const contractId = await createLifecycleNda(page, suffix);
    deleteE2eLifecycleContract(contractId);

    await page.goto(`/contracts/search/?q=Life NDA ${suffix}&search_mode=keyword`);
    await expect(page.getByRole('link', { name: new RegExp(`Life NDA ${suffix}`) })).toHaveCount(0);
  });
});
