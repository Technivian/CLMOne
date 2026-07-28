# PDR-0010: Owner-directed repository and release authorization

**Status:** Accepted — effective 2026-07-28  
**Date:** 2026-07-28  
**Owner:** Repository owner (`@haroonwahed`)  
**Affected Charter sections:** Active Charter §16  
**Related PDRs:** PDR-0004, PDR-0008

## Decision

The authenticated repository owner `@haroonwahed` is the final Product,
Engineering, Security, and Release Authority for this owner-operated
repository. An explicit, attributable owner instruction may authorize a
defined repository change or activation scope without independent reviewers.

Independent specialist review remains encouraged, particularly for
high-impact security and production work, but it is advisory rather than a
mandatory prerequisite when the owner explicitly directs otherwise.

Green CI on the exact release SHA remains the normal technical gate. An owner
override of a failed or unavailable check must identify the check, reason,
scope, target SHA, and rollback plan. Historical reviews, CI results,
attestations, releases, deployments, and incidents remain immutable evidence.

## Boundary

This decision changes repository governance only. It creates no CLM One
product role, workspace permission, runtime privilege, tenant exception, or
automatic activation. Each implementation still requires explicit scope,
testing proportionate to risk, tenant isolation, auditability, migration and
rollback behavior, and operational evidence.

A feature flag never grants authority by itself. Authority comes from the
ordinary gate or an explicit owner decision; the flag controls only exposure.

## Consequences

Delivery no longer depends on recruiting independent reviewers for an
owner-operated repository. Decision authority and accountability are
concentrated in one person, increasing the value of optional specialist
review, exact-SHA CI, narrow reversible changes, and retained operator
evidence.

## Approval

The repository owner explicitly directed removal of the mandatory independent
review requirement and accepted owner-directed authorization on 2026-07-28.
Charter v2.5 and `AGENTS.md` implement that instruction.
