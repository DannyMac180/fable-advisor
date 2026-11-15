---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern — how the session (on whatever model the user chose) delegates implementation to the `implementer` agent on the routine lane (Opus 5.5 · medium) or the complex lane (Opus 5.5 · high), passes each lane's model and effort explicitly, labels every delegation with its model, and gets every deliverable reviewed by the Fable advisor before reporting done. USE WHEN delegating implementation work, choosing between the routine and complex lanes, choosing a reasoning effort for a worker, writing a spec for a subagent, deciding whether to consult fable-advisor, managing session cost or token spend, or running any multi-task build where the session is the architect.
---

# Orchestration — the architect's routing doctrine

The session is the architect: it owns requirements, architecture, decomposition, specs, routing, and verification. It should almost never type implementation code. The session runs on whatever model the user picked — this doctrine doesn't depend on it. Every implementation task goes to the `implementer` agent on the cheapest adequate lane, with the lane's model and effort passed explicitly, and every finished deliverable gets a Fable review before the architect reports done.

## Cost discipline — the prime directive

The economics of this pattern: the session model orchestrates (judgment-heavy, volume-light), Opus 5.5 workers do the typing (volume-heavy, half Fable's per-token price: $4/$20 vs $8/$40 per MTok; cache reads cost $0.20 on both), and Fable 5.2 reviews in a clean context before anything ships. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate, or config files. A code block longer than an interface signature or a few illustrative lines is a spec that hasn't been delegated yet — stop and delegate it. Fixing a worker's bug by hand is the same failure in disguise: send a corrected spec back instead.

**Keep the context lean.** Everything in the architect's context is re-read at the session model's prices on every turn. Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent (`model: "haiku"`) and keep only the conclusions; read files yourself only when the decision genuinely depends on the exact code. Don't paste long files, full diffs, or verbose command output into the conversation when a path reference or an excerpt will do.

**Reason once, then hand off.** Do the hard thinking — the architecture, the interface design, the debugging hypothesis — in one pass, capture it in the spec, and let the worker carry it from there. Re-deriving decisions across turns burns the premium twice.

What stays with the architect regardless of cost: decomposition, interface design, hypothesis selection when debugging, spec writing, lane routing, and judging verification evidence.

## The lanes

| Lane | Agent | Model · effort (default) | Route here when |
|---|---|---|---|
| Routine | `implementer` | Opus 5.5 (`opus`) · `medium` | The spec fully determines the outcome: boilerplate, wiring, CRUD, mechanical edits, straightforward features. **Default lane.** |
| Complex | `implementer` | Opus 5.5 (`opus`) · `high` | The outcome depends heavily on judgment the spec can't capture: subtle concurrency, non-trivial algorithms, security-sensitive paths, hard debugging, wide-blast-radius refactors — or the routine lane already failed the task once. |
| Review | `fable-advisor` | Fable 5.2 (`fable`) · session effort | Not an implementation lane. Commitment boundaries and the mandatory end-of-deliverable review — see below. |

Both worker lanes are the same agent; they differ only in the model and effort the architect passes. **Always pass both on every call** — the Agent tool's `model` and `effort` parameters. Opus 5.5 defaults to `medium` and an agent with no `model` can end up on the session model, so leaving either implicit invites silent drift (and, on a Fable session, Fable prices).

**User-pinned lane models.** Before the first delegation, read `~/.claude/fable-advisor/lanes.json` if it exists (written by `/fable-advisor:setup`). A `"version": 2` file overrides the defaults above: pass `routine.model` / `complex.model` and their `effort` on implementer calls, and `reviewer.model` on `fable-advisor` calls. Label delegations with the pinned model. A file with no version or `version: 1` is the v6 Codex format: ignore it, use the defaults, and tell the user once to re-run `/fable-advisor:setup`. If the file is missing, use the defaults and suggest setup once.

Deciding rule: how much does the outcome depend on judgment the spec can't capture? Little → routine; you will verify anyway. A lot, and mistakes are costly → complex, or keep that piece with the architect. A routine task that fails its spec once gets a corrected spec; twice, it moves to the complex lane — repetition is evidence the task was misclassified.

**Check the model that actually ran.** The implementer's `LANE:` line carries the model ID from its own system prompt. If it doesn't match the lane's pinned model (for example `claude-opus-5-5` for `opus`), say so in your report: Claude Code silently falls back to the session model when a pinned model isn't available, and `CLAUDE_CODE_SUBAGENT_MODEL` overrides every pin.

## Choosing the reasoning effort

The routine lane runs at `medium` and the complex lane at `high` unless the task calls for another rung — then put it on the spec's `LANE:` line and pass the same rung as the call's `effort`. Override deliberately: drop to `low` for purely mechanical edits, raise to `xhigh`/`max` when a task has already resisted an attempt or the blast radius is wide.

| Rung | Use for |
|---|---|
| `low` | Mechanical edits, renames, wiring, config, tests that mirror an existing pattern |
| `medium` | Routine default: ordinary features where the spec decides everything that matters |
| `high` | Complex default: real logic with design decisions left to the worker |
| `xhigh` | Tricky multi-file changes with interactions, the second attempt after a spec correction |
| `max` | The hardest single tasks: concurrency, security-sensitive paths, gnarly debugging |

The architect's own effort and the advisor's come from the session (`/effort`). Raise the session effort before an architecture decision or a final review that deserves it; drop it back for routine turns.

## Showing which model runs each step

- **Label the Agent `description`** with the model and effort, in the form `<Model> · <effort>: <task>` — for example `Opus 5.5 · medium: add pagination to /orders`, `Opus 5.5 · high: fix token-refresh race`, `Fable 5.2: final review`.
- **Announce the routing** in one line before each delegation: `→ implementer · routine · Opus 5.5 · medium (default)`, or `(override)` when the spec names the rung. For the advisor: `→ fable-advisor · Fable 5.2`.
- **Keep the worker's `LANE:` line** when you summarize a report — it names the model that actually ran.

The agents carry UI colours (implementer blue, advisor purple).

## The spec contract

Workers share none of your conversation context. Every delegation prompt carries all six parts:

1. **Objective** — what to build or change, one paragraph, with a short spec ID
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types, or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works
6. **Lane** — required: one line, `LANE: <routine | complex> · EFFORT: <effort>`, matching the `effort` you pass on the call (the lane default, or the override the task calls for). The worker copies it into its report; only the model ID comes from the worker itself

A spec you can't finish writing is a signal the decision isn't made yet — that's architect work, not a reason to hand the ambiguity to a cheaper model.

## Parallelism

Independent specs (no shared files, no ordering dependency) launch as parallel implementer calls in a single message. Sequential chains and single-file surgery stay serial. A worker in the main checkout leaves its changes uncommitted; a worker run with `isolation: "worktree"` commits to its own branch and reports it, and the architect merges. (The full worktree-and-merge flow arrives with `/fable-advisor:build`.)

## Commitment boundaries and the final review

Consult `fable-advisor` (read-only, verdict in under 300 words) at the moments that decide whether the next hour is wasted:

- Before committing to an architecture, data migration, API shape, or refactor strategy
- Whenever the same problem has resisted two distinct attempts
- **Always, once, at the end of a deliverable** — the advisor reads the accumulated changes with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. The architect does not report done before this review.

Pass it the decision (or, for final review, the diff and the stated goal), the constraints, and the options considered. Act on the verdict or surface the disagreement — never silently ignore it.

What the review buys depends on the session model. When the architect runs on something other than Fable, the final review is a second model — the strongest one — reading the diff in a clean context. When the architect is also Fable, it is a fresh-eyes check rather than an independent-model check: still worth it, because it reads the diff against the goal rather than the conversation. Every worker is a Claude model, so none of this is a cross-vendor check — for that, see the optional Codex review below.

## Optional cross-vendor review

If the official OpenAI Codex plugin for Claude Code is installed (`codex@openai-codex`), run `/codex:adversarial-review` on the accumulated diff *before* the `fable-advisor` final review on any deliverable that touched a security-sensitive path, a migration, or an API shape. It is the only check in this pattern from outside the Claude family; feed its findings into the advisor consult. Leave the plugin's stop-time review gate off — it overlaps with the mandatory advisor review and can loop. Without the plugin the pattern is unchanged.

## Verification

Reports are claims, not evidence. Before accepting any worker's work: read the diff, and re-run the verification command (or spot-check its quoted output against the working tree). "Should work", "tests should pass", or a report with no command output means the task is not done. An empty diff is a refusal, not a success — the implementer reports it as `refused`; treat it as one. A worker that reports `spec-gap` gets a corrected spec, not a "use your judgment".
