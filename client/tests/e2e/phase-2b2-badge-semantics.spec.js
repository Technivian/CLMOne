const { test, expect } = require('@playwright/test');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';

test('Phase 2B.2 canonical badge semantics render in dense and responsive layouts', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.goto('/contracts/design-system/');

  for (const tone of ['success', 'progress', 'attention', 'danger', 'special', 'neutral']) {
    await expect(page.locator(`.dc-ds-badge--${tone}`).first()).toBeVisible();
  }
  const tableBadge = page.locator('.dc-ds-table .dc-ds-badge').first();
  await expect(tableBadge).toBeVisible();
  await expect(tableBadge).not.toBeEmpty();
  const badgeStyle = await tableBadge.evaluate((element) => ({
    backgroundColor: getComputedStyle(element).backgroundColor,
    color: getComputedStyle(element).color,
  }));
  expect(badgeStyle.backgroundColor).not.toBe(badgeStyle.color);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  const responsiveBadge = page.locator('.dc-ds-badge--special').first();
  await expect(responsiveBadge).toBeVisible();
  const bounds = await responsiveBadge.boundingBox();
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390);
});
