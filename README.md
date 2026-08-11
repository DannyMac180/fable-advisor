# Fable Advisor

**Opus runs the show. Cheaper typing, smarter escalation, and a Fable review before anything ships.**

Claude Code lets every subagent run on a different model — and lets the session itself run on a different model than its subagents. This plugin exploits that with the **architect pattern**: your session runs on **Opus**, acting as a full-time architect. It owns requirements, decomposition, specs, and verification — routes every implementation task to the right lane — and gets a **Fable 5** review of the finished work before calling anything done:

| Lane | Producer | Invocation | Route here when |
|---|---|---|---|
| Routine | **GPT-5.6 Luna** (the codex lane's pinned model — see [`agents/codex-implementer.md`](agents/codex-implementer.md)) | `codex-implementer` agent (default) | The spec fully determines the outcome — Codex does the typing via the [Codex CLI](https://github.com/openai/codex) |
| High-complexity | **Fable 5** | `fable-implementer` agent | One-off tasks where judgment the spec can't capture decides the outcome: subtle concurrency, hard debugging, security-sensitive paths, wide refactors |
| Review | **Fable 5** | `fable-advisor` agent | Commitment boundaries, and **always once at the end** — the advisor reviews the accumulated changes before the architect reports done |

The routine lane is the default destination, liberally: any unit of work a five-part spec can carry goes there, file-disjoint specs fan out as parallel lanes in a single message, and cost is governed by the lane's effort dial (drop effort for mechanical bulk), not by rationing dispatches — Luna is the project-default slot, Terra the overflow/rate-limit fallback.

Tokens route by capability: Opus emits judgment and specs, the cheap cross-vendor lane emits the bulk of the code, and Fable — the most expensive model available — is spent only where it changes outcomes: the hardest implementations and the final review. Because the routine lane is a *different model family* than the architect, cross-vendor review is built into the routing, not bolted on. For high-stakes work, race `codex-implementer` and `fable-implementer` on the same spec only in separate git worktrees: tell each lane its own working root, point the codex lane's `--cd` argument at that racer's worktree, and have the architect diff both worktrees' results and pick the stronger one.

The plugin ships the **orchestration skill** — the routing doctrine that teaches the session when to use each lane, the cost discipline that keeps expensive-model token volume minimal (emit judgment not volume, keep context lean, reason once then hand off), the five-part spec contract that makes context-free delegation safe, and the verification rules that keep every lane honest.

## Install

```
claude plugin marketplace add DannyMac180/fable-advisor
claude plugin install fable-advisor@fable-advisor
```

Updating an existing installation to the latest release:

```
claude plugin marketplace update fable-advisor
claude plugin update fable-advisor@fable-advisor
```

Then start your session as the architect:

```
/model opus
```

**Lite mode — one file, 30 seconds.** Don't want the full pattern? Copy [`agents/fable-advisor.md`](agents/fable-advisor.md) into `~/.claude/agents/` and keep your session on Sonnet. You get advisor consults at commitment boundaries without the orchestration layer (see "Advisor-only mode" below).

## Requirements

- **Claude Code ≥ 2.1.170** with a subscription that includes Fable 5 (Pro, Max, Team, or Enterprise — all current consumer plans qualify).
- **No Fable access** (e.g. API-key billing)? Change `model: fable` → `model: opus` in the advisor and implementer files. Same pattern, the Fable roles shift down to Opus.
- **Codex lane (the default implementer):** the `codex-implementer` agent needs the [OpenAI Codex CLI](https://github.com/openai/codex) installed and authenticated (`npm i -g @openai/codex`, then `codex login`). It invokes **GPT-5.6 Luna** — the pinned slug and reasoning effort live in one normative place, [`agents/codex-implementer.md`](agents/codex-implementer.md), which also honors a `FABLE_ADVISOR_CODEX_MODEL` env override for repinning without editing files that `claude plugin update` overwrites. GPT-5.6 access may be limited during preview; without model access, an installed/authenticated CLI, or successful authentication, the agent reports `STATUS: unavailable` — it never silently falls back to a Claude model — and the Fable lanes remain unaffected.
- Heads-up: if a pinned Claude model isn't available on your account, Claude Code silently falls back to your session model — the pattern degrades quietly rather than erroring. If results feel unremarkable, check your plan. (This quiet fallback applies only to Claude model pins — the codex lane always fails loudly with a structured error.)

Model resolution order in Claude Code: `CLAUDE_CODE_SUBAGENT_MODEL` env var → per-invocation `model` parameter → agent frontmatter → session model.

## Use it

With the session on Opus, just ask for work — the orchestration skill routes it:

```
Add rate limiting to our public API. Design it, delegate the
implementation, and verify the evidence before you call it done.
```

The architect writes the spec, picks the lane (rate limiting touches concurrency — a good case for `fable-implementer`), or races `codex-implementer` and `fable-implementer` on the same spec in separate git worktrees — each racer gets its own working root, the codex lane's `--cd` points at that racer's worktree, and the architect diffs both worktrees' results and picks the stronger one — then reads the diff and verification evidence when the report comes back, sends the finished work to `fable-advisor` for the final review, and only then reports done.

To make the doctrine always-on, add one line to your project's `CLAUDE.md`:

```
You are the architect — minimize your own token volume. Delegate all
implementation through the orchestration skill's routing table (never
type code yourself), delegate broad codebase exploration to cheap
read-only agents, verify evidence before accepting any lane's report,
and get a fable-advisor review before reporting any deliverable done.
```

## Commitment boundaries and the final review

Even the architect gets a second opinion. The `fable-advisor` agent is a read-only skeptic — consulted before architecture decisions, migrations, API designs, whenever a problem has resisted two attempts, and **always once at the end of a deliverable**, where it reads the accumulated diff with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. It never implements. It sees the code fresh, without your conversation's accumulated assumptions — that context-clean skepticism is what the final review buys.

## Advisor-only mode (the original pattern)

The minimal arrangement, for when you'd rather skip the orchestration layer: run the session on Sonnet and consult `fable-advisor` only at commitment boundaries.

```
Migrate our checkout sessions from Postgres to Redis — plan it,
consult your advisor before committing, then implement.
```

A typical consult costs cents. To make it automatic, add to your project's `CLAUDE.md`:

```
Before committing to any architecture decision, migration, or refactor
touching 3+ files, consult the fable-advisor agent and act on its verdict.
```

## FAQ

**Is this Anthropic's "advisor tool"?** No — that's a server-side API feature. These are plain Claude Code subagents plus a skill: readable, editable, no beta flags.

**Does this work on claude.ai?** No — subagent model routing is Claude Code only (CLI, desktop, VS Code, web).

**Why not just run everything on Fable?** You can. It's excellent. It's also the most expensive lane per token, and most of a session's tokens are orchestration and implementation mechanics that Opus and the codex lane handle at near-parity. Spend the premium where it changes outcomes: the hardest tasks and the final review.

**Upgrading from v3?** v4 restructures the routing: the session architect moves from Fable to **Opus**, the Grok 4.5 lane is **removed**, `codex-implementer` (the Codex lane) becomes the default typing lane, and Fable's premium is refocused on the new `fable-implementer` high-complexity lane plus a now-mandatory end-of-deliverable `fable-advisor` review. If you still want the Grok lane, grab [`grok-implementer.md` from the v3.1 tree](https://github.com/DannyMac180/fable-advisor/blob/b3b50a9/agents/grok-implementer.md).

**Why a GPT lane in a Claude plugin?** Vendor diversity. Models from one family share blind spots; an independent implementation from a different lineage catches what same-family review misses — and with Claude as the architect and reviewer, every routine diff gets cross-vendor review for free. The architect and reviewer stay Claude — the routine lane is a producer, not a judge.

## Go deeper

I write [**Attention Heads**](https://attentionheads.substack.com/?utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) — deep, evidence-backed writing on AI, cognition, and agentic engineering. The **Agentic Engineering Field Notes** series is where I publish practical advice on the craft of using AI. [Subscribe](https://attentionheads.substack.com/subscribe?utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) to get new posts to your inbox.

## License

MIT
