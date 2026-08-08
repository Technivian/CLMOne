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

test('Command Center demo shows DPA, MSA, and NDA workflows with workspace links', async ({ page }) => {
  test.slow();
  await login(page);

  await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
  await expect(page.locator('section[aria-label="Operational queues"]')).toBeVisible();
  await expect(page.getByText('Governance controls')).toBeVisible();

  const priority = page.getByRole('link', { name: 'Northwind DPA Privacy Review Workflow' });
  await expect(priority).toBeVisible();
  await expect(priority).toHaveAttribute('href', /\/contracts\/workflows\/\d+\/?$/);

  const msaAction = page.locator('.cc-v3-portfolio-action-list .cc-v3-operational-row').filter({ hasText: 'Acme MSA' });
  await expect(msaAction).toBeVisible();
  await expect(msaAction).toHaveAttribute('href', /^\/contracts\//);

  const ndaWorkspace = page.getByRole('link', { name: /Brightlane NDA Self-Serve Workflow/ });
  await expect(ndaWorkspace).toBeVisible();
  await ndaWorkspace.click();
  await expect(page).toHaveURL(/\/contracts\/workflows\/\d+\/?$/);
  await expect(page.getByText(/Guided drafting/i).first()).toBeVisible();
});
