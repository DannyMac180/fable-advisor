export const meta = {
  name: 'fable-advisor-build',
  description: 'Implement independent fable-advisor specs in isolated worktrees on the pinned Claude lanes',
  whenToUse: 'Started by /fable-advisor:build with args {specs, lanes}. Not for direct use.',
  phases: [{ title: 'Implement', detail: 'one implementer per spec, each in its own worktree; one retry on failure' }],
}

// args: {
//   specs: [{ id, lane: 'routine' | 'complex', effort?, text }],   // text = spec parts 1-5
//   lanes: { routine: { model, effort, label }, complex: { model, effort, label } },
// }
// Returns: { results: [{ id, lane, model, effort, attempts: [report, ...] }] }

const MAX_SPECS = 5 // with one retry each, stays within the 10-agent default

const REPORT = {
  type: 'object',
  properties: {
    spec_id: { type: 'string' },
    status: { type: 'string', enum: ['done', 'spec-gap', 'failed', 'refused'] },
    lane: { type: 'string' },
    model_id: { type: 'string', description: 'Exact model ID your system prompt says you run on, or "model not stated"' },
    effort: { type: 'string' },
    worktree: { type: 'string', description: 'Output of git rev-parse --show-toplevel' },
    branch: { type: 'string', description: 'Output of git branch --show-current' },
    commit: { type: 'string', description: 'Short SHA, or "none"' },
    changes: { type: 'array', items: { type: 'string' } },
    verified: { type: 'string', description: 'The verification command and its actual output' },
    gaps: { type: 'string' },
  },
  required: ['spec_id', 'status', 'model_id', 'worktree', 'branch', 'commit', 'verified'],
}

const specs = args && args.specs
const lanes = args && args.lanes
if (!Array.isArray(specs) || specs.length === 0) throw new Error('args.specs must be a non-empty array')
if (!lanes || !lanes.routine || !lanes.complex) throw new Error('args.lanes must define routine and complex')
if (specs.length > MAX_SPECS) {
  throw new Error(`${specs.length} specs in one round; the limit is ${MAX_SPECS}. Split the rest into another /build round.`)
}

phase('Implement')

const results = await pipeline(specs, async (spec) => {
  const lane = lanes[spec.lane]
  if (!lane) throw new Error(`spec ${spec.id}: unknown lane ${spec.lane}`)
  const effort = spec.effort || lane.effort
  const prompt = (extra) =>
    `SPEC ID: ${spec.id}\n${spec.text.trim()}\n6. LANE: ${spec.lane} · EFFORT: ${effort} · ISOLATION: worktree\n${extra}`
  const run = (extra, n) =>
    agent(prompt(extra), {
      label: `${lane.label} · ${effort}: ${spec.id}${n > 1 ? ' (retry)' : ''}`,
      phase: 'Implement',
      agentType: 'fable-advisor:implementer',
      model: lane.model,
      effort,
      isolation: 'worktree',
      schema: REPORT,
    })

  const attempts = []
  const first = await run('', 1)
  attempts.push(first)
  if (first && first.status === 'failed') {
    log(`${spec.id} failed; retrying once with the failure attached`)
    const retry = await run(
      `\nA previous attempt at this spec failed. Its verification output:\n${first.verified}\nIts gaps: ${first.gaps || 'none'}\nStart from a clean tree; the earlier attempt's changes are not here.`,
      2,
    )
    attempts.push(retry)
  }
  return { id: spec.id, lane: spec.lane, model: lane.model, effort, attempts }
})

return { results: results.filter(Boolean) }
