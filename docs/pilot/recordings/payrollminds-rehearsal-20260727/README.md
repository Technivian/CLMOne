# PayrollMinds backup walkthrough

This folder contains the local, synthetic backup walkthrough for the
PayrollMinds presenter route. It shows only `payrollminds-demo` data and is
explicitly synthetic, non-production, AI-disabled, and read-only.

`payrollminds-presenter-backup.mov` is a 50-second, 1280 × 720 visual backup
walkthrough assembled from the ten final browser-smoke screenshots (five
seconds per scene; no audio). It is not a claim of a live workflow replay.

Validation completed 2026-07-27:

- AVFoundation reported a 50.0-second playable duration.
- Extracted start and end frames (`backup-start.png`, `backup-end.png`) show
  the dashboard boundary and the read-only obligations-and-dates scene.
- SHA-256: `d705d82ab30dc39eff53d83411ed3ee12435402b671ef0a0a1b2debc82e8dac9`.

Regenerate and validate it with `scripts/create_payrollminds_backup_walkthrough.swift`
and `scripts/validate_payrollminds_backup_walkthrough.swift`, using the
screenshots listed in
[`../../screenshots/payrollminds-rehearsal-20260727/README.md`](../../screenshots/payrollminds-rehearsal-20260727/README.md).
