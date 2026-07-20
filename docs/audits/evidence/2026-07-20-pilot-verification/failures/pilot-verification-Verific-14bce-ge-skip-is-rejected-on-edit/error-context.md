# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pilot-verification.spec.js >> Verification: lifecycle Stage vs Status >> invalid lifecycle stage skip is rejected on edit
- Location: tests/e2e/pilot-verification.spec.js:297:3

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - navigation "Primary navigation" [ref=e3]:
    - link "CLM One — go to dashboard" [ref=e5] [cursor=pointer]:
      - /url: /dashboard/
      - img "CLM One" [ref=e6]
    - button "Collapse sidebar" [expanded] [ref=e7] [cursor=pointer]:
      - img [ref=e8]
    - generic [ref=e11]:
      - link "Command Center" [ref=e12] [cursor=pointer]:
        - /url: /dashboard/
        - img [ref=e13]
        - generic [ref=e16]: Command Center
      - link "New Contract" [ref=e17] [cursor=pointer]:
        - /url: /contracts/new/start/
        - img [ref=e18]
        - generic [ref=e22]: New Contract
      - link "Upload & Review" [ref=e23] [cursor=pointer]:
        - /url: /contracts/new/upload/
        - img [ref=e24]
        - generic [ref=e27]: Upload & Review
      - link "Contracts" [ref=e28] [cursor=pointer]:
        - /url: /contracts/repository/
        - img [ref=e29]
        - generic [ref=e32]: Contracts
      - link "Workflow Operations" [ref=e33] [cursor=pointer]:
        - /url: /contracts/workflows/
        - img [ref=e34]
        - generic [ref=e37]: Workflow Operations
      - link "Workflow Designer" [ref=e38] [cursor=pointer]:
        - /url: /contracts/workflows/templates/
        - img [ref=e39]
        - generic [ref=e42]: Workflow Designer
      - link "DPA Reviews" [ref=e43] [cursor=pointer]:
        - /url: /contracts/dpa-reviews/
        - img [ref=e44]
        - generic [ref=e47]: DPA Reviews
      - link "Obligations" [ref=e48] [cursor=pointer]:
        - /url: /contracts/obligations/
        - img [ref=e49]
        - generic [ref=e53]: Obligations
    - link "E e2e_owner Workspace member" [ref=e55] [cursor=pointer]:
      - /url: /profile/
      - generic [ref=e56]: E
      - generic [ref=e57]: e2e_owner Workspace member
      - img [ref=e58]
  - generic [ref=e60]:
    - generic [ref=e61]:
      - generic "Current page" [ref=e62]:
        - generic [ref=e63]:
          - link "Back to contract" [ref=e64] [cursor=pointer]:
            - /url: /contracts/19/
            - img [ref=e65]
          - heading "Edit contract details" [level=1] [ref=e67]
          - generic [ref=e68]:
            - link "Cancel" [ref=e69] [cursor=pointer]:
              - /url: /contracts/19/
            - button "Save changes" [ref=e70] [cursor=pointer]
      - generic [ref=e73]:
        - img
        - searchbox "Search contracts and workflows…" [ref=e74]
      - generic [ref=e75]:
        - link "Notifications" [ref=e76] [cursor=pointer]:
          - /url: /contracts/notifications/
          - img [ref=e77]
        - button "E e2e_owner" [ref=e80] [cursor=pointer]:
          - generic [ref=e81]: E
          - generic [ref=e82]: e2e_owner
          - img [ref=e83]
    - generic [ref=e88]:
      - generic [ref=e89]:
        - generic "Contract edit context" [ref=e91]:
          - heading "Edit contract details" [level=2] [ref=e92]
          - generic [ref=e93]: Draft
          - generic [ref=e94]:
            - text: Stage ·
            - strong [ref=e95]: Drafting
          - generic [ref=e96]: ·
          - generic [ref=e97]:
            - text: Version ·
            - strong [ref=e98]: v1 (current record)
          - generic [ref=e99]: ·
          - generic [ref=e100]: 2 validation issues
          - generic [ref=e101]: ·
          - group [ref=e102]: View workflow
        - region "Contract identity" [ref=e103]:
          - generic [ref=e104]:
            - generic [ref=e105]:
              - generic [ref=e106]: "1"
              - generic [ref=e107]:
                - generic [ref=e108]: Contract details
                - heading "Contract identity" [level=2] [ref=e109]
            - generic [ref=e110]: Revision unlocked
          - generic [ref=e112]:
            - generic [ref=e113]:
              - generic [ref=e114]: Title *
              - textbox [ref=e115]: NDA — Life NDA 81994
            - generic [ref=e116]:
              - generic [ref=e117]: Contract type *
              - combobox [ref=e118] [cursor=pointer]:
                - option "Select contract type"
                - option "Non-Disclosure Agreement" [selected]
                - option "Non-Compete / Non-Solicitation Agreement"
                - option "Master Service Agreement"
                - option "Statement of Work"
                - option "Subcontractor SOW Agreement"
                - option "Consulting / Independent Contractor Agreement"
                - option "Employment Agreement"
                - option "Lease Agreement"
                - option "License Agreement"
                - option "SaaS Agreement"
                - option "Terms of Service / Terms & Conditions"
                - option "Vendor Agreement"
                - option "Purchase Order"
                - option "Order Confirmation"
                - option "Partnership Agreement"
                - option "Referral / Reseller / Channel Partner Agreement"
                - option "Settlement Agreement"
                - option "Amendment"
                - option "Data Processing Agreement"
                - option "Business Associate Agreement (BAA)"
                - option "Other"
            - generic [ref=e119]:
              - generic [ref=e120]: Counterparty *
              - textbox [ref=e121]: Life NDA 81994
            - generic [ref=e122]:
              - generic [ref=e123]:
                - text: Owner
                - 'button "More information: Active workspace member accountable for this contract." [ref=e125]':
                  - generic [ref=e126]: i
              - combobox [ref=e127] [cursor=pointer]:
                - option "---------" [selected]
                - option "e2e_owner"
                - option "Finance"
                - option "Legal"
            - generic [ref=e128]:
              - generic [ref=e129]: Client
              - combobox [ref=e130] [cursor=pointer]:
                - option "---------" [selected]
                - option "E2E Fixture Client"
            - generic [ref=e131]:
              - generic [ref=e132]: Matter
              - combobox [ref=e133] [cursor=pointer]:
                - option "---------" [selected]
                - option "E2E-0001 - E2E Fixture Matter"
        - group [ref=e134]:
          - generic "Legal posture Commercial terms and jurisdiction Routes review" [ref=e135] [cursor=pointer]:
            - generic [ref=e136]:
              - generic [ref=e137]: "2"
              - generic [ref=e138]:
                - generic [ref=e139]: Legal posture
                - heading "Commercial terms and jurisdiction" [level=2] [ref=e140]
            - generic [ref=e141]:
              - img [ref=e142]
              - text: Routes review
          - option "USD ($)" [selected]
          - option "EUR (€)"
          - option "GBP (£)"
          - option "CHF (Fr)"
          - option "CAD (C$)"
          - option "AUD (A$)"
          - option "Other"
          - option "Select paper source" [selected]
          - option "Our paper"
          - option "Counterparty paper"
        - region "Review triggers" [ref=e144]:
          - generic [ref=e145]:
            - generic [ref=e146]:
              - generic [ref=e147]: "3"
              - generic [ref=e148]:
                - generic [ref=e149]: Privacy & risk
                - heading "Review triggers" [level=2] [ref=e150]
            - generic [ref=e151]: Controls routing
          - generic [ref=e153]:
            - generic [ref=e154]:
              - 'checkbox "Will this agreement involve processing personal data? More information: Include personal data handled by either party under this agreement." [ref=e155] [cursor=pointer]'
              - generic [ref=e157]: Will this agreement involve processing personal data?
              - 'button "More information: Include personal data handled by either party under this agreement." [ref=e159]':
                - generic [ref=e160]: i
            - generic [ref=e161]:
              - 'checkbox "Is the data sensitive, high-volume, or handled in a non-standard way? More information: For example, special-category data, large-scale processing, profiling, or unusual processing terms." [ref=e162] [cursor=pointer]'
              - generic [ref=e164]: Is the data sensitive, high-volume, or handled in a non-standard way?
              - 'button "More information: For example, special-category data, large-scale processing, profiling, or unusual processing terms." [ref=e166]':
                - generic [ref=e167]: i
            - generic [ref=e168]:
              - 'checkbox "Has the counterparty asked for privacy review? More information: Confirm this when the counterparty requires privacy or data-protection review." [ref=e169] [cursor=pointer]'
              - generic [ref=e171]: Has the counterparty asked for privacy review?
              - 'button "More information: Confirm this when the counterparty requires privacy or data-protection review." [ref=e173]':
                - generic [ref=e174]: i
            - generic [ref=e175]:
              - 'checkbox "Will this agreement involve transferring personal data across borders? More information: For example, personal data moving between the UK, EU, US, or another country." [ref=e176] [cursor=pointer]'
              - generic [ref=e178]: Will this agreement involve transferring personal data across borders?
              - 'button "More information: For example, personal data moving between the UK, EU, US, or another country." [ref=e180]':
                - generic [ref=e181]: i
            - generic [ref=e182]:
              - 'checkbox "Is a data processing agreement already included? More information: Confirm this only when the approved processor terms or DPA are included." [ref=e183] [cursor=pointer]'
              - generic [ref=e185]: Is a data processing agreement already included?
              - 'button "More information: Confirm this only when the approved processor terms or DPA are included." [ref=e187]':
                - generic [ref=e188]: i
            - generic [ref=e189]:
              - 'checkbox "Are standard contractual clauses already included? More information: Confirm SCCs, an adequacy mechanism, or another approved transfer safeguard." [ref=e190] [cursor=pointer]'
              - generic [ref=e192]: Are standard contractual clauses already included?
              - 'button "More information: Confirm SCCs, an adequacy mechanism, or another approved transfer safeguard." [ref=e194]':
                - generic [ref=e195]: i
        - group [ref=e196]:
          - generic "Lifecycle control Dates and lifecycle management Creates obligations" [ref=e197] [cursor=pointer]:
            - generic [ref=e198]:
              - generic [ref=e199]: "4"
              - generic [ref=e200]:
                - generic [ref=e201]: Lifecycle control
                - heading "Dates and lifecycle management" [level=2] [ref=e202]
            - generic [ref=e203]:
              - img [ref=e204]
              - text: Creates obligations
          - generic [ref=e207]:
            - generic [ref=e208]:
              - generic [ref=e209]: Effective date
              - textbox [ref=e210]: 2026-10-01
            - generic [ref=e211]:
              - generic [ref=e212]: Expiry date
              - textbox [ref=e213]
            - generic [ref=e214]:
              - generic [ref=e215]: Renewal date
              - textbox [ref=e216]
            - generic [ref=e217]:
              - generic [ref=e218]: Notice period days
              - spinbutton [ref=e219]
            - generic [ref=e220]:
              - generic [ref=e221]: Notice deadline
              - textbox [ref=e222]
            - generic [ref=e223]:
              - checkbox "Auto renew" [ref=e224] [cursor=pointer]
              - generic [ref=e226]: Auto renew
        - group [ref=e227]:
          - generic "Draft brief Source text and drafting instructions Optional" [ref=e228] [cursor=pointer]:
            - generic [ref=e229]:
              - generic [ref=e230]: "5"
              - generic [ref=e231]:
                - generic [ref=e232]: Draft brief
                - heading "Source text and drafting instructions" [level=2] [ref=e233]
            - generic [ref=e234]:
              - img [ref=e235]
              - text: Optional
        - group [ref=e237]:
          - generic "Advanced options Clause templates, governing law…" [ref=e238] [cursor=pointer]:
            - text: Advanced options
            - generic [ref=e239]:
              - img [ref=e240]
              - text: Clause templates, governing law…
          - option "E2E Local Indemnity Clause (v1, Uncategorized)"
      - generic [ref=e242]:
        - generic [ref=e243]:
          - generic [ref=e245]: Contract state
          - generic [ref=e247]:
            - generic [ref=e248]:
              - term [ref=e249]: Contract state
              - definition [ref=e250]: Draft
            - generic [ref=e251]:
              - term [ref=e252]: Current stage
              - definition [ref=e253]: Drafting
            - generic [ref=e254]:
              - term [ref=e255]: Version
              - definition [ref=e256]: v1 (current record)
            - generic [ref=e257]:
              - term [ref=e258]: Change impact
              - definition [ref=e259]: Draft record — changes save in place.
            - generic [ref=e260]:
              - term [ref=e261]: Risk reassessment
              - definition [ref=e262]:
                - generic [ref=e263]: Low risk
                - text: Stored risk level for this contract.
            - generic [ref=e264]:
              - term [ref=e265]: Approval impact
              - definition [ref=e266]: Risk and routing update when governed inputs change.
            - generic [ref=e267]:
              - term [ref=e268]: Validation issues
              - definition [ref=e269]:
                - list [ref=e270]:
                  - listitem [ref=e271]: Contract owner is missing.
                  - listitem [ref=e272]: Expiry date is missing.
        - generic [ref=e273]:
          - generic [ref=e274]:
            - generic [ref=e275]: Original configuration
            - paragraph [ref=e276]: Read-only after creation
          - generic [ref=e278]:
            - generic [ref=e279]:
              - term [ref=e280]: Starting template
              - definition [ref=e281]: Standard Mutual NDA
            - generic [ref=e282]:
              - term [ref=e283]: Playbook
              - definition [ref=e284]: Standard NDA playbook
            - generic [ref=e285]:
              - term [ref=e286]: Contract type
              - definition [ref=e287]: Non-Disclosure Agreement
            - generic [ref=e288]:
              - term [ref=e289]: Paper source
              - definition [ref=e290]: Not set
```

# Test source

```ts
  262 | 
  263 | test.describe('Verification: search fixtures and tenancy', () => {
  264 |   for (const fixture of ['valid', 'list', 'malformed', 'empty', 'error', 'timeout', 'keyword']) {
  265 |     test(`semantic fixture ${fixture} does not 500`, async ({ page }) => {
  266 |       await login(page);
  267 |       const response = await page.goto(
  268 |         `/contracts/search/?q=e2e_fixture:${fixture}&search_mode=semantic`,
  269 |       );
  270 |       expect(response.status()).toBeLessThan(500);
  271 |       await expect(page).not.toHaveURL(/\/login\/?$/);
  272 |       await expect(page.locator('body')).toContainText(/Search|result|clause|No /i);
  273 |       await expect(page.getByRole('link', { name: 'FOREIGN_TENANT_SECRET_CLAUSE_E2E' })).toHaveCount(0);
  274 |     });
  275 |   }
  276 | 
  277 |   test('cross-tenant clause title is excluded from results', async ({ page }) => {
  278 |     await login(page);
  279 |     await page.goto('/contracts/search/?q=FOREIGN_TENANT_SECRET_CLAUSE_E2E&search_mode=keyword');
  280 |     await expect(page.getByRole('link', { name: 'FOREIGN_TENANT_SECRET_CLAUSE_E2E' })).toHaveCount(0);
  281 |     await expect(page.locator('article, .search-hit, .list-row').filter({ hasText: 'FOREIGN_TENANT_SECRET_CLAUSE_E2E' })).toHaveCount(0);
  282 |     await page.goto('/contracts/search/?q=E2E%20Local%20Indemnity%20Clause&search_mode=keyword');
  283 |     await expect(page.locator('body')).toContainText(/E2E Local Indemnity Clause/i);
  284 |   });
  285 | });
  286 | 
  287 | test.describe('Verification: lifecycle Stage vs Status', () => {
  288 |   test('repository Stage sort and Status filter controls', async ({ page }) => {
  289 |     await login(page);
  290 |     await page.goto('/contracts/repository/');
  291 |     await expect(page.locator('button.repo-sort-btn[data-sort="stage"]')).toBeVisible();
  292 |     await page.locator('button.repo-sort-btn[data-sort="stage"]').click();
  293 |     await expect(page).toHaveURL(/sort|stage/);
  294 |     await expect(page.locator('body')).toContainText(/Stage|Status|Contract/i);
  295 |   });
  296 | 
  297 |   test('invalid lifecycle stage skip is rejected on edit', async ({ page }) => {
  298 |     test.slow();
  299 |     await login(page);
  300 |     const suffix = Date.now().toString().slice(-5);
  301 |     await page.goto('/contracts/new/nda/');
  302 |     await page.fill('[data-field-key="counterparty"]', `Life NDA ${suffix}`);
  303 |     await page.fill('[data-field-key="start_date"]', '2026-10-01');
  304 |     await page.fill('[data-field-key="contract_owner"]', 'Avery Brooks');
  305 |     await page.fill('[data-field-key="business_unit"]', 'Revenue Operations');
  306 |     await page.fill('[data-field-key="internal_reference"]', `NDA-L-${suffix}`);
  307 |     await page.selectOption('[data-field-key="nda_type"]', 'Mutual');
  308 |     await page.fill('[data-field-key="confidentiality_purpose"]', 'product diligence');
  309 |     await page.fill('[data-field-key="confidentiality_period"]', '2');
  310 |     await page.fill('[data-field-key="disclosure_scope"]', 'technical architecture');
  311 |     await page.fill('[data-field-key="permitted_recipients"]', 'employees');
  312 |     await page.fill('[data-field-key="governing_law"]', 'Netherlands');
  313 |     await page.fill('[data-field-key="jurisdiction"]', 'Amsterdam');
  314 |     await page.check('[data-field-key="injunctive_relief_included"]');
  315 |     await page.click('#submit-nda-btn');
  316 |     await expect(page).toHaveURL(/\/contracts\/workflows\/\d+/);
  317 |     await page.getByRole('link', { name: 'View contract record' }).click();
  318 |     await expect(page).toHaveURL(/\/contracts\/\d+\/?$/);
  319 |     const detailUrl = page.url().replace(/\/$/, '');
  320 |     const editUrl = `${detailUrl}/edit/`;
  321 |     await page.goto(editUrl);
  322 |     await expect(page).toHaveURL(/\/edit\/?/);
  323 | 
  324 |     // Prove lifecycle rejection (not CSRF failure): include cookie + form token.
  325 |     const result = await page.evaluate(async (url) => {
  326 |       const form = document.querySelector('form[method="post"], form');
  327 |       if (!form) return { ok: false, reason: 'missing-form' };
  328 |       const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
  329 |       const cookieMatch = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  330 |       const csrf =
  331 |         (csrfInput && csrfInput.value) ||
  332 |         (cookieMatch ? decodeURIComponent(cookieMatch[1]) : '');
  333 |       if (!csrf) return { ok: false, reason: 'missing-csrf' };
  334 |       const data = new FormData(form);
  335 |       data.set('csrfmiddlewaretoken', csrf);
  336 |       data.set('lifecycle_stage', 'SIGNATURE');
  337 |       const response = await fetch(url, {
  338 |         method: 'POST',
  339 |         body: data,
  340 |         credentials: 'same-origin',
  341 |         redirect: 'manual',
  342 |         headers: {
  343 |           'X-CSRFToken': csrf,
  344 |           'X-Requested-With': 'XMLHttpRequest',
  345 |         },
  346 |       });
  347 |       const text = await response.text();
  348 |       const rejectedByLifecycle =
  349 |         /invalid lifecycle|lifecycle stage|not allowed|cannot transition|correct the error/i.test(text);
  350 |       return {
  351 |         ok: true,
  352 |         status: response.status,
  353 |         rejectedByLifecycle,
  354 |         stillOnEdit: /\/edit\/?/.test(response.url || '') || response.url.includes('/edit'),
  355 |         csrfBlocked: response.status === 403 && /csrf/i.test(text),
  356 |       };
  357 |     }, editUrl);
  358 | 
  359 |     expect(result.ok).toBeTruthy();
  360 |     expect(result.reason || null).toBeNull();
  361 |     expect(result.csrfBlocked).toBeFalsy();
> 362 |     expect(result.rejectedByLifecycle).toBeTruthy();
      |                                        ^ Error: expect(received).toBeTruthy()
  363 |     expect(result.status).toBeGreaterThanOrEqual(200);
  364 |   });
  365 | });
  366 | 
```