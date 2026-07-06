# Ironclad Visual & Design Audit — Findings and Application to DocClad

Date: 2026-07-04
Method: Ironclad's production app CSS bundle (prod.ironcladcdn.com) was fetched and
parsed directly, plus their marketing-site CSS, support-docs descriptions, and review
sites. Product-token claims below are verified against shipped code, not screenshots.

## 1) What Ironclad's design actually is

### Palette
- **Product neutrals dominate**: ink `#1C212B` (the single most-used color), secondary
  text `#72757B`, borders `#E2E2E8` / hairlines `#EDEEF2`, surfaces `#F9FAFB`/white.
- **Brand green desaturates inside the app**: logo green `#00CA88` becomes working
  greens `#2E846C` (primary button) / `#256E5A` (hover). Saturated color is reserved
  for *meaning*, never chrome.
- Semantic set: green = healthy/active, red `#C62F4A` = expiring/invalid,
  yellow `#EAB308` = auto-renew/warning, gray = inactive, blue = informational,
  purple `#9065F8` = AI only (a signature green→purple→sand gradient border marks
  AI features).

### Type
- Product: variable Inter, 12px and 14px dominate, negative letter-spacing on small
  text, 12px uppercase gray column headers, 24px/500 page titles.
- Marketing: Moderat + SangBleu Kingdom serif + custom illustration — the editorial
  warmth stays *outside* the app.

### Status semantics (their strongest pattern)
- Record status is always a **fully-rounded pill: tinted background + darker same-hue
  text** (Active `#C9E4DC`/`#256E5A`, Expiring `#F9D8DA`/`#A8263E`, Auto-Renewing
  `#FDF0C9`/`#CA8A04`, Inactive `#D7D7DD`/`#43474F`). Never solid saturated chips.
- Pills carry a days-remaining countdown; hover reveals detail.
- Lifecycle is one canonical path — Create → Review → Sign → Archive — narrated on
  the workflow page by a "ProcessBanner": what's next, who's responsible.

### Layout / IA
- Top header bar (white, 1px border), collapsible saved-views sidebar (348px).
- 2025 redesign merged Dashboard + Repository into **one table** with five filter
  chips (Stage, Type, Counterparty, People, Date), AND/OR filter groups, saved
  searches, bulk actions.
- Tables: 60px rows (40px compact), hairline row separators, no zebra, nowrap cells.
- **Borders over shadows, and getting flatter**: the 2025 refresh strips card
  shadows in favor of 1px borders. Radii: 4px controls, 8px buttons/cards,
  12px large cards, full-round only for pills.
- Empty states render a ghost table (skeleton rows) that teaches structure.

### Distilled principles
1. One ink anchors brand and product; saturated color = meaning, not decoration.
2. Status lives in tinted, fully-rounded pills with complete semantic coverage.
3. The table *is* the product (views, filters, bulk actions, search in one place).
4. Guided process over free navigation ("what happens next / who's responsible").
5. Borders over shadows; flat, hairline-separated surfaces.
6. Small type, tight tracking, generous row spacing.
7. AI is a visible, distinctly-marked material (gradient border), used nowhere else.
8. Ship, listen, fast-follow in public.

## 2) What was applied to DocClad (this change)

1. **Complete status→badge mapping, centralized** — `status_badge_class` /
   `phase_badge_class` filters in `contracts/templatetags/docclad_format.py`. All 9
   `Contract.Status` values now have a semantic color (previously IN_REVIEW,
   APPROVED, TERMINATED, COMPLETED, CANCELLED silently fell through to gray).
   Templates no longer hand-roll `{% if status == … %}` badge chains.
2. **Pill-shaped status badges** — `badge-sm` is now fully rounded (9999px), matching
   the tinted-background + same-hue-text pattern both themes already used.
3. **Real lifecycle stepper** — the contract detail "Lifecycle" strip was a hardcoded
   badge chain mixing `case_phase` and `status` with no notion of progress. It is now
   driven by `contract.lifecycle_stage` via the `lifecycle_steps` template tag and
   rendered with new `lc-*` primitives (done / current / upcoming states, progress
   connector, `aria-current="step"`).
4. **Calmer chrome** — removed the decorative background orbs and scanline overlay
   from `base.html`; removed glow box-shadows from `status-dot` indicators. Color now
   only appears where it means something.
5. **Dashboard de-duplication** — the two near-identical KPI strips were merged into
   one 6-card strip (adds Pending signatures; drops the duplicate render lower on
   the page).

## 3) Backlog — larger Ironclad-inspired opportunities (not in this change)

- **Unify Repository + Contract Workspace** into one table with saved views
  (SearchPreset model already exists but has no UI), filter chips, and bulk actions.
- **One lifecycle source of truth**: `status`, `case_phase` (Dutch labels), and
  `lifecycle_stage` are three overlapping wheels. Templates now render each
  consistently, but the model should converge on `lifecycle_stage` + a
  status/sub-status pair (Ironclad: Active/Expired + Evergreen/Auto-Renewing/…).
- **Days-remaining countdown inside the status pill** for expiring/renewing records.
- **Process banner** on the detail page: who's responsible, what happens next,
  assigned-to-you emphasis (the lifecycle stepper is step one of this).
- **AI marker treatment**: if/when genuinely AI-backed features ship, mark them with
  a single distinct gradient-border treatment and use purple for nothing else.
- **Ghost-table empty states** for list pages instead of icon-bubble text.

## 4) Visual screenshot pass — live competitor UIs vs the DocClad dashboard

Date: 2026-07-05
Method: Browser screenshots of Ironclad's shipped product UI (support-docs
screenshots of the April-2025 Unified Dashboard and Insights), Juro's in-app
contract editor (juro.com product imagery), and Clio's marketing/product chrome —
compared against the live DocClad dashboard (demo seed, 1440px viewport).

### What the established dashboards actually look like

**Ironclad Unified Dashboard (April 2025)** — the dashboard IS a work table:
- White surfaces everywhere; separation by 1px hairlines, no card shadows.
- Left "Views" rail: icon + label + right-aligned gray count per row, active row
  gets a light-gray fill; groups labeled with small uppercase headers (WORKFLOWS,
  REPOSITORY, MY VIEWS). Collapsible.
- Content header: one page title (~24px/600) + ONE dark primary button ("New ∨").
- A row of pill filter chips (Stage/Type/Counterparty/People/Date); active chip is
  ink-filled with count, others outlined.
- Table: small uppercase gray column headers, tall rows, hairline separators,
  stage rendered as 4 progress dots + tiny label ("Sign", "Review"), assignees as
  small avatar circles, pagination "1–25 of 4,461".
- Exactly one saturated hue on screen (brand green on the active nav tab / logo);
  everything else is ink/gray until a status needs color.

**Ironclad Insights** — charts live on plain white with a right-hand "Chart
Settings" panel of plain dropdowns; single teal series color; filter bar above.

**Juro editor** — white document canvas, small outlined pill status ("DRAFT"),
one dark toolbar row, icon rail + comments column; nothing decorative.

### DocClad dashboard today (measured, not eyeballed)

- KPI cards: `1px solid #DEE2EA`, `border-radius: 12px`, **plus a soft drop
  shadow** (`0 1px 2px / 0 8px 20px rgba(11,19,48,…)`) — the shadow contradicts
  the "borders over shadows" principle the rest of this audit already adopted.
- Six equal KPI tiles, each numeral 28px in a *different* hue (navy, gold,
  purple, amber, red, blue) regardless of meaning — color as decoration.
  "0 High risk" renders in red even when the number is healthy-zero.
- Two "+ New Contract" primary buttons visible simultaneously (top bar + page
  header), plus a third in the sidebar ("New Contract" nav item).
- Top bar carries: hamburger, logo, search, org chip, 5 icon buttons, primary
  CTA, avatar, and a bare "Sign out" text link — more chrome than any reference.
- "My Work Queue" empty state is a large white void with one centered sentence;
  references use ghost rows or a guidance CTA.
- Donut chart uses 5 hues incl. decorative segment colors; references use one
  series color and let labels carry the categories.
- Page title 32px+/700 vs references' ~24px/500–600.

### Prioritized alignment actions

P1 (cheap, big professionalism gain):
1. Drop the KPI/card drop shadows — hairline border only (the landing page and
   this audit already committed to flat).
2. One primary CTA per screen: keep the top-bar "+ New Contract", demote the
   page-header duplicate to a quiet secondary or remove it.
3. Color discipline on KPI numerals: ink by default; color only the value that
   warrants attention (red only when high-risk > 0, amber only when
   expiring > 0). Zeroes render gray.
4. Move "Sign out" into the avatar menu; thin the icon-button row.

P2:
5. Ghost-row empty state for My Work Queue ("what will appear here" skeleton +
   one CTA), same for other View-all cards.
6. Page title scale down to 24px/600; card titles 14px/700; date line as small
   gray text on the same baseline row as the title.
7. Donut → single-hue bar/stacked bar (or keep donut but one hue + gray), legend
   counts right-aligned like Ironclad's view rail.

P3 (already in §3 backlog, confirmed by screenshots):
8. The dashboard's centerpiece should trend toward the work table with saved
   views + filter chips; KPI tiles shrink to a compact stat strip.
