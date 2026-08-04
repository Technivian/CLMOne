# PayrollMinds UAT defect register

This is a factual blocker register, not a risk acceptance. No approval or
closure is asserted.

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| PM-UAT-01 | Critical | Object-level/private access still needs reviewed exact-SHA release evidence and controlled observation; local tests alone are insufficient. | readiness PM-SEC-01 | OPEN — blocks Go |
| PM-UAT-02 | Critical | Real-upload malware/quarantine, content validation and target operation evidence is absent. | readiness PM-SEC-02 | OPEN — blocks Go |
| PM-UAT-03 | Critical | Candidate/release governance is not an approved immutable production release with required reviews/CI/operator evidence. | readiness PM-SEC-03 | OPEN — blocks Go |
| PM-UAT-04 | High | Private object-store/IAM and revoked-download behavior are not demonstrated in target infrastructure. | readiness PM-SEC-04 | OPEN — blocks Go |
| PM-UAT-05 | High | Demo Blueprint is not an isolated topology; worker, alert, TLS, backup/restore evidence is missing. | readiness PM-SEC-05 / PM-OPS-01 | OPEN — blocks Go |
| PM-UAT-06 | High | Provider governance and canonical suggestion controls are unresolved; AI remains disabled. | PM-AI-01 / AI governance gate | OPEN — blocks AI enablement and Go |
| PM-UAT-07 | High | DPA, retention/deletion, offboarding and customer export evidence is not supplied. | PM-PRIV-01 / offboarding procedure | OPEN — blocks Go |
| PM-UAT-08 | Medium | Local async-job test logs an audit append attempt from a `SimpleTestCase` database restriction while exiting 0. | focused 26-test local run | OPEN — test-harness investigation |

Critical and high rows are unresolved. The acceptance sheet cannot produce a
Go result.
