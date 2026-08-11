# fable-advisor — Improvement Plan

Baseline: `ad2bdc3` (v4.0.0 tag + 2 untagged commits), 2026-08-11.

The doctrine is strong — loud failure over silent substitution, evidence over
claims, a mandatory review gate. The problems are almost all mechanical: one
load-bearing bug in how the codex lane's shell steps are written, a handful of
contract gaps between what one file promises and another file handles, and
release hygiene that has already drifted (the shipped `4.0.0` and the tagged
`v4.0.0` differ in model, effort, and prompt preamble). Plan is ordered by
severity; each item names the problem, the change, and how to know it's done.

---

## P0 — Correctness bugs (ship as v4.0.1)

### 1. Codex invocation breaks across Bash calls
**Problem.** `agents/codex-implementer.md` presents step 1 (write `$SPEC`/`$FINAL`
via `mktemp`) and step 2 (the `codex exec` invocation) as separate fenced
blocks. Claude Code runs each Bash tool call in a fresh shell — env vars don't
persist. An agent that follows the file literally runs step 2 in a shell where
`$SPEC` and `$FINAL` are unset: the `- < "$SPEC"` redirect fails loudly ("No
such file or directory"), and even after the agent recovers by re-running both
blocks together, step 3 in yet another fresh shell can't re-read `$FINAL`. The
failure is loud, but it sits on the plugin's core path and every run trips it.

**Change.** Merge steps 1–2 into one fenced block presented as a single Bash
invocation, and state the constraint explicitly: "Steps 1–2 are ONE Bash call —
shell state does not survive between tool calls." Step 3 (verification) can stay
separate but must re-derive `$FINAL` — simplest fix: have the single block
`echo "FINAL=$FINAL"` so the wrapper can carry the path forward, or `cat "$FINAL"`
at the end of the same block.

**Done when.** The file contains no variable defined in one block and consumed
in another.

### 2. Preflight can't detect a missing login
**Problem.** The file promises "installed and authenticated" preflight, but
`command -v codex && codex --version` only proves installation. The *mapping*
of auth failures to `STATUS: unavailable` is already documented (lines 21–28
cover both cases) — the gap is *detection*: nothing in preflight probes login
state, so a logged-out CLI is only discovered mid-run at `exec` time. That
failure is loud, which makes this the least severe P0 — fine to let it slip to
v4.1.0.

**Change.** Add an auth probe to preflight (`codex login status` exits non-zero
when logged out — verify against the current CLI and pin the actual command) so
the lane reports `unavailable` before burning a run.

**Done when.** Preflight detects a logged-out CLI without invoking `codex exec`.

### 3. Refusal detection dies outside git repos
**Problem.** The flag table sells `--skip-git-repo-check` as "works outside git
repos", but the empty-diff refusal detector — which the file itself calls the
thing that "actually catches a refusal" — is `git diff`. Outside a repo that
command fails outright (fatal, exit 128), leaving the wrapper with no working
refusal check and no documented fallback.

**Change.** Pick one: (a) require a git repo and drop the "works outside git
repos" claim, or (b) keep the flag and add a non-git fallback (snapshot
`find . -type f -newer "$SPEC"` after the run). Recommend (a) — simpler, and
Claude Code sessions are overwhelmingly in repos.

**Done when.** The claim and the detection mechanism agree.

### 4. `fable-advisor` is asked to read diffs it cannot obtain
**Problem.** The advisor's tools are `Read, Grep, Glob` — no Bash — yet its body
says "read the diff against the stated goal" and the skill says to "pass it the
diff". The only remaining channel is pasting the diff into the prompt, which the
skill's own cost doctrine forbids.

**Change.** Define the handoff: the architect writes the diff to a file
(`git diff > /tmp/deliverable.diff` or a path under the session dir) and passes
the *path*; the advisor Reads it plus the touched files. Document this in both
`agents/fable-advisor.md` ("expect a diff path, not an inline diff") and
`skills/orchestration/SKILL.md`'s review section. Alternative — granting the
advisor Bash — is worse: it weakens the "advises only, never implements" wall.

**Done when.** Both files describe the same diff-path handoff.

### 5. Lane racing corrupts the working tree
**Problem.** README and SKILL.md recommend racing `codex-implementer` and
`fable-implementer` on the same spec — two agents writing the same files in the
same tree, two sentences after the parallelism rule requires "no shared files".

**Change.** Require isolation for races: each racer runs in its own git worktree
(Claude Code's Agent tool supports worktree isolation; codex gets `--cd` pointed
at a worktree). Architect diffs the two worktrees and picks. If that's judged
too heavy, delete the racing recommendation instead — as written it's a footgun.

**Done when.** Racing is either isolated or gone from both files.

---

## P1 — Contract gaps (v4.1.0)

### 6. Unify the status vocabulary and complete the failure routing
`codex-implementer` returns `complete|partial|timeout|unavailable|refused`;
`fable-implementer` returns `complete|partial|blocked`. SKILL.md routes only
`unavailable|timeout`. Nothing tells the architect what to do with `refused`,
`partial`, or `blocked` — including the AGENTS.md-refusal mode the plugin went
to great lengths to detect. Define one shared status enum in SKILL.md with an
architect action per status (e.g. `refused` → prepend/adjust preamble once, then
escalate; `partial` → corrected spec with the gap named; `blocked` → architect
decision). Add `REASON:` to the standard report schema (today it appears only in
the preflight example, though a rule requires it for `refused`).

### 7. Document timeout detection
The wrapper is told to "report `STATUS: timeout`" but not how to know: state
that `timeout`/`gtimeout` exits 124, and that 124 ⇒ `STATUS: timeout` with
whatever landed in the diff.

### 8. Temp-file hygiene
Add cleanup to the single merged block (`trap 'rm -f "$SPEC" "$FINAL"' EXIT` —
after `$FINAL` is read) and use a `mktemp` form that behaves the same on GNU and
BSD (`mktemp "${TMPDIR:-/tmp}/codex-spec.XXXXXX"`), since the file already cares
about macOS portability for `timeout`.

---

## P2 — Maintainability and release hygiene (v4.1.0)

### 9. Centralize the model pins
The literal slug `gpt-5.6-luna` appears 4 times across 2 files (README plus
three sites in `codex-implementer.md`); counting prose forms ("GPT-5.6 Luna"),
the model is named in ~13 sites across 5 files — plus `model: fable` ×2 and
`model: sonnet` ×1 in agent frontmatter. Every repin so far (three in four
weeks) touched most of them. Full centralization isn't possible in a prompt-only
plugin, but two moves cut the surface:
- Make `agents/codex-implementer.md` the *only* place the codex slug and effort
  appear normatively; README/SKILL/manifests say "the codex lane's pinned
  model — see codex-implementer.md" instead of naming it.
- Honor an env-var override (`FABLE_ADVISOR_CODEX_MODEL`, read in the merged
  Bash block: `--model "${FABLE_ADVISOR_CODEX_MODEL:-gpt-5.6-luna}"`) so users
  can repin without editing files that `claude plugin update` will overwrite —
  the README already flags that exact failure for Claude pins via
  `CLAUDE_CODE_SUBAGENT_MODEL`; this is the codex-side equivalent.

### 10. Release hygiene
- Bump to 4.0.1/4.1.0 with the P0/P1 fixes — HEAD already differs from the
  v4.0.0 tag in model, effort, and preamble with no bump; that's the defect to
  stop repeating.
- Add `CHANGELOG.md` (backfill from the 11 commit subjects; note untagged
  v1/v2/v2.1/v3/v3.1 SHAs so references like the README's "v3.1 tree" link
  resolve to something named).
- Tag every release going forward; retro-tag `b3b50a9` as `v3.1` so the README
  link is honest.

### 11. CI that would have caught the drift that already happened
Add one GitHub Actions workflow (no tests exist; the AGENTS.md refusal was
found in production):
- JSON validity for both manifests; frontmatter presence/shape for all agents
  (`name`, `model`, `tools`, `description`).
- Consistency greps: version in `plugin.json` == latest `CHANGELOG.md` entry;
  the codex model slug appears only in its one normative site (per item 9);
  no variable defined in one fenced block and consumed in another (per item 1 —
  a ~10-line script can lint this).
- Optional smoke job (manual trigger): preflight against a real codex install.

### 12. Manifest completeness
`marketplace.json` has no version, license, keywords, or category on the plugin
entry, and its two descriptions drift independently from `plugin.json`'s. Add
the missing fields and reduce the three hand-maintained blurbs to one canonical
sentence reused verbatim.

---

## P3 — Doctrine polish (v4.1.x, docs-only)

### 13. Resolve "never type code" vs "keep that piece with the architect"
The CLAUDE.md snippet says never; SKILL.md line 30 offers "keep that piece with
the architect" as a routing outcome. Pick the real rule — suggested: the
architect may type only when a spec would be longer than the diff, and must say
so in its report — and state it identically in both places.

### 14. Reconcile cost discipline with verification duty
"Keep the context lean" and "independently re-run verification / read the diff"
pull opposite directions. State the intended balance: the *wrapper lanes* read
full diffs and quote evidence; the *architect* reads reports and spot-checks,
entering full diffs into its context only at commitment boundaries (where the
advisor gets the diff path anyway, per item 4).

### 15. README accuracy pass
- "Change `model: fable` → `model: opus` in the advisor and implementer files"
  — only two of three agents pin `fable`; name the two files exactly.
- Warn that a globally-set `CLAUDE_CODE_SUBAGENT_MODEL` outranks every
  frontmatter pin in the plugin (the README documents the precedence order but
  not this consequence).
- Note the honest cost accounting: the codex lane's wrapper is a Sonnet agent
  burning Claude tokens on preflight/supervision/re-verification; "never falls
  back to a Claude model" is true of the work, not the babysitter.
- Move "Observed live 2026-08-04" and "Luna supports low/medium/high/xhigh/max;
  there is no `ultra`" from prompt text into CHANGELOG/README where dated claims
  belong; prompts should carry rules, not perishable facts.

---

## Suggested sequencing

1. **v4.0.1** — items 1–5 (correctness) + tag + CHANGELOG started. Small diffs,
   all in `agents/*.md` + SKILL.md; highest payoff per line.
2. **v4.1.0** — items 6–12 (contracts, pins, CI, manifests).
3. **v4.1.x** — items 13–15 (docs-only polish), safe to trickle.

Items 1, 4, 5, and 6 change agent behavior and deserve a live smoke test with a
real codex install before tagging.
