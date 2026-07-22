# PAR-ID-001 R4 staging diagnostic — index

**Baseline `main`:** `2e7b5adc`  
**Named environment:** `par-id-001-r4-staging-equivalent`  
**Status:** R4 **PASS** (Authorized and executed)  
**R5:** **Blocked** — draft package [`../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](../2026-07-22-par-id-001-r5-canonical-authority-cutover/CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md) (votes Requested; not authorized)

| Artifact | Purpose |
|---|---|
| [`STAGING_RESOLVER_PARITY_ACTIVATION_AUTHORIZATION.md`](STAGING_RESOLVER_PARITY_ACTIVATION_AUTHORIZATION.md) | Bundled R4 authorization + runtime requirements |
| [`CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md`](CANONICAL_RESOLVER_AUTHORITY_CUTOVER_AUTHORIZATION.md) | Pointer to R5 draft auth package |
| [`R4_EXIT_REPORT.md`](R4_EXIT_REPORT.md) | Exit verdict + counts |
| [`SUMMARY.md`](SUMMARY.md) | Short programme summary |
| [`staging_env/README.md`](staging_env/README.md) | Named env recreate instructions |
| `flag_state_before.txt` / `during` / `after` | Flag evidence |
| `resolver_parity_during.json` | Authoritative resolver counts |
| `resolver_parity_per_org.json` | Per-org resolver counts |
| `assignment_parity_during.json` | Assignment parity rows |
| `scenarios_executed.json` | Scenario matrix + security |
| `rollback_result.json` | Flag-off rollback proof |
| `django-tests-*.txt` / `django-check.txt` | Test evidence |
| `committed_defaults_check.txt` | Defaults remain false |

**Not authorized by R4:** production activation; canonical authority; dual-return; privilege/ADMIN cutover; legacy-fallback removal; use of `CANONICAL_RESOLVER_ACTIVATION_AUTHORIZATION.md` for this slice.
