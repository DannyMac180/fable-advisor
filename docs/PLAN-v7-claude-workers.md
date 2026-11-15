# Plan — v7: Fable orchestrates, Opus workers implement, Fable reviews

Status: decisions made (2026-11-15). PR 1 merged as 7.0.0 (DannyMac180/fable-advisor#29). PR 2 merged as 7.1.0 (DannyMac180/fable-advisor#30). PR 3 merged as 7.2.0 (DannyMac180/fable-advisor#31). PR 4 (measurements, 7.3.0) on `claude/v7-pr4-measure`. The measurements found `/build` about 2.8× more expensive than Fable alone on small tasks; see `docs/measurements.md`.

**Checked in scratch repos before and during PR 2:**
- An `isolation: "worktree"` Agent call creates `.claude/worktrees/agent-<id>` on branch `worktree-agent-<id>`. A workflow `agent()` with isolation creates `worktree-wf_<run>-<n>`. So `/build` reads the path and branch from the worker's report and never guesses them from a naming pattern.
- A worktree whose agent made changes is kept after the agent finishes, including a failed attempt's uncommitted changes. That's why cleanup lists leftovers and removes them only with a yes.
- Background workers can't ask for approval. Without allow rules for the tests, `git add` and `git commit`, the implementer reported `failed` with the blocked commands quoted (since 7.1.0, the status is `blocked`).
- Running `/fable-advisor:build` headless on Opus, two routine specs that both edit `calc.py` gave: 2 worker commits, a merge conflict resolved by the session, 3/3 tests passing on the merged tree, a Fable 5.2 "ship" review, and both worktrees and branches removed. The write to `.git/info/exclude` was denied in headless mode, and the command now continues when that happens.

**Checked during PR 1 (Claude Code 2.1.316):** the `fable` alias resolves to `claude-fable-5-2` and `opus` to `claude-opus-5-5`. Subagents started with an explicit `model` state their model ID in their system prompt, so the `LANE:` self-report works. That was checked on a `general-purpose` subagent; the plugin's own `implementer` is checked once installed.

**Release note:** the marketplace serves `main`, so merging PR 1 ships the breaking change (Codex lanes removed). PR 1 therefore bumps to **7.0.0**. PRs 2–4 are minor releases (7.1, 7.2, …).

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Worker provider | **Claude workers only.** The Codex lanes (GPT-6 Luna / Sol) are removed. |
| 2 | Complex lane | **Opus 5.5 at `high`.** Routine lane: Opus 5.5 at `medium`. |
| 3 | Parallel writers | **Worktrees + merge.** Workers that touch overlapping files still run in parallel, each in its own git worktree, and the session merges the results. |
| 4 | Naming | **Rename to roles.** The single worker agent is `implementer`. `luna-implementer` and `sol-implementer` are deleted, not aliased. |

Two readings of these answers are mine. Correct them if they're wrong:
- "Claude workers only" covers the *worker lanes*. The optional Codex **plugin** (`/codex:adversarial-review` as a second, cross-vendor reviewer) stays documented as optional. It isn't a worker and needs no Codex lane.
- The reviewer agent keeps the name `fable-advisor`. It's the plugin's name and the file people copy for lite mode. Setup can still point it at another Claude model.

## Goal

A session on **Fable 5.2** breaks the work into specs. A Claude Code **Workflow** hands the specs to **Opus 5.5** workers, in parallel, each in its own worktree. The session merges their branches, a clean-context **Fable 5.2** review reads the merged diff, and the session makes the final call.

Opus 5.5 costs half as much per token as Fable 5.2 ($4/$20 vs $8/$40 per MTok). Cache reads cost the same on both ($0.20), so the saving comes from output tokens and uncached input.

**What's given up:** v6's review across two model families. Every line of code now comes from a Claude model. The optional Codex review plugin is the only remaining cross-vendor check, and the README must say so plainly.

## Design

### 1. `agents/implementer.md`, the only worker

- `model: opus` by default; lanes.json overrides it per call. Tools: `Read, Edit, Write, Bash, Glob, Grep`. UI colour blue.
- It takes the six-part spec. It returns a fixed report: `LANE:` (model + effort), `STATUS:` (`done` / `spec-gap` / `failed` / `refused`), `BRANCH:`, `COMMIT:`, files changed, and the exact verification output.
- **It commits its work in its own worktree** on the branch its isolation worktree was created on (PR 2 checks how that branch is named). The branch is the deliverable. A committed worktree is what lets the session merge (§3). `/build` itself is the user's request to make these local commits. Workers never push and never touch the user's branch.
- An empty diff with exit 0 is reported as `refused`, as the Codex lanes did in v6.
- **To verify in PR 1:** whether subagent system prompts include the model ID, so `LANE:` can report the model that actually ran. That would catch Claude Code's silent fallback and a `CLAUDE_CODE_SUBAGENT_MODEL` override. If they don't include it, drop the self-report and rely on the setup-time warning.

### 2. Lanes and effort

| Lane | Model | Effort | Use when |
|---|---|---|---|
| `routine` | Opus 5.5 (`opus`) | `medium` | The spec fully determines the outcome |
| `complex` | Opus 5.5 (`opus`) | `high` | Judgment the spec can't capture decides the outcome, or routine failed once |
| `reviewer` | Fable 5.2 (`fable`) | session effort | Commitment boundaries and the final review |

Both worker lanes are the same agent at different efforts. Every call passes `effort` explicitly. Opus 5.5 defaults to `medium`, and leaving it implicit invites drift. The spec's required `LANE: <lane> · EFFORT: <effort> · ISOLATION: <worktree | none>` line names the lane's effort or an override (`low` … `max`; `ultra` disappears with Sol). The worker commits only when `ISOLATION: worktree`.

### 3. `/fable-advisor:build <task>`, the workflow entry point

The Workflow tool runs only on explicit opt-in. A command the user invokes that says to call Workflow counts. Steps:

1. **Scope inline.** Read enough code to write the specs. Broad exploration goes to a cheap read-only agent (`model: 'haiku'`).
2. **Write the specs.** Give each one an ID, its files, its lane, and any dependency on another spec.
3. **Make sure the starting tree is clean.** The worktrees branch from `HEAD`. If the tree has uncommitted changes, stop and ask Dan whether to commit or stash them first. Never stash silently.
4. **Call Workflow** with the template script from the skill. **Every `agent()` names its `model`**, because an agent with no model runs on the session model, which here is Fable:
   - `phase('Implement')`: `pipeline(specs, spec => agent(spec, {agentType: 'fable-advisor:implementer', model: 'opus', effort: <lane>, isolation: 'worktree', schema: REPORT}))`. Specs that depend on each other run in order inside one pipeline item. Independent specs fan out.
   - **Retry:** a `failed` spec gets one retry with the failure output attached. If it fails again, it's returned as failed. No automatic escalation.
   - The script returns every report. Merging happens **outside the workflow** (step 5), because it needs the session's judgment and runs in the main checkout.
5. **Merge in the session.** For each `done` branch, merge in spec-ID order (`git merge --no-ff <branch from the report>`) into the current branch:
   - **Clean merge:** continue.
   - **Conflict:** the session resolves it if the fix is obvious. Otherwise it aborts that merge (`git merge --abort`) and re-specs the piece against the merged tree for a second round.
   - **After all merges:** run the project's full verification once on the merged tree. One worktree passing its own check doesn't prove the merge works.
6. **Review.** One `agent(..., {agentType: 'fable-advisor:fable-advisor', model: 'fable'})` reads `git diff <start>..HEAD` against the stated goal and returns ship / fix-first / rethink. This can be a one-agent workflow or a plain Agent call, since `/build` already counts as opting in.
7. **Decide and report.** The session reads the verdict, the verification output and `git diff --stat`. It opens files only on fix-first or rethink, because re-reading the full diff pays Fable twice. It reports each spec's lane, model and effort, plus the merge result.
8. **Clean up.** Delete the merged worktree branches and their worktrees (`git worktree remove`). Keep unmerged ones and list them in the report.

**Limits:** under 10 agents per workflow by default. A larger build runs several `/build` rounds, and the session reads each result before the next.

**To verify in PR 2:** what `isolation: 'worktree'` leaves behind when an agent made changes. Is it a branch name, a path, or both, and is it the agent's own commit or uncommitted files? The commit-in-worktree step in §1 is there to make that answer not matter. Also check whether an `agentType`'s frontmatter `model` wins over the session model when `model` is left out. The template passes it anyway.

**On a session that isn't running Fable** (say, Opus 5.5): `/build` still works. Workers and the reviewer are pinned, so only the architect's judgment changes. Plain advisor-only mode (any session + the `fable-advisor` agent, no `/build`) stays supported.

### 4. The doctrine for Fable 5.2

Rewrite `skills/orchestration/SKILL.md`:
- **Remove:** both Codex lanes, the Luna/Sol effort table, the `blocked` / `unavailable` codex error handling, `/codex:rescue`, and `/codex:setup`.
- **Keep:** `/codex:adversarial-review`, in a short "optional cross-vendor review" note.
- **Replace the fixed rules with costs.** Give Fable the cost table and the trade-offs, not orders. "Never type code yourself" becomes "delegate the volume; a small fix you can see is cheaper to do than to spec".
- **Keep the parts that don't depend on the model:** the six-part spec, treating reports as claims to check, labelling each delegation (`Opus 5.5 · high: fix token-refresh race`), and the final review.
- **Workflows only on opt-in.** A workflow runs only through `/fable-advisor:build` or when the user asks in their own words. The skill loads automatically, which isn't the user opting in. Otherwise, independent specs go out as parallel Agent calls (each with `isolation: "worktree"` when they overlap), and the same merge steps follow.
- Then run the `fable-5-2-prompt-audit` skill on the skill, both agents and both commands.

### 5. Setup and config

- `config/models.json`: Anthropic-only. Worker lanes: `opus` (Opus 5.5), `sonnet` (Sonnet 5.5), `fable` (Fable 5.2), each with its effort list (`low` … `max`). Reviewer: `fable`, `opus`.
- **Models must be aliases** the Agent tool and `agent()` accept (`opus`, `sonnet`, `haiku`, `fable`). Setup rejects any other typed ID instead of saving one that will silently fall back.
- `lanes.json` → `version: 2`: `{routine, complex, reviewer}`, workers `{model, effort}`, reviewer `{model}`. **A v1 file with `provider: "openai"` lanes is ignored, with a one-time notice** to re-run `/fable-advisor:setup`. Workers then use the v7 defaults.
- `commands/setup.md`: drop the codex login check. Warn if `CLAUDE_CODE_SUBAGENT_MODEL` is set in the environment or in `~/.claude/settings.json`. Keep the same-model warning (reviewer == worker model).
- **Find out what the `fable` alias resolves to** in the installed Claude Code. If it's Fable 5.2, only the labels change. If it isn't, find out whether frontmatter accepts a full ID.

### 6. Measure before release

Run three real tasks, two ways each, each in its own session:
- **A:** a Fable 5.2 session working alone at `medium`.
- **B:** `/fable-advisor:build`.

Read each session's cost from the app's per-session usage (`get_usage` / `explain-usage`, not `budget.spent()`, which counts output tokens only). Compare **cost per completed, verified task**, counting every round. Record the results in `docs/measurements.md`. The README's cost claims come from these numbers. If B isn't clearly cheaper, the README says when to use A.

### 7. Docs and release

- **README:** new opening table, the `/build` flow, the worktree and merge behaviour, a section saying the cross-vendor review is gone, the cost section rebuilt from §6, and removal of the Codex requirements.
- **Also:** `plugin.json` description and keywords; the demo script; `docs/TODO.md` (close cross-provider lanes, neutral names, Claude-side effort; drop OpenAI reviewer).
- **CHANGELOG / release notes:** the breaking changes (Codex lanes and agent names removed, lanes.json v2).
- **Version 7.0.0.**

## How to split the work

| PR | Contents | Depends on |
|---|---|---|
| 1 | `implementer` agent; delete luna/sol agents; models.json + lanes.json v2; setup changes; `fable` alias and model-ID checks | none |
| 2 | `/fable-advisor:build`, workflow template, worktree + merge + cleanup steps; worktree behaviour checked against a scratch repo | 1 |
| 3 | Doctrine rewrite, prompt audit, README and TODO | 1, 2 |
| 4 | Measurements (§6), final README numbers | 2, 3 |
