---
description: Pin the model and default reasoning effort for each fable-advisor lane — routine implementer, complex implementer, reviewer.
allowed-tools: Bash, Read, Write, AskUserQuestion
---

Guide the user through choosing a model for each fable-advisor lane, then save the choices. The architect is whatever model the session runs on and is not configured here.

1. Read the catalog at `${CLAUDE_PLUGIN_ROOT}/config/models.json` and any existing config at `~/.claude/fable-advisor/lanes.json`.
   - If the existing file is `"version": 2`, show the current choices.
   - If it is version 1 or has no version (the v6 format, with `provider: "openai"` lanes), tell the user in one line that the Codex lanes were removed in v7, and that this run replaces the file.
2. Check for a subagent model override. Run `echo "${CLAUDE_CODE_SUBAGENT_MODEL:-}"`, and look for `CLAUDE_CODE_SUBAGENT_MODEL` in the `env` block of `~/.claude/settings.json`. If either is set, warn the user that it overrides every lane pin, so every lane, the reviewer included, runs on that one model. Continue either way.
3. Ask one AskUserQuestion with three questions, one per lane (`routine`, `complex`, `reviewer`). For each, list the catalog options with the lane's `recommended` model first, labelled "(Recommended)".
   - If the user types another model through "Other", accept it only if it is one of the catalog's `aliases`. Otherwise explain that Claude Code lanes take only those aliases (a full model ID would fall back silently to the session model), and ask again.
4. For the two implementer lanes, ask a second AskUserQuestion for the default effort. AskUserQuestion takes at most four options: offer the lane's `default_effort` first (marked Recommended), then the next rungs from the chosen model's `efforts`, up to four in all. Any other rung, `max` included, can be typed through "Other". A model that isn't one of the lane's options (for example `haiku`) uses `low`, `medium`, `high`, `xhigh`, `max`.
5. If the reviewer ends up on the same model as an implementer lane, warn once that the review becomes the same model checking its own lane's work: still a clean-context check, but not a second model. Ask whether to keep it.
6. Write `~/.claude/fable-advisor/lanes.json` (create the directory):
   ```json
   {
     "version": 2,
     "routine":  { "model": "opus",  "effort": "medium" },
     "complex":  { "model": "opus",  "effort": "high" },
     "reviewer": { "model": "fable" }
   }
   ```
7. Confirm with a three-line summary, one line per lane: lane, model, effort.
