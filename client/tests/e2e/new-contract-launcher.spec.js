const { test, expect } = require('@playwright/test');

const username = process.env.E2E_USERNAME || 'e2e_owner';
const password = process.env.E2E_PASSWORD || 'e2e_pass_123';

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

test.describe('New Contract launcher', () => {
  test('shows sections, metadata, upload action, and searchable cards', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page.goto('/contracts/new/start/');

    await expect(page.locator('.topbar-page-title')).toHaveText('New Contract');
    await expect(page.locator('.topbar-page-subtitle')).toContainText(
      'Choose an agreement type to start from an approved template, or upload third-party paper for review.',
    );

    await expect(page.getByRole('search')).toBeVisible();
    await expect(page.getByLabel('Search agreement types')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Upload & review agreement' })).toHaveAttribute(
      'href',
      '/contracts/new/upload/',
    );

    await expect(page.getByRole('heading', { name: 'Recommended', exact: true })).toBeVisible();
    await expect(page.getByText('based on your recent requests')).toHaveCount(0);
    for (const heading of ['Commercial', 'Procurement', 'Contract changes']) {
      await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
    }

    const sowCard = page.locator('[data-ctp-card][data-contract-type="SOW"]');
    await expect(sowCard).toBeVisible();
    await expect(sowCard.getByText('Starting template')).toBeVisible();
    await expect(sowCard.getByText('Expected review')).toBeVisible();
    await expect(sowCard.getByText('Start request')).toBeVisible();
    await expect(sowCard).toHaveAttribute('aria-label', 'Start SOW request');

    await page.getByLabel('Search agreement types').fill('nda');
    await expect(page.locator('[data-ctp-card][data-contract-type="NDA"]')).toBeVisible();
    await expect(page.locator('[data-ctp-card][data-contract-type="SOW"]')).toBeHidden();
    await expect(page.getByRole('heading', { name: 'Commercial', exact: true })).toBeHidden();

    await page.getByLabel('Search agreement types').fill('zzzz-no-match');
    await expect(page.getByText('No agreement types match your search.')).toBeVisible();
  });

  for (const viewport of [
    { name: 'desktop', width: 1440, height: 1000, columns: 3 },
    { name: 'tablet', width: 900, height: 1000, columns: 2 },
    { name: 'mobile', width: 390, height: 844, columns: 1 },
  ]) {
    test(`keeps a left-aligned ${viewport.columns}-column grid on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await login(page);
      await page.goto('/contracts/new/start/');

      const layout = await page.locator('.ctp-entry-grid').first().evaluate((grid) => {
        const styles = getComputedStyle(grid);
        const cards = [...grid.querySelectorAll('[data-ctp-card]')];
        const tops = [...new Set(cards.map((card) => Math.round(card.getBoundingClientRect().top)))].sort(
          (a, b) => a - b,
        );
        const firstRow = cards.filter(
          (card) => Math.round(card.getBoundingClientRect().top) === tops[0],
        );
        const lefts = firstRow.map((card) => Math.round(card.getBoundingClientRect().left)).sort((a, b) => a - b);
        const gridLeft = Math.round(grid.getBoundingClientRect().left);
        return {
          template: styles.gridTemplateColumns,
          firstRowCount: firstRow.length,
          firstCardLeft: lefts[0],
          gridLeft,
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: document.documentElement.clientWidth,
        };
      });

      expect(layout.firstRowCount).toBe(viewport.columns);
      expect(Math.abs(layout.firstCardLeft - layout.gridLeft)).toBeLessThanOrEqual(2);
      expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth + 1);
    });
  }
});
