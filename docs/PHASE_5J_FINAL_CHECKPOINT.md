# Phase 5J Final Checkpoint — Canonical URL Hardening

**Date:** 2026-06-23  
**Status:** ✅ **COMPLETE**  
**Exit Code:** 0

---

## Execution Summary

### Full Backend Test Suite (Final Run)

```
Command:
  DJANGO_SETTINGS_MODULE=config.settings_postgres_test \
  pytest tests/ --create-db -q

Results:
  1148 passed, 1 skipped, 8 warnings
  Duration: 62.68 seconds (0:01:02)
  Exit Code: 0

Database: PostgreSQL 17.6 direct connection (port 5432)
Test Config: config.settings_postgres_test (development validation)
```

### Hardening Test Breakdown

| Category | Tests | Status |
|---|---|---|
| Canonical URL builder | 22 | ✅ 22 passed |
| Invitation delivery | 8 | ✅ 8 passed |
| Production config gate | 19 | ✅ 19 passed (fixed) |
| Production storage guard | 5 | ✅ 5 passed (fixed) |
| All other tests | 1094 | ✅ 1094 passed |
| **Total** | **1148** | **✅ 1148 passed** |

---

## What Was Accomplished in Phase 5J

### 1. Canonical URL Builder (Security)

**File:** `contracts/services/url_builder.py` (NEW)

Centralized, request-independent URL builder:
- ✅ Never calls `request.build_absolute_uri()`
- ✅ No Host header injection possible
- ✅ Fail-fast if APP_BASE_URL missing
- ✅ Used exclusively by invitation delivery

### 2. Production Validation (Startup Gate)

**File:** `config/settings_base.py` (MODIFIED)

Enforced at import time:
- ✅ HTTPS required in production (HTTP rejected)
- ✅ Localhost/127.0.0.1 forbidden in production
- ✅ APP_BASE_URL required in production (no fallback)
- ✅ HTTP localhost allowed in development (convenience)

### 3. Invitations Hardened (All Paths)

**Files:** `contracts/services/invitations.py`, `contracts/views_domains/organization_admin.py` (MODIFIED)

All email URLs now use canonical builder:
- ✅ Create path hardened
- ✅ Resend path hardened
- ✅ Retry path hardened
- ✅ Duplicate detection path hardened

### 4. Deployment Configuration

**Files:** `render.yaml`, `.env.example`, `.env`, `tests/test_production_config_gate.py`, `tests/test_document_storage_download.py` (MODIFIED)

Production-ready topology:
- ✅ APP_BASE_URL in render.yaml (sync: false, operator configures)
- ✅ APP_BASE_URL in .env.example (documented)
- ✅ APP_BASE_URL in .env (http://localhost:8000 for dev)
- ✅ Production tests updated with valid HTTPS URL

### 5. Hardening Tests (22 New Tests)

**File:** `tests/test_canonical_url_builder.py` (NEW)

Comprehensive security verification:
- ✅ Host header injection prevention (5 tests)
- ✅ Production configuration validation (3 tests)
- ✅ HTTPS enforcement (1 test)
- ✅ Localhost prevention (2 tests)
- ✅ Fail-fast validation (1 test)
- ✅ End-to-end invitation delivery (3 tests)
- ✅ URL structure correctness (2 tests)
- ✅ Development flexibility (2 tests)

---

## Security Analysis

### Host Header Injection: PREVENTED ✅

**Threat:** Attacker crafts request with `Host: attacker.evil.com`, app generates phishing emails

**Mitigation:** No call to `request.build_absolute_uri()` in email URL path
- Old: `request.build_absolute_uri(reverse(...))` — vulnerable to Host header
- New: `build_canonical_url(reverse(...))` — only uses APP_BASE_URL setting

**Proof:** Test `test_host_header_ignored_in_invitation_delivery` confirms attacker.evil.com cannot appear in email URL

### Localhost in Production: PREVENTED ✅

**Threat:** Admin mistakenly sets `APP_BASE_URL=http://localhost:8000` in production

**Mitigation:** Startup validation raises `ImproperlyConfigured` before app starts
- App refuses to boot if production environment + localhost detected
- Clear error message guides operator to correct configuration

**Proof:** Test `test_production_validation_rules` confirms localhost URLs fail validation

### HTTP in Production: PREVENTED ✅

**Threat:** Admin sets `APP_BASE_URL=http://app.example.com` (unencrypted)

**Mitigation:** Startup validation raises `ImproperlyConfigured` before app starts
- App refuses to boot if production environment + HTTP detected
- Clear error message guides operator to HTTPS requirement

**Proof:** Test `test_production_validation_rules` confirms HTTP URLs fail validation

### Missing Configuration: FAIL-FAST ✅

**Threat:** APP_BASE_URL forgotten, app silently falls back to localhost

**Mitigation:** `build_canonical_url()` raises immediately if APP_BASE_URL empty
- No fallback logic; always explicit
- Exception includes helpful error message

**Proof:** Test `test_missing_app_base_url_raises_on_build` confirms exception on missing config

---

## Evidence Classification (Phase 5J)

| Claim | Evidence Level | Proof |
|---|---|---|
| Canonical URL builder is secure | **Verified** | 22 dedicated tests + 1148-test full suite |
| Host injection prevented | **Verified** | Test verifies request Host never influences URL |
| Localhost detection works | **Verified** | Production tests reject localhost |
| HTTPS enforcement works | **Verified** | Production tests reject HTTP |
| Invitation delivery uses canonical URLs | **Verified** | Service code calls build_invitation_url() internally |
| No request-derived URLs in email | **Verified** | Code inspection + test coverage |
| Production startup validates config | **Verified** | App refuses to boot with invalid config |
| All tests passing | **Verified** | 1148 passed, 1 skipped, exit 0 |

---

## Known Out-of-Scope (Phase 5K or Later)

1. **Live Resend Delivery:** Requires production account upgrade; not tested with real mailbox
2. **DKIM/SPF/DMARC:** DNS configuration required by operator (not code)
3. **Bounce/Complaint Webhooks:** Processing not implemented
4. **Other Email Notifications:** Password reset, MFA, signatures, renewal reminders pending product scope decision

---

## Pilot Notification Matrix

See `docs/PILOT_NOTIFICATION_MATRIX.md` for:
- **Mandatory before pilot launch:** Invitation ✅, Operator job alerts ⏳, Password reset ⏳, MFA ⏳, Signatures ⏳, Renewal reminders ⏳, Obligation reminders ⏳
- **Optional after launch:** Billing, confirmations, approval notifications
- **Scope decisions needed:** Product must confirm which notifications are in pilot scope

---

## Deployment Checklist for Operator

### Before Production Deployment

- [ ] Confirm product notification scope (see PILOT_NOTIFICATION_MATRIX.md)
- [ ] Set APP_BASE_URL to production domain in render.yaml (https://your-domain.com)
- [ ] Upgrade Resend account from sandbox to production
- [ ] Configure DKIM/SPF/DMARC in Resend dashboard
- [ ] Configure sender domain in Resend (align with DEFAULT_FROM_EMAIL)
- [ ] Test invitation delivery with real email address (verify inbox delivery)
- [ ] Configure operator alert email for job failures
- [ ] Document APP_BASE_URL setup in runbook
- [ ] Document Resend credentials rotation process

### Production Validation

- [ ] Production app startup succeeds (no ImproperlyConfigured)
- [ ] App startup verifies APP_BASE_URL is HTTPS
- [ ] App startup verifies APP_BASE_URL is not localhost
- [ ] Invitation emails use configured domain in URLs
- [ ] Bounce/complaint notifications are processed (if implemented)

---

## Files Changed Summary

| File | Change | Purpose |
|---|---|---|
| `config/settings_base.py` | Add APP_BASE_URL + validation | Production gate + startup verification |
| `contracts/services/url_builder.py` | NEW | Canonical URL builder (secure, request-independent) |
| `contracts/services/invitations.py` | Modify deliver_invitation() | Use canonical URL builder internally |
| `contracts/views_domains/organization_admin.py` | Remove _build_invite_url(), update 3 paths | All paths use canonical builder |
| `render.yaml` | Add APP_BASE_URL | Production environment configuration |
| `.env.example` | Add APP_BASE_URL docs | Developer documentation |
| `.env` | Add APP_BASE_URL (dev default) | Local development convenience |
| `tests/test_canonical_url_builder.py` | NEW | 22 hardening tests |
| `tests/test_production_config_gate.py` | Add APP_BASE_URL to _VALID_ENV | Production test suite compatibility |
| `tests/test_document_storage_download.py` | Add APP_BASE_URL to production test env | Production test suite compatibility |

---

## Test Commands

### Phase 5J Hardening Tests Only
```bash
DJANGO_SETTINGS_MODULE=config.settings_postgres_test \
  pytest tests/test_canonical_url_builder.py -v --reuse-db
# Result: 22 passed
```

### Invitation Delivery Tests
```bash
DJANGO_SETTINGS_MODULE=config.settings_postgres_test \
  pytest tests/test_invitation_delivery.py -v --reuse-db
# Result: 8 passed
```

### Full Backend Suite (Final Verification)
```bash
DJANGO_SETTINGS_MODULE=config.settings_postgres_test \
  pytest tests/ --create-db -q
# Result: 1148 passed, 1 skipped, exit 0
```

---

## Sign-Off

**Phase 5J Hardening: CLOSED ✅**

- ✅ Canonical URL builder implemented and verified
- ✅ Host header injection prevented
- ✅ Production validation gates in place
- ✅ All invitations use canonical URLs
- ✅ 1148 tests passing
- ✅ Full backend suite passes
- ✅ Application-layer security hardening complete

**Next Gate:** Product must confirm notification scope (password reset, MFA, signatures, renewal reminders, obligation reminders) before Phase 5K implementation.

**Do NOT proceed to Phase 5K.**
