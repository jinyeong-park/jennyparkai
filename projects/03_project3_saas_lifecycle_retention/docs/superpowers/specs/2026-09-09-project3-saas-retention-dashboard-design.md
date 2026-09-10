# Project 3 SaaS Retention Dashboard Design

## Objective

Build Project 3 as an end-to-end product analytics portfolio project for a product-led B2B SaaS lifecycle. The first usable milestone will include synthetic lifecycle data, reusable analysis utilities, and a Streamlit dashboard modeled after the provided `03_product-led-retention-analytics.png` reference.

The dashboard should help product, growth, and business stakeholders answer which early product behaviors drive activation, paid conversion, retention, churn risk, and revenue impact.

## Recommended Approach

Use a local Streamlit app as the primary interactive artifact, while keeping Hex-oriented documentation for interview positioning. This gives the project a runnable dashboard like Project 2 and still supports the README's stakeholder-facing Hex narrative.

The dashboard will use a clean operations-style interface with:

- A left navigation sidebar for lifecycle sections.
- Executive KPI cards across the top.
- A first-screen overview with funnel, activation, cohort retention, experiment, revenue retention, and churn risk panels.
- Detail pages for users, activation, retention, revenue, experiments, and churn risk.

## Scope

### Included In The First Implementation Plan

- Create the planned project structure under `03_project3_saas_lifecyle_retention`.
- Generate deterministic synthetic SaaS lifecycle data:
  - `organizations`
  - `users`
  - `event_logs`
  - `subscriptions`
  - `experiment_assignments`
- Add analysis logic for lifecycle funnel, activation metrics, cohort retention, A/B experiment performance, NRR, and churn risk segmentation.
- Build a Streamlit app with an overview page visually inspired by the reference image.
- Add process and metric documentation so the project reads like a complete analyst case study.
- Add focused verification checks for data generation and app import/runtime sanity.

### Deferred

- Public Streamlit deployment.
- Full dbt project.
- Live Hex export.
- Predictive churn model beyond rules-based health/risk scoring.

## Data Model

The synthetic data will represent organizations as the primary business unit. Users and events roll up to organizations, subscriptions connect lifecycle behavior to revenue, and experiment assignments enable onboarding treatment analysis.

Activation will be defined as an organization completing enough value-driving actions within seven days of signup. The first implementation will treat workspace creation plus either teammate invite, integration connection, or project creation as the core activation signal.

Retention will be measured from product activity after signup or paid conversion, with 30/60/90-day account-level retention flags. Churn risk will combine recency, activation, feature adoption, subscription state, and recent usage decline.

## App Structure

The app will follow the Project 2 Streamlit convention:

- `app/Summary.py`
- `app/pages/1_Users.py`
- `app/pages/2_Activation.py`
- `app/pages/3_Retention.py`
- `app/pages/4_Revenue.py`
- `app/pages/5_Experiments.py`
- `app/pages/6_Churn_Risk.py`
- `app/utils/data_loader.py`
- `app/utils/theme.py`

The first page will resemble the supplied dashboard reference:

- KPI cards: total signups, activated users, paid customers, average revenue per account.
- Product lifecycle funnel.
- Activation metric tiles.
- Cohort retention line chart.
- A/B experiment performance table.
- Net revenue retention trend.
- Churn risk donut and segment summary.

## Analysis Outputs

The project will produce both dashboard-ready outputs and readable documentation:

- Lifecycle funnel metrics by segment and acquisition source.
- Experiment readout with control/treatment lift and segment-level differences.
- Retention cohorts by signup month, activation status, company size, source, and plan.
- Business impact estimate translating activation lift into incremental MRR.
- Churn risk account list and segment distribution.

## Testing And Verification

Verification will focus on whether the generated data and dashboard can be trusted enough for portfolio use:

- Run the synthetic data generator and confirm expected CSV outputs.
- Check generated tables have non-empty data and required columns.
- Run lightweight Python assertions for core metric calculations where practical.
- Start the Streamlit app locally and confirm it launches without import errors.

## Implementation Decision

The dashboard will be implemented as Streamlit first, with Hex documentation retained. The visual styling should be similar to the provided reference image, but adjusted to fit Streamlit's layout constraints and the repository's existing Project 2 conventions.
