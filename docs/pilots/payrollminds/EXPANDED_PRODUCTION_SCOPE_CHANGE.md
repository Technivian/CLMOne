# PayrollMinds expanded production scope change

**Status:** Product Owner business-scope direction recorded; no technical
activation, merge, deployment, customer-data import or production use is
authorized by this package.

Order Confirmation and Purchase Order are Class B, first proposed Batch 2
types. The required path is PDR-0013 business scope → PDR-0008 approval →
separately approved private-by-default implementation → individual type gate.
They remain **BUSINESS SCOPE APPROVED / TECHNICAL ACTIVATION BLOCKED**.

The shared model currently permits every active workspace member to read all
contracts. `OTHER`/Custom, generic create/upload/import, email, AI, signature,
portal, integration, sharing and every other newly proposed type remain
excluded. No feature flag is authorization.
