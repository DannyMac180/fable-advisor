# TODO

v7 plan: `docs/PLAN-v7-claude-workers.md`. PR 1 (Claude `implementer`, Codex lanes removed, lanes.json v2, 7.0.0) PR 2 (`/fable-advisor:build`, 7.1.0) and PR 3 (Fable 5.2 doctrine rewrite + prompt audit, 7.2.0; see `docs/audit-fable-5-2.md`) are done. Still open:

- [ ] **Measure** (PR 4). Fable-solo vs `/build` on three real tasks, cost per completed and verified task, in `docs/measurements.md`. Also check the audit's R1 test: does a Fable 5.2 architect on the rewritten doctrine delegate about the right amount?
- [ ] **SessionStart first-run nudge.** Hook that detects a missing or v1 lanes.json and tells the architect to suggest setup (hooks can't prompt).
- [ ] **Model catalog upkeep.** Refresh labels in `config/models.json` each release.
- [ ] **Per-project overrides.** Support a project-level lanes.json, kept out of shared repos by default.
