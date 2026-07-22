# ADR-0015 governance acceptance — meeting record

**Meeting type:** Programme governance review (decision record)  
**Date:** 2026-07-22 (UTC)  
**Status:** **Requested** — votes must not be invented  
**Chair:** @haroonwahed (repository steward — Product governance)  
**Quorum required:** Product governance · Engineering governance · Security & privacy (advisory)  
**Package under review:**

- [`0015-exception-request-decision-model.md`](0015-exception-request-decision-model.md)
- [`../../../audits/evidence/2026-07-22-par-exc-001/`](../../../audits/evidence/2026-07-22-par-exc-001/)
- [`../../../audits/evidence/2026-07-22-par-exc-001/DECISION_PACKAGE.md`](../../../audits/evidence/2026-07-22-par-exc-001/DECISION_PACKAGE.md)
- [`../../../audits/evidence/2026-07-22-par-exc-001/DUAL_WRITE_IMPLEMENTATION_AUTHORIZATION.md`](../../../audits/evidence/2026-07-22-par-exc-001/DUAL_WRITE_IMPLEMENTATION_AUTHORIZATION.md)

**Foundation branch:** `cursor/feat-par-exc-001-exception-waiver-discovery-d7f1`  
**Foundation PR:** [#66](https://github.com/Technivian/CLMOne/pull/66)

---

## 1. Motions

### Motion 1 — Accept ADR-0015

**Motion:** Change ADR-0015 status from **Proposed** to **Accepted** as the canonical Exception and Waiver model (`ExceptionRequest`, immutable `ExceptionDecision`, owner/expiry, authority basis, compensating controls, privilege-token boundaries, tenant isolation, Security approval for Critical-control bypasses, governed renewal/closure).

**Acceptance scope limitation:** ADR acceptance establishes the model and invariants. It does **not** authorize retirement of legacy paths, canonical read-path authority, or broad privilege changes.

| Approver | GitHub identity | Governance capacity | Authority basis | Vote | Consent |
|---|---|---|---|---|---|
| Haroon Wahed | @haroonwahed | Product governance / repository steward | `.github/CODEOWNERS` (`/docs/`); `GOVERNANCE_CHARTER.md` v2.0 | **Requested** | — |
| Technivian | @Technivian | Engineering governance / repository steward | `.github/CODEOWNERS` (`/contracts/`, `/docs/`); PDR-0003 | **Requested** | — |
| Security & privacy (advisory) | @Technivian | Security review capacity | `SECURITY_PRIVACY_ACCESS_AND_AUDIT.md`; Charter §7 | **Requested** | — |

**Result:** **Pending quorum**

---

### Motion 2 — Authorize priority dual-write slice (six paths only)

**Motion:** Authorize dual-write implementation and controlled-pilot activation (legacy still authoritative) for these paths only:

1. `keep_exception` → `KEEP_EXCEPTION`
2. `ACCEPTED_RISK` → `ACCEPTED_RISK`
3. AI exception → `AI_EXCEPTION`
4. ConflictCheck `WAIVED` → `CONFLICT_CHECK_WAIVER`
5. deadline defer → `DEADLINE_DEFER`
6. DPA approve-with-blockers → `DPA_APPROVE_WITH_BLOCKERS`

Authorized behavior and exclusions are defined in [`DUAL_WRITE_IMPLEMENTATION_AUTHORIZATION.md`](../../../audits/evidence/2026-07-22-par-exc-001/DUAL_WRITE_IMPLEMENTATION_AUTHORIZATION.md).

| Approver | GitHub identity | Governance capacity | Vote | Consent |
|---|---|---|---|---|
| @haroonwahed | Product | **Requested** | — |
| @Technivian | Engineering | **Requested** | — |
| @Technivian | Security advisory | **Requested** | — |

**Result:** **Pending quorum**

---

## 2. Ballot templates (paste verbatim to authorize)

Votes are authoritative only when provided as direct written consent in the form below. Agents must not invent Approve / Reject text.

### Product — @haroonwahed

```text
APPROVE|REJECT|ABSTAIN — ADR-0015 and PAR-EXC-001 priority dual-write

Approver: @haroonwahed
Capacity: Product governance
Vote: <Approve | Reject | Abstain>
Timestamp: <ISO-8601 UTC>

Motions covered:
1. Accept ADR-0015
2. Authorize priority dual-write (six paths; legacy authoritative; default-off until pilot allowlist)

Conditions (if any):
```

### Engineering — @Technivian

```text
APPROVE|REJECT|ABSTAIN — ADR-0015 and PAR-EXC-001 priority dual-write

Approver: @Technivian
Capacity: Engineering governance
Vote: <Approve | Reject | Abstain>
Timestamp: <ISO-8601 UTC>

Motions covered:
1. Accept ADR-0015
2. Authorize priority dual-write (six paths; legacy authoritative; default-off until pilot allowlist)

Conditions (if any):
```

### Security advisory — @Technivian

```text
APPROVE|APPROVE WITH CONDITIONS|REJECT|ABSTAIN — ADR-0015 and PAR-EXC-001 priority dual-write

Approver: @Technivian
Capacity: Security & privacy advisory
Vote: <Approve | Approve with conditions | Reject | Abstain>
Timestamp: <ISO-8601 UTC>

Motions covered:
1. Accept ADR-0015 (Critical-control clauses)
2. Authorize priority dual-write Security gates

Conditions (if any):
```

---

## 3. Merge gate for PR #66

Merge of foundation PR #66 requires:

1. Motion 1 carried (ADR-0015 Accepted);
2. CI green on rebased HEAD;
3. Scope limited to foundation artifacts (no dual-write cutover in #66).

Dual-write lands on a follow-up branch/PR after Motion 2.

---

## 4. Approvers and effective date

| Field | Value |
|---|---|
| **Status** | Requested |
| **Ratified** | _pending_ |
| **Effective date** | _pending Acceptance_ |
