# Shared Card System

## Purpose

`theme/templates/design_system/card.html` is the canonical card shell for
repeated CLM One card surfaces. It preserves a calm enterprise density while
making the main next step, supporting metadata, and keyboard interaction
consistent. A card represents one coherent destination or governed object; it
does not replace sections, tables, or arbitrary page containers.

## Shell Contract

Every shared card has the same information sequence:

1. **Header** — icon, human-readable title, optional subtitle, and optional
   badge or count.
2. **Body** — one concise description or summary.
3. **Meta** — structured supporting information, not a prose list.
4. **Footer** — one clear primary action, with optional secondary actions only
   when the card is an operational object with confirmed actions.

The shell uses a white surface, soft border, restrained shadow, 16px radius,
20px padding, shared typography, shared hover/focus states, and a footer that
is held to the bottom of equal-height grid cards. Linked cards are one native
link with a visible focus ring; nested interactive controls are not allowed.
Unlinked operational cards may contain their own native action controls.

Keep metadata muted and concise. Show at most three visible chips. If more are
needed, render the first three plus a `+n more` disclosure affordance rather
than widening the card or creating a badge cloud. Counts use tabular numerals;
badges express a true status only, never decoration.

## Approved Variants

| Variant | Class | Purpose | Emphasis |
|---|---|---|---|
| Launch | `dc-ds-card--launch` | Start a governed request or choose a starting route | The valid first action |
| Catalog | `dc-ds-card--catalog` | Browse reusable capabilities or configuration areas | Capability and availability/count |
| Operational | `dc-ds-card--operational` | Manage a live, governed object | Current state and the next valid action |

Variants may adjust density and information emphasis, but they never change
the header → body → meta → footer anatomy. Propose a new design-system variant
before adding a page-specific card layout for a fundamentally different
purpose. Operational cards use the compact treatment: a two-line summary,
the current status and path, and one concise update/use line. Detailed owner
and change-history information remains in the designer rather than repeating
on every card. Catalog cards use the compact density: an 184px minimum height,
12px grid gap, and the shared 20px shell padding. They may place their one
linked action at the right of the status/update summary when that removes
redundant footer space; the card remains one native destination.

## Current Product Mapping

| Surface | Variant | Shared behaviour retained |
|---|---|---|
| New Contract / agreement-type chooser | Launch | Search, controlled route selection, and approved-template links |
| Templates & Playbooks | Catalog | Role-aware availability, counts, and destination links |
| Workflow Designer template list | Operational | Selection mode, setup notices, secondary template actions, version and archive controls |

The Workflow Designer retains its existing `template-tile` hook only for
selection and menu behaviour. Its visual shell and common content slots now
compose the operational-card classes; behaviour-specific controls remain
outside the reusable linked-card template to avoid nested controls and to
preserve permissions.

## Retired One-off Card Patterns

- New Contract: `ctp-card`, `ctp-entry-card`, and `ctp-entry-*` visual card
  anatomy were replaced by the launch card grid and shell. The `data-ctp-card`
  wrapper remains only as the existing client-side search hook.
- Templates & Playbooks: `tph-grid`, `tph-card`, and the `tph-card__*` visual
  anatomy were replaced by the catalog card grid and shell.
- Workflow Designer: the base `template-tile` visual shell is now shared
  operational-card styling. Its selection, menu, and permission-action hooks
  are intentionally retained until a dedicated behaviour extraction can prove
  no workflow action changes.

## Verification

The design-system catalogue at `/contracts/design-system/` shows all three
variants. Component tests assert the shared shell, variants, metadata limit,
and mapped pages. Product-page tests continue to cover New Contract search,
Templates & Playbooks permission gating, and workflow-template actions.
