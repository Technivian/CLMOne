# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: pilot-verification.spec.js >> Verification: MSA finance threshold matrix >> Finance action absent below $100000 and present at/above threshold
- Location: tests/e2e/pilot-verification.spec.js:147:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator:  getByText(/MSA submitted to .* for review|Finance|approval/i).first()
Expected: visible
Received: hidden
Timeout:  8000ms

Call log:
  - Expect "toBeVisible" with timeout 8000ms
  - waiting for getByText(/MSA submitted to .* for review|Finance|approval/i).first()
    12 × locator resolved to <p class="dc-ds-shell__page-subtitle topbar-page-subtitle">Drafting · Review Finance approval route</p>
       - unexpected value "hidden"

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
          - link "Back to workflows" [ref=e64] [cursor=pointer]:
            - /url: /contracts/workflows/
            - img [ref=e65]
          - heading "MSA · Exact Thr 21212" [level=1] [ref=e67]
      - generic [ref=e70]:
        - img
        - searchbox "Search contracts and workflows…" [ref=e71]
      - generic [ref=e72]:
        - link "Notifications" [ref=e73] [cursor=pointer]:
          - /url: /contracts/notifications/
          - img [ref=e74]
        - button "E e2e_owner" [ref=e77] [cursor=pointer]:
          - generic [ref=e78]: E
          - generic [ref=e79]: e2e_owner
          - img [ref=e80]
    - generic [ref=e83]:
      - generic [ref=e84]:
        - generic [ref=e85]:
          - generic [ref=e87]:
            - heading "MSA · Exact Thr 21212" [level=1] [ref=e88]
            - generic "Contract status" [ref=e89]:
              - generic [ref=e90]: High risk
              - button "1 open exception" [ref=e91] [cursor=pointer]:
                - generic [ref=e92]: 1 open exception
          - generic [ref=e93]:
            - button "Review Finance approval route" [ref=e94] [cursor=pointer]
            - group [ref=e95]:
              - generic "Actions" [ref=e96] [cursor=pointer]
        - generic [ref=e97]:
          - generic [ref=e98]:
            - generic [ref=e99]: Current stage
            - generic [ref=e100]: Drafting
          - generic [ref=e101]:
            - generic [ref=e102]: Owner
            - generic [ref=e103]: e2e_owner
          - generic [ref=e104]:
            - generic [ref=e105]: Risk
            - generic [ref=e106]: High
          - generic [ref=e107]:
            - generic [ref=e108]: Next action
            - generic [ref=e109]: Review Finance approval route
      - region "Lifecycle stages" [ref=e110]:
        - generic [ref=e111]: Lifecycle
        - generic [ref=e112]:
          - generic [ref=e113]:
            - generic [ref=e114]: ✓
            - generic [ref=e115]: Intake
          - generic [ref=e116]:
            - generic [ref=e117]: "2"
            - generic [ref=e118]: Drafting
          - generic [ref=e119]:
            - generic [ref=e120]: "3"
            - generic [ref=e121]: Commercial review
          - generic [ref=e122]:
            - generic [ref=e123]: "4"
            - generic [ref=e124]: Legal review
          - generic [ref=e125]:
            - generic [ref=e126]: "5"
            - generic [ref=e127]: Finance approval
          - generic [ref=e128]:
            - generic [ref=e129]: "6"
            - generic [ref=e130]: Signature
          - generic [ref=e131]:
            - generic [ref=e132]: "7"
            - generic [ref=e133]: Active
        - generic [ref=e134]:
          - generic [ref=e135]:
            - generic [ref=e136]: Active stage owner
            - strong [ref=e137]: e2e_owner
          - generic [ref=e138]:
            - generic [ref=e139]: Status
            - strong [ref=e140]: In Progress
      - generic [ref=e141]:
        - tabpanel [ref=e142]:
          - generic [ref=e143]:
            - generic [ref=e144]:
              - generic [ref=e145]:
                - generic [ref=e146]: Guided drafting
                - paragraph [ref=e147]: Section status drives the next review move. Provenance stays secondary.
              - generic [ref=e148]: 10 sections
            - generic [ref=e150]:
              - group [ref=e151]:
                - generic "Generated MSA draft Approved template Complete" [ref=e152] [cursor=pointer]:
                  - generic [ref=e153]:
                    - generic [ref=e154]: Generated MSA draft
                    - generic [ref=e155]: Approved template
                  - generic [ref=e156]: Complete
                - generic [ref=e157]:
                  - generic [ref=e158]: Enterprise Services MSA · Netherlands · B2B
                  - generic [ref=e159]:
                    - generic [ref=e160]: Counterparty name
                    - generic [ref=e161]: Effective date
                  - link "Open in contract preview" [ref=e162] [cursor=pointer]:
                    - /url: "#generated-msa-draft"
              - group [ref=e163]:
                - generic "MSA clause Approved template Complete" [ref=e164] [cursor=pointer]:
                  - generic [ref=e165]:
                    - generic [ref=e166]: MSA clause
                    - generic [ref=e167]: Approved template
                  - generic [ref=e168]: Complete
              - group [ref=e169]:
                - generic "Services AI-assisted suggestion Complete" [ref=e170] [cursor=pointer]:
                  - generic [ref=e171]:
                    - generic [ref=e172]: Services
                    - generic [ref=e173]: AI-assisted suggestion
                  - generic [ref=e174]: Complete
              - group [ref=e175]:
                - generic "Fees and Payment Approved template Exception" [ref=e176] [cursor=pointer]:
                  - generic [ref=e177]:
                    - generic [ref=e178]: Fees and Payment
                    - generic [ref=e179]: Approved template
                  - generic [ref=e180]: Exception
              - group [ref=e181]:
                - generic "Term and Renewal Approved template Complete" [ref=e182] [cursor=pointer]:
                  - generic [ref=e183]:
                    - generic [ref=e184]: Term and Renewal
                    - generic [ref=e185]: Approved template
                  - generic [ref=e186]: Complete
              - group [ref=e187]:
                - generic "Liability Approved clause library Complete" [ref=e188] [cursor=pointer]:
                  - generic [ref=e189]:
                    - generic [ref=e190]: Liability
                    - generic [ref=e191]: Approved clause library
                  - generic [ref=e192]: Complete
              - group [ref=e193]:
                - generic "Intellectual Property Approved clause library Complete" [ref=e194] [cursor=pointer]:
                  - generic [ref=e195]:
                    - generic [ref=e196]: Intellectual Property
                    - generic [ref=e197]: Approved clause library
                  - generic [ref=e198]: Complete
              - group [ref=e199]:
                - generic "Data Protection Approved template Complete" [ref=e200] [cursor=pointer]:
                  - generic [ref=e201]:
                    - generic [ref=e202]: Data Protection
                    - generic [ref=e203]: Approved template
                  - generic [ref=e204]: Complete
              - group [ref=e205]:
                - generic "Governing Law Approved template Complete" [ref=e206] [cursor=pointer]:
                  - generic [ref=e207]:
                    - generic [ref=e208]: Governing Law
                    - generic [ref=e209]: Approved template
                  - generic [ref=e210]: Complete
              - group [ref=e211]:
                - generic "MSA clause Approved template Complete" [ref=e212] [cursor=pointer]:
                  - generic [ref=e213]:
                    - generic [ref=e214]: MSA clause
                    - generic [ref=e215]: Approved template
                  - generic [ref=e216]: Complete
        - tabpanel [ref=e217]:
          - generic [ref=e218]:
            - generic [ref=e219]:
              - generic [ref=e220]:
                - generic [ref=e221]: Live contract preview
                - paragraph [ref=e222]: Synced with the selected drafting section. Exception and changed clauses are highlighted.
              - generic [ref=e223]:
                - generic [ref=e224]: Version 1
                - button "Expand" [ref=e225] [cursor=pointer]
            - generic [ref=e227]:
              - article [ref=e228]:
                - generic [ref=e229]:
                  - generic [ref=e230]: Generated MSA draft
                  - generic [ref=e231]: Complete
                - paragraph [ref=e232]: MASTER SERVICES AGREEMENT
              - article [ref=e233]:
                - generic [ref=e234]:
                  - generic [ref=e235]: MSA clause
                  - generic [ref=e236]: Complete
                - paragraph [ref=e237]: "This Master Services Agreement is entered into between Payrollminds B.V. and Exact Thr 21212 as of October 01, 2026. Client contact: Nina van Dijk (nina.vandijk@example.com)."
              - article [ref=e238]:
                - generic [ref=e239]:
                  - generic [ref=e240]: Services
                  - generic [ref=e241]: Complete
                - paragraph [ref=e242]:
                  - text: 1. Services
                  - text: "Payrollminds shall provide Advisory services described in Threshold verification services. and any applicable Order Confirmation. Worker classification: . Payrollminds Professional involved: False."
              - article [ref=e243]:
                - generic [ref=e244]:
                  - generic [ref=e245]: Fees and Payment
                  - generic [ref=e246]: Exception
                - paragraph [ref=e247]:
                  - text: 2. Fees and Payment
                  - text: "The total contract value is 100000 EUR. Rate: . Payment terms are Net 30. Travel or kilometre rate: . Administrative fee: ."
              - article [ref=e248]:
                - generic [ref=e249]:
                  - generic [ref=e250]: Term and Renewal
                  - generic [ref=e251]: Complete
                - paragraph [ref=e252]:
                  - text: 3. Term and Renewal
                  - text: "This Agreement starts on October 01, 2026 and continues for 12 months. End date: . Renewal type: Manual renewal. Termination notice period: 30 days."
              - article [ref=e253]:
                - generic [ref=e254]:
                  - generic [ref=e255]: Liability
                  - generic [ref=e256]: Complete
                - paragraph [ref=e257]:
                  - text: 4. Liability
                  - text: Supplier's liability is capped at 1x annual fees, except for excluded claims.
              - article [ref=e258]:
                - generic [ref=e259]:
                  - generic [ref=e260]: Intellectual Property
                  - generic [ref=e261]: Complete
                - paragraph [ref=e262]:
                  - text: 5. Intellectual Property
                  - text: "IP ownership position: Provider."
              - article [ref=e263]:
                - generic [ref=e264]:
                  - generic [ref=e265]: Data Protection
                  - generic [ref=e266]: Complete
                - paragraph [ref=e267]:
                  - text: 6. Data Protection
                  - text: No personal data processing terms are currently required under this draft.
              - article [ref=e268]:
                - generic [ref=e269]:
                  - generic [ref=e270]: Governing Law
                  - generic [ref=e271]: Complete
                - paragraph [ref=e272]:
                  - text: 7. Governing Law
                  - text: "This Agreement is governed by the laws of Netherlands. Jurisdiction: Amsterdam."
              - article [ref=e273]:
                - generic [ref=e274]:
                  - generic [ref=e275]: MSA clause
                  - generic [ref=e276]: Complete
                - paragraph [ref=e277]: 8. Special Conditions
    - contentinfo [ref=e278]:
      - text: © 2026 CLM One B.V. All rights reserved.
      - link "Privacy Policy" [ref=e279] [cursor=pointer]:
        - /url: /privacy/
      - text: ·
      - link "Terms of Service" [ref=e280] [cursor=pointer]:
        - /url: /terms/
```

# Test source

```ts
  70  |   await selectField(page, 'currency', 'EUR');
  71  |   await fillField(page, 'payment_terms', 'Net 30');
  72  |   await fillField(page, 'initial_term', '12 months');
  73  |   await selectField(page, 'renewal_type', 'Manual renewal');
  74  |   await fillField(page, 'termination_notice_period', '30');
  75  |   await fillField(page, 'consultant_service_type', 'Advisory');
  76  |   await fillField(page, 'services_description', 'Threshold verification services.');
  77  |   await fillField(page, 'governing_law', 'Netherlands');
  78  |   await fillField(page, 'jurisdiction', 'Amsterdam');
  79  |   await fillField(page, 'liability_cap', '1x annual fees');
  80  |   await fillField(page, 'confidentiality_period', '3 years');
  81  |   await selectField(page, 'ip_ownership', 'Provider');
  82  |   await checkField(page, 'sow_required');
  83  |   await checkField(page, 'deliverables_defined');
  84  |   await checkField(page, 'acceptance_criteria_required');
  85  |   if (confirmThreshold) {
  86  |     await checkField(page, 'value_above_threshold_confirmed');
  87  |   }
  88  |   await page.click('#submit-msa-btn');
  89  |   await expect(page).toHaveURL(/\/contracts\/workflows\/\d+/, { timeout: 30000 });
  90  | }
  91  | 
  92  | test.describe('Verification: authentication', () => {
  93  |   test('logout returns to login and blocks dashboard', async ({ page }) => {
  94  |     await login(page);
  95  |     await page.getByRole('button', { name: /e2e_owner/i }).click();
  96  |     await Promise.all([
  97  |       page.waitForURL(/\/(login\/?)?$/),
  98  |       page.getByRole('menuitem', { name: 'Sign out' }).click(),
  99  |     ]);
  100 |     // LOGOUT_REDIRECT_URL is '/' — unauthenticated dashboard must bounce to login.
  101 |     await page.goto('/dashboard/');
  102 |     await expect(page).toHaveURL(/\/login\/?/);
  103 |   });
  104 | 
  105 |   test('session idle expiry redirects to login', async ({ page }) => {
  106 |     await login(page);
  107 |     await page.goto('/dashboard/?e2e_force_idle=1');
  108 |     await expect(page).toHaveURL(/\/login\/?/);
  109 |   });
  110 | 
  111 |   test('unrelated IP is not blocked by another IP counter', async ({ page, request }) => {
  112 |     await page.goto('/login/');
  113 |     const csrf = await page.locator('input[name="csrfmiddlewaretoken"]').inputValue();
  114 |     const cookies = await page.context().cookies();
  115 |     const cookieHeader = cookies.map((c) => `${c.name}=${c.value}`).join('; ');
  116 |     const blockedIp = `198.51.100.${Math.floor(Math.random() * 50) + 10}`;
  117 |     const otherIp = `198.51.100.${Math.floor(Math.random() * 50) + 60}`;
  118 |     let saw429 = false;
  119 |     for (let i = 0; i < 8; i += 1) {
  120 |       const response = await request.post('/login/', {
  121 |         form: { username: 'nobody', password: 'wrong', csrfmiddlewaretoken: csrf },
  122 |         headers: {
  123 |           'X-Forwarded-For': blockedIp,
  124 |           Cookie: cookieHeader,
  125 |           Referer: 'http://127.0.0.1:8010/login/',
  126 |         },
  127 |       });
  128 |       if (response.status() === 429) {
  129 |         saw429 = true;
  130 |         break;
  131 |       }
  132 |     }
  133 |     expect(saw429).toBeTruthy();
  134 |     const other = await request.post('/login/', {
  135 |       form: { username: 'nobody', password: 'wrong', csrfmiddlewaretoken: csrf },
  136 |       headers: {
  137 |         'X-Forwarded-For': otherIp,
  138 |         Cookie: cookieHeader,
  139 |         Referer: 'http://127.0.0.1:8010/login/',
  140 |       },
  141 |     });
  142 |     expect(other.status()).toBe(200);
  143 |   });
  144 | });
  145 | 
  146 | test.describe('Verification: MSA finance threshold matrix', () => {
  147 |   test('Finance action absent below $100000 and present at/above threshold', async ({ page }) => {
  148 |     test.slow();
  149 |     await login(page);
  150 |     const suffix = Date.now().toString().slice(-5);
  151 | 
  152 |     await generateMsa(page, {
  153 |       counterparty: `Below Thr ${suffix}`,
  154 |       value: 99999,
  155 |       confirmThreshold: false,
  156 |     });
  157 |     await openWorkspaceActions(page);
  158 |     await expect(page.getByRole('menuitem', { name: 'Send to Finance' })).toHaveCount(0);
  159 | 
  160 |     await generateMsa(page, {
  161 |       counterparty: `Exact Thr ${suffix}`,
  162 |       value: 100000,
  163 |       confirmThreshold: false,
  164 |     });
  165 |     await openWorkspaceActions(page);
  166 |     await expect(page.getByRole('menuitem', { name: 'Send to Finance' })).toBeVisible();
  167 |     await page.getByRole('menuitem', { name: 'Send to Finance' }).click();
  168 |     await expect(page.getByText(/MSA submitted to .* for review/i).first()).toBeVisible();
  169 |     await page.reload();
> 170 |     await expect(page.getByText(/MSA submitted to .* for review|Finance|approval/i).first()).toBeVisible();
      |                                                                                              ^ Error: expect(locator).toBeVisible() failed
  171 | 
  172 |     await generateMsa(page, {
  173 |       counterparty: `Above Thr ${suffix}`,
  174 |       value: 100001,
  175 |       confirmThreshold: false,
  176 |     });
  177 |     await openWorkspaceActions(page);
  178 |     await expect(page.getByRole('menuitem', { name: 'Send to Finance' })).toBeVisible();
  179 |     await page.getByRole('menuitem', { name: 'Send to Finance' }).click();
  180 |     await expect(page.getByText(/MSA submitted to .* for review/i).first()).toBeVisible();
  181 |   });
  182 | 
  183 |   test('Legal submit persists after refresh and shows audit history', async ({ page }) => {
  184 |     test.slow();
  185 |     await login(page);
  186 |     const suffix = Date.now().toString().slice(-5);
  187 |     await generateMsa(page, {
  188 |       counterparty: `Audit MSA ${suffix}`,
  189 |       value: 150000,
  190 |       confirmThreshold: true,
  191 |     });
  192 |     await openWorkspaceActions(page);
  193 |     await page.getByRole('menuitem', { name: 'Send to Legal Review' }).click();
  194 |     await expect(page.getByText(/MSA submitted to .* for review/i).first()).toBeVisible();
  195 |     const workflowUrl = page.url();
  196 |     await page.reload();
  197 |     await expect(page).toHaveURL(workflowUrl);
  198 |     // Governance drawer carries Audit details for MSA (no Activity rail tab).
  199 |     await page.getByRole('button', { name: /Review Finance|Review MSA|Review privacy|Review generated|open exception/i }).first().click();
  200 |     const governanceDrawer = page.getByRole('dialog', { name: 'Governance details' });
  201 |     await expect(governanceDrawer.getByRole('heading', { name: 'Audit details' })).toBeVisible();
  202 |     await expect(governanceDrawer).toContainText(/Legal|review|submitted|Audit|approval/i);
  203 |     await governanceDrawer.getByRole('button', { name: 'Close governance details' }).click();
  204 |   });
  205 | });
  206 | 
  207 | test.describe('Verification: NDA supported actions', () => {
  208 |   test('click View contract record and Activity audit rail', async ({ page }) => {
  209 |     test.slow();
  210 |     await login(page);
  211 |     const suffix = Date.now().toString().slice(-6);
  212 |     await page.goto('/contracts/new/nda/');
  213 |     await page.fill('[data-field-key="counterparty"]', `Verify NDA ${suffix}`);
  214 |     await page.fill('[data-field-key="start_date"]', '2026-10-01');
  215 |     await page.fill('[data-field-key="contract_owner"]', 'Avery Brooks');
  216 |     await page.fill('[data-field-key="business_unit"]', 'Revenue Operations');
  217 |     await page.fill('[data-field-key="internal_reference"]', `NDA-V-${suffix}`);
  218 |     await page.selectOption('[data-field-key="nda_type"]', 'Mutual');
  219 |     await page.fill('[data-field-key="confidentiality_purpose"]', 'product diligence');
  220 |     await page.fill('[data-field-key="confidentiality_period"]', '2');
  221 |     await page.fill('[data-field-key="disclosure_scope"]', 'technical architecture');
  222 |     await page.fill('[data-field-key="permitted_recipients"]', 'employees');
  223 |     await page.fill('[data-field-key="governing_law"]', 'Netherlands');
  224 |     await page.fill('[data-field-key="jurisdiction"]', 'Amsterdam');
  225 |     await page.check('[data-field-key="injunctive_relief_included"]');
  226 |     await page.click('#submit-nda-btn');
  227 |     await expect(page).toHaveURL(/\/contracts\/workflows\/\d+\/?$/);
  228 |     await expect(page.getByRole('button', { name: 'Send for signature' })).toHaveCount(0);
  229 |     await expect(page.getByRole('button', { name: 'Export Word' })).toHaveCount(0);
  230 |     await expect(page.getByRole('button', { name: 'Send to Legal Review' })).toHaveCount(0);
  231 |     await page.getByRole('link', { name: 'View contract record' }).click();
  232 |     await expect(page).toHaveURL(/\/contracts\/\d+\/?$/);
  233 |     await page.reload();
  234 |     await expect(page.getByText(`Verify NDA ${suffix}`).first()).toBeVisible();
  235 |   });
  236 | });
  237 | 
  238 | test.describe('Verification: DPA supported actions', () => {
  239 |   test('unsupported CTAs absent; View record + Activity persist', async ({ page }) => {
  240 |     test.slow();
  241 |     await login(page);
  242 |     // Full generate covered by dpa-workflow.spec.js; assert workspace honesty on existing path.
  243 |     await page.goto('/contracts/new/dpa/');
  244 |     await expect(page.getByRole('heading', { name: /^New DPA\b/ })).toBeVisible();
  245 |     await page.locator('[data-field-key="counterparty"]').fill(`Verify DPA ${Date.now().toString().slice(-5)}`);
  246 |     await page.locator('[data-field-key="contract_owner"]').fill('Avery Brooks');
  247 |     await page.locator('[data-field-key="start_date"]').fill('2026-09-01');
  248 |     await page.getByRole('button', { name: /^(Continue|Review and generate)$/ }).click();
  249 |     // Stop early if validation blocks — full path is in dpa-workflow.spec.js.
  250 |     // Honesty check: launcher must not advertise inert legal/export actions.
  251 |     await expect(page.getByRole('button', { name: 'Send to Legal Review' })).toHaveCount(0);
  252 |     await expect(page.getByRole('button', { name: 'Export Word' })).toHaveCount(0);
  253 |     await expect(page.getByRole('link', { name: 'Review next action' })).toHaveCount(0);
  254 |   });
  255 | });
  256 | 
  257 | test.describe('Verification: search fixtures and tenancy', () => {
  258 |   for (const fixture of ['valid', 'list', 'malformed', 'empty', 'error', 'timeout', 'keyword']) {
  259 |     test(`semantic fixture ${fixture} does not 500`, async ({ page }) => {
  260 |       await login(page);
  261 |       const response = await page.goto(
  262 |         `/contracts/search/?q=e2e_fixture:${fixture}&search_mode=semantic`,
  263 |       );
  264 |       expect(response.status()).toBeLessThan(500);
  265 |       await expect(page).not.toHaveURL(/\/login\/?$/);
  266 |       await expect(page.locator('body')).toContainText(/Search|result|clause|No /i);
  267 |       await expect(page.getByRole('link', { name: 'FOREIGN_TENANT_SECRET_CLAUSE_E2E' })).toHaveCount(0);
  268 |     });
  269 |   }
  270 | 
```