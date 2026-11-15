# TODO

v7 plan: `docs/PLAN-v7-claude-workers.md`. PR 1 (Claude `implementer`, Codex lanes removed, lanes.json v2, 7.0.0) and PR 2 (`/fable-advisor:build`, 7.1.0) are done. Still open:

- [ ] **Doctrine rewrite for Fable 5.2** (PR 3). Replace fixed delegation rules with the cost facts; run the `fable-5-2-prompt-audit` skill on the skill, agents and commands.
- [ ] **Measure** (PR 4). Fable-solo vs `/build` on three real tasks, cost per completed and verified task, in `docs/measurements.md`.
- [ ] **SessionStart first-run nudge.** Hook that detects a missing or v1 lanes.json and tells the architect to suggest setup (hooks can't prompt).
- [ ] **Model catalog upkeep.** Refresh labels in `config/models.json` each release.
- [ ] **Per-project overrides.** Support a project-level lanes.json, kept out of shared repos by default.
