# Phases

## AI-Powered Creative Optimization & Growth Operations Agent

**Format:** End-to-end portfolio project  
**Recommended duration:** 10–12 weeks  
**Estimated commitment:** 8–12 hours per week  
**Project type:** Independent portfolio simulation  
**Simulated company:** Tablr — AI-powered growth OS for independent restaurants  
**Primary outcome:** An interview-ready growth, creative, analytics, and AI operations portfolio

## 1. Phases Purpose

This Phases turns the project described in `README.md` and `PROJECT_BRIEF.md` into a sequence of buildable, reviewable phases.

Each phase builds a complete local simulation first, proves that the underlying business logic and analytics are correct, and adds optional platform integrations only after safety and quality requirements are satisfied.

The Phases develops four connected capabilities:

1. Growth and performance marketing strategy
2. Performance creative strategy and testing
3. Acquisition, retention, and LTV analytics
4. AI-assisted growth operations and governance

## 2. What This Portfolio Demonstrates

- Translating a business objective into a funnel and KPI hierarchy.
- Defining target personas and message hypotheses.
- Designing controlled creative experiments.
- Building a reproducible synthetic marketing dataset.
- Analyzing media efficiency and acquired-owner quality.
- Calculating activation, retention, LTV, LTV:CAC, and payback.
- Explaining why high CTR or low trial CAC may not indicate good growth.
- Generating structured creative outputs with an LLM.
- Evaluating and validating AI-generated marketing content.
- Producing explainable campaign recommendations.
- Designing human approval and audit controls.
- Communicating findings through dashboards, written reviews, and interviews.

## 3. Prerequisites

### Required

- Basic Python syntax
- Basic SQL concepts
- Familiarity with paid-media metrics such as CPM, CTR, CPC, CVR, CAC, and ROAS
- Basic understanding of marketing funnels and A/B testing
- Git and GitHub fundamentals

### Helpful but not required

- Pandas
- DuckDB
- Pydantic
- Cohort analysis
- Marketing-platform campaign structure
- LLM APIs
- Dashboard development

Each of these areas can be learned during the relevant phase. The project evaluates applied reasoning more heavily than memorization.

## 4. Required Repository Documents

Before implementation begins, the repository should contain:

| Document           | Purpose                                             |
| ------------------ | --------------------------------------------------- |
| `README.md`        | Public project overview and usage                   |
| `PROJECT_BRIEF.md` | Business, audience, funnel, and success definitions |
| `PHASES.md`        | Phase sequence, tasks, and completion criteria      |
| `AGENTS.md`        | Rules for AI coding agents                          |
| `ARCHITECTURE.md`  | System components, interfaces, and data flow        |
| `DECISIONS.md`     | Important decisions, alternatives, and rationale    |
| `CASE_STUDY.md`    | Final portfolio narrative                           |
| `DEMO.md`          | Reproducible demonstration instructions             |

`AGENTS.md` and `ARCHITECTURE.md` are created during Phase 0 before feature implementation.

## 5. Phases Rules

### Accountability

AI may assist with research, planning, coding, testing, debugging, and documentation. The portfolio owner remains responsible for:

- Understanding every important business and technical decision
- Checking calculations and generated claims
- Explaining tradeoffs without relying on AI-generated language
- Distinguishing assumptions from evidence
- Reviewing code before accepting it
- Maintaining honest portfolio disclosures

### AI usage record

For every phase, record:

- What I decided
- What AI helped generate
- What I changed or rejected
- How the output was verified
- What remains uncertain

These notes may be maintained in `DECISIONS.md` or phase reflection files.

### Safety defaults

```env
DRY_RUN=true
RECOMMEND_ONLY=true
ALLOW_LIVE_MUTATIONS=false
```

No phase may silently enable live publishing, budget changes, bid changes, audience uploads, or campaign pauses.

### Honest presentation

All synthetic datasets, simulated findings, and hypothetical business assumptions must be labeled clearly in code, reports, dashboards, and interviews.

## 6. Suggested Timeline

| Week | Phase    | Main outcome                                         |
| ---: | -------- | ---------------------------------------------------- |
|    1 | Phase 0  | Strategy, measurement, architecture, and agent rules |
|    2 | Phase 1  | Reproducible synthetic data foundation               |
|    3 | Phase 2  | Personas, message map, and creative strategy         |
|    4 | Phase 3  | Structured AI creative generation                    |
|    5 | Phase 4  | Experiment registry and measurement logic            |
|    6 | Phase 5  | Paid-media and creative performance analytics        |
|    7 | Phase 6  | Activation, retention, LTV, and budget analysis      |
|    8 | Phase 7  | Explainable decision and recommendation agent        |
|    9 | Phase 8A | Mock connectors, orchestration, and governance       |
|   10 | Phase 8B | Optional authorized draft-only API integration       |
|   11 | Phase 9A | Dashboard, weekly review, and case study             |
|   12 | Phase 9B | Demo, interview practice, and final audit            |

Phases 5–7 contain the strongest evidence of growth decision-making and deserve the most time.

---

## Phase 0 — Growth Strategy and Project Foundation

### Business question

What business outcome should the growth system optimize, and how will the team distinguish cheap acquisition from valuable acquisition?

### Learning objectives

- Translate a product concept into a measurable growth model.
- Define the customer journey and activation event.
- Separate leading indicators from business outcomes.
- Establish project scope, assumptions, safety boundaries, and architecture.

### Concepts

- North Star metrics
- Funnel design
- Activation definitions
- Metric hierarchy
- Channel roles
- Attribution assumptions
- Guardrail metrics
- Decision logs
- Human-in-the-loop automation

### Build tasks

1. Review `PROJECT_BRIEF.md` and identify every assumption.
2. Confirm or revise the hypothetical product, business model, market, and currency.
3. Map the journey from ad impression through paid subscription.
4. Define Monthly Active Restaurants (MAR).
5. Define an Activated Owner for the MVP (campaign launched within 14 days of trial signup).
6. Define CPAO and explain why it is primary over trial CAC.
7. Create a KPI specification with formulas and owners.
8. Document initial attribution and retention-window assumptions.
9. Create `AGENTS.md` with coding-agent rules.
10. Create `ARCHITECTURE.md` with component boundaries and data flow.
11. Initialize `DECISIONS.md` and record open decisions.
12. Create the Python project scaffold and CI skeleton without implementing business features.

### Required deliverables

- Updated `PROJECT_BRIEF.md`
- `AGENTS.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `docs/kpi_specification.md`
- `docs/measurement_plan.md`
- Initial repository directories
- Basic CI workflow

### Acceptance criteria

- Every primary metric has a definition, formula, grain, and data source.
- Activation is behavioral rather than based only on signup.
- Primary and guardrail metrics are clearly separated.
- Simulation assumptions are labeled.
- MVP and advanced scope are separated.
- Live mutations are disabled by default.
- An AI agent can determine which files it must read before editing.
- A reviewer can explain Tablr’s business goal and growth challenge in under two minutes.

### Tests and checks

- Markdown links and headings are valid.
- The Python environment installs successfully.
- A minimal test command runs successfully.
- CI executes formatting and tests.
- `.env`, credentials, and generated data are handled by `.gitignore` as intended.

### Decision checkpoint

Without AI-generated wording, explain:

1. Why is CPAO more useful than trial CAC?
2. What behavior represents initial product value for a restaurant owner?
3. What could make the activation definition misleading?
4. Which decisions remain assumptions?

### Portfolio evidence

- KPI tree
- Customer journey diagram
- Measurement plan
- Architecture overview
- Initial decision log

### Interview questions

- How did you choose MAR as the North Star metric over MRR?
- How would you know if campaign launch within 14 days predicts M3 retention?
- What would change if the business optimized only for trial signups?
- Which project decisions did you intentionally defer?

---

## Phase 1 — Synthetic Data Foundation

### Business question

What data is required to connect paid-media activity to activation, retention, and revenue without access to a real company dataset?

### Learning objectives

- Design campaign and product-event schemas.
- Generate reproducible synthetic data.
- Preserve lineage between creative, experiment, campaign, and user outcomes.
- Build data-quality checks before analysis.

### Concepts

- Data grain and primary keys
- Event data
- Fact and dimension tables
- Join paths
- Data lineage
- Random seeds
- Missing and delayed data
- Data contracts
- Schema validation

### Build tasks

1. Define Pydantic models for personas, creatives, experiments, campaigns, daily performance, users, product events, revenue, and recommendations.
2. Define campaign hierarchy across Meta, TikTok, Google Search, and YouTube.
3. Implement deterministic IDs and join keys.
4. Build a generator for 12 weeks of synthetic performance.
5. Generate at least 10 campaigns, 30 targeting groups, 90 creatives, and 5,000 restaurant owner trials.
6. Generate acquisition, product, retention, subscription, and revenue events.
7. Encode intentional analytical patterns listed in `PROJECT_BRIEF.md`.
8. Add delayed conversions, null attribution, immature cohorts, and one detectable data-quality issue.
9. Write CSV and Parquet outputs.
10. Create the complete data dictionary.
11. Add schema, uniqueness, range, referential-integrity, and reproducibility tests.

### Required deliverables

- `scripts/generate_synthetic_data.py`
- `data/synthetic/README.md`
- `data/data_dictionary.md`
- Synthetic campaign tables
- Synthetic product-event tables
- `tests/unit/test_schemas.py`
- `tests/data/test_data_quality.py`
- `tests/data/test_reproducibility.py`

### Required synthetic patterns

- High CTR with low activation
- Lower CTR with higher LTV
- Creative fatigue after early success
- Platform-attributed winner with weak blended economics
- New creative with insufficient data
- Strong simulated winner across activation and retention
- Delayed conversions
- Missing attribution
- Immature retention cohorts
- Detectable data-quality defect

### Acceptance criteria

- The same seed produces the same rows and results.
- Every performance row links to valid campaign and creative records.
- Product events can be connected to acquisition where attribution exists.
- Invalid enum values and impossible metrics fail validation.
- Synthetic labels appear in filenames or metadata and documentation.
- The encoded patterns are verified by tests, not merely described.
- No real personal data or customer identifiers are used.

### Tests and checks

- Unique keys are unique.
- Foreign keys resolve.
- Spend and counts are non-negative.
- Clicks do not exceed impressions.
- Conversions do not exceed the relevant upstream population.
- Event timestamps follow valid event order.
- Revenue and subscription relationships are internally consistent.
- Reproducibility test passes for a fixed seed.

### Decision checkpoint

Explain:

1. Which synthetic patterns were intentionally created?
2. Which patterns could accidentally bias the final recommendation system?
3. Why were CSV and Parquet both included?
4. What can synthetic data validate, and what can it never prove?

### Portfolio evidence

- Entity and event model
- Data dictionary
- Data-quality test results
- Example lineage from creative to retained user

### Interview questions

- How did you model delayed conversions?
- How would the schema change with a real warehouse?
- How did you ensure synthetic data did not make the answer too obvious?
- What data-quality failures could corrupt CAC or retention?

---

## Phase 2 — Audience and Performance Creative Strategy

### Business question

Which audiences, motivations, barriers, messages, and creative formats should be tested to acquire users who reach product value?

### Learning objectives

- Translate audience hypotheses into distinct messaging.
- Create useful creative briefs rather than disconnected copy variations.
- Define creative attributes that can later be analyzed.
- Connect each concept to a business and customer hypothesis.

### Concepts

- Persona hypotheses
- Awareness stages
- Jobs to be done
- Message hierarchy
- Hook taxonomy
- Proof mechanisms
- UGC and product demonstration
- Creative fatigue
- Message match
- Organic-to-paid pipelines

### Build tasks

1. Expand the five initial personas using evidence-based assumptions.
2. Create a message map covering pain, desired outcome, barrier, value proposition, and proof.
3. Develop a hook taxonomy.
4. Define initial creative formats for each channel.
5. Create at least 15 strategic creative briefs.
6. Include static, short-form video, UGC, product-demo, and landing-page concepts.
7. Identify the single primary variable tested by each experiment.
8. Define a creative naming convention and metadata standard.
9. Create a creative QC checklist.
10. Document unsupported or prohibited claim patterns.

### Required deliverables

- `data/config/personas.yaml`
- `data/config/brand.yaml`
- `docs/message_map.md`
- `docs/hook_taxonomy.md`
- `docs/creative_testing_matrix.md`
- `docs/creative_qc_checklist.md`
- `docs/examples/creative_briefs/`

### Acceptance criteria

- Personas differ by motivation and barrier, not only demographics.
- Each brief contains a hypothesis and primary variable.
- Visual concepts are specific enough for a producer to execute.
- Creative concepts match channel behavior without becoming platform clichés.
- Claims are supportable within the hypothetical scenario.
- Landing-page message matching is represented.
- At least three briefs address downstream acquisition quality, not only clicks.

### Tests and checks

- Creative IDs are unique.
- Required metadata validates against schema.
- Each variant links to an experiment or documented exploratory concept.
- Unsupported absolute claims are flagged.
- Control and variant naming is consistent.

### Decision checkpoint

Explain:

1. How are the five personas meaningfully different?
2. Why should one experiment isolate one variable?
3. Which concepts are expected to drive clicks versus activation?
4. Which AI-generated ideas were rejected, and why?

### Portfolio evidence

- Persona-to-message matrix
- Hook taxonomy
- Three strongest creative briefs
- Testing matrix
- QC checklist

### Interview questions

- How do you turn campaign data into creative direction?
- How would you establish an organic-to-paid feedback loop?
- How do you maintain creative quality at high production volume?
- What makes a creative brief actionable?

---

## Phase 3 — Structured AI Creative Generation

### Business question

How can an AI system increase creative velocity without losing strategic intent, schema consistency, brand quality, or human accountability?

### Learning objectives

- Design structured LLM input and output contracts.
- Implement provider abstraction and mock mode.
- Validate content before downstream use.
- Evaluate quality beyond successful JSON parsing.

### Concepts

- System and task prompts
- Structured output
- Pydantic validation
- Prompt injection boundaries
- Retries and fallbacks
- LLM evaluation
- Cost and latency tracking
- Claim and brand-safety checks

### Build tasks

1. Define input and output schemas for creative generation.
2. Implement an LLM provider interface.
3. Implement a deterministic mock provider for tests.
4. Add an Anthropic provider selected through configuration.
5. Generate variants from an approved creative brief.
6. Validate required fields and platform constraints.
7. Add claim, brand-voice, duplication, and strategic-alignment checks.
8. Create a small evaluation dataset with approved and rejected examples.
9. Track model, prompt version, latency, token usage, and estimated cost.
10. Fail safely after bounded retries.

### Required deliverables

- `docs/prompts/system_prompt.md`
- `docs/prompts/creative_generation.md`
- `evals/creative_generation_cases.yaml`
- `tests/unit/test_creative_generator.py`
- `tests/integration/test_llm_contract.py`

### Acceptance criteria

- The pipeline runs without an API key through mock mode.
- Invalid output never reaches downstream campaign objects.
- Prompt and model versions are recorded.
- Generated concepts remain linked to briefs and hypotheses.
- Duplicate or near-duplicate variations are detected.
- Unsupported claims are flagged for review.
- Tests do not depend on live LLM calls.
- API errors produce a clear, non-destructive failure.

### Tests and checks

- Valid response parsing
- Invalid JSON and missing-field handling
- Retry limits
- Timeout handling
- Duplicate detection
- Claim-rule violations
- Prompt-version recording
- Mock-provider determinism

### Decision checkpoint

Explain:

1. Why is valid JSON not enough to establish creative quality?
2. What belongs in deterministic code versus an LLM prompt?
3. How did you reduce repetitive creative output?
4. What should always require human creative judgment?

### Portfolio evidence

- Input brief and final structured variants
- Evaluation results
- Example of a rejected AI output
- Cost and latency summary

### Interview questions

- How would you evaluate an AI creative workflow?
- What happens when the model changes?
- How do you prevent unsupported claims?
- Why did you build a mock provider?

---

## Phase 4 — Experiment Registry and Measurement Engine

### Business question

How can the team distinguish real learning from uncontrolled creative variation and noisy campaign results?

### Learning objectives

- Register hypotheses, controls, and variants.
- Select primary and guardrail metrics.
- Define evidence requirements and evaluation windows.
- Represent experiment states and decisions.

### Concepts

- Hypothesis design
- Control and treatment
- Unit of randomization
- Sample ratio and contamination
- Practical versus statistical significance
- Multiple comparisons
- Sequential decision risk
- Experiment maturity

### Build tasks

1. Define the experiment schema and state machine.
2. Implement experiment creation and validation.
3. Link creative variants to controls.
4. Require one declared primary variable.
5. Configure primary and guardrail metrics.
6. Add minimum evidence and maturity rules.
7. Implement evaluation windows and cohort maturity flags.
8. Calculate absolute and relative differences.
9. Add a basic uncertainty method appropriate to the metric.
10. Produce an experiment readout template.

### Required deliverables

- `data/config/experiments.yaml`
- `docs/experiment_playbook.md`
- `docs/examples/experiment_readout.md`
- Experiment unit and integration tests

### Acceptance criteria

- An experiment cannot start without a hypothesis and primary metric.
- Every controlled variant references a valid control.
- Immature experiments cannot be declared winners.
- Guardrail damage appears in the readout.
- Results include effect size and uncertainty, not only winner labels.
- Exploratory analysis is clearly distinguished from confirmatory testing.

### Tests and checks

- Missing-control validation
- Duplicate-variant validation
- Insufficient-sample handling
- Immature-cohort handling
- Zero-denominator handling
- Metric-direction validation
- Known synthetic effect recovery

### Decision checkpoint

Explain:

1. What is the experiment’s unit of comparison?
2. When would you continue collecting data rather than act?
3. Why can repeated daily winner checks be misleading?
4. When is practical significance more important than statistical significance?

### Portfolio evidence

- Experiment registry
- One complete test readout
- Example of `INSUFFICIENT_DATA`
- Example where the guardrail changes the decision

### Interview questions

- How do you decide whether a creative test has enough evidence?
- How do you handle multiple variants?
- What would invalidate the experiment?
- How do you balance speed with rigor?

---

## Phase 5 — Paid Acquisition and Creative Performance Analytics

### Business question

What happened in paid acquisition, which creative attributes explain it, and where should the team investigate further?

### Learning objectives

- Calculate platform and blended media metrics correctly.
- Analyze performance across channel, campaign, persona, and creative.
- Detect creative fatigue and data-quality problems.
- Separate descriptive findings from causal claims.

### Concepts

- CPM, CTR, CPC, CVR, CAC, and ROAS
- Weighted aggregation
- Simpson’s paradox
- Attribution bias
- Creative decomposition
- Time-series diagnostics
- Fatigue and frequency
- Marginal performance

### Build tasks

1. Build a DuckDB analytical layer.
2. Create canonical daily performance models.
3. Calculate media metrics safely at each grain.
4. Compare platform-reported and blended outcomes.
5. Analyze results by channel, persona, hook, angle, format, and creative.
6. Detect high-CTR, low-activation patterns.
7. Implement creative fatigue indicators.
8. Identify missing, late, or anomalous data.
9. Produce a reusable performance report.
10. Add tests for weighted metrics and aggregation errors.

### Required deliverables

- `scripts/sql/` analytical models
- `docs/notebooks/01_acquisition_analysis.ipynb`
- `reports/acquisition_baseline.md`
- Analytics unit and regression tests

### Acceptance criteria

- Aggregate CTR and CPC use weighted calculations.
- Zero and null denominators are handled explicitly.
- Results can be reproduced outside the notebook.
- The analysis identifies the intentional synthetic patterns.
- Creative fatigue is based on time and supporting signals.
- Findings distinguish correlation from causation.
- Platform and first-party results are not blended without labeling.

### Tests and checks

- Formula tests using hand-calculated fixtures
- Aggregation consistency
- Duplicate-row handling
- Currency and time-zone consistency
- Missing-date detection
- Fatigue-pattern recovery
- Data-quality defect detection

### Decision checkpoint

Explain:

1. Why should CTR not be averaged across rows directly?
2. Which result changed after weighting correctly?
3. How did you distinguish fatigue from ordinary daily noise?
4. Which finding is descriptive rather than causal?

### Portfolio evidence

- Channel scorecard
- Creative attribute analysis
- Fatigue example
- High-CTR, low-quality example
- Data-quality finding and correction

### Interview questions

- How do you diagnose a rising CAC?
- How do you know whether creative is the problem?
- What can platform ROAS fail to capture?
- What would you test after finding a high-CTR, low-CVR ad?

---

## Phase 6 — Activation, Retention, LTV, and Budget Allocation

### Business question

Which acquisition sources produce users who reach value, return, and generate enough economic value to justify further investment?

### Learning objectives

- Build acquisition cohorts.
- Calculate activation and retention consistently.
- Estimate LTV and payback with explicit limitations.
- Compare media efficiency with downstream quality.
- Simulate budget allocation without overstating certainty.

### Concepts

- Cohort analysis
- Right censoring
- Retention windows
- Activation validation
- Observed versus modeled LTV
- Payback period
- LTV:CAC
- Marginal CAC
- Exploration versus exploitation

### Build tasks

1. Build signup and acquisition cohorts.
2. Calculate activation within 14 days (campaign launched within 14 days of trial signup).
3. Calculate M1, M3, and M6 retention using documented subscription windows.
4. Flag immature cohorts (M6 cohorts with less than 180 days of observation).
5. Calculate observed cohort revenue.
6. Build a simple, transparent LTV estimate.
7. Calculate LTV:CAC and payback period.
8. Analyze outcome quality by channel, persona, experiment, and creative.
9. Compare optimization based on CTR, trial CAC, CPAO, and LTV.
10. Build a configurable budget-allocation simulator.
11. Preserve an exploration budget instead of allocating entirely to winners.

### Required deliverables

- `docs/notebooks/02_retention_ltv.ipynb`
- `reports/acquisition_quality.md`
- `docs/examples/budget_recommendation.json`
- Cohort, LTV, and allocation tests

### Acceptance criteria

- Cohort denominators remain consistent.
- Immature M6 cohorts are not reported as final.
- Observed revenue and projected LTV are visibly different.
- Model assumptions appear beside LTV outputs.
- The analysis reveals at least one ranking reversal after downstream quality is included.
- Budget recommendations respect minimums, maximums, and exploration allocation.
- The allocator does not imply causal certainty.

### Tests and checks

- Retention-window boundary tests
- Cohort maturity tests
- Revenue reconciliation
- LTV assumption sensitivity
- Budget sums to the configured total
- Channel constraints are respected
- Zero-conversion and sparse-data handling

### Decision checkpoint

Explain:

1. Which source looked best by trial CAC but worse by CPAO or LTV?
2. How does right censoring affect M6 retention?
3. Which part of LTV is observed, and which part is modeled?
4. Why should some budget remain exploratory?

### Portfolio evidence

- Cohort retention view
- Creative-to-retention analysis
- LTV:CAC comparison
- Budget-allocation scenario
- Sensitivity analysis

### Interview questions

- How do you connect acquisition to retention?
- When would you accept a higher CAC?
- How do you evaluate LTV with limited history?
- How would you allocate an additional $20,000?

---

## Phase 7 — Explainable Growth Decision Agent

### Business question

How can the system convert multi-layer performance evidence into useful recommendations without hiding uncertainty or removing human accountability?

### Learning objectives

- Separate deterministic metric calculation from narrative synthesis.
- Create a transparent recommendation policy.
- Represent insufficient evidence explicitly.
- Generate next-test proposals from observed patterns.

### Concepts

- Decision-support systems
- Rules versus models
- Confidence and evidence quality
- Guardrails
- Recommendation provenance
- Human review
- Feedback loops
- Auditability

### Build tasks

1. Implement the allowed recommendation states.
2. Create evidence and maturity checks before recommendation generation.
3. Generate deterministic metric summaries.
4. Pass only validated summaries to the LLM for narrative synthesis.
5. Require recommendation rationale, tradeoff, risk, and next action.
6. Add a human-review state and reviewer notes.
7. Create next-experiment suggestions tied to findings.
8. Prevent a single metric threshold from determining a live action.
9. Add an audit record for each recommendation and status change.
10. Test contradictory, sparse, delayed, and anomalous inputs.

### Required deliverables

- `docs/prompts/performance_diagnosis.md`
- `docs/prompts/winner_iteration.md`
- Recommendation examples
- Decision-policy and agent tests

### Acceptance criteria

- Every recommendation links to source metrics and an evaluation period.
- Insufficient evidence results in `INSUFFICIENT_DATA` or `OBSERVE`.
- A recommendation cannot become an approved action automatically.
- Conflicting acquisition and retention signals are surfaced.
- The LLM cannot alter calculated metrics.
- Every next test contains a hypothesis and primary variable.
- Audit history records who or what changed the recommendation state.

### Tests and checks

- Sparse-data behavior
- Conflicting-signal behavior
- Delayed-conversion behavior
- Immutable metric summary
- Unsupported recommendation-state rejection
- Approval-state transitions
- Audit completeness
- Narrative grounding checks

### Decision checkpoint

Explain:

1. Which decisions are deterministic and which use AI?
2. Why should the LLM not calculate authoritative metrics?
3. When should the system recommend observation rather than action?
4. How can reviewer rejection improve future recommendations?

### Portfolio evidence

- Example scale candidate
- Example pause candidate
- Example insufficient-data decision
- Human-review flow
- Next-test recommendation

### Interview questions

- What makes the system agentic?
- Where did you deliberately limit autonomy?
- How do you prevent hallucinated performance claims?
- How would you measure recommendation quality?

---

## Phase 8 — Orchestration, Connectors, and Governance

### Business question

How can the workflow operate reliably across systems while preventing duplicate, unauthorized, or unsafe campaign actions?

### Learning objectives

- Build stable connector interfaces.
- Use mock implementations for reliable development.
- Design idempotent and auditable operations.
- Handle API failures, limits, and credentials safely.

### Concepts

- Ports and adapters
- API contracts
- Idempotency
- Retries and backoff
- Rate limits
- Secret management
- Draft versus live actions
- Approval gates
- Observability

### Phase 8A: Required local orchestration

#### Build tasks

1. Define connector interfaces for campaign drafts and reporting data.
2. Implement deterministic mock Meta and TikTok connectors.
3. Implement campaign naming and UTM validation.
4. Add a local pipeline for generation, analysis, triage, review, and reporting.
5. Add idempotency keys and duplicate prevention.
6. Add structured logging without secrets or personal data.
7. Add bounded retries and clear failure states.
8. Add explicit approval commands without enabling live mutation.
9. Add end-to-end integration tests.

#### Required deliverables

- `scripts/run_pipeline.py`
- Contract and end-to-end tests

#### Acceptance criteria

- The full local demo runs without external credentials.
- Repeating the same command does not create duplicate objects.
- Failures do not leave partially approved states.
- Dry-run output clearly shows intended actions.
- Logs contain no secrets.
- No command can enable live mutation accidentally.

### Phase 8B: Optional authorized draft-only integration

This phase is optional and should be attempted only with an authorized developer or sandbox account and current official API documentation.

#### Optional tasks

1. Add one platform at a time.
2. Implement read-only reporting first.
3. Implement draft creation only after read-only tests pass.
4. Verify permissions, rate limits, token expiration, and API versioning.
5. Add contract fixtures with secrets removed.
6. Document every manual platform prerequisite.
7. Keep activation and destructive actions disabled.

#### Optional acceptance criteria

- Credentials are provided only through approved secret configuration.
- Live calls are excluded from ordinary CI.
- Draft objects are distinguishable from active objects.
- API errors fail safely.
- The repository works fully when the optional connector is absent.
- No real spend or delivery is triggered.

### Decision checkpoint

Explain:

1. Why did the project begin with mock connectors?
2. How does idempotency prevent operational harm?
3. Which failures are safe to retry?
4. Why is a live API connection not required to prove the project’s core value?

### Portfolio evidence

- End-to-end local demo
- Connector contract
- Approval and audit trail
- Duplicate-prevention test
- Optional draft screenshot with sensitive information removed

### Interview questions

- How would this architecture integrate with a warehouse?
- How do you handle rate limits and partial failures?
- What controls would you require before production use?
- Why did you separate reporting and mutation permissions?

---

## Phase 9 — Dashboard, Case Study, and Interview Readiness

### Business question

Can a hiring team quickly understand the business problem, reasoning, results, limitations, and value of the project?

### Learning objectives

- Build decision-oriented reporting.
- Communicate a complex system clearly.
- Present simulated findings honestly.
- Defend strategic and technical decisions in interviews.

### Concepts

- Executive information hierarchy
- Decision-oriented dashboards
- Data storytelling
- Case-study structure
- Demo design
- Portfolio integrity
- Interview communication

### Build tasks

1. Build a Creative Intelligence dashboard.
2. Include acquisition, activation, retention, and economic views.
3. Include data maturity and simulation labels.
4. Add filters for channel, persona, experiment, creative, and date.
5. Produce a weekly growth review with decisions and next tests.
6. Complete `CASE_STUDY.md`.
7. Complete `DEMO.md` with reproducible steps.
8. Record a three-to-five-minute demo.
9. Prepare a concise interview presentation.
10. Create an interview question-and-answer bank.
11. Audit every public claim against repository evidence.
12. Run a clean-clone test of the project.

### Required dashboard views

- Executive growth scorecard
- Funnel from click to activated owner (trial → onboarding → campaign launch → paid)
- Channel and persona acquisition quality
- Creative performance and fatigue
- Cohort retention (M1, M3, M6)
- LTV:CAC and payback
- Experiment readouts
- Recommendation and approval queue
- Budget-allocation scenario

### Required weekly review sections

1. What changed?
2. What appears to be working?
3. What appears weak or uncertain?
4. Which result should not be trusted yet?
5. What should be observed, revised, held, scaled, or paused?
6. How did activation and retention affect the conclusion?
7. What will be tested next?
8. Which assumptions require real-world validation?

### Required case-study sections

- Business problem
- Audience and growth hypotheses
- Measurement strategy
- Creative strategy
- Experiment design
- Architecture
- Simulated findings
- Decisions and tradeoffs
- Safety and governance
- Limitations
- Next experiment

### Acceptance criteria

- The dashboard prioritizes decisions over visual decoration.
- Every displayed metric has a documented definition.
- Simulated and projected values are visibly labeled.
- A reviewer can trace a recommendation back to evidence.
- The case study explains at least one counterintuitive finding.
- The demo can run from a clean environment.
- Public claims match repository evidence.
- The work can be explained without reading a script.

### Tests and checks

- Clean clone and installation
- End-to-end demo command
- Dashboard metric reconciliation
- Broken-link check
- Secret scan
- License check
- Accessibility and color-contrast review
- Portfolio-claim audit

### Decision checkpoint

Explain:

1. What is the single most important finding?
2. Which recommendation would you make to leadership?
3. What evidence would change your mind?
4. What part of the project best demonstrates your personal judgment?

### Portfolio evidence

- Public GitHub repository
- Dashboard screenshots or live demo
- Weekly growth review
- Case study
- Demo video
- Interview presentation

### Interview questions

- Walk me through the project in three minutes.
- What did you personally decide rather than delegate to AI?
- What result surprised you?
- What would you do with real customer and spend data?
- What would you change before production deployment?

---

## 7. Phase Completion Template

Create a short completion note after each phase using this structure:

```markdown
# Phase N Completion Review

## Business Question

## What I Built

## Key Decisions I Made

## How AI Assisted

## What I Changed or Rejected

## Tests and Verification

## Key Finding

## Limitations

## Open Decisions

## Portfolio Evidence

## Ready for Next Phase?

- [ ] All deliverables exist
- [ ] Acceptance criteria pass
- [ ] Tests pass
- [ ] Documentation is current
- [ ] Simulation labels are visible
- [ ] I can explain the work without AI assistance
```

## 8. Phase Gate Policy

A phase is complete only when:

1. Required deliverables exist.
2. Acceptance criteria are checked with evidence.
3. Relevant automated tests pass.
4. Important assumptions and decisions are documented.
5. The decision checkpoint can be answered independently without AI assistance.
6. The repository remains runnable.
7. No safety default has been weakened.

Do not begin optional live integrations while any core local phase is incomplete.

## 9. AI Coding Agent Workflow

Use one bounded request per phase or subtask. Do not ask an AI agent to build the entire repository in one turn.

Recommended task format:

```text
Read README.md, PROJECT_BRIEF.md, PHASES.md, AGENTS.md,
ARCHITECTURE.md, and DECISIONS.md.

Implement only: [PHASE / SUBTASK].

Required deliverables:
- [FILES OR BEHAVIORS]

Acceptance criteria:
- [OBJECTIVE CONDITIONS]

Constraints:
- Use synthetic data only.
- Keep DRY_RUN=true.
- Keep RECOMMEND_ONLY=true.
- Keep ALLOW_LIVE_MUTATIONS=false.
- Do not add unrelated features.
- Do not expose or request credentials.

Before editing:
1. Inspect the relevant existing files.
2. Restate the intended changes.
3. Identify assumptions or conflicts.

After editing:
1. Run relevant tests and quality checks.
2. Report files changed.
3. Report test results.
4. Report limitations and open decisions.
5. Stop; do not continue to the next phase.
```

## 10. Assessment Rubric

| Area                 | Weight | Strong performance                                           |
| -------------------- | -----: | ------------------------------------------------------------ |
| Growth strategy      |    15% | Clear funnel, personas, KPI tree, and channel logic          |
| Creative strategy    |    20% | Distinct hypotheses, useful briefs, controlled variables     |
| Analytics            |    20% | Correct metrics, cohorts, retention, LTV, and caveats        |
| Experimentation      |    15% | Sound controls, maturity rules, and evidence-based decisions |
| AI system design     |    10% | Structured outputs, evaluation, cost controls, safe failure  |
| Engineering quality  |    10% | Modular code, tests, CI, documentation, observability        |
| Safety and integrity |    10% | Approval gates, audit trail, honest simulation labels        |

### Passing standard

- Overall score of at least 75%
- No score below 60% in Analytics, Experimentation, or Safety and Integrity
- All required Phase 9 deliverables complete
- No unsupported claims in public portfolio materials

## 11. Recommended Final Demonstration

The final demo should take three to five minutes:

1. Introduce the hypothetical business problem.
2. Show one persona and creative hypothesis.
3. Generate or load validated variants.
4. Show the experiment registry.
5. Display acquisition performance.
6. Reveal how activation or retention changes the apparent winner.
7. Show the recommendation and human-review state.
8. Show the proposed next experiment.
9. Close with limitations and what real data would validate.

## 12. Graduation Checklist

### Strategy

- [ ] Business objective and North Star metric are clear
- [ ] Activation definition is documented
- [ ] Personas and channel roles are testable hypotheses
- [ ] KPI tree connects media to business outcomes

### Creative

- [ ] Message map and hook taxonomy exist
- [ ] At least 15 strategic briefs exist
- [ ] Every controlled variant identifies its primary variable
- [ ] Creative QC and claim checks exist

### Data and analytics

- [ ] Synthetic data is reproducible
- [ ] Data dictionary is complete
- [ ] Acquisition metrics are tested
- [ ] Activation and retention cohorts are correct
- [ ] Observed and modeled LTV are separated
- [ ] Budget simulation preserves exploration

### AI and decisioning

- [ ] Mock provider works without an API key
- [ ] LLM outputs are validated and evaluated
- [ ] Recommendations show evidence and uncertainty
- [ ] Human approval is required for actions
- [ ] Audit history is complete

### Engineering

- [ ] Clean installation succeeds
- [ ] Unit, integration, contract, and data tests pass
- [ ] CI passes
- [ ] Logs contain no secrets
- [ ] Pipeline is idempotent where required

### Portfolio

- [ ] Dashboard supports the required decisions
- [ ] Weekly growth review is complete
- [ ] Case study clearly labels simulation
- [ ] Demo is reproducible
- [ ] Video and presentation are concise
- [ ] All decisions can be explained independently without AI

## 13. Definition of Done

The portfolio is complete when the full reasoning chain can be clearly explained and demonstrated:

```text
Business objective
→ Audience hypothesis
→ Creative hypothesis
→ Controlled experiment
→ Acquisition result
→ Activation and retention result
→ Economic interpretation
→ Human-reviewed recommendation
→ Next test
```

The strongest portfolio outcome is not the most complex automation. It is a credible demonstration of growth judgment, creative strategy, analytical rigor, AI-assisted execution, and responsible operational design.
