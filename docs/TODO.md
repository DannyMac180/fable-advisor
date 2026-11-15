# TODO

v7 plan: `docs/PLAN-v7-claude-workers.md`. PR 1 (Claude `implementer`, Codex lanes removed, lanes.json v2, 7.0.0) PR 2 (`/fable-advisor:build`, 7.1.0) and PR 3 (Fable 5.2 doctrine rewrite + prompt audit, 7.2.0; see `docs/audit-fable-5-2.md`) are done. Still open:

- [ ] **Measure larger builds.** PR 4 found `/build` about 2.8× more expensive than Fable alone on small tasks (`docs/measurements.md`). A larger reviewed task (t4) narrowed the gap to about 12%. Still open: tasks larger than t4, more repetitions, a split of the Fable overhead between the session and the reviewer (per-model tokens are now recorded); and the audit's R1 test, whether a Fable 5.2 architect delegates about the right amount.
- [ ] **SessionStart first-run nudge.** Hook that detects a missing or v1 lanes.json and tells the architect to suggest setup (hooks can't prompt).
- [ ] **Model catalog upkeep.** Refresh labels in `config/models.json` each release.
- [ ] **Per-project overrides.** Support a project-level lanes.json, kept out of shared repos by default.
