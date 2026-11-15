---
name: orchestration
description: How the architect session (often Fable 5.2) weighs delegating implementation to the `implementer` agent — routine lane (Opus 5.5 · medium) or complex lane (Opus 5.5 · high) — against doing it itself, writes the spec, labels each delegation with its model, checks the evidence, and gets the work reviewed by the Fable advisor before reporting done. USE WHEN deciding whether to delegate implementation, choosing between the routine and complex lanes or an effort level, writing a spec for a subagent, consulting fable-advisor, managing session cost or token spend, or running a multi-task build where the session is the architect.
---

# Orchestration — the architect's doctrine

The session is the architect. It owns the requirements, the design, the specs, the routing and the judgment of evidence. The `implementer` agent can do the typing on a cheaper model, and the `fable-advisor` agent reviews the finished work in a clean context. Whether a given piece of work is worth delegating is the architect's call, made from the costs below. The session can run on any model; this doctrine is written with a Fable 5.2 architect in mind.

## What delegation costs, and when it pays

| | Input $/MTok | Output $/MTok | Cache read $/MTok |
|---|---|---|---|
| Fable 5.2 (architect, reviewer) | $8 | $40 | $0.20 |
| Opus 5.5 (implementer) | $4 | $20 | $0.20 |
| Haiku 5.5 (read-only exploration) | $0.10 | $0.50 | — |

- **The saving is on the volume.** Output tokens and fresh input cost half as much on Opus as on Fable. Cache reads cost the same, so a long, mostly cached context saves less than the headline price suggests.
- **A worker starts from nothing.** It re-reads the files it needs. You pay Fable prices for writing its spec and for reading its report and diff.
- **Judge by cost per finished, verified task.** A cheap call that comes back wrong and needs a second round can cost more than doing the work yourself.
- **Measured:** on three small multi-part tasks (each one to two minutes of solo Fable work), `/fable-advisor:build` cost about 2.8× what a Fable session working alone did, with the same pass rate. The Opus workers were 14% of that; the rest was Fable's own overhead (specs, merges, checks, review). On one larger four-part task, with a review in both arms, `/build` cost about 12% more than working alone. Opus took about 30% of the spend, and Fable's own spend fell by about 21%. When you can finish a task yourself in a few minutes, do it yourself. Larger builds may come out closer, but no saving has been measured. See `docs/measurements.md`.

Delegation pays when:
- the work is large next to its spec: features and test suites big enough that writing them yourself would take well beyond a few minutes, or mechanical edits across many files;
- pieces can run in parallel, though in the measured small tasks two parallel workers still cost more and took longer than doing it alone, so this is unproven beyond small tasks;
- a search would read many files whose contents you won't need afterwards. Give it to a read-only agent with `model: "haiku"` and keep only its conclusion.

It doesn't pay when:
- the change is one you can see and make in fewer tokens than the spec would take, such as a one-line fix, a rename in a file you've already read, or a small fix to a worker's diff;
- the hard part is a judgment you'd have to write out in full in the spec anyway;
- the change itself is small, and you'd read the same two or three files yourself to write the spec.

If you keep patching the same worker's output, the task was on the wrong lane, or the spec was missing a decision. Fix that, not the diff.

**Write decisions down once.** Put the architecture, the interface choices and the debugging hypothesis into the spec, so no worker has to re-derive them. Revisit a decision when a report, a test or the review contradicts it, or when you see it was wrong.

## The lanes

| Lane | Agent | Model · effort (default) | Use when |
|---|---|---|---|
| Routine | `implementer` | Opus 5.5 (`opus`) · `medium` | The spec fully determines the outcome: wiring, CRUD, mechanical edits, straightforward features |
| Complex | `implementer` | Opus 5.5 (`opus`) · `high` | Judgment the spec can't capture decides the outcome: concurrency, non-trivial algorithms, security-sensitive paths, hard debugging, wide refactors, or a routine task that has failed twice |
| Review | `fable-advisor` | Fable 5.2 (`fable`) · session effort | Commitment boundaries and the end-of-deliverable review (below) |

Both worker lanes are the same agent. They differ only in the `model` and `effort` you pass on the Agent call, and you pass both every time. An agent started without a model can end up on the session model (on a Fable session, at Fable prices), and Opus 5.5 defaults to `medium` effort.

**Pinned models.** Before the first delegation, read `~/.claude/fable-advisor/lanes.json` if it exists (written by `/fable-advisor:setup`).
- **A `"version": 2` file overrides the defaults above.** Pass `routine` / `complex` `model` and `effort` on implementer calls, and `reviewer.model` on advisor calls.
- **A file with no version, or `version: 1`,** is the v6 Codex format. Use the defaults and tell the user once to re-run setup.
- **No file:** use the defaults and suggest setup once.

**Check the model that actually ran.** The implementer's report carries the model ID from its own system prompt. If it doesn't match the pinned lane (`claude-opus-5-5` for `opus`, `claude-fable-5-2` for `fable`, `claude-sonnet-5-5` for `sonnet`, `claude-haiku-5-5` for `haiku`), say so. The advisor's verdict starts with a `REVIEWER:` line, which works the same way: on Claude Code before 2.1.321, `fable` resolves to Fable 5.1. Claude Code also silently falls back to the session model when a pinned model isn't available, and `CLAUDE_CODE_SUBAGENT_MODEL` overrides every pin.

**Choosing the lane.** How much does the outcome depend on judgment the spec can't carry? Little → routine. A lot, and mistakes are costly → complex, or keep the piece yourself. A routine task that fails once gets a corrected spec; if it fails twice, move it to complex.

**Effort.** Move off the lane default when the task gives a reason:
- `low`: purely mechanical edits;
- `xhigh`: a second attempt, or a change with a wide blast radius;
- `max`: only where time and tokens don't matter.

The architect's and the advisor's effort come from the session (`/effort`). Fable 5.2 is tuned to start at `high`; drop to `medium` for routine turns where the quality holds.

## Briefing a worker: the spec

Workers share none of your conversation. Every implementer prompt carries all six parts:

1. **Objective:** what to build or change, in one paragraph, with a short spec ID.
2. **Files:** the exact paths to create or modify.
3. **Interfaces:** the signatures, types or API shapes the code must match.
4. **Constraints:** project conventions, and what not to touch.
5. **Verification:** the command or commands that prove it works.
6. **Lane:** one line, `LANE: <routine | complex> · EFFORT: <effort> · ISOLATION: <worktree | none>`.
   - `EFFORT` matches the `effort` you pass on the call.
   - `ISOLATION` is `worktree` only when you pass `isolation: "worktree"`. The worker commits only then.

If you can't finish writing the spec, the decision isn't made yet. Make it before delegating.

## Showing which model runs each step

- **Label each call.** Put `<Model> · <effort>: <task>` in the Agent `description`, for example `Opus 5.5 · medium: add pagination to /orders` or `Fable 5.2: final review`.
- **Announce the routing** in one line before the call, for example `→ implementer · routine · Opus 5.5 · medium`.
- **Keep the report's `LANE:` line** when you summarize it.

## Parallel work and `/fable-advisor:build`

Independent specs (no shared files, no ordering dependency) can go out as parallel implementer calls in one message, each with `ISOLATION: none`. Those workers leave their changes uncommitted in your checkout. Specs that touch the same files run one after another, or go through `/fable-advisor:build`.

Outside `/build`, start a worker with `isolation: "worktree"` only when the user has asked for local commits. That worker commits on its worktree's branch. You then merge it and clean up as `/build`'s steps 4 and 6 describe, including asking before removing anything unmerged.

**Workflows.** A Workflow runs only when the user invokes `/fable-advisor:build` or asks for a workflow in their own words. This skill loading isn't that opt-in. The command holds the full procedure. What matters when choosing it:
- **Rounds:** up to 5 independent specs per round. Each runs in its own worktree under `.claude/worktrees/`, on its own `worktree-…` branch (the report names both). A `failed` spec gets one automatic retry. `blocked`, `spec-gap`, `refused` and crashed workers come back to you.
- **Dependent work waits for the next round,** because every worktree branches from `HEAD`.
- **Permissions:** workers can't ask for approval. Each spec's verification command, `git add` and `git commit` must be allowed, or the spec comes back `blocked`.
- **Merging and checks:** the session merges in spec-ID order with `--no-ff`, resolving each conflict or re-speccing the piece. The full checks then run once on the merged tree, before the review.
- **Cleanup:** merged worktrees and branches are removed. Unmerged ones, and leftovers from earlier runs, are listed, and removed only on the user's yes.

## Commitment boundaries and the final review

Consult `fable-advisor` (read-only; it answers in under ~300 words) when a wrong call would waste the next stretch of work:
- before committing to an architecture, data migration, API shape or refactor strategy;
- when the same problem has resisted two distinct attempts;
- **once at the end of every deliverable,** before you report done. It reads the changes against the stated goal rather than the conversation, and returns ship, fix-first or rethink.

Give it the decision, or for the final review the diff and the goal, plus the constraints and the options you considered. Act on the verdict, or tell the user where you disagree and why.

When the architect is also Fable, the review is the same model with a fresh context. It still catches what the conversation's assumptions hid, but it isn't a second model's opinion. Every worker is a Claude model too.

**Optional cross-vendor review.** If the OpenAI Codex plugin for Claude Code is installed (`codex@openai-codex`), run `/codex:adversarial-review` on the diff before the advisor's final review, for deliverables that touch security-sensitive code, a migration or an API shape. It's the only check in this pattern from outside the Claude family; pass its findings to the advisor. Leave that plugin's stop-time review gate off, since it overlaps with the advisor review and can loop.

## Checking the evidence

A report is a claim. For a direct implementer call, read the diff and re-run the verification command, or check its quoted output against the working tree, before accepting the work. Inside `/fable-advisor:build`, three things stand in for reading every diff: step 4's validation of each report, the full checks on the merged tree, and the advisor review. A report with no command output isn't done.

| Status | What it means | What to do |
|---|---|---|
| `failed` | Verification failed after the worker's fix attempts | Send a corrected spec; after two failures, move it to the complex lane or do it yourself |
| `refused` | An empty diff, so nothing was done | Find out why, then re-spec it or do it yourself |
| `blocked` | The permission system denied a command the worker needed | Show the user the denied commands. Getting them allowed is the user's decision, so don't route around the denial |
| `spec-gap` | The spec was missing a decision | Send a corrected spec, not "use your judgment" |
