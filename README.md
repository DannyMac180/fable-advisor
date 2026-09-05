# arch-advisor

**Your Claude session runs the show as an architect. Codex does the typing, on whichever model you configure, at the effort each task deserves. A clean-context advisor reviews before anything ships.**

Claude Code lets every subagent run on a different model — and lets the session itself run on a different model than its subagents. This plugin exploits that with the **architect pattern**: your session acts as a full-time architect. It owns requirements, decomposition, specs, and verification — routes every implementation task to the right lane at the right reasoning effort — and gets a clean-context review of the finished work before calling anything done.

| Lane | Ships as | Invocation | Route here when |
|---|---|---|---|
| `routine` | GPT-5.6 Luna | `implementer-routine` (default) | The spec fully determines the outcome — Codex does the typing via the [Codex CLI](https://github.com/openai/codex) |
| `complex` | GPT-6 Astra | `implementer-complex` | Judgment the spec can't capture decides the outcome: subtle concurrency, hard debugging, security-sensitive paths, wide refactors — and the second runner when you race two lanes on one spec |
| review | strongest Claude you have | `arch-advisor` | Commitment boundaries, and always once at the end of a deliverable |

## What this fork changes

This is a fork of [DannyMac180/fable-advisor](https://github.com/DannyMac180/fable-advisor), whose architecture and prose it keeps almost entirely. One thing is different, and it is the reason the fork exists:

**Nothing is hardcoded to a model.** Upstream bakes `gpt-5.6-luna` and `gpt-5.6-sol` into the agent files, along with each one's legal effort rungs. Here, every lane's model, effort rungs and wall-clock cap live in [`config/lanes.json`](config/lanes.json), resolved at runtime by [`scripts/lane.sh`](scripts/lane.sh). Pointing a lane at a new Codex model is a config edit, not an agent rewrite — which is what you want the week a new model ships.

The plugin is also no longer named after one specific Claude model, because the architect model is your choice (`/model`), not the plugin's.

**No Sol lane.** Upstream escalates to `gpt-5.6-sol`; this fork escalates to `gpt-6-astra` instead. Re-point it in `lanes.json` if you disagree — that is the whole point of the config.

**Effort validation now actually happens.** The `codex` CLI does *not* validate `model_reasoning_effort` client-side: hand it a garbage rung and it prints `reasoning effort: garbage` and lets the API reject the run minutes later. Upstream's "refuse rather than round" promise rests entirely on a list written in prose inside a markdown file. Here `lane.sh validate` checks the requested rung against the lane's declared rungs and fails closed, before a token is spent.

## Install

```bash
claude plugin marketplace add rubensousa-uw/arch-advisor
claude plugin install arch-advisor@arch-advisor
```

Requires `jq` (`brew install jq`) for lane resolution, and the [OpenAI Codex CLI](https://github.com/openai/codex) installed and authenticated (`npm i -g @openai/codex`, then `codex login`) for the implementation lanes.

Then set your session model — anything capable will do; the doctrine doesn't care which:

```
/model
```

## Configuring the lanes

See what is in effect:

```bash
scripts/lane.sh list
```

To change it, copy `config/lanes.json` to whichever scope you want and edit it. The first match wins:

| Precedence | Location | Scope |
|---|---|---|
| 1 | `$ARCH_ADVISOR_CONFIG` | Explicit, per-invocation |
| 2 | `./.arch-advisor/lanes.json` | This project |
| 3 | `~/.claude/arch-advisor/lanes.json` | All your projects |
| 4 | `config/lanes.json` | Plugin default |

Each lane declares four things:

```json
"routine": {
  "agent": "implementer-routine",
  "model": "gpt-5.6-luna",
  "efforts": ["low", "medium", "high", "xhigh", "max"],
  "timeout_seconds": 600
}
```

`efforts: null` means *undeclared* — the lane then omits the effort flag entirely and lets codex fall back to your `~/.codex/config.toml` default, flagging it in the report. Use it when you add a model whose rungs you have not confirmed.

### Effort rungs, measured

The shipped rungs were probed against the live CLI on 2026-09-05 rather than copied from documentation, which turned out to matter — upstream's lists are wrong in two places:

| | `minimal` | `none` | `low`–`max` | `ultra` |
|---|---|---|---|---|
| `gpt-5.6-luna` | rejected | accepted by the API | accepted | **accepted** (upstream says Sol-only) |
| `gpt-6-astra` | rejected | rejected | accepted | accepted |

`ultra` is not an API `reasoning.effort` value at all — the API's own error message lists only `low, medium, high, xhigh, max`. It is a Codex CLI construct that adds internal task delegation, and it passes on both models.

**`ultra` ships disabled**, even though it is verified working, because it burns tokens fast enough to deserve a deliberate opt-in rather than a default. `lane.sh` refuses it like any undeclared rung; add `"ultra"` to a lane's `efforts` array when you actually want it. `none` is real on Luna but likewise omitted: an implementation lane should not run without reasoning.

**One honest limitation:** a lane maps 1:1 to an agent file, because Claude Code discovers agents statically at startup. You can re-point the two shipped lanes at any models you like without touching an agent — but a genuinely *third* lane also needs a new `agents/*.md`, copied from an existing one.

## Testing it

Three levels, cheapest first.

**Free — the routing logic, no model calls.** Everything except codex itself:

```bash
scripts/lane.sh list                    # what is configured
scripts/lane.sh validate routine xhigh  # exit 0
scripts/lane.sh validate routine ultra  # exit 4, refuses rather than rounding
scripts/smoke.sh --dry-run              # print each lane's exact codex command
```

**A few thousand tokens — that codex actually answers.** One tiny read-only call per lane, at the lowest declared rung:

```bash
scripts/smoke.sh              # every lane
scripts/smoke.sh complex      # one lane
scripts/smoke.sh --effort max # at a specific rung
```

It fails loudly on an unauthenticated CLI, a model your account cannot reach, a spent quota, or a rung the API rejects — the four things that actually break a lane in practice.

**A real task — the whole pattern.** Ask the architect for something small in a scratch repo and watch it route, delegate, verify and review. This is the only level that exercises the spec contract and the empty-diff check, and the only one that costs real money.

## Use it

Just ask for work — the orchestration skill routes it:

```
Add rate limiting to the public API. Design it, delegate the implementation,
and verify with evidence before you call it done.
```

The architect writes the spec, picks the lane and effort, reads the diff and verification evidence when the report comes back, sends the finished work to `arch-advisor` for final review, and only then reports done.

To make the doctrine always-on, add one line to your project's `CLAUDE.md`:

```
You are the architect — minimize your own token volume. Delegate all implementation
through the orchestration skill's routing table (never type code yourself), name a
reasoning effort per task, delegate broad codebase exploration to cheap read-only
agents, verify evidence before accepting any lane's report, and get an arch-advisor
review before reporting any deliverable done.
```

## Commitment boundaries and final review

Even the architect gets a second opinion. The `arch-advisor` agent is a read-only skeptic on the same model as the architect but in a clean context — consulted before architecture decisions, migrations and API designs, whenever a problem has resisted two attempts, and **always once at the end of a deliverable**, where it reads the accumulated diff with fresh eyes, against the stated goal rather than the conversation, and returns ship / fix-first / rethink. It never implements.

It is a fresh-eyes check, not an independent-model check — the cross-vendor independence comes from the Codex lanes producing the code. For an independent-model review on top, the official [Codex plugin](https://github.com/openai/codex-plugin-cc)'s `/codex:adversarial-review` slots in just before it.

## Credit

The pattern, the orchestration doctrine, the spec contract and nearly all of the prose are [Dan McAteer's](https://github.com/DannyMac180). He writes [Attention Heads](https://attentionheads.substack.com/), where the pattern is explained at length. MIT licensed, upstream and here.
