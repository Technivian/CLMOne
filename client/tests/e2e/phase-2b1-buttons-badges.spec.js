const { test, expect } = require('@playwright/test');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.goto('/dashboard/');
}

async function detailPath(page) {
  await page.goto('/contracts/repository/');
  await expect(page.locator('#contracts-tbody')).not.toContainText('Loading contracts', { timeout: 15000 });
  const row = page.locator('tr.contract-row').first();
  await expect(row).toBeVisible();
  const contractId = await row.getAttribute('data-contract-id');
  expect(contractId).toMatch(/^\d+$/);
  return `/contracts/${contractId}/?tab=activity`;
}

test.describe('Phase 2B.1 canonical buttons and badges', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
  });

  test('list family keeps canonical actions and semantic badges responsive', async ({ page }) => {
    await page.goto('/contracts/repository/');
    await expect(page.locator('#contracts-tbody')).not.toContainText('Loading contracts', { timeout: 15000 });
    const primary = page.locator('.repo-view-actions .dc-ds-button--primary');
    const badge = page.locator('.contract-row .dc-ds-badge--sm').first();
    await expect(primary).toBeVisible();
    await expect(badge).toBeVisible();
    await expect(badge).not.toBeEmpty();
    await primary.focus();
    await expect(primary).toBeFocused();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload();
    await expect(primary).toBeVisible();
  });

  test('standard detail and modal actions preserve keyboard focus', async ({ page }) => {
    await page.goto(await detailPath(page));
    await page.locator('[data-open-note-dialog]').first().click();
    const dialog = page.locator('#contract-note-dialog');
    await expect(dialog).toHaveAttribute('open', '');
    await expect(dialog.locator('.dc-ds-control').first()).toBeFocused();
    await page.keyboard.press('Tab');
    await expect(dialog.locator('.dc-ds-button--primary')).toBeVisible();
    const close = dialog.getByRole('button', { name: 'Close note form' });
    await close.click();
    await expect(page.locator('[data-open-note-dialog]').first()).toBeFocused();
  });

  test('admin settings preserve destructive and primary actions', async ({ page }) => {
    await page.goto('/contracts/privacy/data-controls/');
    const aiControl = page.getByRole('button', { name: /AI features for this organisation/ });
    await expect(aiControl).toBeVisible();
    await expect(aiControl).toHaveClass(/dc-ds-button--(?:danger|primary)/);
    await aiControl.focus();
    await expect(aiControl).toBeFocused();
  });
});
