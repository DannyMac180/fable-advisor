#!/usr/bin/env python3
"""Measure Fable-solo vs /fable-advisor:build on the bench tasks.

Each run gets a fresh copy of bench/fixture as its own git repo, runs one
headless Claude Code session, then scores the result with the hidden
acceptance test for that task (never shown to the model).

  python3 bench/run.py --out DIR [--tasks t1,t2,t3] [--arms solo,build] [--reps 1] [--budget 15]

Set CLAUDE_BIN to pick the Claude Code binary. The `fable` alias means Fable 5.2
only on Claude Code 2.1.321 or later; 2.1.316 resolves it to Fable 5.1, so check
the per-model costs in the results.

Writes DIR/results.jsonl (one line per run) and prints a summary table.
Cost comes from the session's own `--output-format json` result
(`total_cost_usd` and per-model `modelUsage[*].costUSD`, list prices).
"""
import argparse, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TASKS = {"t1": "t1-io.md", "t2": "t2-query.md", "t3": "t3-cli.md"}
TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(python3 *)", "Bash(git *)"]


def sh(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, **kw)


def fresh_repo(path):
    shutil.copytree(os.path.join(HERE, "fixture"), path)
    sh(["git", "init", "-q", "-b", "main"], path)
    sh(["git", "add", "."], path)
    sh(["git", "-c", "user.name=bench", "-c", "user.email=bench@example.invalid", "commit", "-q", "-m", "fixture"], path)


def session_cmd(arm, task_text, budget):
    base = [os.environ.get("CLAUDE_BIN", "claude"), "-p", "--model", "fable", "--effort", "medium", "--strict-mcp-config",
            "--setting-sources", "project,local", "--permission-mode", "acceptEdits",
            "--max-budget-usd", str(budget), "--output-format", "json", "--no-session-persistence"]
    if arm == "solo":
        prompt = task_text + "\n\nImplement this yourself in this repository; don't start subagents."
        return base + ["--disallowedTools", "Agent", "Workflow", "--allowedTools", *TOOLS], prompt
    if arm == "build":
        prompt = "/fable-advisor:build " + task_text
        return base + ["--plugin-dir", REPO, "--allowedTools", "Workflow", "Agent", *TOOLS], prompt
    raise ValueError(arm)


def accept(path, task):
    src = os.path.join(HERE, "acceptance", f"accept_{task}.py")
    env = dict(os.environ, PYTHONPATH=os.path.join(HERE, "acceptance"))
    r = sh([sys.executable, "-m", "unittest", f"accept_{task}"], path, env=env, timeout=120)
    own = sh([sys.executable, "-m", "unittest"], path, timeout=120)
    return r.returncode == 0, (r.stderr or r.stdout)[-1500:], own.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tasks", default="t1,t2,t3")
    ap.add_argument("--arms", default="solo,build")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--budget", type=float, default=15)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    out = open(os.path.join(a.out, "results.jsonl"), "a")
    for rep in range(1, a.reps + 1):
        for task in a.tasks.split(","):
            text = open(os.path.join(HERE, "tasks", TASKS[task])).read()
            for arm in a.arms.split(","):
                path = os.path.join(a.out, f"{task}-{arm}-r{rep}")
                if os.path.exists(path):
                    shutil.rmtree(path)
                fresh_repo(path)
                cmd, prompt = session_cmd(arm, text, a.budget)
                t0 = time.time()
                p = subprocess.run(cmd, cwd=path, input=prompt, capture_output=True, text=True, timeout=3600)
                wall = round(time.time() - t0)
                try:
                    res = json.loads(p.stdout)
                except json.JSONDecodeError:
                    res = {"is_error": True, "result": (p.stdout + p.stderr)[-2000:]}
                ok, detail, own_ok = accept(path, task)
                row = {
                    "task": task, "arm": arm, "rep": rep, "wall_s": wall,
                    "cost_usd": res.get("total_cost_usd"),
                    "cost_by_model": {m: round(u.get("costUSD", 0), 4) for m, u in (res.get("modelUsage") or {}).items()},
                    "tokens_by_model": {m: {k: u.get(k, 0) for k in ("inputTokens", "outputTokens", "cacheCreationInputTokens", "cacheReadInputTokens", "thinkingTokens")}
                                        for m, u in (res.get("modelUsage") or {}).items()},
                    "turns": res.get("num_turns"), "subagents": (res.get("subagent_stats") or {}).get("spawned"),
                    "session_error": res.get("is_error"), "terminal": res.get("terminal_reason"),
                    "accept_pass": ok, "own_tests_pass": own_ok, "accept_detail": None if ok else detail,
                    "final_message": res.get("result") or "",
                }
                out.write(json.dumps(row) + "\n"); out.flush()
                print(f"{task} {arm} r{rep}: ${row['cost_usd']} accept={'PASS' if ok else 'FAIL'} own={'pass' if own_ok else 'fail'} {wall}s {row['cost_by_model']}", flush=True)


if __name__ == "__main__":
    main()
