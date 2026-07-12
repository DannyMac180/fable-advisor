# Fable Advisor

**The smartest model runs the show. Cheaper models do the typing.**

Claude Code lets every subagent run on a different model — and lets the session itself run on a different model than its subagents. This plugin exploits that with the **architect pattern**: your session runs on **Fable 5**, Anthropic's most capable model, acting as a full-time architect. It owns requirements, decomposition, specs, and verification — and routes every implementation task to the cheapest adequate lane:

| Lane | Producer | Invocation | Route here when |
|---|---|---|---|
| Routine | **Grok 4.5** | `grok-implementer` agent (default) | The spec fully determines the outcome — Grok does the typing via the [Grok CLI](https://x.ai/cli) |
| Cross-vendor | GPT-5.6 Sol (high reasoning) | `codex-implementer` agent | Correctness-critical, or you want a second independent implementation to compare |
| Judgment | Fable 5 | `fable-advisor` agent | Commitment boundaries — see below |

Tokens route by volume: the expensive model emits the fewest tokens (judgment and specs), cheap lanes emit the most (code). Implementation mechanics are ~90% of a session's tokens and Grok 4.5 handles them at near-parity — so this runs far cheaper than Fable-for-everything, and every implementation comes from a *different model family* than the architect that reviews it: cross-vendor review is built into the routing, not bolted on. For high-stakes work, race `grok-implementer` and `codex-implementer` on the same spec and let the architect pick the stronger diff.

The plugin ships the **orchestration skill** — the routing doctrine that teaches the session when to use each lane, the cost discipline that keeps the expensive model's own token volume minimal (emit judgment not volume, keep context lean, reason once then hand off), the five-part spec contract that makes context-free delegation safe, and the verification rules that keep cheap lanes honest.

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

- **Claude Code ≥ 2.1.170** with a subscription that includes Fable 5 (Pro, Max, Team, or Enterprise — all current consumer plans qualify).
- **No Fable access** (e.g. API-key billing)? Use `/model opus` for the session and change `model: fable` → `model: opus` in the advisor file. Same pattern, model tiers shift down one.
- **Grok lane (the default implementer):** the `grok-implementer` agent needs the [xAI Grok CLI](https://x.ai/cli) installed and authenticated (install from [x.ai/cli](https://x.ai/cli), then `grok login`). It drives **Grok 4.5** headlessly (`grok --prompt-file … -m grok-4.5`). Without it the agent reports `STATUS: unavailable` — it never silently falls back to a Claude model.
- **Codex lane (optional):** the `codex-implementer` agent needs the [OpenAI Codex CLI](https://github.com/openai/codex) installed and authenticated (`npm i -g @openai/codex`, then `codex login`). It invokes **GPT-5.6 Sol** as `gpt-5.6-sol` with `model_reasoning_effort=high`. GPT-5.6 access may be limited during preview; without model access, an installed/authenticated CLI, or successful authentication, the agent reports `STATUS: unavailable` and the other lanes remain unaffected.
- Heads-up: if a pinned Claude model isn't available on your account, Claude Code silently falls back to your session model — the pattern degrades quietly rather than erroring. If results feel unremarkable, check your plan. (This quiet fallback applies only to Claude model pins — the grok and codex lanes always fail loudly with a structured error.)

Model resolution order in Claude Code: `CLAUDE_CODE_SUBAGENT_MODEL` env var → per-invocation `model` parameter → agent frontmatter → session model.

## Use it

With the session on Fable, just ask for work — the orchestration skill routes it:

```
Add rate limiting to our public API. Design it, delegate the
implementation, and verify the evidence before you call it done.
```

The architect writes the spec, picks the lane (rate limiting touches concurrency — a good case for racing `grok-implementer` against `codex-implementer` and picking the stronger diff), reads the diff and verification evidence when the report comes back, and only then reports done.

### Smithers workflow

This repo also ships a durable Smithers workflow that turns a work request into the Fable Advisor routing packet: intake, CLI preflight, lane decision, five-part implementer spec, advisor prompt, and verification contract.

```bash
bunx smithers-orchestrator workflow run fable-advisor \
  --input '{
    "prompt":"Add rate limiting to our public API",
    "risk":"correctness-critical",
    "files":["src/api/**"],
    "interfaces":"Do not change public response bodies.",
    "verification":"npm test && npm run lint"
  }'
```

The workflow is orchestration-only by design: it does not silently edit code or substitute unavailable lanes. If `grok`, `codex`, or `claude` are missing from the shell, the output says so and downgrades or blocks according to the routing doctrine.

To make the doctrine always-on, add one line to your project's `CLAUDE.md`:

```
You are the architect running the most expensive model — minimize your
own token volume. Delegate all implementation through the orchestration
skill's routing table (never type code yourself), delegate broad codebase
exploration to cheap read-only agents, and verify evidence before
accepting any lane's report.
```

## Commitment boundaries

Even the architect gets a second opinion. The `fable-advisor` agent is a read-only skeptic — consulted before architecture decisions, migrations, API designs, and whenever a problem has resisted two attempts. It reads your actual code and returns a verdict in under 300 words. It never implements. Running it from a Fable session still pays: it sees the code fresh, without your conversation's accumulated assumptions.

## Advisor-only mode (the original pattern)

The inverse arrangement, for when you'd rather keep the session cheap: run the session on Sonnet and consult `fable-advisor` only at commitment boundaries.

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

**Why not just run everything on Fable?** You can. It's excellent. It's also the most expensive lane per token, and most of a session's tokens are implementation mechanics that the cheap lanes handle at near-parity. Spend the premium where judgment lives.

**Upgrading from v2?** v3 replaced the Sonnet/Opus `implementer` agent with `grok-implementer` — Grok 4.5 via the [Grok CLI](https://x.ai/cli) is now the default typing lane. v3.1 upgrades the optional `codex-implementer` lane from GPT-5.5 to GPT-5.6 Sol at high reasoning. The `fable-advisor` agent and advisor-only mode work exactly as before. If you preferred the Claude implementer, grab [`implementer.md` from the v2.1.0 tag](https://github.com/DannyMac180/fable-advisor/blob/3c1846c/agents/implementer.md).

**Why Grok and GPT-5.6 Sol lanes in a Claude plugin?** Vendor diversity. Models from one family share blind spots; an independent implementation from a different lineage catches what same-family review misses — and with Claude as the architect, *every* diff now gets cross-vendor review for free. The architect stays Claude — the lanes are producers, not judges.

## Go deeper

I write [**Attention Heads**](https://attentionheads.substack.com/?utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) — deep, evidence-backed writing on AI, cognition, and agentic engineering. The **Agentic Engineering Field Notes** series is where I publish practical advice on the craft of using AI. [Subscribe](https://attentionheads.substack.com/subscribe?utm_source=github&utm_medium=readme&utm_campaign=fable-advisor) to get new posts to your inbox.

## License

MIT
