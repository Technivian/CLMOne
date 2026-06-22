# DocClad agent implementation

## Source of truth
Use `docs/docclad-approved-brand-board.png` as the visual authority.

## Use only these supplied assets
- Light backgrounds and login pages:
  `assets/docclad-primary-light.png`

- Centered onboarding or splash layout:
  `assets/docclad-stacked-light.png`

- Dark application header:
  `assets/docclad-dark-header-logo.png`

- App icon / compact navigation:
  `assets/docclad-app-icon.png`

- Browser tab / favicon / tiny UI:
  `assets/docclad-favicon-small-mark.png`

## Rules
1. Do not redraw, recolor, vectorize, sharpen, compress, or rebuild the logo.
2. Do not recreate the logo with HTML text or CSS.
3. Do not crop inside these files.
4. Preserve the original aspect ratio.
5. Use `object-fit: contain`.
6. Never upscale beyond the source asset's natural size.
7. Replace visible `CMS Aegis` branding with `DocClad`.
8. Keep internal code names unchanged unless explicitly requested.
9. Validate the result against the approved brand board before completion.

## Recommended placements
- Dark top navigation: use `docclad-dark-header-logo.png`
- Login left panel: use `docclad-primary-light.png` only on a light logo surface
- Login form header: use `docclad-app-icon.png` or `docclad-favicon-small-mark.png`
- Onboarding/empty state: use `docclad-stacked-light.png`
