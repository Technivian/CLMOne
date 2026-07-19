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

async function fillField(page, key, value) {
  await page.locator(`[data-field-key="${key}"]`).fill(value);
}

async function continueStep(page) {
  await page.getByRole('button', { name: /^(Continue|Review and generate)$/ }).click();
}

async function reachStep3(page, counterparty) {
  await page.goto('/contracts/new/dpa/');
  await fillField(page, 'counterparty', counterparty);
  await fillField(page, 'contract_owner', 'Avery Brooks');
  await fillField(page, 'start_date', '2026-09-01');
  await continueStep(page);
  await expect(page).toHaveURL(/step=2/);
  await fillField(page, 'processing_purpose', 'Hosted logistics analytics and support.');
  await continueStep(page);
  await expect(page).toHaveURL(/step=3/);
}

test.describe('Phase 5G builder error and blocked states', () => {
  test('step 3 failed validation recovers after required answers', async ({ page }) => {
    await login(page);
    const suffix = Date.now().toString().slice(-6);
    await reachStep3(page, `E2E DPA Validate ${suffix}`);

    await continueStep(page);
    await expect(page.getByText('Step 3 of 4')).toBeVisible();
    await expect(page.locator('.dpa-field-error').first()).toBeVisible();
    await expect(page.getByText(/Select at least one data category/i).first()).toBeVisible();

    await page.locator('details.dpa-option-picker', { hasText: 'Choose data categories' }).locator('summary').click();
    await page.locator('label.dpa-option-picker-option', { hasText: 'Identity and contact details' }).click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data categories' }).locator('summary').click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data subjects' }).locator('summary').click();
    await page.locator('label.dpa-option-picker-option').filter({ hasText: /^Employees$/ }).click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data subjects' }).locator('summary').click();
    await page.locator('input[name="step3_sensitive_data"][value="no"]').check();
    await page.locator('input[name="step3_subprocessors"][value="no"]').check();
    await page.locator('[data-multiselect-search]').fill('Netherlands');
    await page.locator('.dpa-multiselect-option', { hasText: 'Netherlands' }).click();
    await page.locator('[data-multiselect-search]').focus();
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-multiselect-menu]')).toBeHidden();
    await continueStep(page);
    await expect(page).toHaveURL(/step=4/);
    await expect(page.getByText('Step 4 of 4')).toBeVisible();
  });

  test('review surfaces governance blocked findings and recovers via Back to edit', async ({ page }) => {
    test.slow();
    await login(page);
    const suffix = Date.now().toString().slice(-6);
    await reachStep3(page, `E2E DPA Blocked ${suffix}`);

    await page.locator('details.dpa-option-picker', { hasText: 'Choose data categories' }).locator('summary').click();
    await page.locator('label.dpa-option-picker-option', { hasText: 'Identity and contact details' }).click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data categories' }).locator('summary').click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data subjects' }).locator('summary').click();
    await page.locator('label.dpa-option-picker-option').filter({ hasText: /^Employees$/ }).click();
    await page.locator('details.dpa-option-picker', { hasText: 'Choose data subjects' }).locator('summary').click();
    await page.locator('input[name="step3_sensitive_data"][value="not_sure"]').check();
    await expect(page.locator('[data-step3-reveal="sensitive-data-uncertain"]')).toBeVisible();
    await page.locator('input[name="step3_subprocessors"][value="no"]').check();
    await page.locator('[data-multiselect-search]').fill('Netherlands');
    await page.locator('.dpa-multiselect-option', { hasText: 'Netherlands' }).click();
    await page.locator('[data-multiselect-search]').focus();
    await page.keyboard.press('Escape');
    await continueStep(page);
    await expect(page).toHaveURL(/step=4/);

    for (const name of [
      'step4_security_measures_provided',
      'step4_security_assurance_available',
      'step4_encryption_confirmed',
      'step4_access_controls_mfa_confirmed',
    ]) {
      await page.locator(`input[name="${name}"][value="yes"]`).check();
    }
    await page.fill('#step4-privacy-name', 'Jordan Lee');
    await page.fill('#step4-privacy-role', 'Privacy Officer');
    await page.fill('#step4-privacy-email', `privacy.${suffix}@example.com`);
    await page.locator('input[name="step4_breach_notification_commitment"][value="approved_standard"]').check();
    await page.locator('input[name="step4_governing_law_mode"][value="manual"]').check();
    await page.selectOption('#step4-governing-law', 'State of Delaware');
    for (const key of ['audit_rights', 'deletion_return', 'dpa_liability']) {
      await page.locator(`input[name="step4_${key}_position"][value="accepted"]`).check();
    }
    await page.getByRole('button', { name: 'Review and generate' }).click();

    await expect(page).toHaveURL(/\/contracts\/new\/dpa\/review\/?$/);
    await expect(page.getByText('Governance results')).toBeVisible();
    const blocked = page.locator('.dpa-finding', { hasText: 'Privacy review required' });
    await expect(blocked).toBeVisible();
    await expect(blocked.locator('.dpa-finding-status')).toHaveText(/Blocked/i);
    const back = page.getByRole('button', { name: 'Back to edit' });
    await back.focus();
    await expect(back).toBeFocused();

    await back.click();
    await expect(page).toHaveURL(/\/contracts\/new\/dpa\//);
    await expect(page.getByRole('navigation', { name: 'DPA intake steps' })).toBeVisible();
  });

  test('contract record shows deterministic signature routing blockers', async ({ page }) => {
    await login(page);
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto('/contracts/1/');
    await expect(page.locator('.dc-ds-workspace--record')).toBeVisible();
    const blockers = page.locator('[aria-label="Workflow blockers"]');
    await expect(blockers).toBeVisible();
    await expect(blockers.getByText('Blocked')).toHaveCount(2);
    await expect(blockers.locator('.dc-ds-badge--attention', { hasText: 'Blocked' })).toHaveCount(2);
    await expect(blockers.getByText('The contract must be fully approved before signature routing.')).toBeVisible();
    await expect(blockers.getByText('At least one approval is required before signature routing.')).toBeVisible();

    const primary = page.locator('.dc-ds-workspace--record .dc-ds-button--primary').first();
    await primary.focus();
    await expect(primary).toBeFocused();

    await page.setViewportSize({ width: 390, height: 844 });
    await page.reload();
    await expect(page.locator('[aria-label="Workflow blockers"]')).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    expect(dimensions.documentWidth).toBeLessThanOrEqual(dimensions.viewportWidth);
  });

  test('review without intake redirects with recovery messaging', async ({ page }) => {
    await login(page);
    await page.goto('/contracts/new/dpa/review/');
    await expect(page).toHaveURL(/\/contracts\/new\/dpa\/?/);
    await expect(page.getByText(/Start the DPA intake before reviewing/i)).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'DPA intake steps' })).toBeVisible();
  });
});
