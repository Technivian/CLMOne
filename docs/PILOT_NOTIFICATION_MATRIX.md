# DocClad Pilot Launch: Notification Requirements Matrix

## Summary

This matrix identifies which email notifications are **mandatory before pilot launch**, **nice-to-have**, and **not required**. It serves as the gate for enabling Resend provider delivery and confirming all email-generated links use canonical APP_BASE_URL.

---

## Notification Types

| Email Type | Status | Mandatory | Evidence Label | Implementation |
|---|---|---|---|---|
| **Invitation (org membership)** | ✅ Complete | **MANDATORY** | Production-compatible verified through SMTP sink (mocked in tests, Resend configured) | Phase 5J: implemented, tested, URL hardened |
| **Invitation acceptance confirmation** | ❌ Missing | **DEFERRED** | Not implemented | User receives redirect + flash message on web; email not sent |
| **Invitation expiry notification** | ❌ Missing | **DEFERRED** | Not implemented | Invitations expire silently; no email notification |
| **Invitation revocation notification** | ❌ Missing | **DEFERRED** | Not implemented | Admin revokes; invitee gets no notification (only valid invites work) |
| **Password reset / recovery** | ⚠️ Not verified | **MANDATORY** | Django default available; not verified through Resend in Phase 5J | Must use canonical URL builder; test through Resend sandbox |
| **MFA enrollment/verification** | ⚠️ Not verified | **MANDATORY** | Django+custom flow; MFA tests exist but email path not verified | Must use canonical URL builder; test through Resend sandbox |
| **MFA totp recovery codes** | ⚠️ Not verified | **DEFERRED** | Not verified | If MFA implemented, recovery code delivery deferred post-launch |
| **Contract approval request** | ❌ Missing | **DEFERRED** | Not implemented | Approval workflow exists (Phase 5G); notification deferred |
| **Approval decision notification** | ❌ Missing | **DEFERRED** | Not implemented | Approver decision tracked; deferred |
| **Signature request** | ❌ Missing | **MANDATORY (if eSign enabled)** | Not implemented | Signature workflow exists; **MANDATORY if e-signature is pilot-enabled** |
| **Signature request reminder** | ❌ Missing | **DEFERRED** | Not implemented | If signature requests enabled, reminders deferred |
| **Signature complete notification** | ❌ Missing | **DEFERRED** | Not implemented | Signature completion tracked; deferred |
| **Contract expiration reminder** | ❌ Missing | **DEFERRED** | Not implemented | Expiration scheduler exists; deferred |
| **Renewal reminder** | ❌ Missing | **MANDATORY (if renewal enabled)** | Not implemented | Renewal logic exists; **MANDATORY if renewal journey is pilot-enabled** |
| **Obligation/deadline reminder** | ❌ Missing | **MANDATORY (if obligations enabled)** | Not implemented | Obligation tracking exists; **MANDATORY if obligation journey is pilot-enabled** |
| **Contract archived/deleted notification** | ❌ Missing | **DEFERRED** | Not implemented | Archival is silent operation |
| **Document uploaded notification** | ❌ Missing | **DEFERRED** | Not implemented | Upload tracked; deferred |
| **Operator job failure alert** | ❌ Missing | **MANDATORY** | Not implemented | Jobs have error handling; **MANDATORY: operator must be alerted on job failures before launch** |
| **DSAR/evidence export ready** | ❌ Missing | **NO** | Not implemented | DSAR scope boundary; export completed but no notification |
| **Invoice issued** | ❌ Missing | **OPTIONAL** | Not implemented | Billing not in pilot scope |
| **Payment received** | ❌ Missing | **OPTIONAL** | Not implemented | Billing not in pilot scope |
| **Subscription renewal** | ❌ Missing | **OPTIONAL** | Not implemented | Billing not in pilot scope |
| **Bounce/complaint notification** | ❌ Missing | **NO** | Not implemented | Webhook processing TBD in production; not required for pilot |

---

## Mandatory-Before-Launch Emails (Approved Scope)

### 1. Invitation (Organization Membership) ✅ READY
- **Status**: ✅ **APPROVED — PHASE 5J COMPLETE**
- **Implementation**: Complete (Phase 5J)
- **Evidence**: Production-compatible via Resend; tested with mocked send_mail; URL hardened with canonical APP_BASE_URL
- **Configuration**: Resend SMTP configured in render.yaml; DEFAULT_FROM_EMAIL verified
- **Tested paths**: Create, resend, retry, failure handling, authorization, cross-tenant isolation
- **Verified**: No token leakage in audit; no branding in email; HTTPS URLs only (configurable)
- **Action for production**:
  - [ ] Resend account upgrade from sandbox
  - [ ] DKIM/SPF/DMARC verification (operator)
  - [ ] Bounce webhook integration (Phase 5K)

### 2. Password Reset / Recovery ⏳ IMPLEMENT BEFORE LAUNCH
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY before pilot launch
- **Current state**: Django password reset middleware available; email path not yet hardened
- **Implementation**:
  - [ ] Update password reset token generation to use `build_canonical_url()`
  - [ ] Test end-to-end through Resend sandbox
  - [ ] Verify no localhost URLs in production
  - [ ] Add authorization checks (only authenticated user can reset own password)
- **Deadline**: Before pilot launch

### 3. MFA Enrollment/Verification ⏳ IMPLEMENT BEFORE LAUNCH
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY before pilot launch
- **Current state**: MFA infrastructure exists (tests, middleware); email path not yet hardened
- **Implementation**:
  - [ ] Verify all MFA emails use `build_canonical_url()`
  - [ ] Test through Resend sandbox
  - [ ] Verify TOTP/backup codes email path
  - [ ] Add authorization checks (only MFA-enabled user receives MFA email)
- **Deadline**: Before pilot launch

### 4. Operator Job Failure Alerts ⏳ IMPLEMENT BEFORE LAUNCH
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY before pilot launch
- **What it does**: Notifies operators when scheduled background jobs (expiration checks, renewal reminders, lifecycle jobs, etc.) fail
- **Implementation**:
  - [ ] Add job failure exception handler
  - [ ] Configure operator alert email address (via environment or settings)
  - [ ] Create email template with error classification (safe errors only, no secrets)
  - [ ] Implement rate limiting (don't spam on repeated failures)
  - [ ] Add audit logging of job failures
  - [ ] Test via Resend sandbox
- **Deadline**: Before pilot launch

### 5. Signature Request Notification (IF e-signature enabled) ⏳ CONDITIONAL
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY only if e-signature is pilot-enabled
- **Current state**: Signature request workflow exists (Phase 5F); email notification not yet implemented
- **Implementation** (if enabled):
  - [ ] Implement signature request email
  - [ ] Use `build_canonical_url()` for accept/decline links
  - [ ] Include recipient name, contract title, action deadline
  - [ ] Test end-to-end through Resend sandbox
  - [ ] Add signer authorization verification
- **Condition**: Only implement if e-signature is in pilot scope
- **Deadline**: Before pilot launch (if enabled)

### 6. Renewal Reminder (IF renewal journey enabled) ⏳ CONDITIONAL
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY only if renewal is pilot-enabled
- **Current state**: Renewal logic exists; email notification not yet implemented
- **Implementation** (if enabled):
  - [ ] Implement renewal reminder email
  - [ ] Use `build_canonical_url()` for renewal action link
  - [ ] Schedule reminders (e.g., 30/7 days before expiration)
  - [ ] Test through Resend sandbox
  - [ ] Add authorization checks
- **Condition**: Only implement if renewal journey is in pilot scope
- **Deadline**: Before pilot launch (if enabled)

### 7. Obligation/Deadline Reminder (IF obligations enabled) ⏳ CONDITIONAL
- **Status**: ⚠️ **NOT YET IMPLEMENTED**
- **Requirement**: MANDATORY only if obligation tracking is pilot-enabled
- **Current state**: Obligation tracking exists; email notification not yet implemented
- **Implementation** (if enabled):
  - [ ] Implement obligation reminder email
  - [ ] Use `build_canonical_url()` for obligation action link
  - [ ] Schedule reminders (e.g., 7/1 days before deadline)
  - [ ] Test through Resend sandbox
  - [ ] Add authorization checks
- **Condition**: Only implement if obligation journey is in pilot scope
- **Deadline**: Before pilot launch (if enabled)

---

## Optional Notifications (After Pilot Launch)

- Invoice issued (billing scope)
- Payment received (billing scope)
- Contract expiration reminder (can use in-app notification instead)
- Renewal reminder (can use in-app notification instead)
- Obligation/deadline reminder (can use in-app notification instead)
- Approval decision notification (can use in-app notification instead)
- Document uploaded notification (can use in-app notification instead)

---

## Gateway Requirements

### Application-Layer Hardening (Phase 5J) ✅ COMPLETE

- ✅ App passes full test suite (1148 tests) with direct PostgreSQL
- ✅ All canonical URL tests pass (22 tests)
- ✅ Invitation delivery tests pass (8 tests)
- ✅ APP_BASE_URL validation enforces HTTPS + non-localhost in production
- ✅ No hard-coded or request-derived URLs in email generation
- ✅ No token leakage in audit logs or error messages
- ✅ Production startup gate prevents misconfiguration

### Before Enabling Resend Live Provider (Exit Sandbox)

- [ ] Mandatory notification implementation (Phase 5K):
  - [ ] Password recovery with canonical URLs
  - [ ] MFA communication with canonical URLs
  - [ ] Operator job failure alerts
  - [ ] Signature notifications (if pilot-enabled)
  - [ ] Renewal reminders (if pilot-enabled)
  - [ ] Obligation reminders (if pilot-enabled)
- [ ] Each mandatory email tested end-to-end through Resend sandbox
- [ ] Canonical URL builder verified for all email types
- [ ] Authorization and cross-tenant isolation verified for each email
- [ ] Resend account promoted from sandbox to production
- [ ] DKIM/SPF/DMARC configured for sender domain
- [ ] Bounce/complaint webhook configured (Phase 5K)

### Before Pilot Launch

- [ ] All mandatory notifications implemented and tested
- [ ] Production runbook documents:
  - APP_BASE_URL setup and validation
  - Resend credentials (API key, account upgrade)
  - Operator alert email configuration
  - DKIM/SPF/DMARC verification process
  - Credentials rotation procedures
- [ ] Operator trained on job failure alert monitoring

---

## Configuration Changes Required

### Immediate (Phase 5J)
- ✅ APP_BASE_URL added to settings_base.py with production validation
- ✅ Canonical URL builder implemented in contracts/services/url_builder.py
- ✅ Invitations updated to use build_invitation_url()
- ✅ APP_BASE_URL added to render.yaml as sync: false
- ✅ Tests added for Host injection prevention, localhost detection, HTTPS enforcement

### Before Production Handoff
- [ ] Password reset updated (if in scope)
- [ ] MFA email updated (if in scope)
- [ ] Signature request email implemented (if in scope)
- [ ] All new email types use build_canonical_url()
- [ ] No request.build_absolute_uri() called for any email-generated URLs

---

## Evidence Classification

| Item | Classification | Evidence |
|---|---|---|
| Invitation delivery | **Mocked only** | Tested via in-memory backend; Resend configured but not live-tested |
| Canonical URL builder | **Production-compatible verified** | Tested to prevent Host injection; localhost detection; HTTPS enforcement |
| Authorization enforcement | **Verified via unit tests** | OWNER/ADMIN only, MEMBER blocked, cross-tenant isolated |
| Audit no-leak | **Verified via unit tests** | Token, password, credentials never stored in audit |
| Branding | **Verified** | "DocClad" in UI, no CMS Aegis found, sender domain configurable |
| Live Resend delivery | **NOT VERIFIED** | Sandbox API key only; bounce/complaint webhooks not integrated |
| DKIM/SPF/DMARC | **NOT VERIFIED** | Not configured; requires DNS + Resend dashboard setup |
| Bounce handling | **NOT IMPLEMENTED** | Webhook processing TBD |

---

## Approval Sign-Off (Product Scope Confirmed)

**Phase 5J Hardening (Canonical URLs)**: ✅ **COMPLETE & VERIFIED**
- All invitation emails use APP_BASE_URL
- No Host injection possible
- Production validates HTTPS + non-localhost
- 1148 tests passing, exit 0
- Application-layer security hardening closed

**Mandatory Notifications (Approved Scope)**:
- ✅ **Invitations**: Complete (Phase 5J)
- ⏳ **Password recovery**: Implementation required before launch
- ⏳ **MFA communication**: Implementation required before launch
- ⏳ **Operator job failure alerts**: Implementation required before launch
- ⏳ **Signature notifications**: Implementation required ONLY if e-signature pilot-enabled
- ⏳ **Renewal reminders**: Implementation required ONLY if renewal journey pilot-enabled
- ⏳ **Obligation reminders**: Implementation required ONLY if obligation journey pilot-enabled
- ✅ **Other notifications**: May be deferred with approved pilot-scope decision

**Pilot Launch Gate**: ⏳ **CONDITIONAL READY**
- ✅ Application-layer hardening complete
- ⏳ All mandatory notifications implemented with canonical URLs (implement list above)
- ⏳ Resend account promoted to production
- ⏳ DKIM/SPF/DMARC verified (operator responsibility)
