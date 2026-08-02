# PayrollMinds Pilot Risk Register

**Status:** Proposed
**Method:** Risks remain open until their listed evidence is attached to an immutable reviewed SHA, operator record or applicable customer/privacy record. No risk is accepted by this document.

| ID | Risk | Severity | Safeguards / mitigation | Evidence required | Stop condition / owner |
|---|---|---|---|---|---|
| PM-R01 | Workspace-wide membership access reveals a private contract or metadata. | Critical | Keep pilot inactive; implement and approve PDR-0008 policy path; negative read/search/count/export/AI tests. | Exact-SHA CI, access-revocation rehearsal, operator evidence. | Any leak; Product/Engineering/Security authority. |
| PM-R02 | Malicious or wrong-type file reaches canonical document processing. | Critical | ADR-0016 quarantine-first path, private storage, scanner/type checks, fail closed. | Scanner/storage configuration, clean/malicious/outage tests, operator drill. | Scanner/type/quarantine failure; Security owner. |
| PM-R03 | Release from stale, dirty or unreviewed source. | Critical | Clean branch from selected release SHA, submitted reviews, green CI, controlled deploy. | GitHub PR/reviews/checks and deployment record. | SHA/scope divergence; Release Authority. |
| PM-R04 | Backup/restore, migration or rollback fails in production. | Critical | Isolated pre-production drill, verified backup, restoration, migration and compensating plan. | Timestamped operator results, rollback runbook. | Failed/unproven drill; Infrastructure owner. |
| PM-R05 | Full test quality gate remains red. | Critical | Triage each failure; retain full green CI for unchanged release SHA. | CI result and test evidence pack. | Any unresolved critical/high test finding; Engineering owner. |
| PM-R06 | Prohibited payroll or employee data is uploaded. | High | Classification/terms/training; restricted browser flow; quarantine and incident stop procedure. | Data handling briefing, synthetic UAT, incident runbook. | Suspected prohibited data; Launch/Privacy owner. |
| PM-R07 | Retention, deletion, export, data location or subprocessors are undocumented. | High | Do not load real data until DPA/privacy package and operational procedures exist. | Approved privacy/customer records and operator procedure. | Missing or conflicting privacy terms; Privacy owner. |
| PM-R08 | AI provider receives contract data or AI output becomes authoritative. | High | `GEMINI_AI_ENABLED=false`; no AI routes in scope; audit configuration before launch. | Environment preflight and smoke evidence. | Any AI enablement/provider call; Launch owner. |
| PM-R09 | Reminder/email job fails silently or sends to an ineligible recipient. | High | Dedicated worker/scheduler, configured SMTP, job retry/dead-letter and alert rehearsal. | Delivery/failure/retry evidence and recipient authorization test. | Missing worker/alert or misdirected reminder; Operations owner. |
| PM-R10 | Uncontrolled scope growth adds integrations, identities or signature workflow. | Medium | Scope-control process, default-off flags, named exclusions, weekly launch-control review. | Scope log and PR evidence. | Any excluded capability activation; Product Owner. |
| PM-R11 | Support ownership or incident response is unclear. | Medium | Named launch owner, one support channel, escalation/runbook and contact rehearsal. | Contact record and drill. | No reachable responsible owner; Launch owner. |

## Risk treatment rules

- Critical risks are launch blockers. High risks are launch blockers when their
  affected capability is used or real data is introduced.
- A risk may be reduced only with evidence; confidence language is not evidence.
- A feature flag can disable exposure but cannot accept a risk or authorize use.
- Exceptions may be used only for deliberately deferred non-critical
  capabilities and must not waive tenant isolation, object access, quarantine,
  privacy, audit, backup/restore, release controls or prohibited-data rules.
