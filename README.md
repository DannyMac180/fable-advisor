# Fable Advisor

**Fable 5.1 runs the show. Codex does the typing at the effort each task deserves, and Fable reviews before anything ships.**

Claude Code lets every subagent run on a different model — and lets the session itself run on a different model than its subagents. This plugin exploits that with the **architect pattern**: your session runs on **Fable 5.1**, acting as a full-time architect. It owns requirements, decomposition, specs, and verification — routes every implementation task to the right lane at the right reasoning effort — and gets a clean-context **Fable 5.1** review of the finished work before calling anything done:

| Lane | Producer | Invocation | Route here when |
|---|---|---|---|
| Routine | **GPT-5.6 Luna** | `codex-implementer` agent (default) | The spec fully determines the outcome — Codex does the typing via the [Codex CLI](https://github.com/openai/codex) |
| High-complexity | **GPT-5.6 Sol** | `sol-implementer` agent | One-off tasks where judgment the spec can't capture decides the outcome: subtle concurrency, hard debugging, security-sensitive paths, wide refactors |
| Review | **Fable 5.1** | `fable-advisor` agent | Commitment boundaries, and **always once at the end** — the advisor reviews the accumulated changes before the architect reports done |

**Nothing is pinned to a reasoning effort.** The architect names the effort per task in the spec (`REASONING: low … max`, and `ultra` on Sol), and the lanes pass it through unchanged — mechanical edits run cheap and fast, the hard escalations run at max or ultra. The session and the advisor run at whatever `/effort` you set.

Tokens route by capability: Fable emits judgment and specs, the cross-vendor lanes emit all of the code, and the premium is spent only where it changes outcomes: the architecture and the final review. Because both implementation lanes are a *different model family* than the architect, cross-vendor review is built into the routing, not bolted on. For high-stakes work, run `codex-implementer` and `sol-implementer` on the same spec and let the architect pick the stronger diff.

The plugin ships the **orchestration skill** — the routing doctrine that teaches the session when to use each lane and each effort rung, the cost discipline that keeps Fable token volume minimal (emit judgment not volume, keep context lean, reason once then hand off), the six-part spec contract that makes context-free delegation safe, the verification rules that keep every lane honest, and how to fold in the official [Codex plugin for Claude Code](https://github.com/openai/codex-plugin-cc) when it's installed.

## Go deeper

I write [**Attention Heads**](https://attentionheads.substack.com/?utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) — deep, evidence-backed writing on AI, cognition, and agentic engineering. The **Agentic Engineering Field Notes** series is where I publish practical advice on the craft of using AI. [Subscribe](https://attentionheads.substack.com/subscribe?

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
/model fable
```

**Lite mode — one file, 30 seconds.** Don't want the full pattern? Copy [`agents/fable-advisor.md`](agents/fable-advisor.md) into `~/.claude/agents/` and keep your session on Sonnet. You get advisor consults at commitment boundaries without the orchestration layer (see "Advisor-only mode" below).

## Requirements

- **Claude Code ≥ 2.1.170** with a subscription that includes Fable 5.1 (Pro, Max, Team, or Enterprise — all current consumer plans qualify). The agents use the `fable` alias, which resolves to Fable 5.1.
- **No Fable access** (e.g. API-key billing)? Change `model: fable` → `model: opus` in `agents/fable-advisor.md` and run the session on Opus. Same pattern, the Fable role shifts down to Opus.
- **Both implementation lanes** need the [OpenAI Codex CLI](https://github.com/openai/codex) installed and authenticated (`npm i -g @openai/codex`, then `codex login`). `codex-implementer` invokes **GPT-5.6 Luna** (`gpt-5.6-luna`, efforts low–max) and `sol-implementer` invokes **GPT-5.6 Sol** (`gpt-5.6-sol`, efforts low–ultra). GPT-5.6 access may be limited during preview; without model access, an installed/authenticated CLI, or successful authentication, a lane reports `STATUS: unavailable` — it never silently falls back to a Claude model. Without Codex at all, the pattern degrades to advisor-only mode (below).
- **Optional: the [Codex plugin for Claude Code](https://github.com/openai/codex-plugin-cc)** (`/plugin marketplace add openai/codex-plugin-cc`, then `/plugin install codex@openai-codex`). When it's enabled, the orchestration skill uses `/codex:adversarial-review` as a GPT-family second reviewer ahead of the Fable review, `/codex:rescue` as a user-driven delegation path, and `/codex:setup` to diagnose a lane that reports `unavailable`. Not a dependency — the lanes drive `codex exec` directly either way.
- Heads-up: if a pinned Claude model isn't available on your account, Claude Code silently falls back to your session model — the pattern degrades quietly rather than erroring. If advisor verdicts feel unremarkable, check your plan. (This quiet fallback applies only to Claude model pins — the codex lanes always fail loudly with a structured error.)

Model resolution order in Claude Code: `CLAUDE_CODE_SUBAGENT_MODEL` env var → per-invocation `model` parameter → agent frontmatter → session model. Effort resolution: `CLAUDE_CODE_EFFORT_LEVEL` env var → agent frontmatter `effort` → session `/effort`. None of this plugin's agents set `effort`, so the advisor follows your session; the codex lanes take theirs from the spec.

## Use it

With the session on Fable, just ask for work — the orchestration skill routes it:

```
Add rate limiting to our public API. Design it, delegate the
implementation, and verify the evidence before you call it done.
```

The architect writes the spec, picks the lane and effort (rate limiting touches concurrency — a good case for `sol-implementer` at `max`, or for racing it against `codex-implementer` and picking the stronger diff), reads the diff and verification evidence when the report comes back, sends the finished work to `fable-advisor` for the final review, and only then reports done.

To make the doctrine always-on, add one line to your project's `CLAUDE.md`:

```
You are the architect — minimize your own token volume. Delegate all
implementation through the orchestration skill's routing table (never
type code yourself), name a reasoning effort per task, delegate broad
codebase exploration to cheap read-only agents, verify evidence before
accepting any lane's report, and get a fable-advisor review before
reporting any deliverable done.
```

## Commitment boundaries and the final review

Even the architect gets a second opinion. The `fable-advisor` agent is a read-only skeptic on the same model as the architect but in a clean context — — consulted before architecture decisions, migrations, API designs, whenever a problem has resisted two attempts, and **always once at the end of a deliverable**, where it reads the accumulated diff with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. It never implements. It sees the code fresh, without your conversation's accumulated assumptions — that context-clean skepticism is what the final review buys. For an independent-model review on top, the Codex plugin's `/codex:adversarial-review` slots in just before it.

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

**Why not just let Fable write the code too?** You can. It's excellent. It's also the most expensive model per token, and most of a session's tokens are implementation mechanics that the codex lanes handle at near-parity — and from a different vendor, which buys you a real second opinion. Spend the premium where it changes outcomes: the architecture and the final review.

**Upgrading from v4?** v5 moves the session architect from Opus to **Fable 5.1**, replaces the Fable 5 `fable-implementer` lane with **`sol-implementer`** (GPT-5.6 Sol via Codex), and **unpins reasoning effort everywhere** — the architect names it per task in a new sixth spec line. The advisor is now Fable 5.1. The Codex plugin integration is new and optional. If you still want a Claude implementation lane, grab [`fable-implementer.md` from the v4.0 tree](https://github.com/DannyMac180/fable-advisor/blob/ad2bdc3/agents/fable-implementer.md).

**Upgrading from v3?** v4 moved the architect to Opus, removed the Grok 4.5 lane, and made `codex-implementer` the default typing lane; if you still want the Grok lane, grab [`grok-implementer.md` from the v3.1 tree](https://github.com/DannyMac180/fable-advisor/blob/b3b50a9/agents/grok-implementer.md).

**Why GPT lanes in a Claude plugin?** Vendor diversity. Models from one family share blind spots; an independent implementation from a different lineage catches what same-family review misses — and with Claude as the architect and reviewer, every diff gets cross-vendor review for free. The architect and reviewer stay Claude — the lanes are producers, not judges.
utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) to get new posts to your inbox.

## License

MIT
