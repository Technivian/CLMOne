const { test, expect } = require('@playwright/test');

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

async function assertNoHorizontalOverflow(page) {
  const overflow = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: document.documentElement.clientWidth,
    bodyWidth: document.body.scrollWidth,
  }));
  expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth);
  expect(overflow.bodyWidth).toBeLessThanOrEqual(overflow.viewportWidth);
}

test.describe('Phase 5H Command Center consolidation', () => {
  test('keeps expressive hero and canonical CTAs at 1440 and 1280', async ({ page }) => {
    await login(page);
    for (const width of [1440, 1280]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto('/dashboard/');
      await expect(page.locator('.command-center.cc-v3')).toBeVisible();
      await expect(page.locator('.cc-v3-portfolio-hero.dc-ds-surface--feature')).toBeVisible();
      await expect(page.locator('.cc-v3-portfolio-actions .dc-ds-button--primary')).toBeVisible();
      await expect(page.locator('.cc-v3-portfolio-actions .dc-ds-button--link')).toBeVisible();
      await expect(page.locator('.dc-ds-metric').first()).toBeVisible();
      await expect(page.locator('.cc-v3-matters.dc-ds-surface')).toBeVisible();
      const primary = page.locator('.cc-v3-portfolio-actions .dc-ds-button--primary').first();
      await primary.focus();
      await expect(primary).toBeFocused();
      await assertNoHorizontalOverflow(page);
    }
  });

  test('keeps 390px operable without overflow and preserves empty/setup states', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await login(page);
    await page.goto('/dashboard/');
    await expect(page.locator('.command-center.cc-v3')).toBeVisible();
    await expect(page.locator('#portfolio-health-title')).toBeVisible();
    const emptyOrQueue = page.locator('.cc-v3-rail-state, .cc-v3-action-row, .dc-ds-setup-action').first();
    await expect(emptyOrQueue).toBeVisible();
    const mattersEmpty = page.locator('.cc-v3-matters .cc-v3-empty');
    if (await mattersEmpty.count()) {
      await expect(mattersEmpty.first()).toBeVisible();
    }
    await assertNoHorizontalOverflow(page);
  });

  test('section toolbar links use canonical link buttons', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page.goto('/dashboard/');
    const viewAll = page.locator('.cc-v3-section-head .dc-ds-button--link', { hasText: 'View all' }).first();
    await expect(viewAll).toBeVisible();
    await viewAll.focus();
    await expect(viewAll).toBeFocused();
  });
});
