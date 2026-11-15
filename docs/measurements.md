# Measurements — Fable alone vs `/fable-advisor:build`

**Results (2026-11-15).** `/fable-advisor:build` never cost less than a Fable 5.2 session working alone. Every run of both arms passed the hidden acceptance tests (16 of 16).

- **Small tasks (t1–t3):** Fable alone, with no closing review, was about **2.8× cheaper** and about **3× faster** than `/build`.
- **One larger task (t4), with a closing Fable review in both arms:** the gap narrowed to `/build` costing **about 12% more** ($3.53 vs $3.14 per run, means of 2). Wall-clock time was similar.

Orchestrating Opus workers moved real volume off Fable on the larger task: Fable spent about 21% less inside `/build` than working alone. The Opus work added that saving back, and a little more. No saving was measured at either size.

## Small tasks (t1–t3)

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

## Larger task (t4), both arms reviewed

- **The task:** `bench/tasks/t4-large.md` combines the three small tasks with a fourth part, a reservations module. Its hidden test `bench/acceptance/accept_t4.py` covers all four parts.
- **The solo arm** (`solo_review`) is a Fable session that implements the task itself, then calls a reviewer once and acts on what it raises. The reviewer is defined from this branch's `agents/fable-advisor.md`, loaded with `--agents`, so no implementer agent or orchestration skill is present.
- **The `/build` arm** is unchanged.
- Both arms ran at `--effort medium` with `--max-budget-usd 10`, on Claude Code 2.1.325.

| Run | Fable 5.2 | Opus 5.5 | Total | Acceptance | Time |
|---|---|---|---|---|---|
| Fable alone + review, run 1 | $3.08 | — | **$3.08** | pass | 336 s |
| Fable alone + review, run 2 | $3.20 | — | **$3.20** | pass | 413 s |
| `/build`, run 1 | $2.37 | $1.12 | **$3.49** | pass | 344 s |
| `/build`, run 2 | $2.59 | $0.98 | **$3.57** | pass | 367 s |
| **Means** | alone $3.14 · `/build` Fable $2.48 + Opus $1.05 | | **$3.14 vs $3.53 (1.12×)** | 4/4 | 375 s vs 356 s |

- **Fable output tokens:** 38–48k working alone, 26–28k inside `/build`. The workers did take over part of the writing.
- **Opus share:** about 30% of `/build`'s cost here, against 14% on the small tasks.
- **The review ran in all four runs:**
  - Both `/build` final reports name the reviewer as `claude-fable-5-2`, the ID its new `REVIEWER:` first line reports, and give its verdict (ship).
  - Both solo final reports say the reviewer ran once and raised no fix-first items, and list the optional suggestions taken. They don't quote the `REVIEWER:` line, so the model the solo reviewer ran on isn't confirmed by the record.
  - Each of the four sessions reports `subagents: 1`, consistent with one reviewer call and with workflow workers not being counted.
- **Two runs per arm can't settle a 12% gap.** The ranges don't overlap ($3.08–3.20 against $3.49–3.57), but that's thin evidence. Read it as "about the same, slightly more for `/build`", not as a precise ratio.

## What this means

- **On small tasks, do them with Fable alone.** If Fable can finish a task by itself in a couple of minutes, `/build`'s fixed Fable overhead per round costs more than the whole solo task.
- **On the one larger task, the costs were about even.** `/build` moved about 30% of the spend to Opus and cut Fable's own spend by about 21%, but it still cost slightly more in total. The gap shrank from 2.8× to 1.12× as the task grew, and the solo arm also gained a review. Whether `/build` gets cheaper than Fable alone on still larger builds is untested, and no breakeven point is claimed.
- **What `/build` reliably buys isn't a saving.** It buys parallel isolated work, a full-check run on the merged result, a reviewer in a separate Fable context, and a model label on every step.
- **Direct implementer calls are unmeasured.** These numbers are about `/build`, not about a Fable session making one-off implementer calls without the merge and review steps.

## Not like for like

- **On t1–t3, only `/build` ends with a review.** It includes the merge, the full checks and a `fable-advisor` review. The solo runs there had no review, although the doctrine says every deliverable should end with one, so the 2.8× ratio overstates the gap by up to the cost of one review. The t4 runs give both arms a review.
- **Parallelism was barely exercised.** Only t1's `/build` runs split the work across two workers. In t2 and t3, the session wrote a single spec, so one worker ran.
- **The `/build` runs hit some friction.** The write to `.git/info/exclude` was denied in 4 of the 6 runs, and in 1 run the Workflow tool rejected the script path before the inline fallback worked. Both added a little Fable time.
- **The environment wasn't fully isolated.** `--setting-sources` didn't stop the `/build` runs from reading the user's old (v1) `~/.claude/fable-advisor/lanes.json`. Each run noted it and used the default lanes, which are what was intended anyway.
- **`subagents: 1` is unexplained.** The session JSON reports it in all six `/build` rows, including t1's two-worker runs, so it probably doesn't count workflow workers. What it counts isn't documented, so it isn't used as evidence of the review.
- **None of this flips the direction.** The cheapest `/build` run ($1.81) still cost more than the most expensive solo run ($1.00).
- **The review is confirmed from the record in only 2 of 6 small-task `/build` runs.** The t4 runs suggest `subagents: 1` counts the reviewer call, which would put it at 6 of 6, but that isn't documented.
- **The detail behind the 2-of-6 figure:** In those, the stored final message shows the verdict. The runner kept only the last 1,200 characters of each final message, so the other four can't be confirmed from the record. `bench/run.py` now keeps the full message and per-model token counts for future runs.

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
- **Raw data:** `bench/results/2026-11-15-v7.2.jsonl`. Total spend was $16.40. The unusable 2.1.316 pilot (task t1, Fable 5.1, $4.57) is in `bench/results/2026-11-15-pilot-cc2.1.316.jsonl`. The t4 rows (including per-model token counts and full final messages) are in `bench/results/2026-11-15-t4-large.jsonl`; that batch spent $13.34 of its $40 budget.

To reproduce:

```bash
CLAUDE_BIN=/path/to/claude python3 bench/run.py --out /tmp/bench --reps 2
CLAUDE_BIN=/path/to/claude python3 bench/run.py --out /tmp/bench-t4 --tasks t4 --arms solo_review,build --reps 2 --budget 10
```
