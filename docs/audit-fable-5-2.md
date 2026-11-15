# Fable 5.2 prompt audit — 2026-11-15

This is the audit of fable-advisor's prompts against "Prompting Claude Fable 5.2" → *Review prompts and harnesses designed for earlier models*. It used the `fable-5-2-prompt-audit` skill's seven checks (R1–R7).

**Checklist status:** the checklist's fingerprints are dated 2026-11-10, and 20 of 35 no longer match the live guide, because its wording has changed. I read the live section (fetched 2026-11-15). It still lists the same seven practices with the same actions, so every check was applied against the live text.

**Surfaces read (6):**
- `skills/orchestration/SKILL.md`
- `agents/implementer.md`
- `agents/fable-advisor.md`
- `commands/build.md`
- `commands/setup.md`
- the suggested `CLAUDE.md` line in `README.md`

**Not prompt surfaces:**
- `workflows/build.js`: a workflow script, not a message harness. It builds each worker's prompt once and never edits an earlier turn, so it can't match R3.
- `.claude-plugin/*.json`: plugin metadata only.
- `demo/`: historical scripts.
- the repo's `.claude/settings.local.json`: no prompt text.

**Findings:** R1 ×3, R4 ×1, R7 ×2. None for R2, R3, R5 or R6.

## Findings and what was done

| # | Where (before PR 3) | Check | Finding | Action taken |
|---|---|---|---|---|
| 1 | `SKILL.md` §intro, "Cost discipline — the prime directive" | R1 | Standing delegation rules: "It should almost never type implementation code", "It does not type implementation code, test bodies, boilerplate, or config files", "Fixing a worker's bug by hand is the same failure in disguise", "everything else is a candidate for delegation". The guide says to review standing delegation lines first. In a tool description, it says to state what a subagent costs, when delegation is worth it and when it isn't, and how to brief one. | **Rewritten**, not removed: this is an orchestrator skill, so the checklist treats it as a judgment call. A new "What delegation costs, and when it pays" section gives the price table, the hidden costs (re-reading, spec and report tokens, cost per verified task), and when delegation pays and when it doesn't. A small fix to a worker's diff is now allowed. Whether Fable now delegates the right amount is measured in PR 4. |
| 2 | `SKILL.md` "Keep the context lean" | R1 | A standing rule: "Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent." | **Rewritten** as a condition: delegate a search when it would read many files you won't need afterwards. |
| 3 | `README.md`, suggested `CLAUDE.md` line | R1 | "Delegate all implementation through the orchestration skill's routing table (never type code yourself)… delegate broad codebase exploration". A standing delegation rule in an instruction file users copy. | **Rewritten:** use the skill's cost table to decide what to hand off. |
| 4 | `SKILL.md` "Reason once, then hand off" | R4 (by meaning) | "Do the hard thinking… in one pass… Re-deriving decisions across turns burns the premium twice." Like the "treat that answer as done" lines, this pushes the model not to revisit earlier conclusions. The guide warns that such lines make Fable 5.2 far less likely to point out its own mistakes. | **Rewritten** as "Write decisions down once": capture decisions in the spec, and revisit one when a report, test or review contradicts it. |
| 5 | `agents/implementer.md` step 5 | R7 | "Never push, never rewrite history, and never switch or touch any other branch." An absolute rule with no reason. | **Rewritten** with scope and reason: the architect owns the branch and the remote, and `/build`'s merge expects exactly one commit on top of the starting commit. |
| 6 | `commands/build.md` line 10 | R7 | "Never push, never switch the user's branch…". The delete part names its go-ahead, but push and switch have no reason. | **Rewritten** as three scoped rules, each with its reason. The delete rule keeps the user's yes, since the guide keeps confirmation for irreversible actions. |

## Read and cleared

- **Hard rules that state their reason or go-ahead:** "pass both every time" (reason given), "nothing unmerged is deleted without a yes" (a confirmation step for an irreversible action), "never stash silently" (reason given), and "workers can't ask for permission" (a fact, not a caution).
- **`agents/fable-advisor.md`:**
  - "What you never do" gives its reason ("You advise; the working model builds").
  - "Stay under ~300 words" and "A sound plan gets one line" are length preferences, not limits on sentence shape (R6 doesn't apply).
  - "Do not manufacture objections" isn't an instruction to think less.
- **`commands/setup.md`:** procedural, with no cautions.
- **No token budget anywhere (R2).** "minimize your own token volume" in the old README line was a goal, not a number. It was removed with finding 3 anyway.

## Outside the checklist, not changed here

- **Effort and lengths:**
  - The guide says to start Fable 5.2 at `high`; the skill now says so for the architect and the advisor.
  - The routine lane runs Opus 5.5 at `medium`. The Fable guide's "Finish the whole task" advice for low and medium effort is written for Fable, not Opus, so it wasn't added to the implementer.
- **Applying these changes:** the guide says to change prompts only in new conversations. These are plugin files, loaded when a session starts, so they take effect in sessions started after the update.
