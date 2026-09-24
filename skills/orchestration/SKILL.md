---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern — how the session (on whatever model the user chose) delegates routine implementation to the GPT-6 Luna lane, escalates high-complexity one-offs to the GPT-6 Sol lane, keeps or overrides each lane's default reasoning effort, labels every delegation with its model, and gets every deliverable reviewed by the Fable advisor before reporting done. USE WHEN delegating implementation work, choosing between luna-implementer/sol-implementer lanes, choosing a reasoning effort for a lane, writing a spec for a subagent, deciding whether to consult fable-advisor, using the Codex plugin's review skills, managing session cost or token spend, or running any multi-task build where the session is the architect.
---

# Orchestration — the architect's routing doctrine

The session is the architect: it owns requirements, architecture, decomposition, specs, routing, and verification. It should almost never type implementation code. The session runs on whatever model the user picked — this doctrine doesn't depend on it. Every implementation task gets routed to the cheapest adequate lane — escalation to Sol is deliberate, per task — at that lane's default reasoning effort unless the task gives a reason to override it, and every finished deliverable gets a Fable review before the architect reports done.

## Cost discipline — the prime directive

The economics of this pattern: the session model orchestrates (judgment-heavy, volume-light), GPT-6 Luna does the routine typing (volume-heavy, cheap, cross-vendor), GPT-6 Sol takes the hard one-offs (cross-vendor, expensive, only when judgment decides the outcome), and Fable 5.1 reviews in a clean context before anything ships. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate, or config files. A code block longer than an interface signature or a few illustrative lines is a spec that hasn't been delegated yet — stop and delegate it. Fixing a lane's bug by hand is the same failure in disguise: send a corrected spec back to the lane instead.

**Keep the context lean.** Everything in the architect's context is re-read at the session model's prices on every turn. Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent and keep only the conclusions; read files yourself only when the decision genuinely depends on the exact code. Don't paste long files, full diffs, or verbose command output into the conversation when a path reference or an excerpt will do.

**Reason once, then hand off.** Do the hard thinking — the architecture, the interface design, the debugging hypothesis — in one pass, capture it in the spec, and let the lane carry it from there. Re-deriving decisions across turns burns the premium twice.

What stays with the architect regardless of cost: decomposition, interface design, hypothesis selection when debugging, spec writing, lane and effort routing, and judging verification evidence. Those tokens are what the premium is for — everything else is a candidate for delegation.

## The lanes

| Lane | Producer | Invoke | Route here when |
|---|---|---|---|
| Routine | GPT-6 Luna (`gpt-6-luna`, default effort `max`) | `luna-implementer` agent | The spec fully determines the outcome: boilerplate, wiring, CRUD, mechanical edits, straightforward features. **Default lane.** Requires the codex CLI. |
| High-complexity | GPT-6 Sol (`gpt-6-sol`, default effort `high`, up to `ultra`) | `sol-implementer` agent | The outcome depends heavily on judgment the spec can't capture: subtle concurrency, non-trivial algorithms, security-sensitive paths, hard debugging, wide-blast-radius refactors — or the routine lane has already failed the task once. One-off escalations, never the default. Requires the codex CLI. |
| Review | Fable 5.1 (inherits session effort) | `fable-advisor` agent | Not an implementation lane. Commitment boundaries and the mandatory end-of-deliverable review — see below. |

**User-pinned lane models.** Before the first delegation, read `~/.claude/fable-advisor/lanes.json` if it exists (written by `/fable-advisor:setup`). Its choices override the defaults in the table above: put `routine.model` / `complex.model` into the spec's model line and their `effort` as the default `REASONING:` rung for `luna-implementer` / `sol-implementer`, and pass `reviewer.model` as the Agent tool's `model` when calling `fable-advisor`. Label delegations with the pinned model, not the default. If the file is missing, use the defaults and suggest `/fable-advisor:setup` once.

Deciding rule: how much does the outcome depend on judgment the spec can't capture? Little → the default Luna lane; you will verify anyway. A lot, and mistakes are costly → escalate to `sol-implementer`, or keep that piece with the architect. A routine-lane task that fails its spec once gets a corrected spec; twice, it escalates to Sol — repetition is evidence the task was misclassified.

Both implementation lanes are the cross-vendor half of the pattern: their output comes from a non-Anthropic family, so the Claude architect's verification and the Fable review are genuine cross-vendor checks, not same-family self-review.

If a lane returns `blocked`, Claude Code's permission system denied its codex run. Report the denial text to the user and let them decide: allow the command, or keep the piece with the architect. Never send the lane back with a reworded prompt to get past the block. If either lane returns `unavailable` or `timeout`, say so explicitly in your report and decide: re-route to the other codex lane (Luna ↔ Sol), or keep the piece with the architect. Never quietly absorb the substitution or the cost change. Both lanes fail loudly on a missing or unauthenticated codex CLI — there is no Claude fallback inside a lane by design.

## Choosing the reasoning effort

Each lane has a default effort: **Luna runs at `max`, Sol at `high`**. A spec with no `REASONING:` line runs at the default; a spec that names a rung overrides it, and the lane passes that rung through unchanged. Override deliberately — drop Luna to `low`/`medium` for purely mechanical edits where `max` only buys wall-clock, and raise Sol to `xhigh`/`max`/`ultra` when the task has already resisted an attempt or the blast radius is wide.

| Rung | Luna | Sol | Use for |
|---|---|---|---|
| `low` / `medium` | ✓ | ✓ | Mechanical edits, renames, wiring, boilerplate, config, tests that mirror an existing pattern |
| `high` | ✓ | ✓ | Ordinary features with a couple of design decisions left to the lane; most routine work with real logic in it |
| `xhigh` | ✓ | ✓ | Tricky logic, multi-file changes with interactions, the second attempt after a spec correction |
| `max` | ✓ | ✓ | The hardest single-lane tasks: concurrency, security-sensitive paths, gnarly debugging |
| `ultra` | — | ✓ | Sol only. Maximum reasoning plus codex's own internal task delegation — slow; reserve for wide-blast-radius refactors and problems that have resisted two attempts |

Luna has no `ultra` and the lane will refuse rather than round it; a task that seems to need `ultra` is a task for Sol. The lanes always pass an effort to codex, so the user's own codex config never decides it silently.

The architect's own effort and the advisor's come from the session (`/effort`), since Claude Code sets subagent effort per agent definition, not per call. Raise the session effort before an architecture decision or a final review that deserves it; drop it back for routine turns.

## Showing which model runs each step

Claude Code's UI shows each subagent call by its agent name and the `description` you pass, and the lane wrappers themselves run on Sonnet — so without a label, nobody watching can tell that GPT-6 is doing the typing. Make every step's model visible:

- **Label the Agent `description`** with the model and effort, in the form `<Model> · <effort>: <task>` — for example `GPT-6 Luna · max: add pagination to /orders`, `GPT-6 Sol · xhigh: fix token-refresh race`, `Fable 5.1: final review`.
- **Announce the routing** in one line before each delegation: `→ luna-implementer · GPT-6 Luna · max (default)`, or `(override)` when the spec names the rung. For the advisor: `→ fable-advisor · Fable 5.1`.
- **Keep the lane's `LANE:` line** when you summarize a report. It names the model and the effort that actually ran, and whether it came from the spec or the default.

The agents also carry a UI colour (Luna blue, Sol orange, advisor purple) so the lanes are easy to tell apart in the transcript.

## The spec contract

Implementers share none of your conversation context. Every delegation prompt carries all six parts:

1. **Objective** — what to build or change, one paragraph
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types, or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works
6. **Reasoning** — optional: one line, `REASONING: <effort>`, only when overriding the lane's default

A spec you can't finish writing is a signal the decision isn't made yet — that's architect work, not a reason to hand the ambiguity to a cheaper model.

## Parallelism

Independent specs (no shared files, no ordering dependency) launch as parallel agents in a single message. Sequential chains and single-file surgery stay serial. For high-stakes work, run `luna-implementer` and `sol-implementer` on the same spec and let the architect pick the stronger diff — two capability tiers, one judged result.

## Commitment boundaries and the final review

Consult `fable-advisor` (read-only, verdict in under 300 words) at the moments that decide whether the next hour is wasted:

- Before committing to an architecture, data migration, API shape, or refactor strategy
- Whenever the same problem has resisted two distinct attempts
- **Always, once, at the end of a deliverable** — the advisor reads the accumulated changes with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. The architect does not report done before this review.

Pass it the decision (or, for final review, the diff and the stated goal), the constraints, and the options considered. Act on the verdict or surface the disagreement — never silently ignore it.

What the review buys depends on the session model. When the architect runs on something other than Fable (Opus 5.5, say), the final review is a second model — and the strongest one — reading the diff in a clean context. When the architect is also Fable, it is the same model, so it is a fresh-eyes check rather than an independent-model check: still worth it, because it reads the diff against the goal rather than the conversation, without the assumptions the architect accumulated while writing the specs. Cross-vendor independence comes from the codex lanes producing the code, and, when the Codex plugin is installed, from its review skills (below).

## The Codex plugin (optional)

If the official OpenAI Codex plugin for Claude Code is installed (`codex@openai-codex` under `enabledPlugins` in the user's Claude Code settings; `/plugin list` shows it), its commands become available in the session. It talks to the local `codex` binary over its app-server protocol, so it shares the same install and login as the lanes. The doctrine uses it three ways:

- **`/codex:adversarial-review`** — run it on the accumulated diff *before* the `fable-advisor` final review on any deliverable that touched a security-sensitive path, a migration, or an API shape. It is a GPT-family reviewer and so an independent-model check on the Claude reviewer's blind spots. Feed its findings into the advisor consult as context. `/codex:review` is the lighter pass for ordinary deliverables when the user wants cross-vendor review.
- **`/codex:rescue --model <slug> --effort <rung>`** — a write-capable delegation the user can drive directly, with `/codex:status`, `/codex:result`, and `/codex:cancel` for background jobs. Use it when the user asks for it, or for a long-running investigation you want off the session's critical path. It caps effort at `xhigh` and returns Codex's output rather than the lane report, so the architect still reads the diff and re-runs verification itself. For `max`/`ultra`, or whenever you want the structured report and the empty-diff check, use the lanes.
- **`/codex:setup`** — point the user here when a lane reports `unavailable`; it verifies the binary, version, and login.

The plugin's optional stop-time review gate (`/codex:setup --enable-review-gate`) runs a Codex review every time the session stops; it overlaps with the mandatory advisor review and can loop, so leave it off under this pattern unless the user chooses otherwise. Without the plugin the pattern is unchanged — it adds a reviewer and a manual delegation path, it is not a dependency.

## Verification

Reports are claims, not evidence. Before accepting any lane's work: read the diff, and re-run the verification command (or spot-check its quoted output against the working tree). "Should work", "tests should pass", or a report with no command output means the task is not done. An empty diff with a clean exit is a refusal, not a success — the lanes report it as `refused`; treat it as one. A lane that reports a spec gap gets a corrected spec, not a "use your judgment".
