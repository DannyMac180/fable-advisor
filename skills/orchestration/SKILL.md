---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern — how an Opus session delegates routine implementation to a cheaper cross-vendor lane, escalates high-complexity one-offs to Fable, and gets every deliverable reviewed by the Fable advisor before reporting done. USE WHEN delegating implementation work, choosing between codex-implementer/fable-implementer lanes, writing a spec for a subagent, deciding whether to consult fable-advisor, managing session cost or token spend, or running any multi-task build where the session is the architect.
---

# Orchestration — the architect's routing doctrine

The session is the architect: it owns requirements, architecture, decomposition, specs, routing, and verification. It should almost never type implementation code. Every implementation task gets routed to the cheapest lane that is adequate for it — escalation to Fable is deliberate, per task, never a fixed binding — and every finished deliverable gets a Fable review before the architect reports done.

## Cost discipline — the prime directive

The economics of this pattern: Opus orchestrates (judgment-heavy, volume-light), GPT-5.6 Sol does the routine typing (volume-heavy, cheap, cross-vendor), and Fable — the most expensive model available — is spent only where it changes outcomes: the hardest one-off implementations and the final review. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate, or config files. A code block longer than an interface signature or a few illustrative lines is a spec that hasn't been delegated yet — stop and delegate it. Fixing a lane's bug by hand is the same failure in disguise: send a corrected spec back to the lane instead.

**Keep the context lean.** Everything in the architect's context is re-read at architect prices on every turn. Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent and keep only the conclusions; read files yourself only when the decision genuinely depends on the exact code. Don't paste long files, full diffs, or verbose command output into the conversation when a path reference or an excerpt will do.

**Reason once, then hand off.** Do the hard thinking — the architecture, the interface design, the debugging hypothesis — in one pass, capture it in the spec, and let the lane carry it from there. Re-deriving decisions across turns burns the premium twice.

What stays with the architect regardless of cost: decomposition, interface design, hypothesis selection when debugging, spec writing, lane routing, and judging verification evidence. Those tokens are what the premium is for — everything else is a candidate for delegation.

## The lanes

| Lane | Producer | Invoke | Route here when |
|---|---|---|---|
| Routine | GPT-5.6 Sol (high reasoning) | `codex-implementer` agent | The spec fully determines the outcome: boilerplate, wiring, CRUD, mechanical edits, straightforward features. **Default lane.** Requires the codex CLI. |
| High-complexity | Fable 5 | `fable-implementer` agent | The outcome depends heavily on judgment the spec can't capture: subtle concurrency, non-trivial algorithms, security-sensitive paths, hard debugging, wide-blast-radius refactors — or the routine lane has already failed the task once. One-off escalations, never the default. |
| Review | Fable 5 | `fable-advisor` agent | Not an implementation lane. Commitment boundaries and the mandatory end-of-deliverable review — see below. |

Deciding rule: how much does the outcome depend on judgment the spec can't capture? Little → the default codex lane; you will verify anyway. A lot, and mistakes are costly → escalate to `fable-implementer`, or keep that piece with the architect. A routine-lane task that fails its spec once gets a corrected spec; twice, it escalates to Fable — repetition is evidence the task was misclassified.

The codex lane is also the cross-vendor half of the pattern: its output comes from a non-Anthropic family, so the Claude architect's verification and the Fable review are genuine cross-vendor checks, not same-family self-review.

If the codex lane returns `unavailable` or `timeout`, re-route the same spec to `fable-implementer` and say so explicitly in your report — never quietly absorb the substitution or the cost change.

## The spec contract

Implementers share none of your conversation context. Every delegation prompt carries all five parts:

1. **Objective** — what to build or change, one paragraph
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types, or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works

A spec you can't finish writing is a signal the decision isn't made yet — that's architect work, not a reason to hand the ambiguity to a cheaper model.

## Parallelism

Independent specs (no shared files, no ordering dependency) launch as parallel agents in a single message. Sequential chains and single-file surgery stay serial. For high-stakes work, run `codex-implementer` and `fable-implementer` on the same spec and let the architect pick the stronger diff — two model families, one judged result.

## Commitment boundaries and the final review

Consult `fable-advisor` (read-only, verdict in under 300 words) at the moments that decide whether the next hour is wasted:

- Before committing to an architecture, data migration, API shape, or refactor strategy
- Whenever the same problem has resisted two distinct attempts
- **Always, once, at the end of a deliverable** — the advisor reads the accumulated changes with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. The architect does not report done before this review.

Pass it the decision (or, for final review, the diff and the stated goal), the constraints, and the options considered. Act on the verdict or surface the disagreement — never silently ignore it.

One honest caveat: when the deliverable came from `fable-implementer`, the reviewer and the implementer are the same model. The final review is still worth it — it reads the diff in a clean context, against the goal rather than the conversation — but it is a fresh-eyes check there, not an independent-model check. Cross-vendor independence comes from the codex lane.

## Verification

Reports are claims, not evidence. Before accepting any lane's work: read the diff, and re-run the verification command (or spot-check its quoted output against the working tree). "Should work", "tests should pass", or a report with no command output means the task is not done. A lane that reports a spec gap gets a corrected spec, not a "use your judgment".
