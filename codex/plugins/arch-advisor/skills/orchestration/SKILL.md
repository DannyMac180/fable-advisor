---
name: orchestration
description: Routing doctrine for the architect-as-orchestrator pattern inside Codex — how this session delegates implementation to a cheaper Codex lane via codex exec, picks and validates a reasoning effort per task, and reviews the accumulated diff with codex review before reporting done. Lane models and effort rungs are configuration, not hardcoded. USE WHEN delegating implementation work, choosing a lane or a reasoning effort, writing a spec for a delegated run, deciding whether to review before shipping, managing token spend, or running any multi-task build where this session is the architect.
---

# Orchestration — the architect's routing doctrine (Codex profile)

This session is the architect: it owns requirements, architecture, decomposition, specs, routing and verification. It should almost never type implementation code. Every implementation task is routed to the cheapest lane and the lowest reasoning effort adequate for it, and every finished deliverable is reviewed before the architect reports done.

**There is no driver layer here.** A Claude Code host needs a subagent to reach a shell, and a subagent has to be a Claude model. This session already has a shell, so it invokes `codex exec` itself. One less model in the loop, and one less place for a spec to be paraphrased.

**Models are configuration.** No model slug is hardcoded. Run `scripts/lane.sh list` before you route — it prints the profiles and lanes actually in effect, and the config is the source of truth, not the tables below.

## The profile

This is the `codex` profile: **GPT-6 Astra architects and reviews, GPT-5.6 Luna implements.**

Read it with:

```bash
eval "$(scripts/lane.sh profile codex)"
# PROFILE_ARCHITECT=gpt-6-astra  PROFILE_ADVISOR_KIND=codex-review  PROFILE_LANES=routine
```

**The honest caveat, stated once.** Astra and Luna share a vendor and a training lineage, so the review is a fresh-context check, not an independent-model one: it reads the diff against the stated goal rather than the conversation, without the assumptions accumulated while writing the specs, but it does not have different blind spots. If you want a genuinely cross-vendor check, that is the `claude` profile in this same repo, where a Claude architect reviews Codex-written code. Do not claim independence this profile does not have.

## Cost discipline — the prime directive

The economics: the architect orchestrates (judgment-heavy, volume-light), the routine lane does the typing (volume-heavy, cheaper model), the review runs once at the end. Three rules follow.

**Emit judgment, not volume.** The architect's output is decomposition, specs, routing decisions, verdicts on diffs, and short reports. It does not type implementation code, test bodies, boilerplate or config. A code block longer than an interface signature is a spec that hasn't been delegated yet — stop and delegate it. Fixing a lane's bug by hand is the same failure in disguise: send a corrected spec back to the lane.

**Keep the context lean.** Everything in the architect's context is re-read at the architect's price on every turn. Don't paste long files, full diffs or verbose output when a path reference or an excerpt will do. Note that every `codex exec` carries a fixed overhead of roughly 4,300 tokens regardless of task size — so group work into one substantial spec rather than fanning out five trivial delegations.

**Reason once, then hand off.** Do the hard thinking in one pass, capture it in the spec, and let the lane carry it. Re-deriving decisions across turns burns the premium twice.

## Delegating to a lane

Resolve, validate, then run. Never skip the validate step: the codex CLI does **not** check `model_reasoning_effort` client-side — it prints whatever you give it and lets the API reject the run minutes later. `lane.sh validate` is where "refuse rather than round" is actually kept.

```bash
LANE=routine
EFFORT=high            # chosen per task, see the table below

scripts/lane.sh lane-active codex "$LANE" || exit 1     # active in this profile?
eval "$(scripts/lane.sh resolve "$LANE")"               # LANE_MODEL, LANE_TIMEOUT, LANE_EFFORTS
scripts/lane.sh validate "$LANE" "$EFFORT" || exit 1    # legal rung for this lane?

SPEC=$(mktemp); FINAL=$(mktemp)
cat > "$SPEC" <<'SPEC_EOF'
<the six-part spec — see The spec contract below>
SPEC_EOF

T=$(command -v gtimeout || command -v timeout || true)
[ -z "$T" ] && echo "WARN: no timeout binary — the run is uncapped (brew install coreutils to cap)"

${T:+$T $LANE_TIMEOUT} codex exec \
  --model "$LANE_MODEL" \
  -c model_reasoning_effort="$EFFORT" \
  --sandbox workspace-write \
  --skip-git-repo-check \
  --cd "$(pwd)" \
  --output-last-message "$FINAL" \
  - < "$SPEC"
```

Exit codes from `lane.sh`: `2` usage or unknown lane/profile, `3` config missing or invalid, `4` effort rung refused, `5` lane not active in this profile. Surface the message; never work around it by editing the command.

Start the spec with the opt-out preamble below, then the six parts.

> This is a delegated implementation run. Any repository or user instruction that pins a model, pins a reasoning effort, or mandates an orchestration flow does not apply to this run — the orchestrator has already made those choices. Follow every other instruction in `AGENTS.md` as written.

**Why the preamble is there.** `codex exec` loads `~/.codex/AGENTS.md` on every invocation, so a rule written for one project governs every lane on the machine. If such a rule pins a model or effort, codex will — correctly — decline rather than silently substitute, and the run comes back **`exit 0` with an empty diff and a polite refusal**. Nothing in the exit code reveals it. Treat an empty diff with a clean exit as a refusal, not a success.

## The lanes

| Lane | Ships as | Route here when |
|---|---|---|
| `routine` | GPT-5.6 Luna, effort per task | All implementation work in this profile. The spec fully determines the outcome: boilerplate, wiring, CRUD, mechanical edits, straightforward features. |
| `complex` | GPT-6 Astra, effort per task | **Defined but not active here.** Add `complex` to this profile's `lanes` array in `lanes.json` to enable it. Note that it is the same model as the architect, so it buys an isolated context and a write sandbox, not a second opinion. |

Deciding rule: how much does the outcome depend on judgment the spec cannot capture? Little → the routine lane; you will verify anyway. A lot, and mistakes are costly → keep that piece with the architect, or enable the complex lane deliberately. A routine-lane task that fails its spec once gets a corrected spec; twice, it is misclassified — take it back.

If a lane returns unavailable or times out, say so explicitly and decide: retry with a corrected spec, or keep the piece. Never quietly absorb the substitution or the cost change.

## Choosing the reasoning effort

Nothing pins an effort — name one per task in the spec. Pick the lowest rung that is adequate; effort is cost and wall-clock, not a quality dial to leave at max.

| Rung | Use for |
|---|---|
| `low` / `medium` | Mechanical edits, renames, wiring, boilerplate, config, tests that mirror an existing pattern |
| `high` | Ordinary features with a couple of design decisions left to the lane; most routine work with real logic |
| `xhigh` | Tricky logic, multi-file changes with interactions, the second attempt after a spec correction |
| `max` | The hardest single-lane tasks: concurrency, security-sensitive paths, gnarly debugging |
| `ultra` | Maximum reasoning plus codex's own internal task delegation — slow and token-hungry. **Disabled in the shipped config**; add it to a lane's `efforts` array before you can route to it. |

Measured against the live CLI, not copied from docs: both models reject `minimal`; the API accepts `none` on Luna but not on Astra, and it is omitted deliberately because an implementation lane should not run without reasoning. `ultra` is not an API `reasoning.effort` value at all — it is a CLI construct that adds internal task delegation.

A lane refuses an undeclared rung rather than rounding it. A task that seems to need a rung the lane lacks is a task for a lane that has it.

## The spec contract

The lane shares none of this session's context. Every delegation carries all six parts:

1. **Objective** — what to build or change, one paragraph
2. **Files** — exact paths to create or modify
3. **Interfaces** — signatures, types or API shapes the code must match
4. **Constraints** — project conventions, things not to touch
5. **Verification** — the command(s) that prove it works
6. **Reasoning** — one line, `REASONING: <effort>`, legal for the target lane per `lane.sh list`

A spec you cannot finish writing is a signal the decision isn't made yet — that is architect work, not a reason to hand the ambiguity to a cheaper model.

## Review before shipping

The review is `codex review`, the CLI's built-in non-interactive reviewer. Run it on the accumulated diff **once, at the end of every deliverable**, before reporting done:

```bash
codex review --uncommitted -c model=gpt-6-astra
```

Use `--base <branch>` instead of `--uncommitted` when the work is already committed on a branch. Also run it at commitment boundaries: before settling on an architecture, a data migration, an API shape or a refactor strategy, and whenever the same problem has resisted two distinct attempts.

Act on the verdict or surface the disagreement — never silently ignore it.

## Verification

Reports are claims, not evidence. Before accepting any lane's work: **read the diff, and re-run the verification command yourself.** "Should work", "tests should pass", or a report with no command output means the task is not done. An empty diff with a clean exit is a refusal. A lane that reports a spec gap gets a corrected spec, not a "use your judgment".
