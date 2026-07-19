const { test, expect } = require('@playwright/test');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.goto('/contracts/repository/');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

test.describe('Phase 5A authenticated application shell', () => {
  test('uses canonical shell hooks while preserving active navigation and keyboard focus', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await expect(page.locator('.dc-ds-shell')).toBeVisible();
    await expect(page.locator('.dc-ds-shell__sidebar')).toHaveAttribute('aria-label', 'Primary navigation');
    const activeNavigation = page.locator('.dc-ds-shell__sidebar .nav-link.active').first();
    await activeNavigation.focus();
    await expect(activeNavigation).toBeFocused();
    await expect(page.locator('.dc-ds-shell__topbar')).toBeVisible();
    await expect(page.locator('.dc-ds-shell__content')).toBeVisible();
  });

  test('keeps mobile navigation operable without viewport overflow', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page);
    const toggle = page.locator('.dc-ds-shell__mobile-toggle');
    await toggle.focus();
    await expect(toggle).toBeFocused();
    await toggle.click();
    await expect(page.locator('body')).toHaveClass(/mobile-nav-open/);
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await page.keyboard.press('Escape');
    await expect(page.locator('body')).not.toHaveClass(/mobile-nav-open/);
    await expect(toggle).toHaveAttribute('aria-expanded', 'false');
    const overflow = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      bodyWidth: document.body.scrollWidth,
    }));
    expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth);
    expect(overflow.bodyWidth).toBeLessThanOrEqual(overflow.viewportWidth);
  });

  test('keeps the dashboard shell consumer aligned at desktop and 390px', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page.goto('/dashboard/');
    await expect(page.locator('.dc-ds-shell__main')).toBeVisible();
    await expect(page.locator('.dc-ds-shell__topbar')).toBeVisible();
    await expect(page.locator('.dc-ds-shell__sidebar .nav-link.active')).toHaveCount(1);

    await page.setViewportSize({ width: 390, height: 844 });
    const overflow = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      bodyWidth: document.body.scrollWidth,
    }));
    expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth);
    expect(overflow.bodyWidth).toBeLessThanOrEqual(overflow.viewportWidth);
  });
});
