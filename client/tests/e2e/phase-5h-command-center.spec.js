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
      const heroPrimary = page.locator('.cc-v3-portfolio-actions .dc-ds-button--primary, .cc-v3-top-priority-actions .dc-ds-button--primary').first();
      const heroSecondary = page.locator('.cc-v3-portfolio-actions .dc-ds-button--link, .cc-v3-portfolio-actions .dc-ds-button--secondary, .cc-v3-top-priority-actions .dc-ds-button--secondary').first();
      await expect(heroPrimary).toBeVisible();
      await expect(heroSecondary).toBeVisible();
      await expect(page.locator('.dc-ds-metric').first()).toBeVisible();
      await expect(page.locator('.cc-v3-matters.dc-ds-surface')).toBeVisible();
      const primary = heroPrimary;
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
    const emptyOrQueue = page.locator('.cc-v3-rail-state, .cc-v3-operational-row, .cc-v3-deadline-row').first();
    await expect(emptyOrQueue).toBeVisible();
    const attentionState = page.locator('.cc-v3-attention-empty, .cc-v3-attention-table-wrap').first();
    await expect(attentionState).toBeVisible();
    await assertNoHorizontalOverflow(page);
  });

  test('section toolbar links use canonical link buttons', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page.goto('/dashboard/');
    const viewAll = page.locator(
      '.cc-v3-portfolio-actions .dc-ds-button--secondary, .cc-v3-top-priority-actions .dc-ds-button--secondary'
    ).first();
    await expect(viewAll).toBeVisible();
    await viewAll.focus();
    await expect(viewAll).toBeFocused();
  });
});
