---
description: Pin the model (and default reasoning effort) for each fable-advisor lane — routine implementer, high-complexity implementer, reviewer.
allowed-tools: Bash, Read, Write, AskUserQuestion
---

Guide the user through choosing a model for each fable-advisor lane, then save the choices. The orchestrator is whatever model the session runs on and is not configured here.

1. Read the catalog at `${CLAUDE_PLUGIN_ROOT}/config/models.json` and any existing config at `~/.claude/fable-advisor/lanes.json` (show current choices if present).
2. Run `codex login status`. If codex is missing or not logged in, tell the user the two implementer lanes need it (`npm i -g @openai/codex && codex login`) and continue — their choices still save.
3. Ask one AskUserQuestion with three questions, one per lane (`routine`, `complex`, `reviewer`). For each, list the catalog options with the lane's `recommended` model first, labelled "(Recommended)". The user can type any other model ID via "Other".
4. For each implementer lane, ask a second AskUserQuestion for the default effort, offering only that model's `efforts` (default_effort first, marked Recommended). A typed model ID not in the catalog keeps its lane's catalog default effort.
5. If the reviewer and an implementer lane end up on the same model, warn once that the review loses its cross-model second opinion, and ask whether to keep it.
6. Write `~/.claude/fable-advisor/lanes.json` (create the directory):
   ```json
   {
     "version": 1,
     "routine":  { "provider": "openai",    "model": "gpt-6-luna", "effort": "max" },
     "complex":  { "provider": "openai",    "model": "gpt-6-sol",  "effort": "high" },
     "reviewer": { "provider": "anthropic", "model": "fable" }
   }
   ```
7. Confirm with a three-line summary, one line per lane: lane, model, effort.
