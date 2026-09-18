# AGENTS.md

## AI-Powered Creative Optimization & Growth Operations Agent

This file defines the operating rules for every AI coding agent working in this repository. These instructions apply to the entire repository unless a more specific `AGENTS.md` exists in a subdirectory.

The project is an independent portfolio simulation. Safety, analytical integrity, reproducibility, and honest representation take priority over speed or feature count.

## 1. Instruction Priority

Follow instructions in this order:

1. The user’s explicit request for the current task
2. This `AGENTS.md`
3. `PROJECT_BRIEF.md`
4. The active phase in `PHASES.md`
5. `ARCHITECTURE.md`
6. Recorded decisions in `DECISIONS.md`
7. Existing tests, schemas, and code conventions
8. General conventions in `README.md`

If two sources conflict:

- Stop before making a consequential or irreversible change.
- Identify the exact conflict.
- Prefer the safer interpretation temporarily.
- Ask the user to resolve any conflict that changes scope, business logic, data definitions, or safety controls.
- Record the approved resolution in `DECISIONS.md`.

Do not silently choose between conflicting definitions.

## 2. Project Identity

Treat this project as:

- A hypothetical AI-powered mobile gaming company
- A consumer B2C growth portfolio simulation
- A synthetic-data project by default
- A decision-support system, not an autonomous media buyer
- A learning environment in which the student remains accountable

Never imply that simulated campaigns, spend, users, revenue, or performance came from a real company.

## 3. Core Objective

Build a system that connects:

```text
Business Objective
→ Audience Hypothesis
→ Creative Hypothesis
→ Controlled Experiment
→ Acquisition Result
→ Activation and Retention Result
→ Economic Interpretation
→ Human-Reviewed Recommendation
→ Next Test
```

Optimize for clear growth reasoning and reliable evidence. Do not optimize merely for creative volume, code volume, architectural complexity, or visual polish.

## 4. Mandatory Pre-Work Protocol

Before editing any file:

1. Read this file in full.
2. Read `PROJECT_BRIEF.md`.
3. Read the relevant section of `PHASES.md`.
4. Read `ARCHITECTURE.md` when it exists.
5. Read `DECISIONS.md` when it exists.
6. Inspect the relevant existing code, tests, configurations, and documentation.
7. Check the worktree and preserve unrelated user changes.
8. Restate the requested scope internally or in the work update.
9. Identify assumptions, missing inputs, and conflicts.
10. Confirm that the task belongs to the active phase.

Do not start implementation based only on the latest prompt when repository documentation provides relevant constraints.

## 5. Scope Control

### Work on one bounded task

- Implement only the requested phase or subtask.
- Do not continue automatically to the next phase.
- Do not add adjacent features merely because they seem useful.
- Do not refactor unrelated modules.
- Do not replace working technology without an approved decision.
- Do not create production infrastructure during an MVP task.

### When to ask for clarification

Ask before proceeding when:

- The request conflicts with the project brief or a recorded decision.
- A missing business definition changes metric meaning.
- Several reasonable technical choices would materially affect the architecture.
- Real credentials, customer data, spend, or platform access would be required.
- The task could trigger an external or live action.
- Existing user changes overlap materially with the requested work.
- Completion would require weakening a safety control.

### When to proceed with a documented assumption

Proceed only when the assumption is:

- Reversible
- Low risk
- Limited to the current task
- Consistent with existing documentation
- Clearly recorded in the result or `DECISIONS.md`

## 6. Non-Negotiable Safety Defaults

These values must remain the default:

```env
DRY_RUN=true
RECOMMEND_ONLY=true
ALLOW_LIVE_MUTATIONS=false
```

Never change these defaults without an explicit user request, updated documentation, appropriate tests, and a recorded decision.

### Prohibited by default

Do not:

- Publish or activate an advertisement.
- Change a live campaign, budget, bid, audience, schedule, or optimization event.
- Pause, archive, or delete a live campaign object.
- Upload a customer list or audience file.
- Use or request production credentials for ordinary development.
- Store secrets in source code, notebooks, fixtures, logs, screenshots, or documentation.
- Commit `.env` or credential files.
- Circumvent platform approval, review, or policy requirements.
- Send generated marketing content to an external destination without approval.
- Treat a recommendation as authorization.

### Human approval required

Explicit approval is required before:

- Any platform write operation
- Any campaign-status mutation
- Any change that can spend money
- Any audience or customer-data transfer
- Any production scheduling or publishing
- Any destructive operation

Approval must identify the proposed action and its exact target. A general request to “optimize campaigns” is not sufficient authorization for live mutations.

## 7. Synthetic Data Rules

Synthetic data is the default and must be visibly labeled.

### Required properties

- Use no real personal information.
- Use deterministic generation with a documented random seed.
- Preserve referential integrity across tables.
- Document intentional behavioral patterns.
- Include realistic missingness, delays, and immature cohorts.
- Keep generated data separate from source code.
- Make regeneration reproducible through a documented command.

### Integrity requirements

Do not generate data solely to make the intended system look successful. The dataset must include:

- Positive patterns
- Negative patterns
- Conflicting signals
- Insufficient evidence
- Data-quality defects
- Attribution uncertainty

Tests must verify intentional patterns without forcing every output to support the same conclusion.

### Labeling

The word `synthetic`, `simulated`, or an equivalent unambiguous label must appear in:

- Dataset documentation
- Generated report metadata
- Dashboard disclosure
- Case-study findings
- Demo narration

## 8. Marketing Measurement Rules

### Source of truth

- Define formulas in `data/data_dictionary.md`.
- Calculate authoritative metrics in deterministic Python or SQL.
- Do not ask an LLM to calculate or rewrite authoritative metric values.
- Do not maintain conflicting formulas in several modules.
- Add tests using hand-calculated fixtures for key metrics.

### Required metric discipline

- Use weighted aggregation for ratio metrics.
- Handle zero and null denominators explicitly.
- Preserve currency and time-zone metadata.
- State the grain of every table and metric.
- Separate platform-attributed and first-party outcomes.
- Separate observed revenue from projected LTV.
- Mark immature retention cohorts.
- Do not compare incompatible attribution windows without disclosure.
- Do not interpret correlation as causation.

### Activation

For the MVP, an Activated Creator is a newly acquired user who publishes a first game within seven days of signup.

Do not change this definition silently. Alternative activation definitions may be analyzed, but the baseline and rationale must remain visible.

### Primary paid-growth metric

Use Cost per Activated Creator as the primary paid-growth metric unless a recorded decision changes it.

```text
CPAC = Paid Media Spend / Paid-Acquired Activated Creators
```

Do not use signup CAC alone to identify a winner.

## 9. Experimentation Rules

Every controlled experiment must include:

- A business question
- A falsifiable hypothesis
- A control when appropriate
- One declared primary variable
- An audience and channel
- A primary metric
- Guardrail metrics
- Minimum evidence requirements
- An evaluation window
- A maturity rule
- A decision rule
- A next action

### Required behavior

- Reject invalid experiment definitions early.
- Distinguish exploratory analysis from confirmatory testing.
- Do not declare winners from immature or insufficient samples.
- Surface effect size and uncertainty.
- Surface guardrail damage even when the primary metric improves.
- Record changes to an active experiment definition.
- Preserve the original hypothesis after results are known.

### Forbidden shortcuts

Do not:

- Label every generated creative an experiment.
- Change several primary variables while claiming a controlled test.
- Choose the primary metric after viewing results.
- Ignore delayed conversions.
- Declare significance based only on direction.
- Use one universal CTR, CVR, or spend threshold for every campaign.

## 10. Creative Strategy and Generation Rules

### Strategy before generation

Do not generate final copy or scripts until the relevant input includes:

- Persona
- Awareness stage
- Customer pain or motivation
- Value proposition
- Message angle
- Proof type
- Creative format
- Hypothesis
- Primary variable tested
- CTA
- Claim or compliance constraints

### Structured output

- Validate LLM output with Pydantic before downstream use.
- Record prompt version, provider, model identifier, and generation time.
- Maintain a deterministic mock provider for tests.
- Limit retries and fail clearly.
- Detect missing fields, duplicates, unsupported claims, and format violations.
- Keep model identifiers configurable rather than hardcoded throughout the codebase.

### Human creative judgment

AI-generated output is a draft. It is not approved merely because it passes schema validation.

Human review should consider:

- Strategic relevance
- Distinctiveness
- Brand fit
- Clarity
- Channel fit
- Production feasibility
- Claim support
- Ethical and policy risk

Do not equate valid JSON with good creative.

## 11. Decision-Agent Rules

Allowed recommendation states are:

- `OBSERVE`
- `REVISE`
- `HOLD`
- `SCALE_CANDIDATE`
- `PAUSE_CANDIDATE`
- `INSUFFICIENT_DATA`

Do not introduce additional states without updating schemas, documentation, and tests.

Every recommendation must include:

- Source metrics
- Comparison or baseline
- Evaluation period
- Data volume
- Maturity status
- Evidence or confidence assessment
- Activation and retention context
- Tradeoff or risk
- Suggested next action
- Human-review status
- Provenance or audit identifier

### Separation of responsibilities

- Deterministic code computes metrics and eligibility.
- The LLM may synthesize a narrative from validated summaries.
- The LLM must not modify source metrics.
- The LLM must not approve its own recommendation.
- A recommendation must never trigger a live mutation by default.

### Insufficient evidence

Represent missing or weak evidence honestly. Prefer `INSUFFICIENT_DATA` or `OBSERVE` over a forced recommendation.

## 12. Platform Connector Rules

### Development sequence

1. Define an abstract connector contract.
2. Build deterministic mock connectors.
3. Add contract tests.
4. Implement read-only integration only when authorized.
5. Add draft creation only after read-only behavior is verified.
6. Keep activation and live mutation outside the MVP.

### Connector requirements

- Separate read and write permissions.
- Use idempotency keys where supported or implement equivalent safeguards.
- Prevent duplicate campaign objects.
- Use bounded retries with backoff.
- Respect rate limits.
- Handle token expiration explicitly.
- Redact secrets and sensitive payloads from logs.
- Keep API versions configurable and documented.
- Fail safely on partial responses.
- Maintain fixtures without real identifiers or credentials.

### Live integrations

When a task depends on a current external API:

- Consult current official documentation.
- Do not rely only on remembered endpoints or permissions.
- Document the version and access prerequisites.
- Keep live integration optional.
- Ensure the local project still works without external access.

## 13. Architecture Rules

Until `ARCHITECTURE.md` states otherwise:

- Keep business logic separate from API connectors.
- Keep analytics separate from LLM narrative generation.
- Keep schemas independent of one vendor when practical.
- Keep configuration out of business logic.
- Prefer simple local infrastructure for the MVP.
- Use interfaces at external system boundaries.
- Avoid circular dependencies.
- Preserve a clear data flow from raw inputs to reports.

Do not introduce Celery, distributed services, cloud infrastructure, or a production warehouse unless the current phase requires them and the user approves the expansion.

## 14. Coding Standards

### Python

- Target Python 3.11 or later.
- Use type annotations for public functions and important internal boundaries.
- Use Pydantic for external and cross-module data contracts.
- Write small functions with explicit inputs and outputs.
- Avoid hidden global state.
- Use `pathlib` for filesystem paths.
- Use timezone-aware timestamps.
- Use `Decimal` or a documented precision strategy for money when exactness matters.
- Raise specific exceptions with actionable messages.
- Do not catch broad exceptions without adding context or re-raising appropriately.

### Data and SQL

- Use explicit column names.
- Avoid `SELECT *` in maintained analytical models.
- Document table grain.
- Keep transformations deterministic.
- Avoid row-by-row processing when vectorized or SQL operations are clearer.
- Test joins for unintended row multiplication.

### Configuration

- Put non-secret defaults in versioned configuration.
- Put secrets only in environment variables or an approved secret store.
- Validate configuration at startup.
- Fail fast when required non-secret configuration is invalid.
- Do not require optional platform credentials for local simulation.

### Dependencies

- Prefer the standard library or existing dependencies when suitable.
- Add a dependency only when it materially reduces risk or complexity.
- Pin or constrain versions appropriately.
- Explain significant new dependencies in the work summary.
- Do not add overlapping libraries for the same purpose without justification.

## 15. Testing Requirements

Every material behavior change requires appropriate tests.

### Test categories

- Unit tests for formulas and business rules
- Schema tests for valid and invalid payloads
- Data-quality tests for generated datasets
- Reproducibility tests for synthetic data
- Contract tests for connectors
- Integration tests for module boundaries
- End-to-end tests for the local demo
- Regression tests for discovered bugs

### Testing principles

- Tests must not depend on live advertising platforms.
- Ordinary tests must not depend on a paid LLM call.
- Use deterministic fixtures.
- Include negative and edge cases.
- Verify outputs, not implementation details, where practical.
- Do not delete or weaken a failing test merely to make the suite pass.
- Do not mark tests as skipped without explaining why.
- Test financial and ratio metrics against hand-calculated examples.

### Minimum checks before completion

Run the relevant subset and, when feasible, the full suite:

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

If a configured command cannot run, report the exact reason and do not claim that it passed.

## 16. Security, Privacy, and Logging

- Never expose secrets in output.
- Never commit credentials, access tokens, cookies, or private keys.
- Never log complete authorization headers or raw secret-bearing payloads.
- Use obviously fictional identifiers in examples.
- Do not use real customer or employee data.
- Sanitize fixtures, screenshots, and notebook outputs.
- Add sensitive files and local outputs to `.gitignore` as appropriate.
- Preserve sufficient audit detail without recording sensitive content.

If a secret is discovered in the worktree, stop displaying it, report the presence without repeating its value, and follow the user’s direction for remediation.

## 17. Documentation Requirements

Update documentation when behavior, interfaces, schemas, formulas, or commands change.

### Source-of-truth locations

| Information                       | Source of truth           |
| --------------------------------- | ------------------------- |
| Public project overview           | `README.md`               |
| Business assumptions and outcomes | `PROJECT_BRIEF.md`        |
| Phase tasks and gates             | `PHASES.md`               |
| Agent behavior                    | `AGENTS.md`               |
| Components and interfaces         | `ARCHITECTURE.md`         |
| Metric and field definitions      | `data/data_dictionary.md` |
| Important decisions               | `DECISIONS.md`            |
| Final portfolio narrative         | `CASE_STUDY.md`           |
| Reproducible demo                 | `DEMO.md`                 |

Avoid duplicating authoritative definitions. Link to the source of truth when possible.

### Documentation integrity

- Do not document features that do not exist.
- Mark planned features as planned.
- Keep example commands executable.
- Keep project-status tables current.
- Label optional integrations clearly.
- Label all simulated results.

## 18. Decision Log Requirements

Record a decision in `DECISIONS.md` when it materially affects:

- Business definitions
- Metric formulas
- Attribution or retention windows
- Data schemas
- Architecture
- External dependencies
- Model or provider strategy
- Safety boundaries
- Public portfolio claims

Recommended entry format:

```markdown
## ADR-XXX — Decision title

- Date:
- Status: Proposed | Accepted | Superseded
- Context:
- Decision:
- Alternatives considered:
- Consequences:
- Validation plan:
```

Do not rewrite historical decisions to hide earlier reasoning. Supersede them with a new entry.

## 19. Git and File-Editing Rules

- Inspect the worktree before editing.
- Preserve unrelated user changes.
- Keep commits focused when commits are requested.
- Do not rewrite history unless explicitly requested.
- Do not use destructive reset or checkout commands to discard work.
- Do not commit generated secrets, large transient files, or local environments.
- Do not commit unless the user asks for a commit.
- Do not push unless the user explicitly asks for a push.
- Do not create a pull request unless explicitly requested.
- Prefer small, reviewable changes over broad rewrites.

## 20. Failure Handling

When something fails:

1. Preserve the original error message and relevant context.
2. Determine whether the failure is code, data, environment, permission, or specification related.
3. Try safe, relevant diagnostics.
4. Do not bypass tests, permissions, approvals, or safety controls.
5. Implement a safe correction only when within scope.
6. Add a regression test for a code defect.
7. Report unresolved blockers clearly.

Do not claim success based on partial output when a required step failed.

## 21. Definition of Done for an Agent Task

A task is complete only when:

- The requested scope is implemented.
- Acceptance criteria are satisfied or exceptions are reported.
- Relevant tests and checks pass.
- Documentation is current.
- Simulation labels remain visible.
- Safety defaults remain intact.
- No credentials or real personal data were introduced.
- Important decisions are recorded.
- Unrelated files were not changed.
- The agent reports limitations and remaining work.

## 22. Required Completion Report

End every implementation task with a concise report using this structure:

```markdown
## Outcome

[What is now implemented]

## Files Changed

- `path/to/file`: purpose

## Verification

- `command`: passed/failed/not run

## Decisions and Assumptions

- [Decision or assumption]

## Limitations

- [What remains simulated, incomplete, or uncertain]

## Next Recommended Step

- [One bounded next step]
```

Do not hide failed checks. Use `not run` when verification was not possible.

## 23. Phase Gate

Do not proceed to the next phase until:

1. Required deliverables for the active phase exist.
2. Acceptance criteria have evidence.
3. Required tests pass.
4. The student completes the decision checkpoint.
5. Documentation is updated.
6. The user explicitly authorizes the next phase.

An AI agent must stop after the requested phase or subtask and wait for review.

## 24. Explicitly Disallowed Claims

Unless independently supported by genuine evidence, do not write or imply:

- “Managed $150K per month in real ad spend”
- “Improved real ROAS, CAC, retention, or revenue”
- “Built this for a named gaming company”
- “Deployed autonomous live campaign optimization”
- “Proved that a channel or creative causes higher LTV”

Use language such as:

- “Simulated”
- “Modeled”
- “Synthetic dataset”
- “Portfolio scenario”
- “Recommendation candidate”
- “Would require validation with real data”

## 25. Agent Self-Check

Before finishing, answer internally:

- Did I work only on the requested scope?
- Did I read the relevant project instructions?
- Did I preserve unrelated changes?
- Did I keep live mutations disabled?
- Did deterministic code calculate authoritative metrics?
- Did I add or update appropriate tests?
- Did I label synthetic results?
- Did I introduce an unsupported claim?
- Did I expose a secret or real identifier?
- Did I record material decisions?
- Can the student understand and explain the result?
- Did I report what was not verified?

If any answer reveals a problem, resolve it before declaring the task complete or report the blocker honestly.
