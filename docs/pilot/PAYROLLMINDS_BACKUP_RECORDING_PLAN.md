# PayrollMinds Backup Walkthrough Plan

1. Reset the local synthetic workspace, run the focused demo evidence suite,
   and use the presenter click-path checklist as the recording order.
2. Record only the ten listed presenter scenes at the approved presentation
   resolution, with no personal
   browser profile, notifications, or data outside `payrollminds-demo`.
3. Open the recordings with a local player from start to finish before the
   meeting. Introduce and close the fallback with: **synthetic /
   non-production / AI disabled / read-only presenter route**.
4. Store the video and its validation note under
   `docs/pilot/recordings/payrollminds-rehearsal-20260727/`. Do not commit
   recorded credentials or real data.
5. Before a live session, reset again, verify `/_health/`, sign in as the
   selected fictional role, and keep the validated walkthrough ready.
6. If a route fails, stop live navigation, play the matching scene, log the
   route and request ID, and do not improvise around security or workflow
   controls.

## Current validated fallback

The final fallback is
[`recordings/payrollminds-rehearsal-20260727/payrollminds-presenter-backup.mov`](recordings/payrollminds-rehearsal-20260727/payrollminds-presenter-backup.mov):
a 50-second, 1280 × 720 no-audio visual walkthrough of the final ten browser
screens. Its AVFoundation duration and start/end frames were verified on
2026-07-27; the validation details and checksum are in the recording folder's
[README](recordings/payrollminds-rehearsal-20260727/README.md).
