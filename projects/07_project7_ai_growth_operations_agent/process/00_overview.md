# AI Growth Operations Agent — Project Overview

## Business Question

How can a growth team distinguish cheap acquisition from valuable acquisition, and use AI to increase creative velocity without losing strategic accountability?

## Simulated Company

**Tablr** — an AI-powered growth OS for independent restaurant owners. Freemium B2B SaaS. Restaurant owners sign up for a free trial and are considered activated when they launch a marketing campaign within 14 days.

## Workflow

```text
Define metrics and strategy (Phase 0)
→ Generate synthetic data (Phase 1)
→ Build creative strategy and briefs (Phase 2)
→ AI creative generation with validation (Phase 3)
→ Experiment registry and measurement engine (Phase 4)
→ Paid acquisition analytics (Phase 5)
→ Retention, LTV, and budget allocation (Phase 6)
→ Decision and recommendation agent (Phase 7)
→ Orchestration and governance (Phase 8)
→ Dashboard, case study, and demo (Phase 9)
```

## North Star Metric

**MAR** — Monthly Active Restaurants (restaurants that launched at least one campaign in the month)

## Primary Acquisition Metric

**CPAO** — Cost Per Activated Owner (spend ÷ owners who launched a campaign within 14 days of trial signup)

Why CPAO over trial CAC: trial CAC can be gamed with broad targeting or low-quality clicks. CPAO connects spend to a behavioral signal that predicts subscription and retention.

## Key Analytical Patterns Built Into the Data

| Pattern | What it tests |
|---|---|
| High CTR, low activation | Whether the analyst looks past vanity metrics |
| META trial CAC 2nd → CPAO last | Whether channel ranking changes with better metric |
| Creative fatigue after early success | Whether creative refresh logic is in place |
| Missing attribution (7.6%) | Whether imperfect data is handled honestly |
| Immature M6 cohorts | Whether retention is reported with maturity flags |

## Deliverables

- Reproducible synthetic dataset (2,000 restaurant owner trials, 12 weeks)
- 16 strategic creative briefs across 5 personas and 4 channels
- AI creative generation pipeline (mock + Anthropic providers)
- Experiment registry with z-test measurement engine
- DuckDB analytics: channel scorecard, CPAO, retention, LTV:CAC
- Budget allocation simulator (RECOMMEND_ONLY)
- Streamlit dashboard (Phase 9)
- Case study HTML (Phase 9)

## Interview Positioning

This project demonstrates how a growth analyst connects paid media strategy, creative testing, product activation, retention economics, and AI tooling into one accountable system — with human approval gates throughout.
