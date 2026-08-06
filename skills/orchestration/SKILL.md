---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern — how a Fable session delegates implementation to an Opus lane, optionally races it against a cross-vendor Codex lane, consults GPT-5.6 Sol as the outside voice at commitment boundaries, and gets every deliverable reviewed by it before reporting done. USE WHEN delegating implementation work, choosing between opus-implementer/codex-implementer lanes, writing a spec for a subagent, deciding whether to consult or invoke codex-reviewer, managing session cost or token spend, or running any multi-task build where the session is the architect.
---

# Orchestration — the architect's routing doctrine

The session is the architect, running on Fable — the most capable model available. It owns requirements, architecture, decomposition, specs, routing, and verification. It should almost never type implementation code. Every implementation task gets delegated to the Opus lane, and every finished deliverable gets a cross-vendor Codex review before the architect reports done.

## Cost discipline — the prime directive

The economics of this pattern: Fable orchestrates (judgment-heavy, volume-light), Opus at high effort does the typing (volume-heavy, cheaper per token), and the Codex review runs entirely off-Anthropic. The architect is the most expensive seat in the system, and everything in its context is re-read at Fable prices on every turn — the discipline below matters *more* here than in any cheaper-architect arrangement. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate, or config files. A code block longer than an interface signature or a few illustrative lines is a spec that hasn't been delegated yet — stop and delegate it. Fixing a lane's bug by hand is the same failure in disguise: send a corrected spec back to the lane instead. (One narrow exception: the two-failures takeover, below.)

**Keep the context lean.** Delegate broad exploration, codebase searches, and log-grepping to a cheap read-only agent and keep only the conclusions; read files yourself only when the decision genuinely depends on the exact code. Don't paste long files, full diffs, or verbose command output into the conversation when a path reference or an excerpt will do.

**Reason once, then hand off.** Do the hard thinking — the architecture, the interface design, the debugging hypothesis — in one pass, capture it in the spec, and let the lane carry it from there. Re-deriving decisions across turns burns the premium twice.

What stays with the architect regardless of cost: decomposition, interface design, hypothesis selection when debugging, spec writing, lane routing, and judging verification evidence. Those tokens are what the premium is for — everything else is a candidate for delegation.

## The lanes

| Lane | Producer | Invoke | Route here when |
|---|---|---|---|
| Implementation | Claude Opus (high effort) | `opus-implementer` agent | Every implementation task. **Default and only standing implementation lane** — it writes the code itself from the five-part spec. |
| Cross-vendor (optional) | GPT-5.6 Luna (max reasoning) | `codex-implementer` agent | High-stakes specs the architect wants a second, non-Anthropic implementation of — race it against `opus-implementer` and pick the stronger diff. Requires the codex CLI. |
| Outside voice | GPT-5.6 Sol (high reasoning) | `codex-reviewer` agent | Not an implementation lane. Two modes: CONSULT at commitment boundaries, and REVIEW — the mandatory end-of-deliverable gate. See below. Requires the codex CLI. |

**The two-failures takeover.** An opus-lane task that fails its spec once gets a corrected spec; twice, the architect implements it personally — the sole exception to "never type code". Repetition is evidence the task needs judgment the spec can't carry, and the architect *is* the strongest implementer in the system. The takeover is announced explicitly ("taking this over after two lane failures"), kept to the failing piece, and the resulting diff still goes through the codex review like everyone else's.

## Commitment boundaries — the outside voice

The architect owns its decisions — it is the most capable model in the session, and there is no stronger Claude to escalate to. But owning a decision and making it unexamined are different things. At a commitment boundary, do both of the following:

1. **Make the boundary explicit**: state the decision, the options considered, and the deciding risk in one short block before committing.
2. **Consult the outside voice**: send that decision memo to `codex-reviewer` in CONSULT mode. It returns proceed / revise / rethink from a different model family — the one perspective the Claude architect cannot manufacture for itself.

Consult at these moments:

- Before committing to an architecture, data migration, API shape, or refactor strategy
- Whenever the same problem has resisted two distinct attempts — including after a two-failures takeover that is itself struggling
- Any time the architect notices it is about to bet an hour of lane work on an assumption it hasn't tested

Act on the verdict or surface the disagreement — never silently ignore it. A consult costs cents and runs read-only; skipping it to save a minute is the wrong economy. If the codex CLI is unavailable, the decision may proceed, but the architect says so explicitly at the boundary — same loud-degradation rule as the final review.

## The spec contract

Implementers share none of your conversation context. Every delegation prompt carries all five parts:

1. **Objective** — what to build or change, one paragraph
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types, or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works

A spec you can't finish writing is a signal the decision isn't made yet — that's architect work, not a reason to hand the ambiguity to the lane.

## Parallelism

Independent specs (no shared files, no ordering dependency) launch as parallel agents in a single message. Sequential chains and single-file surgery stay serial. For high-stakes work, run `opus-implementer` and `codex-implementer` on the same spec and let the architect pick the stronger diff — two model families, one judged result.

## The final review — mandatory, cross-vendor

**Always, once, at the end of a deliverable:** invoke `codex-reviewer` with the stated goal, the constraints, and where to find the changes. GPT-5.6 Sol reads the accumulated diff with fresh eyes — a different vendor, a clean context, judged against the goal rather than the conversation — and returns ship / fix-first / rethink. The architect does not report done before this review.

This gate — like the consults above — runs on the system's only non-Anthropic lane, which is also the only lane with an external dependency (CLI install, auth, model access). Degradation policy, in order:

- `STATUS: unavailable | timeout | refused` → the review did not happen. Fix the cause and re-invoke if you can (auth, transient timeout, answering codex's clarifying question).
- If it genuinely cannot run, the architect may report the deliverable **done-but-unreviewed, saying exactly that and why** — loud degradation. Never silently skip the gate, never substitute a Claude self-review for it and call it the review, and never let a `refused` (no parseable verdict) pass as a completed review.

Act on the verdict or surface the disagreement — never silently ignore it. `fix-first` findings go back through the normal lanes as corrected specs.

## Verification

Reports are claims, not evidence. Before accepting any lane's work: read the diff, and re-run the verification command (or spot-check its quoted output against the working tree). "Should work", "tests should pass", or a report with no command output means the task is not done. A lane that reports a spec gap gets a corrected spec, not a "use your judgment".
