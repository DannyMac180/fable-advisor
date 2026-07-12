// smithers-source: fable-advisor
// smithers-metadata-version: 1
// smithers-display-name: Fable Advisor Orchestrator
// smithers-description: Durable Smithers version of the Fable Advisor pattern: turn a work request into a lane decision, CLI preflight, five-part delegation spec, and verification/advisor contract.
// smithers-tags: fable, advisor, orchestration, model-routing, grok, codex
/** @jsxImportSource smithers-orchestrator */
import { execFileSync } from "node:child_process";
import { createSmithers } from "smithers-orchestrator";
import { z } from "zod/v4";

const laneSchema = z.enum(["auto", "grok", "codex", "race", "advisor-only"]);
const riskSchema = z.enum(["routine", "correctness-critical", "architecture", "blocked"]);

const inputSchema = z.object({
  prompt: z.string().nullish().describe("The work request to route through the Fable Advisor pattern."),
  files: z.array(z.string()).nullish().describe("Known files or globs the work should touch."),
  interfaces: z.string().nullish().describe("Interfaces, APIs, schemas, or contracts the implementation must preserve."),
  constraints: z.string().nullish().describe("Project constraints or things the implementation lane must not change."),
  verification: z.string().nullish().describe("Command(s) or evidence that prove the implementation works."),
  risk: riskSchema.nullish().describe("How costly a wrong implementation would be."),
  lane: laneSchema.nullish().describe("Force a lane, or use auto routing."),
});

const intakeSchema = z.object({
  objective: z.string(),
  files: z.array(z.string()),
  interfaces: z.string(),
  constraints: z.string(),
  verification: z.string(),
  risk: riskSchema,
  requestedLane: laneSchema,
  sideEffectPolicy: z.string(),
});

const commandProbeSchema = z.object({
  command: z.string(),
  available: z.boolean(),
  evidence: z.string(),
});

const preflightSchema = z.object({
  probes: z.array(commandProbeSchema),
  grokAvailable: z.boolean(),
  codexAvailable: z.boolean(),
  claudeAvailable: z.boolean(),
  warnings: z.array(z.string()),
});

const routingSchema = z.object({
  selectedLane: z.enum(["grok-implementer", "codex-implementer", "race-grok-and-codex", "fable-advisor", "blocked"]),
  reason: z.string(),
  advisorRequired: z.boolean(),
  implementationAllowed: z.boolean(),
  warnings: z.array(z.string()),
});

const delegationSpecSchema = z.object({
  objective: z.string(),
  files: z.array(z.string()),
  interfaces: z.string(),
  constraints: z.string(),
  verification: z.string(),
  implementerPrompt: z.string(),
  advisorPrompt: z.string(),
});

const outputSchema = z.object({
  status: z.enum(["ready", "blocked"]),
  selectedLane: z.string(),
  advisorRequired: z.boolean(),
  preflightSummary: z.string(),
  implementerPrompt: z.string(),
  advisorPrompt: z.string(),
  warnings: z.array(z.string()),
});

const { Workflow, Task, Sequence, smithers, outputs } = createSmithers({
  input: inputSchema,
  intake: intakeSchema,
  preflight: preflightSchema,
  routing: routingSchema,
  delegationSpec: delegationSpecSchema,
  output: outputSchema,
});

const DEFAULT_OBJECTIVE = "Route this work through the Fable Advisor architect pattern.";
const DEFAULT_VERIFICATION = "The implementation lane must run the project-relevant tests or provide concrete evidence if no test command exists.";
const DEFAULT_CONSTRAINTS = "Keep the architect lean: implementation lanes type code; the architect owns requirements, routing, and verification. Never silently substitute a missing producer lane.";
const DEFAULT_INTERFACES = "No interface constraints supplied. The architect must fill this before delegating if the implementation depends on API/type/schema details.";

function shellProbe(command: string, script: string): { command: string; available: boolean; evidence: string } {
  try {
    const evidence = execFileSync("bash", ["-lc", script], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 5000,
    }).trim();
    return { command, available: evidence.length > 0, evidence: evidence || "available" };
  } catch (error: unknown) {
    const stderr = (error as { stderr?: unknown })?.stderr;
    const stdout = (error as { stdout?: unknown })?.stdout;
    const evidence = [stdout, stderr]
      .filter((part): part is string => typeof part === "string" && part.trim().length > 0)
      .join("\n")
      .trim();
    return { command, available: false, evidence: evidence || `${command} not available on PATH` };
  }
}

function buildIntake(input: z.input<typeof inputSchema>): z.infer<typeof intakeSchema> {
  return {
    objective: input.prompt?.trim() || DEFAULT_OBJECTIVE,
    files: input.files?.filter((file) => file.trim().length > 0) ?? [],
    interfaces: input.interfaces?.trim() || DEFAULT_INTERFACES,
    constraints: input.constraints?.trim() || DEFAULT_CONSTRAINTS,
    verification: input.verification?.trim() || DEFAULT_VERIFICATION,
    risk: input.risk ?? "routine",
    requestedLane: input.lane ?? "auto",
    sideEffectPolicy: "This workflow is orchestration-only: it produces a route, preflight, delegation spec, advisor prompt, and verification contract. Code edits stay behind the selected implementation lane and its own Smithers/effect gate.",
  };
}

function runPreflight(): z.infer<typeof preflightSchema> {
  const probes = [
    shellProbe("grok", "command -v grok >/dev/null && grok --version 2>&1 | head -1"),
    shellProbe("codex", "command -v codex >/dev/null && codex --version 2>&1 | head -1"),
    shellProbe("claude", "command -v claude >/dev/null && claude --version 2>&1 | head -1"),
  ];
  const byCommand = new Map(probes.map((probe) => [probe.command, probe]));
  const grokAvailable = byCommand.get("grok")?.available ?? false;
  const codexAvailable = byCommand.get("codex")?.available ?? false;
  const claudeAvailable = byCommand.get("claude")?.available ?? false;
  const warnings: string[] = [];
  if (!grokAvailable) warnings.push("grok-implementer unavailable: Grok CLI is missing or not authenticated; do not silently use a Claude fallback.");
  if (!codexAvailable) warnings.push("codex-implementer unavailable: Codex CLI is missing or not authenticated; route elsewhere explicitly.");
  if (!claudeAvailable) warnings.push("fable-advisor unavailable in this shell: Claude CLI is missing or not authenticated.");
  return { probes, grokAvailable, codexAvailable, claudeAvailable, warnings };
}

function chooseRoute(intake: z.infer<typeof intakeSchema>, preflight: z.infer<typeof preflightSchema>): z.infer<typeof routingSchema> {
  const warnings = [...preflight.warnings];
  const blocked = (reason: string): z.infer<typeof routingSchema> => ({
    selectedLane: "blocked",
    reason,
    advisorRequired: intake.risk !== "routine",
    implementationAllowed: false,
    warnings,
  });

  if (intake.requestedLane === "advisor-only") {
    return {
      selectedLane: preflight.claudeAvailable ? "fable-advisor" : "blocked",
      reason: preflight.claudeAvailable ? "User requested an advisor-only commitment-boundary review." : "Advisor-only mode requested, but Claude/Fable advisor lane is unavailable.",
      advisorRequired: true,
      implementationAllowed: false,
      warnings,
    };
  }

  if (intake.requestedLane === "grok") {
    return preflight.grokAvailable
      ? { selectedLane: "grok-implementer", reason: "User forced the routine Grok implementation lane.", advisorRequired: intake.risk !== "routine", implementationAllowed: true, warnings }
      : blocked("User forced grok, but the Grok CLI preflight failed.");
  }

  if (intake.requestedLane === "codex") {
    return preflight.codexAvailable
      ? { selectedLane: "codex-implementer", reason: "User forced the Codex implementation lane.", advisorRequired: intake.risk !== "routine", implementationAllowed: true, warnings }
      : blocked("User forced codex, but the Codex CLI preflight failed.");
  }

  if (intake.requestedLane === "race") {
    return preflight.grokAvailable && preflight.codexAvailable
      ? { selectedLane: "race-grok-and-codex", reason: "User requested a cross-vendor race; both producer lanes passed preflight.", advisorRequired: true, implementationAllowed: true, warnings }
      : blocked("Race requested, but both Grok and Codex lanes are not available.");
  }

  if (intake.risk === "architecture") {
    if (preflight.claudeAvailable) {
      return { selectedLane: "fable-advisor", reason: "Architecture/refactor decisions need advisor review before any implementation lane types code.", advisorRequired: true, implementationAllowed: false, warnings };
    }
    return blocked("Architecture risk needs an advisor pass, but Claude/Fable advisor lane is unavailable.");
  }

  if (intake.risk === "correctness-critical") {
    if (preflight.grokAvailable && preflight.codexAvailable) {
      return { selectedLane: "race-grok-and-codex", reason: "Correctness-critical work benefits from independent Grok and Codex implementations before the architect chooses a diff.", advisorRequired: true, implementationAllowed: true, warnings };
    }
    if (preflight.codexAvailable) {
      warnings.push("Only Codex is available; cross-vendor race downgraded to codex-implementer.");
      return { selectedLane: "codex-implementer", reason: "Correctness-critical work, but only the Codex producer lane passed preflight.", advisorRequired: true, implementationAllowed: true, warnings };
    }
    if (preflight.grokAvailable) {
      warnings.push("Only Grok is available; cross-vendor race downgraded to grok-implementer.");
      return { selectedLane: "grok-implementer", reason: "Correctness-critical work, but only the Grok producer lane passed preflight.", advisorRequired: true, implementationAllowed: true, warnings };
    }
    return blocked("Correctness-critical implementation needs at least one producer lane, but no producer lane passed preflight.");
  }

  if (preflight.grokAvailable) {
    return { selectedLane: "grok-implementer", reason: "Routine work defaults to Grok: the spec should determine the outcome and the architect verifies evidence afterward.", advisorRequired: false, implementationAllowed: true, warnings };
  }
  if (preflight.codexAvailable) {
    warnings.push("Routine lane downgraded to Codex because Grok is unavailable.");
    return { selectedLane: "codex-implementer", reason: "Routine work, but Grok is unavailable and Codex passed preflight.", advisorRequired: false, implementationAllowed: true, warnings };
  }
  return blocked("No implementation producer lane passed preflight.");
}

function buildDelegationSpec(intake: z.infer<typeof intakeSchema>, routing: z.infer<typeof routingSchema>): z.infer<typeof delegationSpecSchema> {
  const files = intake.files.length > 0 ? intake.files : ["TBD by architect before delegation"];
  const fileList = files.map((file) => `- ${file}`).join("\n");
  const implementerPrompt = [
    "OBJECTIVE",
    intake.objective,
    "",
    "FILES",
    fileList,
    "",
    "INTERFACES",
    intake.interfaces,
    "",
    "CONSTRAINTS",
    intake.constraints,
    "",
    `SELECTED LANE: ${routing.selectedLane}`,
    "Never silently substitute an unavailable model/CLI lane. If the selected producer is unavailable, return STATUS: unavailable with exact evidence.",
    "",
    "VERIFICATION",
    intake.verification,
    "Run the verification command yourself and include actual output in the final report. Claims without command output are not evidence.",
  ].join("\n");

  const advisorPrompt = [
    "Decision to review before commitment:",
    intake.objective,
    "",
    `Proposed route: ${routing.selectedLane}`,
    `Reason: ${routing.reason}`,
    "",
    "Constraints:",
    intake.constraints,
    "",
    "Files/interfaces:",
    fileList,
    intake.interfaces,
    "",
    "Give a verdict in under 300 words: proceed, change route, or block. Name the single risk that decides it.",
  ].join("\n");

  return {
    objective: intake.objective,
    files,
    interfaces: intake.interfaces,
    constraints: intake.constraints,
    verification: intake.verification,
    implementerPrompt,
    advisorPrompt,
  };
}

export default smithers((ctx) => {
  const intake = ctx.outputMaybe("intake", { nodeId: "fable-advisor:intake" });
  const preflight = ctx.outputMaybe("preflight", { nodeId: "fable-advisor:preflight" });
  const routing = ctx.outputMaybe("routing", { nodeId: "fable-advisor:route" });
  const spec = ctx.outputMaybe("delegationSpec", { nodeId: "fable-advisor:delegation-spec" });

  return (
    <Workflow name="fable-advisor">
      <Sequence>
        <Task id="fable-advisor:intake" output={outputs.intake}>
          {() => buildIntake(ctx.input)}
        </Task>
        {intake ? (
          <Task id="fable-advisor:preflight" output={outputs.preflight}>
            {() => runPreflight()}
          </Task>
        ) : null}
        {intake && preflight ? (
          <Task id="fable-advisor:route" output={outputs.routing}>
            {() => chooseRoute(intake, preflight)}
          </Task>
        ) : null}
        {intake && routing ? (
          <Task id="fable-advisor:delegation-spec" output={outputs.delegationSpec}>
            {() => buildDelegationSpec(intake, routing)}
          </Task>
        ) : null}
        {preflight && routing && spec ? (
          <Task id="fable-advisor:output" output={outputs.output}>
            {() => ({
              status: routing.implementationAllowed || routing.selectedLane === "fable-advisor" ? "ready" : "blocked",
              selectedLane: routing.selectedLane,
              advisorRequired: routing.advisorRequired,
              preflightSummary: preflight.probes.map((probe) => `${probe.command}: ${probe.available ? "available" : "unavailable"} (${probe.evidence})`).join("; "),
              implementerPrompt: spec.implementerPrompt,
              advisorPrompt: spec.advisorPrompt,
              warnings: routing.warnings,
            })}
          </Task>
        ) : null}
      </Sequence>
    </Workflow>
  );
});
