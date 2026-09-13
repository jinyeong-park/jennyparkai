# AI-Powered Creative Optimization & Growth Operations Agent

An end-to-end portfolio project demonstrating how a B2B SaaS growth team can use AI, experimentation, analytics, and marketing APIs to improve paid acquisition and creative operations.

The simulated company is **Tablr** — an AI-powered growth OS for independent restaurant owners. The system generates structured creative concepts, prepares draft campaigns, analyzes simulated performance data, recommends actions, and converts findings into the next round of testable hypotheses.

**[Dashboard](https://jennypark-growth-operation-agent.streamlit.app/)**

> **Portfolio disclosure:** This is an independently built portfolio simulation using synthetic data and a hypothetical company (Tablr). It demonstrates how a growth team could structure creative generation, campaign operations, experimentation, and performance analysis. It must not be presented as evidence of managing a real ad budget unless supported by verifiable professional experience.

## Why This Project Exists

Fast-growing B2B SaaS companies need marketers who can connect:

- Creative strategy and performance creative production
- Paid acquisition across multiple channels (Meta, TikTok, Google, LinkedIn)
- Experiment design and measurement
- Trial CAC, CPAO, LTV, activation, and retention
- AI-assisted workflows and operational automation

This project demonstrates those capabilities through a working, explainable, and safety-conscious system — not merely an AI copy generator.

## Default Use Case

The default case study is **Tablr** — a simulated AI-powered growth OS for independent restaurant owners. Tablr helps indie operators attract new customers, convert them, and build loyalty without a marketing team.

Target audiences:

- Independent restaurant owners (1–3 locations)
- New restaurant owners building their first customer base
- Delivery-heavy owners wanting to own the customer relationship
- Growth-minded operators looking to scale without adding headcount
- Community-focused chef-owners with strong local identity

See `docs/PROJECT_BRIEF.md` for full persona definitions, funnel design, and KPI tree.

## Project Status

Keep this table accurate. Never describe planned or simulated functionality as production-ready.

| Capability          | MVP                            | Advanced version              |
| ------------------- | ------------------------------ | ----------------------------- |
| Creative generation | Anthropic API or mock provider | Evaluated multi-step workflow |
| Campaign creation   | Local mock connector           | Authorized platform drafts    |
| Performance data    | Synthetic dataset              | Authorized reporting data     |
| Performance triage  | Recommendation only            | Human-approved action         |
| Auto-pause          | Disabled                       | Optional, guarded, audited    |
| Product events      | Simulated first-party events   | Authorized analytics source   |
| Retention and LTV   | Cohort simulation              | Observed first-party outcomes |
| Feedback loop       | Offline portfolio workflow     | Scheduled monitored workflow  |

## Workflow

```mermaid
flowchart TD
    A[Brand and persona inputs] --> B[Creative strategy agent]
    B --> C[Structured creative variants]
    C --> D[Experiment registry]
    D --> E[Draft campaign or simulation]
    E --> F[Campaign and product events]
    F --> G[Analytics and triage]
    G --> H[Human review]
    H --> I[Next-test recommendations]
    I --> B
```

The default workflow is `dry-run` and `recommend-only`. The system must not spend money, publish an ad, modify a budget, or pause a live campaign without explicit authorization and an audit trail.

## Scope

### Included

- Persona and messaging configuration
- AI-assisted briefs, hooks, copy, scripts, and visual concepts
- Experiment registration and variant tracking
- Campaign naming and UTM generation
- Synthetic campaign and product-event data
- Performance, cohort, retention, and LTV analysis
- Creative-performance diagnostics
- Human-reviewed scale, hold, revise, and pause recommendations
- Optional draft-only Meta and TikTok connectors
- Weekly growth review and portfolio case study

### Non-goals

- Claiming simulated results as real outcomes
- Unsupervised production budget changes
- Circumventing platform policy or review
- Treating platform attribution as ground truth
- Replacing legal, privacy, brand, or compliance review
- Applying one KPI threshold to every campaign

## Architecture

| Layer           | Responsibility                                            |
| --------------- | --------------------------------------------------------- |
| Strategy        | Brand, audience, funnel, messaging, and hypotheses        |
| Generation      | Structured briefs and creative variants                   |
| Experimentation | Controls, variables, evidence rules, and decisions        |
| Connectors      | Mock or authorized marketing and product data             |
| Analytics       | Campaign, cohort, retention, LTV, and creative analysis   |
| Decisioning     | Explainable recommendations with confidence and rationale |
| Governance      | Approvals, audit logs, secrets, policy, and cost controls |
| Reporting       | Dashboards, weekly reviews, and portfolio outputs         |

## Creative Intelligence Schema

Each creative must preserve the strategy behind it—not just the final copy.

```yaml
creative_id: cr_001
persona: scrappy_independent_owner
awareness_stage: problem_aware
customer_pain: losing_customers_to_chains_and_delivery_apps
value_proposition: marketing_infrastructure_without_a_marketing_team
angle: compete_with_chains
hook_type: contrast
primary_hook: "Chains have a full marketing team. You don't. Tablr fixes that."
supporting_claim: null
proof_type: social_proof_owner_testimonial
visual_concept: side_by_side_chain_vs_indie_results
opening_3_seconds: show_empty_tables_then_waitlist
script: "..."
headline: "Stop losing to the chains"
primary_text: "..."
cta: start_free_trial
landing_page_message: get_your_first_100_loyal_customers
hypothesis: contrast_hooks_increase_qualified_trial_signups
variable_tested: hook
control_id: cr_000
compliance_notes: avoid_unsubstantiated_revenue_claims
```

Outputs may support static ads, short-form video scripts, UGC concepts, landing-page message matching, lifecycle email, and organic-to-paid candidates.

## Experimentation Framework

Generating many ads is not the same as running an experiment. Each test should isolate one meaningful variable whenever practical.

Every experiment must define:

- Business question and hypothesis
- Control and variants
- Variable tested
- Audience and channel
- Primary and guardrail metrics
- Minimum evidence requirement
- Evaluation window
- Decision rule
- Result, confidence, learning, and next action

```yaml
experiment_id: exp_001
question: Which hook attracts restaurant owners more likely to launch their first campaign?
hypothesis: Contrast hooks (chain vs. indie) improve cost per activated owner vs. outcome hooks.
channel: meta
variable_tested: hook_type
control: cr_000
variants: [cr_001, cr_002]
primary_metric: cost_per_activated_owner
guardrail_metrics: [ctr, trial_signup_cvr, m1_retention]
minimum_clicks_per_variant: 300
evaluation_window_days: 14
decision_rule: recommend_only
```

## Measurement Framework

### Acquisition

- Spend, impressions, reach, and CPM
- Clicks, CTR, and CPC
- Landing-page views and signups
- CVR, CAC, and ROAS

### Activation

- Trial signup
- Onboarding completed
- First campaign launched (within 14 days)
- First customer acquired via Tablr
- Activated-owner rate and cost per activated owner (CPAO)

### Retention and Revenue

- Month 1, Month 3, and Month 6 subscription retention
- Trial-to-paid conversion rate
- Subscription starts and cohort MRR
- LTV, LTV:CAC, and payback period
- Net Revenue Retention (NRR)

### Creative Intelligence

- Performance by hook, angle, format, persona, and CTA
- Creative fatigue
- Video hold rate when available
- CTR-to-activation relationship
- Creative-level retention and LTV
- High-click, low-quality acquisition patterns

### Operational Efficiency

- Time from brief to approval
- Variants generated and approved
- Schema validation failure rate
- Cost per approved concept
- Recommendation acceptance rate
- Failed or duplicate API operations

## Data Model

The synthetic dataset must include advertising and first-party product events.

Recommended events:

- `ad_click`
- `landing_page_view`
- `trial_signup`
- `onboarding_completed`
- `profile_created`
- `campaign_launched`
- `first_customer_acquired`
- `subscription_started`
- `location_added`
- `revenue_generated`

Preserve these join keys where applicable:

- `user_id`, `anonymous_id`, `event_timestamp`
- `campaign_id`, `ad_set_id`, `creative_id`, `experiment_id`
- `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`

Document fields, formulas, attribution assumptions, time zones, currencies, null handling, and limitations in `data/data_dictionary.md`.

## Decision and Safety Model

A rule such as `Spend > $50 AND CVR < 1%` is not sufficient for a production decision. Recommendations should consider:

- Campaign objective and optimization event
- Attribution and conversion-delay windows
- Minimum impressions, clicks, and conversions
- Learning phase and exploration budget
- Audience size and saturation
- Baselines and cohort differences
- Statistical uncertainty
- Creative fatigue
- Blended versus platform-reported CAC
- Downstream activation and retention

| State           | Meaning                                      |
| --------------- | -------------------------------------------- |
| Observe         | Insufficient evidence; keep collecting data  |
| Revise          | Preserve the hypothesis but change execution |
| Hold            | Continue without increasing investment       |
| Scale           | Increase cautiously after review             |
| Pause candidate | Recommend pausing with evidence              |
| Approved action | A human authorized the platform change       |

Live mutations must be idempotent, logged, reversible where possible, and protected by explicit approval.

## Repository Structure

Folders and files are created incrementally by phase. The table below shows what exists after each phase completes.

| Phase                 | What gets created                                                                                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 (Strategy)          | `README.md`, `docs/PROJECT_BRIEF.md`, `docs/PHASES.md`, `docs/ARCHITECTURE.md`, `docs/AGENTS.md`                                                                     |
| 1 (Synthetic data)    | `scripts/generate_synthetic_data.py`, `data/synthetic/`, `data/data_dictionary.md`, `tests/data/`                                                                    |
| 2 (Creative strategy) | `data/config/`, `docs/message_map.md`, `docs/hook_taxonomy.md`, `docs/creative_testing_matrix.md`, `docs/creative_qc_checklist.md`, `docs/examples/creative_briefs/` |
| 3 (AI generation)     | `docs/prompts/`, `docs/evals/`, `tests/unit/test_creative_generator.py`                                                                                              |
| 4 (Experiments)       | `data/config/experiments.yaml`, `docs/experiment_playbook.md`, `docs/experiment_readout.md`                                                                          |
| 5 (Analytics)         | `scripts/sql/`, `docs/notebooks/01_acquisition_analysis.ipynb`, `docs/reports/`                                                                                      |
| 6 (Retention / LTV)   | `docs/notebooks/02_retention_ltv.ipynb`, `docs/examples/budget_recommendation.json`                                                                                  |
| 7 (Decision agent)    | `docs/prompts/performance_diagnosis.md`                                                                                                                              |
| 8 (Orchestration)     | `scripts/run_pipeline.py`                                                                                                                                            |
| 9 (Dashboard / Demo)  | `app/`, `docs/CASE_STUDY.md`, `docs/DEMO.md`                                                                                                                         |

```text
├── README.md                          # start here
│
├── process/                           # project story (human-readable)
│   ├── 00_overview.md
│   ├── 01_data_foundation.md          # Phase 1
│   ├── 02_creative_strategy.md        # Phase 2
│   ├── 03_ai_creative_generation.md   # Phase 3
│   ├── 04_experiments.md              # Phase 4
│   ├── 05_acquisition_analytics.md    # Phase 5
│   ├── 06_retention_ltv.md            # Phase 6
│   └── 07_decision_agent.md           # Phase 7
│
├── docs/                              # all reference documents
│   ├── PHASES.md
│   ├── PROJECT_BRIEF.md
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md
│   ├── CASE_STUDY.md                  # Phase 9
│   ├── DEMO.md                        # Phase 9
│   ├── message_map.md
│   ├── hook_taxonomy.md
│   ├── creative_testing_matrix.md
│   ├── creative_qc_checklist.md
│   ├── experiment_playbook.md
│   ├── experiment_readout.md
│   ├── evals/
│   ├── reports/
│   ├── examples/                      # creative briefs, sample outputs
│   │   ├── creative_briefs/
│   │   ├── channel_recommendations.json
│   │   └── budget_recommendation.json
│   ├── notebooks/                     # analysis notebooks
│   │   ├── 01_acquisition_analysis.ipynb
│   │   └── 02_retention_ltv.ipynb
│   └── prompts/                       # LLM prompt templates
│
├── app/                               # Streamlit dashboard (Phase 9)
├── data/
│   ├── config/                        # YAML configs (brand, channels, personas)
│   ├── synthetic/                     # synthetic dataset
│   └── data_dictionary.md
├── scripts/
│   ├── generate_synthetic_data.py
│   └── sql/                           # DuckDB analytical queries
└── tests/                             # unit, data, integration tests
```

## Recommended Build Curriculum

Do not begin with live marketing APIs. Build an end-to-end local system first, then replace mock components selectively.

| Phase | Focus                         | Required evidence                       |
| ----- | ----------------------------- | --------------------------------------- |
| 0     | Business problem and KPI tree | Brief, funnel, metric definitions       |
| 1     | Synthetic data and baseline   | Dataset, SQL/Pandas analysis, report    |
| 2     | Persona and creative strategy | Research, message map, briefs           |
| 3     | Structured AI generation      | Validated outputs and prompt tests      |
| 4     | Experiment registry           | Controls, variants, decision rules      |
| 5     | Performance triage            | Explainable recommendations             |
| 6     | Retention and LTV             | Cohort and acquisition-quality analysis |
| 7     | Platform connectors           | Mock first; draft mode optional         |
| 8     | Agentic workflow              | Review gates, audit and cost controls   |
| 9     | Portfolio packaging           | Dashboard, demo, case study, deck       |

Each phase should have acceptance criteria in `docs/PHASES.md`.

## AI Agent Working Rules

The complete coding-agent instructions belong in `docs/AGENTS.md`. At minimum, the agent must:

- Read the brief, architecture, and relevant module before editing.
- Default to mock data, dry-run, and recommendation-only behavior.
- Never expose credentials or commit `.env`.
- Never publish ads, change budgets, or pause campaigns without approval.
- Never present synthetic outcomes as real results.
- Add or update tests for material behavior changes.
- Validate LLM outputs before downstream use.
- Record significant decisions in `DECISIONS.md`.
- Update documentation when behavior changes.
- Report what was tested, what remains simulated, and known limitations.

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Optional Anthropic API key
- Marketing-platform credentials only for authorized advanced connectors

The local simulation must run without Meta or TikTok credentials.

### Installation

```bash
git clone https://github.com/your-username/ai-growth-operations-agent.git
cd ai-growth-operations-agent
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

```env
APP_ENV=development
DRY_RUN=true
RECOMMEND_ONLY=true
ALLOW_LIVE_MUTATIONS=false

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=your-supported-model-id

META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=
TIKTOK_ACCESS_TOKEN=
TIKTOK_ADVERTISER_ID=
```

Do not commit `.env` or real customer data.

### Run the Local Demo

```bash
python scripts/generate_synthetic_data.py
python scripts/run_pipeline.py generate --dry-run
python scripts/run_pipeline.py analyze
python scripts/run_pipeline.py triage --recommend-only
python scripts/run_pipeline.py report --weekly
```

Advanced commands may include:

```bash
python scripts/run_pipeline.py publish --platform meta --draft-only
python scripts/run_pipeline.py approve --action-id ACTION_ID
```

Advanced commands should remain unavailable until safety controls and integration tests pass.

## Testing and Quality Gates

Before a phase is complete, verify:

- Unit tests pass.
- Pydantic validates all structured outputs.
- Mock connector contract tests pass.
- Duplicate operations are prevented.
- Missing and delayed conversion data are handled.
- Formulas match the data dictionary.
- Simulation labels appear in all reports.
- LLM outputs are checked for unsupported claims.
- Logs contain no credentials or personal data.
- README commands match actual behavior.

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

## Required Demo Scenarios

1. **Creative strategy:** Generate three strategically distinct concepts for one persona and objective.
2. **Controlled experiment:** Register a control and variants that isolate one variable.
3. **Acquisition quality:** Show why the highest-CTR creative may not be best after activation and retention.
4. **Weekly growth review:** Produce evidence-based scale, hold, revise, or pause recommendations and define the next tests.

## Portfolio Deliverables

- Working local demo
- Architecture diagram
- Synthetic dataset and data dictionary
- Creative strategy and message map
- Briefs and generated variants
- Experiment registry
- Acquisition and retention dashboard
- Budget-allocation simulation
- Weekly growth review
- Test suite and CI workflow
- Three-to-five-minute demo video
- Interview-ready case study

## Case Study Structure

Use `docs/CASE_STUDY.md` to explain:

1. Business problem
2. Customer and growth hypothesis
3. Measurement strategy
4. Creative and experiment design
5. System architecture
6. Key simulated findings
7. Decision recommendations
8. Limitations and risks
9. What real data would validate
10. Next experiment

Label simulated metrics clearly. The quality of reasoning matters more than manufacturing impressive results.

## Evaluation Rubric

| Area                 | Weight | Strong evidence                                |
| -------------------- | -----: | ---------------------------------------------- |
| Growth strategy      |    15% | Clear funnel, personas, hypotheses, KPI tree   |
| Creative strategy    |    20% | Distinct concepts and actionable briefs        |
| Analytics            |    20% | Correct metrics, cohorts, retention, LTV       |
| Experimentation      |    15% | Sound controls and decision criteria           |
| AI system design     |    10% | Validation, evaluation, retries, cost controls |
| Engineering quality  |    10% | Modular code, tests, CI, documentation         |
| Safety and integrity |    10% | Approval gates, audit, honest labeling         |

## Operational Considerations

A production-oriented extension should address:

- Rate limits and exponential backoff
- Credential rotation and token expiration
- Idempotency and duplicate prevention
- Partial failures and retry policy
- Structured logs and audit history
- Model and API version changes
- LLM cost limits
- Data privacy and retention
- Attribution uncertainty
- Rollback and incident response
- Advertising-platform policies

## Limitations

- Synthetic behavior cannot prove real market response.
- Platform-reported conversions may be incomplete or biased.
- Retention and LTV require first-party data and sufficient time.
- Small samples produce unstable creative rankings.
- LLMs can generate plausible but unsupported claims.
- APIs, permissions, schemas, and models change over time.
- Recommendations still require business context and human judgment.

## Responsible Portfolio Presentation

Recommended wording:

> I built a portfolio simulation of an AI-assisted growth operations system for a B2B SaaS restaurant platform (Tablr). It connects performance creative and paid acquisition to trial activation, subscription retention, and LTV — with human approval required for any campaign action.

Do not claim autonomous management of a real ad budget unless supported by genuine, verifiable experience.

## Roadmap

- [x] Define the business brief, funnel, and KPI tree (Phase 0)
- [x] Build synthetic acquisition and product-event data (Phase 1)
- [x] Implement validated creative briefs and variants (Phase 2)
- [x] Structured AI creative generation with validation (Phase 3)
- [x] Add experiment tracking and UTM governance (Phase 4)
- [x] Build acquisition and creative performance analytics (Phase 5)
- [x] Build activation, retention, LTV, and budget analysis (Phase 6)
- [x] Add explainable triage recommendations (Phase 7)
- [x] Create Creative Intelligence Dashboard and case study (Phase 9)
- [ ] Add mock connector contract tests and orchestration (Phase 8)
- [ ] Add optional authorized draft-mode connectors (Phase 8B)
- [ ] Publish demo video and interview presentation

## License

MIT License. See `LICENSE` for details.
