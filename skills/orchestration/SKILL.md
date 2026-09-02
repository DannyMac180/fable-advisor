---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern — how a Fable 5.1 session delegates routine implementation to the GPT-5.6 Luna lane, escalates high-complexity one-offs to the GPT-5.6 Sol lane, picks a reasoning effort per task, and gets every deliverable reviewed by the Fable advisor before reporting done. USE WHEN delegating implementation work, choosing between codex-implementer/sol-implementer lanes, choosing a reasoning effort for a lane, writing a spec for a subagent, deciding whether to consult fable-advisor, using the Codex plugin's review skills, managing session cost or token spend, or running any multi-task build where the session is the architect.
---

# Orchestration — the architect's routing doctrine

The session is the architect: it owns requirements, architecture, decomposition, specs, routing, and verification. It should almost never type implementation code. Every implementation task gets routed to the cheapest lane and the lowest reasoning effort that is adequate for it — escalation to Sol, or to a higher effort, is deliberate, per task, never a fixed binding — and every finished deliverable gets a Fable review before the architect reports done.

## Cost discipline — the prime directive

The economics of this pattern: Fable 5.1 orchestrates (judgment-heavy, volume-light), GPT-5.6 Luna does the routine typing (volume-heavy, cheap, cross-vendor), GPT-5.6 Sol takes the hard one-offs (cross-vendor, expensive, only when judgment decides the outcome), and Fable 5.1 reviews in a clean context before anything ships. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate, or config files. A code block longer than an interface signature or a few illustrative lines is a spec that hasn't been delegated yet — stop and delegate it. Fixing a lane's bug by hand is the same failure in disguise: send a corrected spec back to the lane instead.

**Keep the context lean.** Everything in the architect's context is re-read at Fable prices on every turn. Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent and keep only the conclusions; read files yourself only when the decision genuinely depends on the exact code. Don't paste long files, full diffs, or verbose command output into the conversation when a path reference or an excerpt will do.

**Reason once, then hand off.** Do the hard thinking — the architecture, the interface design, the debugging hypothesis — in one pass, capture it in the spec, and let the lane carry it from there. Re-deriving decisions across turns burns the premium twice.

What stays with the architect regardless of cost: decomposition, interface design, hypothesis selection when debugging, spec writing, lane and effort routing, and judging verification evidence. Those tokens are what the premium is for — everything else is a candidate for delegation.

## The lanes

| Lane | Producer | Invoke | Route here when |
|---|---|---|---|
| Routine | GPT-5.6 Luna (effort per task) | `codex-implementer` agent | The spec fully determines the outcome: boilerplate, wiring, CRUD, mechanical edits, straightforward features. **Default lane.** Requires the codex CLI. |
| High-complexity | GPT-5.6 Sol (effort per task, up to `ultra`) | `sol-implementer` agent | The outcome depends heavily on judgment the spec can't capture: subtle concurrency, non-trivial algorithms, security-sensitive paths, hard debugging, wide-blast-radius refactors — or the routine lane has already failed the task once. One-off escalations, never the default. Requires the codex CLI. |
| Review | Fable 5.1 (inherits session effort) | `fable-advisor` agent | Not an implementation lane. Commitment boundaries and the mandatory end-of-deliverable review — see below. |

Deciding rule: how much does the outcome depend on judgment the spec can't capture? Little → the default Luna lane; you will verify anyway. A lot, and mistakes are costly → escalate to `sol-implementer`, or keep that piece with the architect. A routine-lane task that fails its spec once gets a corrected spec; twice, it escalates to Sol — repetition is evidence the task was misclassified.

Both implementation lanes are the cross-vendor half of the pattern: their output comes from a non-Anthropic family, so the Claude architect's verification and the Fable review are genuine cross-vendor checks, not same-family self-review.

If either lane returns `unavailable` or `timeout`, say so explicitly in your report and decide: re-route to the other codex lane (Luna ↔ Sol), or keep the piece with the architect. Never quietly absorb the substitution or the cost change. Both lanes fail loudly on a missing or unauthenticated codex CLI — there is no Claude fallback inside a lane by design.

## Choosing the reasoning effort

Nothing in the lanes pins an effort — the architect names one per task in the spec, and the lane passes it through unchanged. Pick the lowest rung that is adequate; effort is cost and wall-clock, not a quality dial to leave at max.

| Rung | Luna | Sol | Use for |
|---|---|---|---|
| `low` / `medium` | ✓ | ✓ | Mechanical edits, renames, wiring, boilerplate, config, tests that mirror an existing pattern |
| `high` | ✓ | ✓ | Ordinary features with a couple of design decisions left to the lane; most routine work with real logic in it |
| `xhigh` | ✓ | ✓ | Tricky logic, multi-file changes with interactions, the second attempt after a spec correction |
| `max` | ✓ | ✓ | The hardest single-lane tasks: concurrency, security-sensitive paths, gnarly debugging |
| `ultra` | — | ✓ | Sol only. Maximum reasoning plus codex's own internal task delegation — slow; reserve for wide-blast-radius refactors and problems that have resisted two attempts |

Luna has no `ultra` and the lane will refuse rather than round it; a task that seems to need `ultra` is a task for Sol. If you omit the effort, the lane runs codex at the user's own configured default and flags that in `GAPS` — acceptable for trivial work, never for an escalation.

The architect's own effort and the advisor's come from the session (`/effort`), since Claude Code sets subagent effort per agent definition, not per call. Raise the session effort before an architecture decision or a final review that deserves it; drop it back for routine turns.

## The spec contract

Implementers share none of your conversation context. Every delegation prompt carries all six parts:

1. **Objective** — what to build or change, one paragraph
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types, or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works
6. **Reasoning** — one line, `REASONING: <effort>`, chosen from the table above

A spec you can't finish writing is a signal the decision isn't made yet — that's architect work, not a reason to hand the ambiguity to a cheaper model.

## Parallelism

Independent specs (no shared files, no ordering dependency) launch as parallel agents in a single message. Sequential chains and single-file surgery stay serial. For high-stakes work, run `codex-implementer` and `sol-implementer` on the same spec and let the architect pick the stronger diff — two capability tiers, one judged result.

## Commitment boundaries and the final review

Consult `fable-advisor` (read-only, verdict in under 300 words) at the moments that decide whether the next hour is wasted:

- Before committing to an architecture, data migration, API shape, or refactor strategy
- Whenever the same problem has resisted two distinct attempts
- **Always, once, at the end of a deliverable** — the advisor reads the accumulated changes with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. The architect does not report done before this review.

Pass it the decision (or, for final review, the diff and the stated goal), the constraints, and the options considered. Act on the verdict or surface the disagreement — never silently ignore it.

One honest caveat: the advisor and the architect are the same model. The final review is still worth it — it reads the diff in a clean context, against the goal rather than the conversation, without the assumptions the architect accumulated while writing the specs — but it is a fresh-eyes check, not an independent-model check. Cross-vendor independence comes from the codex lanes producing the code, and, when the Codex plugin is installed, from its review skills (below).

## The Codex plugin (optional)

If the official OpenAI Codex plugin for Claude Code is installed (`codex@openai-codex` under `enabledPlugins` in the user's Claude Code settings; `/plugin list` shows it), its commands become available in the session. It talks to the local `codex` binary over its app-server protocol, so it shares the same install and login as the lanes. The doctrine uses it three ways:

- **`/codex:adversarial-review`** — run it on the accumulated diff *before* the `fable-advisor` final review on any deliverable that touched a security-sensitive path, a migration, or an API shape. It is a GPT-family reviewer and so an independent-model check on the Claude reviewer's blind spots. Feed its findings into the advisor consult as context. `/codex:review` is the lighter pass for ordinary deliverables when the user wants cross-vendor review.
- **`/codex:rescue --model <slug> --effort <rung>`** — a write-capable delegation the user can drive directly, with `/codex:status`, `/codex:result`, and `/codex:cancel` for background jobs. Use it when the user asks for it, or for a long-running investigation you want off the session's critical path. It caps effort at `xhigh` and returns Codex's output rather than the lane report, so the architect still reads the diff and re-runs verification itself. For `max`/`ultra`, or whenever you want the structured report and the empty-diff check, use the lanes.
- **`/codex:setup`** — point the user here when a lane reports `unavailable`; it verifies the binary, version, and login.

The plugin's optional stop-time review gate (`/codex:setup --enable-review-gate`) runs a Codex review every time the session stops; it overlaps with the mandatory advisor review and can loop, so leave it off under this pattern unless the user chooses otherwise. Without the plugin the pattern is unchanged — it adds a reviewer and a manual delegation path, it is not a dependency.

## Verification

Reports are claims, not evidence. Before accepting any lane's work: read the diff, and re-run the verification command (or spot-check its quoted output against the working tree). "Should work", "tests should pass", or a report with no command output means the task is not done. An empty diff with a clean exit is a refusal, not a success — the lanes report it as `refused`; treat it as one. A lane that reports a spec gap gets a corrected spec, not a "use your judgment".
