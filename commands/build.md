---
description: Build a task with fable-advisor's workflow — specs go to Claude implementer workers in isolated git worktrees, the session merges their branches, runs the full checks, and gets a Fable review before reporting.
argument-hint: <task to build>
---

The user invoked `/fable-advisor:build`, which is their explicit request to run this as a Workflow and to make local commits and merges for it in this repository. Follow the orchestration skill (`fable-advisor:orchestration`) for lanes, labels and the spec contract. The task:

$ARGUMENTS

Never push, never switch the user's branch, and never delete a worktree or branch that holds unmerged work without the user's yes.

## 1. Preflight

1. **Clean tracked tree.** Run `git status --porcelain --untracked-files=no`. If anything shows, stop and ask the user whether to commit or stash it first. The worktrees branch from `HEAD`, so uncommitted work would be invisible to the workers and could collide with the merge. Never stash silently. Record `START=$(git rev-parse HEAD)` and the current branch.
2. **Keep worktrees out of git status.** Workers' worktrees live under `.claude/worktrees/`. If `git check-ignore -q .claude/worktrees/x` fails, append `.claude/worktrees/` to `.git/info/exclude` (local to this clone, never committed) and say so in one line. If that write is denied, say the worktrees will show as untracked while they exist, and continue.
3. **Leftover worktrees from earlier runs.** Run `git worktree list --porcelain` and pick out the entries under `.claude/worktrees/`. For each, show its branch (`worktree-…`: `worktree-agent-<id>` from a single Agent call, `worktree-wf_<run>-<n>` from a workflow), whether it has commits that aren't on the current branch (`git log --oneline HEAD..<branch>`), and whether it has uncommitted changes (`git -C <path> status --short`). Don't remove any of them here; step 6 offers that.
4. **Lanes.** Read `~/.claude/fable-advisor/lanes.json`, as the skill describes. You'll pass each worker lane's `model`, `effort` and a display `label` (for example `Opus 5.5`) to the workflow.

## 2. Specs

Scope the task inline, reading only as much code as the specs need. Broad exploration goes to a read-only agent with `model: "haiku"`. Then write the specs:

- Each spec has an `id` (short, unique), a `lane` (`routine` or `complex`), an optional `effort` override, and `text` holding parts 1–5 of the spec contract: objective, files, interfaces, constraints, verification. Don't write part 6; the workflow appends the `LANE: … · EFFORT: … · ISOLATION: worktree` line itself.
- **The specs in one round must be independent.** Every worktree branches from `HEAD`, so a spec can't see another spec's changes. Work that depends on another spec goes into a later round, after the merge.
- **At most 5 specs per round.** With one retry each, that keeps the workflow within 10 agents. Larger builds run several rounds.

**Permissions.** Workers run in the background and can't ask for approval. They need Bash for each spec's verification command, `git add` and `git commit`. Look for matching allow rules in `.claude/settings.local.json`, `.claude/settings.json` and `~/.claude/settings.json`. If any are missing:
- Offer once (AskUserQuestion) to add them to `.claude/settings.local.json`, as `Bash(<verification command>:*)`, `Bash(git add:*)` and `Bash(git commit:*)`.
- If the user declines, or you can't ask, say plainly that those specs will come back `failed` with the commands blocked, and continue.

## 3. Run the workflow

Call the Workflow tool with `scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/build.js"` and:

```json
"args": {
  "specs": [{ "id": "...", "lane": "routine", "text": "1. Objective: ...\n2. Files: ...\n3. Interfaces: ...\n4. Constraints: ...\n5. Verification: ..." }],
  "lanes": {
    "routine": { "model": "opus", "effort": "medium", "label": "Opus 5.5" },
    "complex": { "model": "opus", "effort": "high", "label": "Opus 5.5" }
  }
}
```

Pass `args` as a JSON object, not a string. If the Workflow tool rejects the `scriptPath`, Read that file and pass its contents as `script` with the same `args`. Announce the round in one line first, for example `→ /build round 1 · 3 specs · routine Opus 5.5 · medium, complex Opus 5.5 · high`.

## 4. Check and merge

The workflow returns each spec's attempts. The last attempt counts. Take each worktree's path and branch from the report's `worktree` and `branch` fields; don't guess them from a naming pattern. For each spec:

- **Check the model.** `model_id` should match the lane's pinned model (`claude-opus-5-5` for `opus`, `claude-fable-5-2` for `fable`, `claude-sonnet-5-5` for `sonnet`, `claude-haiku-5-5` for `haiku`). Report any mismatch.
- **Accept only `done` with real output.** A `done` needs a commit SHA and real verification output. `spec-gap`, `failed` or `refused` means that spec isn't merged; note why.

Merge the accepted branches in spec-ID order into the current branch with `git merge --no-ff --no-edit <branch>`.
- **Conflict you can see how to fix:** resolve it, run that spec's verification, and commit the merge.
- **Anything else:** `git merge --abort`, and queue the spec to be re-written against the merged tree for the next round.

Then run the project's full checks once on the merged tree: the union of the specs' verification commands, plus the project's own test command if there is one. One worktree passing its own check doesn't prove the merge works.

## 5. Review

Call `fable-advisor` with the reviewer lane's `model` and the description `<reviewer label>: final review`. Pass it the task, the specs, the merged diff (`git diff $START..HEAD`) and the full-check output. Then read its verdict and `git diff --stat $START..HEAD`. Open files yourself only on fix-first or rethink, so the review isn't paid for twice. Act on the verdict: fix-first items go into another round as specs, or into a small fix you make directly.

## 6. Clean up

- **Merged specs:** run `git worktree remove <worktree>`, then `git branch -d <branch>`.
- **Everything else:** list it with path, branch and state. That covers this round's unmerged and failed attempts (a failed attempt's worktree stays if it had changes) and the leftovers from step 1.3. Offer to remove them (`git worktree remove --force <path>`, `git branch -D <branch>`), and remove them only on the user's yes. Never remove one silently.

## 7. Report

One line per spec: `<id> · <lane> · <model_id> · <effort> · <status> · merged | not merged (why)`. Then:
- the full-check result;
- the review verdict;
- `git diff --stat $START..HEAD`;
- what is left: queued specs, leftover worktrees, the review's fix-first items.

The merges are local commits on the user's branch. Say so, and say that nothing was pushed.
