# Measurements — Fable alone vs `/fable-advisor:build`

**Result (2026-11-15, v7.2):** on three small multi-part tasks, a Fable 5.2 session working alone was about **2.8× cheaper** and about **3× faster** than `/fable-advisor:build`. Both passed every hidden acceptance test (12 of 12 runs).

At this task size, orchestrating Opus workers did not save money. The workers themselves were cheap. The cost was Fable's own overhead inside `/build`.

## Results

Each cell is the mean of 2 runs, with the range in brackets. Costs are what each session reported (`total_cost_usd`, at list prices).

| Task | Fable alone | `/build` | `/build` ÷ alone | Opus share of `/build` | Time alone → `/build` |
|---|---|---|---|---|---|
| t1: CSV + JSON import/export | $0.99 (0.97–1.00) | $2.22 (2.11–2.32) | 2.2× | $0.32 | 114 s → 242 s |
| t2: query, total value, low stock | $0.61 (0.44–0.78) | $1.82 (1.81–1.83) | 3.0× | $0.24 | 68 s → 220 s |
| t3: CLI with five commands | $0.56 (0.53–0.58) | $2.01 (1.99–2.03) | 3.6× | $0.30 | 64 s → 256 s |
| **All 6 runs** | **$4.30** | **$12.09** | **2.8×** | **14%** | |

- **The gap holds on every task.** Every `/build` run cost more than every solo run ($1.81–2.32 against $0.44–1.00). That's far wider than the run-to-run spread, so two runs per cell is enough to settle the direction, though not the exact ratio.
- **Fable alone was enough.** All 12 runs passed the acceptance tests and their own tests.
- **Where `/build`'s money went:**
  - the Opus 5.5 workers cost $0.23–0.33 a run;
  - Fable 5.2 inside `/build` cost $1.57–1.99 a run, which is more than any whole solo run.

  That Fable share covers the session itself (preflight, writing specs, merging, running the full checks) and the `fable-advisor` review. The session report doesn't split the two.

## What this means

- **On small tasks, do them with Fable alone.** If Fable can finish a task by itself in a couple of minutes, `/build`'s fixed Fable overhead per round costs more than the whole solo task.
- **What `/build` buys is not a saving at this size.** It buys parallel isolated work, a full-check run on the merged result, and a review from a separate Fable context.
- **Larger tasks are unmeasured.** Larger builds, where implementation volume would dominate, weren't measured. No breakeven point is claimed: the overhead probably grows with task size too (more specs to write, a bigger diff to review).
- **Direct implementer calls are unmeasured.** These numbers are about `/build`, not about a Fable session making one-off implementer calls without the merge and review steps.

## Not like for like

- **Only `/build` ends with a review.** It includes the merge, the full checks and a `fable-advisor` review. The solo runs had no review, although the doctrine says every deliverable should end with one. A fair comparison would add one reviewer call to each solo run. It wasn't run, so the 2.8× ratio overstates the gap by up to the cost of one review.
- **Parallelism was barely exercised.** Only t1's `/build` runs split the work across two workers. In t2 and t3, the session wrote a single spec, so one worker ran.
- **The `/build` runs hit some friction.** The write to `.git/info/exclude` was denied in 4 of the 6 runs, and in 1 run the Workflow tool rejected the script path before the inline fallback worked. Both added a little Fable time.
- **The environment wasn't fully isolated.** `--setting-sources` didn't stop the `/build` runs from reading the user's old (v1) `~/.claude/fable-advisor/lanes.json`. Each run noted it and used the default lanes, which are what was intended anyway.
- **`subagents: 1` is unexplained.** The session JSON reports it in all six `/build` rows, including t1's two-worker runs, so it probably doesn't count workflow workers. What it counts isn't documented, so it isn't used as evidence of the review.
- **None of this flips the direction.** The cheapest `/build` run ($1.81) still cost more than the most expensive solo run ($1.00).
- **The review is confirmed in only 2 of 6 `/build` runs.** In those, the stored final message shows the verdict. The runner kept only the last 1,200 characters of each final message, so the other four can't be confirmed from the record. `bench/run.py` now keeps the full message and per-model token counts for future runs.

## Method

- **Sample repo:** `bench/fixture`, a small standard-library Python package (`inventory`, about 100 lines plus tests).
- **Tasks:** `bench/tasks/`, each with exact interfaces and several independent parts.
- **Scoring:** `bench/acceptance/` holds hidden tests the model never sees; a run passes only if they pass.
- **Runner:** `bench/run.py`. Each run gets a fresh git copy of the fixture and one headless session. Both arms used:
  - `--model fable --effort medium`;
  - `--strict-mcp-config` and `--setting-sources project,local`, so the user's MCP servers and plugins didn't load;
  - `--max-budget-usd 15`.
- **The solo arm** had the Agent and Workflow tools disabled.
- **The `/build` arm** loaded this repo with `--plugin-dir`, used the default lanes (Opus 5.5, routine at `medium`, complex at `high`), and allowed `python3` and `git` commands.
- **Claude Code version:** 2.1.325. On 2.1.316, `--model fable` resolves to Fable 5.1, which made a first pilot unusable. The README now requires 2.1.321 or later.
- **Mid-run edits:** the `REVIEWER:` first line in `agents/fable-advisor.md` and the matching line in the skill were added while the runs were in progress, so later runs loaded them. Their effect on cost is negligible.
- **Raw data:** `bench/results/2026-11-15-v7.2.jsonl`. Total spend was $16.40. The unusable 2.1.316 pilot (task t1, Fable 5.1, $4.57) is in `bench/results/2026-11-15-pilot-cc2.1.316.jsonl`.

To reproduce:

```bash
CLAUDE_BIN=/path/to/claude python3 bench/run.py --out /tmp/bench --reps 2
```
