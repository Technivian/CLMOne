# PDR 0002: Contract Stage and Status

Status: **Approved**

Approved on: 2026-07-20  
Owner: Product / Contract Lifecycle

## Definitions

| Field | Purpose | Authoritative storage |
|---|---|---|
| **Stage** (`lifecycle_stage`) | Lifecycle position in the governed workflow graph (Drafting → Internal review → … → Archive) | `Contract.lifecycle_stage` |
| **Status** (`status`) | Operational/business condition (Draft, In review, Approved, Active, …) | `Contract.status` |

Stage answers **where the contract is in the lifecycle journey**. Status answers
**what operational state the record is in right now**. They are related but not
interchangeable.

## Allowed combinations (pilot matrix)

- Drafting stages (`DRAFTING`, `INTERNAL_REVIEW`, `NEGOTIATION`) commonly pair
  with `DRAFT`, `PENDING`, `IN_REVIEW`, or AI-review statuses.
- Approval stage (`APPROVAL`) pairs with `PENDING`, `IN_REVIEW`, or `APPROVED`.
- Signature stage (`SIGNATURE`) pairs with `APPROVED` until activation.
- Executed / obligation / renewal stages pair with `ACTIVE` or terminal statuses.
- Invalid pairings (for example `ARCHIVED` stage with `ACTIVE` status) must be
  prevented by transition services, not by UI labels alone.

## Transition ownership

| Change | Authority |
|---|---|
| `status` | `ContractLifecycleService.transition()` only |
| `lifecycle_stage` | `ContractLifecycleService.transition_lifecycle_stage()` only |
| Combined operational updates (AI review, bulk edit) | `apply_contract_operational_position()` helper |

Direct model writes from views, AI endpoints, or jobs bypassing these services
are defects.

## Audit requirements

Every stage or status change writes a chained `AuditLog` event with before/after
values and a reason string.

## UI display rules

- Repository **Stage** column sorts/filters on `lifecycle_stage`, never `status`.
- Repository status filters operate on `status` only.
- Contract record pages show stage stepper + status badge as separate controls.
- Do not merge stage and status into one unstructured label.

## Tests

Lifecycle matrix tests must cover valid transitions, blocked invalid pairings,
repository sort keys, and AI/document review paths that mutate operational state.
