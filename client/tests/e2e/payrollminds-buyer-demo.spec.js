const { test, expect } = require('@playwright/test');

const username = 'payrollminds_admin';
// Local-only synthetic seed fixture; this is deliberately not a customer
// credential and may be overridden by the isolated E2E environment.
const password = process.env.PAYROLLMINDS_DEMO_PASSWORD || 'payrollminds-demo-2026!';

async function login(page) {
  await page.goto('/login/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).not.toHaveURL(/\/login\/?$/);
}

async function openRepositoryContract(page, title) {
  await page.goto(`/contracts/repository/?q=${encodeURIComponent(title)}`);
  // Repository records are keyboard-operable rows. The title is deliberately
  // not an extra nested link, which avoids competing click targets in the
  // dense canonical table.
  const row = page.locator('.contract-row', { hasText: title });
  await expect(row).toBeVisible();
  await row.click();
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
}

test('Payrollminds buyer demo tells a complete contract lifecycle story', async ({ page }) => {
  test.slow();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);

  await page.goto('/contracts/repository/');
  await expect(page.locator('.topbar-page-title')).toHaveText('Contracts');
  for (const title of [
    'Payrollminds Master Services Agreement',
    'Global Payroll Transformation Engagement — Implementation SOW',
    'Consultancy Services Agreement — HRIS rollout',
    'Data Processing Agreement — Cloud payroll',
    'Mutual NDA — FinTalent partnership',
    'Addendum — 2026 pricing and service levels',
  ]) {
    await expect(page.locator('.contract-row', { hasText: title })).toBeVisible();
  }

  await openRepositoryContract(page, 'Payrollminds Master Services Agreement');
  await expect(page.getByText('Related records', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: /Global Payroll Transformation Engagement — Implementation SOW/ })).toBeVisible();
  await expect(
    page.locator('#contract-tab-overview').getByText('Payrollminds MSA — executed agreement', { exact: true }),
  ).toBeVisible();

  await page.getByRole('tab', { name: 'Documents' }).click();
  await expect(page.getByText('Payrollminds MSA — negotiated draft', { exact: true })).toBeVisible();
  await expect(
    page.locator('#contract-tab-documents').getByText('Payrollminds MSA — executed agreement', { exact: true }),
  ).toBeVisible();

  await page.getByRole('tab', { name: 'Workflow' }).click();
  await expect(page.getByRole('region', { name: 'Full workflow' })).toBeVisible();
  await expect(page.getByText('Signature requirement', { exact: true })).toBeVisible();
  await expect(page.getByText('At least one approval is required before signature routing.', { exact: true }).first()).toBeVisible();

  await openRepositoryContract(page, 'Global Payroll Transformation Engagement — Implementation SOW');
  await expect(page.getByRole('link', { name: 'Governing agreement: Payrollminds Master Services Agreement' })).toBeVisible();
  await page.getByRole('tab', { name: 'Workflow' }).click();
  await expect(page.getByRole('region', { name: 'Full workflow' })).toBeVisible();
  await expect(page.getByText('Current stage', { exact: true })).toBeVisible();
  await expect(page.getByText('Approval', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Run contract review before submitting for approval.', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('All open approval requirements must be satisfied before signature routing.', { exact: true })).toBeVisible();

  await page.goto('/contracts/dpa-reviews/');
  const dpaLink = page.getByRole('link', { name: 'Data Processing Agreement — Cloud payroll', exact: true });
  await expect(dpaLink).toBeVisible();
  await dpaLink.click();
  await expect(page.getByText('DPA overrides the MSA liability cap', { exact: true })).toBeVisible();
  await expect(page.getByText('24-hour breach notice is operationally unrealistic', { exact: true })).toBeVisible();
  await expect(page.getByText('Payrollminds Master Services Agreement', { exact: true })).toBeVisible();

  await page.goto('/contracts/obligations/');
  for (const obligation of [
    'MSA renewal and notice decision',
    'Review next subprocessor notification',
    'Approve HRIS discovery milestone',
    'Review 2027 pricing indexation',
    'Confirm NDA term before partnership launch',
  ]) {
    await expect(page.getByText(obligation, { exact: true })).toBeVisible();
  }
});

test('Payrollminds repository and contract detail fit a 390 px mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);

  for (const path of ['/contracts/repository/', '/contracts/obligations/']) {
    await page.goto(path);
    // Dense canonical list tables preserve all governed columns in an
    // internal horizontal-scroll region on a phone; they do not widen the
    // visible application shell. Wait for the table's rows before measuring.
    const tableWrap = page.locator('.dc-ds-table-wrap').first();
    await expect(tableWrap).toBeVisible();
    const layout = await tableWrap.evaluate((wrap) => ({
      clientWidth: wrap.clientWidth,
      scrollWidth: wrap.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      pageOverflow: getComputedStyle(document.body).overflowX,
    }));
    expect(layout.clientWidth, `${path} table-wrap width`).toBeLessThanOrEqual(layout.viewportWidth);
    expect(layout.scrollWidth, `${path} internal table scroll`).toBeGreaterThan(layout.clientWidth);
    expect(layout.pageOverflow, `${path} page overflow containment`).toBe('hidden');
  }

  await openRepositoryContract(page, 'Payrollminds Master Services Agreement');
  const widths = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
    body: document.body.scrollWidth,
  }));
  expect(widths.document, 'contract detail document overflow').toBeLessThanOrEqual(widths.viewport);
  expect(widths.body, 'contract detail body overflow').toBeLessThanOrEqual(widths.viewport);

  await page.locator('#mobileNavToggle').click();
  await expect(page.locator('.sidebar-brand .logo-wordmark')).toBeHidden();
  await expect(page.locator('.sidebar-brand .logo-mark')).toBeVisible();
});
