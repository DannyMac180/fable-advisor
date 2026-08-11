# Changelog

## [4.1.1] - 2026-08-11

### Changed

- Architect-typing rule resolved: type implementation only when the spec would be longer than the diff, and say so in the report — stated identically in the README snippet and the skill's deciding rule.
- Verification labor reconciled with cost discipline: lanes read full diffs and quote evidence; the architect reads reports and spot-checks scoped diffs; the full deliverable diff enters architect context only at commitment boundaries.
- README accuracy pass: the fable→opus downgrade names its two exact files; the CLAUDE_CODE_SUBAGENT_MODEL global-override consequence is stated; the codex lane's Sonnet wrapper cost is acknowledged.
- Perishable dated facts (observed-live date, Luna tier list, codex-cli version) removed from agent prompt text or relocated to the README requirements.
- Reasoning effort is now caller-routable: `-c model_reasoning_effort="${FABLE_ADVISOR_CODEX_EFFORT:-max}"`, with Model/Effort documented as spec-level routing parameters.

## [4.1.0] - 2026-08-11

### Added

- Unified lane status vocabulary (complete, partial, refused, timeout, unavailable, blocked) with an architect action per status.
- REASON line in the codex report schema.
- Unattributed-changes rule: out-of-scope working-tree changes are reported as unattributed, not blamed on the lane.
- Timeout detection: timeout/gtimeout exit code 124 maps to STATUS: timeout.
- FABLE_ADVISOR_CODEX_MODEL env override; agents/codex-implementer.md is now the only normative site for the codex model slug.
- Liberal routing posture: Luna is the default routine lane, Terra the overflow, and the effort dial governs cost.

### Changed

- Temp-file cleanup trap and portable mktemp in the merged codex invocation block.
- One canonical description reused verbatim across plugin.json and both marketplace.json blurbs; the marketplace plugin entry gains license, keywords, and category.
- Retro-tagged v3.1 at b3b50a9.

## [4.0.1] - 2026-08-11

### Added

- Preflight auth probe via a Codex login-status check.
- Git repo requirement for the codex-implementer lane.
- Diff-path handoff for the read-only fable-advisor reviewer.

### Changed

- Merged the Codex invocation into a single Bash-call block because shell state does not persist across tool calls; the final message is read in the same call.
- Removed the claim that the codex-implementer lane works outside git repositories; the empty-diff refusal detector depends on git diff.
- Required per-racer git worktree isolation for lane racing.

## [4.0.0] - 2026-07-25

### Changed

- Opus orchestrates as architect, Codex is the routine implementation lane, and Fable escalates high-complexity work and reviews every deliverable. ([2cf102d], 2026-07-25)
- Post-v4.0.0-tag commits shipped without a version bump:
  - Repinned the routine lane to GPT-5.6 Luna at max reasoning. ([3088622], 2026-08-04)
  - Made codex-implementer opt out of machine-wide orchestration defaults. ([ad2bdc3], 2026-08-04)

## [3.1] - 2026-07-09

### Changed

- Upgraded the Codex lane to GPT-5.6 Sol. ([8236e9b], 2026-07-09)
- Related untagged README follow-up. ([b3b50a9], 2026-07-09)

## [3.0.0] - 2026-07-08

### Changed

- Grok 4.5 replaces the Sonnet implementer lane. ([92e35f4], 2026-07-08)

## [2.1.0] - 2026-07-04

### Added

- Cost-discipline doctrine for orchestration. ([b12f1fb], 2026-07-04; [3c1846c], 2026-07-04)

## [2.0.0] - 2026-07-03

### Added

- Architect-as-orchestrator primary pattern.
- Orchestration routing doctrine skill.
- Codex-implementer GPT-5.5 lane. ([4a65f4e], 2026-07-03)

## [1.0.0] - 2026-07-02

### Added

- fable-advisor, advisor-only. ([dd8cd2e], 2026-07-02)
