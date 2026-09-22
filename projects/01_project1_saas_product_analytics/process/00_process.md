# Case Study Process

## Target Roles

This project is designed to support interviews for:
- **Tavus** — Growth Marketer (B2B SaaS, PLG, developer activation, lifecycle analytics)
- **Meta** — Product Growth Analyst (SQL, experimentation, user behavior, multivariate testing)
- **Data Analyst III / Data Analyst** — SaaS customer lifecycle, funnel/cohort/retention, root cause analysis

## Product Question

Which early product behaviors help B2B SaaS accounts activate, convert to paid, and retain long enough to create durable recurring revenue? And when key metrics move, how do we distinguish a real product problem from a population mix shift?

## Workflow

```text
Define product question
  → Generate synthetic lifecycle data (5 tables, 2,500 accounts)
  → Build account-level metrics (activation, retention, revenue, churn risk)
  → Write BigQuery SQL marts (funnel, activation, cohort, experiment, revenue, behavior, root cause)
  → Analyze A/B and multivariate experiment results
  → Root cause decomposition (rate effect vs. mix effect)
  → Build stakeholder dashboard (Streamlit, 7 pages)
  → Recommend rollout with measurement plan
```

## Analyst Deliverables

| Deliverable | File | Purpose |
|---|---|---|
| Synthetic dataset | `scripts/generate_synthetic_data.py` | Reproducible lifecycle data (seed=42) |
| BigQuery SQL marts | `sql/marts/*.sql` (8 files) | Interview SQL practice; all analytical domains |
| SQL practice guide | `process/06_sql_practice.md` | Business context + queries + interview Q&A |
| Metric definitions | `process/02_lifecycle_metrics.md` | CAC, LTV, NRR, expansion, root cause |
| Experiment framework | `process/03_experiment_readout.md` | A/B + multivariate; Bonferroni correction |
| Analysis findings | `process/05_analysis_findings.md` | Funnel findings + root cause case + recommendations |
| Dashboard | `app/` | Streamlit 7-page stakeholder app |

## SQL Coverage by Job Requirement

| JD Requirement | SQL File | Covered |
|---|---|---|
| Funnel, cohort, conversion, retention analysis | `mart_funnel.sql`, `mart_cohort_retention.sql` | ✅ |
| Root-cause analysis (why metrics move) | `mart_root_cause.sql` | ✅ |
| Experiment design and analysis | `mart_experiment.sql` | ✅ |
| Multivariate testing (Meta) | `mart_multivariate.sql` | ✅ |
| Advanced SQL (window functions, CTEs) | All marts | ✅ |
| CAC, LTV, payback period (Tavus) | `mart_revenue.sql` | ✅ |
| Expansion MRR, NRR | `mart_revenue.sql`, `mart_cohort_retention.sql` | ✅ |
| User behavior & engagement depth | `mart_user_behavior.sql` | ✅ |
| Growth recommendations & opportunity sizing | `mart_root_cause.sql` Domain 7 | ✅ |

## Interview Positioning

**Tavus angle**: "I built an end-to-end analytics system for a B2B SaaS developer platform — modeled after Tavus's API-first environment. I measured developer activation (integration_connected as the aha moment), free-to-paid conversion, expansion MRR, and built a lifecycle experiment to improve onboarding. I can walk through CAC/LTV by channel and opportunity sizing for each segment."

**Meta angle**: "I designed and analyzed a multivariate onboarding experiment with Bonferroni correction for multiple comparisons, ran HTE analysis to identify segment-level treatment effects, and built a root cause decomposition framework to distinguish rate-driven metric changes from population mix shifts. Every analysis connects back to a product decision."

**Data Analyst III angle**: "I covered the full SaaS customer lifecycle — acquisition, activation, retention, revenue, and churn — with advanced SQL across 8 BigQuery marts including window functions, maturity-gated cohort retention, and weekly metric decomposition."
