# Fable Advisor (Fable-architect fork)

**Fable runs the show. Opus does the typing, and GPT-5.6 Sol reviews everything before it ships.**

> Experimental fork of [DannyMac180/fable-advisor](https://github.com/DannyMac180/fable-advisor) (v4). The upstream pattern puts Opus in the architect seat to save tokens; this fork spends the premium on the architect instead — Fable owns every judgment call — and moves the cross-vendor check from the implementation side to the review side.

Claude Code lets every subagent run on a different model — and lets the session itself run on a different model than its subagents. This fork exploits that with the **architect pattern**: your session runs on **Fable 5**, acting as a full-time architect. It owns requirements, decomposition, specs, and verification — delegates the typing to Opus — and gets a **cross-vendor GPT-5.6 Sol review** of the finished work before calling anything done:

| Lane | Producer | Invocation | Route here when |
|---|---|---|---|
| Implementation | **Claude Opus** (high effort) | `opus-implementer` agent (default) | Every implementation task — Opus writes the code itself from the architect's five-part spec |
| Cross-vendor (optional) | **GPT-5.6 Luna** (max reasoning) | `codex-implementer` agent | High-stakes specs worth a second, non-Anthropic implementation — race both lanes, pick the stronger diff |
| Outside voice | **GPT-5.6 Sol** (high reasoning) | `codex-reviewer` agent | Consults at commitment boundaries (proceed / revise / rethink) and the mandatory end-of-deliverable review (ship / fix-first / rethink) — the architect does not report done before it |

Tokens route by capability: Fable emits judgment and specs (volume-light, the priciest seat kept lean), Opus emits the bulk of the code, and the review runs entirely off-Anthropic. Because the architect and implementer are both Claude, the reviewer being a *different model family* is what keeps the system honest — same-family blind spots get caught at the gate, not shipped through it. There is no separate escalation lane: when a task fails its spec twice in the Opus lane, the architect — the strongest implementer in the system — takes it over personally, and that diff still goes through the review.

The plugin ships the **orchestration skill** — the routing doctrine, the cost discipline that keeps the Fable seat volume-light (emit judgment not volume, keep context lean, reason once then hand off), the five-part spec contract that makes context-free delegation safe, and the verification rules that keep every lane honest.

## Install

```
claude plugin marketplace add haorui/fable-advisor
claude plugin install fable-advisor@fable-advisor
```

Then start your session as the architect:

```
/model fable
```

## Requirements

- **Claude Code ≥ 2.1.170** with a subscription that includes Fable 5 (Pro, Max, Team, or Enterprise — all current consumer plans qualify), since the session itself runs on Fable.
- **Codex lanes (reviewer + optional implementer):** both need the [OpenAI Codex CLI](https://github.com/openai/codex) installed and authenticated (`npm i -g @openai/codex`, then `codex login`). The reviewer invokes **GPT-5.6 Sol** as `gpt-5.6-sol` with `model_reasoning_effort=high`; the optional implementer invokes **GPT-5.6 Luna** at `max`. Without model access, an installed/authenticated CLI, or successful authentication, these agents report `STATUS: unavailable` — they never silently fall back to a Claude model. The review gate then degrades *loudly*: the architect reports the deliverable done-but-unreviewed, saying exactly that.
- Heads-up: if a pinned Claude model isn't available on your account, Claude Code silently falls back to your session model — `model: opus` in `opus-implementer` would quietly become Fable, making the typing lane *more* expensive than intended. If costs feel off, check your plan. (This quiet fallback applies only to Claude model pins — the codex lanes always fail loudly with a structured error.)

Model resolution order in Claude Code: `CLAUDE_CODE_SUBAGENT_MODEL` env var → per-invocation `model` parameter → agent frontmatter → session model.

## Use it

With the session on Fable, just ask for work — the orchestration skill routes it:

```
Add rate limiting to our public API. Design it, delegate the
implementation, and verify the evidence before you call it done.
```

The architect writes the spec, delegates to `opus-implementer` (or races it against `codex-implementer` on a high-stakes spec), reads the diff and verification evidence when the report comes back, sends the finished work through `codex-reviewer` for the cross-vendor final review, and only then reports done.

To make the doctrine always-on, add one line to your project's `CLAUDE.md`:

```
You are the architect — minimize your own token volume. Delegate all
implementation through the orchestration skill's routing table (never
type code yourself, except the documented two-failures takeover),
delegate broad codebase exploration to cheap read-only agents, consult
codex-reviewer at commitment boundaries, verify evidence before
accepting any lane's report, and get a codex-reviewer verdict before
reporting any deliverable done.
```

## The final review

Every deliverable ends at the `codex-reviewer` gate: GPT-5.6 Sol reads the accumulated diff in a read-only sandbox, with fresh eyes and no accumulated conversational assumptions, against the stated goal rather than the conversation — and returns ship / fix-first / rethink. It is the system's one non-Anthropic check: the architect and implementer share a vendor, the reviewer deliberately doesn't. A missing or unparseable verdict counts as *no review*, never as a pass — the failure modes (`unavailable`, `timeout`, `refused`) are structured and loud by design.

The same lane doubles as the **outside voice** before anything is committed. At commitment boundaries — architecture choices, migrations, API shapes, refactor strategies, or a problem that has resisted two attempts — the architect writes a short decision memo (decision, options, deciding risk) and sends it through `codex-reviewer` in CONSULT mode for a proceed / revise / rethink verdict. The decision stays with the Fable architect — there is no stronger Claude to escalate to — but it is never made unexamined: the one perspective the architect cannot manufacture for itself is a different vendor's.

## FAQ

**Why put the most expensive model in the architect seat?** Because the architect seat is where judgment concentrates: decomposition, interface design, debugging hypotheses, and verdicts on evidence. This fork bets that better judgment there beats cheaper tokens there — while the cost discipline (delegate the volume, keep the context lean) keeps the Fable seat from ever carrying the token bulk. It is still far cheaper than running a single Fable session that does its own typing.

**Why is the reviewer a GPT model?** Vendor diversity, concentrated at the gate. With Fable architecting and Opus implementing, everything productive is one family — the review is deliberately the other family, so shared blind spots get one independent look before shipping. The upstream project kept the judge Claude and the producer GPT; this fork inverts that, and the honest trade is stated plainly: the final verdict quality now rides on GPT-5.6 Sol's judgment of Claude-written code.

**What happened to fable-implementer and fable-advisor?** Both collapsed into the architect. The session *is* Fable now, so a Fable escalation lane and a Fable advisor would be the same model reviewing itself at extra hand-off cost. Hard tasks that defeat the Opus lane twice go to the architect directly; fresh-eyes review moved to the cross-vendor gate.

**Upstream versions?** This fork's lineage: upstream v4 (Opus architect, Codex routine lane, Fable escalation + review) → this v5 (Fable architect, Opus lane, Codex review). For the original pattern, use [DannyMac180/fable-advisor](https://github.com/DannyMac180/fable-advisor).

## License

MIT
