# TODO — per-lane model selection follow-ups

Prototype shipped: `/fable-advisor:setup` + `~/.claude/fable-advisor/lanes.json`. Still open:

- [ ] **Cross-provider lanes.** Codex lanes are Bash wrappers with no Edit/Write; a Claude implementer needs its own agent. Ship one agent per provider per role and route by `provider` in lanes.json.
- [ ] **Neutral role names.** Agent descriptions and the routing doctrine hardcode "GPT-6 Luna", "Fable 5.1", etc. Rename to roles ("routine implementer") and show the model only in delegation labels.
- [ ] **OpenAI reviewer.** The advisor is a read-only Claude agent; an OpenAI reviewer needs a `codex review` / read-only `codex exec` wrapper.
- [ ] **SessionStart first-run nudge.** Hook that detects a missing lanes.json and tells the orchestrator to suggest setup (hooks can't prompt).
- [ ] **Claude-side effort.** Claude agents take `/effort`, not a flag; decide how a pinned effort applies to Claude lanes.
- [ ] **Model catalog upkeep.** Refresh `config/models.json` each release; validate typed IDs (e.g. a cheap codex ping).
- [ ] **Per-project overrides.** Support a project-level lanes.json, but keep it out of shared repos by default (teammates may lack codex).
