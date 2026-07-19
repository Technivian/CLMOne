# Casefile Migration Status

Casefile is the application-wide default. The production Command Center is its
visual and layout reference, not a separate dashboard theme.

| Layer | Production standard |
|---|---|
| Components | CLM One-owned Django primitives inspired by shadcn/ui composition |
| Styling | Tailwind CSS v4 plus semantic Casefile tokens |
| Icons | Central Lucide-compatible `design_system/icon.html` adapter |
| Typography | Inter, light mode, zero negative tracking |
| Motion | CSS transitions and `CLMOne.motion` Web Animations adapter |
| Charts | Framework-neutral `CLMOne.chartTheme`; engine loaded only with a real chart |
| Tables | Casefile markup and server/client ownership contract; TanStack Core only for a qualifying client-owned table |
| Command palette | Accessible Django/JavaScript palette around global search |
| Toasts | Shared `CLMOne.toast`, including Django server messages |

## Compatibility Policy

Authenticated templates use `.dc-ds-*` controls. Global `.btn-*` / `.badge-*`
CSS aliases remain only for approved public/legal exceptions until optional
Phase 6.1. Deprecated `--ds-*` token aliases remain until repository-wide
usage is zero.

Migration through Phase 6 for the authenticated app is complete
([`PHASE_6_LEGACY_RETIREMENT.md`](PHASE_6_LEGACY_RETIREMENT.md),
ADR/PDR [`0008`](../adr/0008-frontend-design-system-phase-1.md)). Optional
public-shell work:
[`PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md`](PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md).

Shared shell, dashboard, repository, and queue icons must use the central icon
adapter. Custom SVG is reserved for brand marks, diagrams, and domain visuals
that do not exist in Lucide.

## Verification

The design-system test suite enforces light-only core assets, the corrected
spacing scale, central shell icons, shared feedback, data-table ownership, and
runtime motion/chart contracts. Representative desktop and mobile workflows
must also be checked before release.
