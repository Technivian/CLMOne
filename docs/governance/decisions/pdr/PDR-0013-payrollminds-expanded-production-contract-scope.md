# PDR-0013: PayrollMinds expanded production contract scope

**Status:** Proposed — Product Owner business-scope direction recorded; GitHub
decision evidence and technical activation authorization remain pending.
**Date:** 2026-08-09

## Direction and dependency

Order Confirmation and Purchase Order are the first proposed Batch 2 technical
cohort. This records business scope only. Neither a type, route, flag, role,
permission, integration, AI setting nor deployment changes under this PDR.

The mandatory sequence is:

> PDR-0013 business scope → PDR-0008 access-policy approval → separately
> authorized access implementation → per-type technical activation gate.

Both types remain **BUSINESS SCOPE APPROVED / TECHNICAL ACTIVATION BLOCKED**
until the shared access implementation and their individual evidence gates are
green. `OTHER`/Custom, generic/legacy upload and import, and all later types
remain excluded.
