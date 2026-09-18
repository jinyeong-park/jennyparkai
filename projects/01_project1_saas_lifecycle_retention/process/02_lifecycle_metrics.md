# Lifecycle Metrics

## Account Lifecycle

```text
Signup -> Workspace Created -> Activated -> Trial Started -> Paid Customer -> Retained 30/60/90 Days
```

The dashboard rolls user events and subscription records to one account-level record. This allows product, growth, and customer-success stakeholders to compare lifecycle outcomes by company size, acquisition source, plan, cohort, and onboarding variant.

## Activation Definition

An account is activated when it creates a workspace and completes at least one qualifying key action within seven days of signup:

- `teammate_invited`
- `integration_connected`
- `project_created`

Workspace creation alone is an onboarding milestone, not activation. The distinction prevents the funnel from treating a partially configured account as one that has reached product value.

## Revenue And Retention

The overview reports `Indexed Active MRR` using month-end active-MRR snapshots indexed to the first observed month. Current paid customers, current MRR, and current ARPA exclude churned and trial-only accounts while preserving ever-paid conversion as a separate historical fact.

Paid retention uses explicit `eligible_30d`, `eligible_60d`, and `eligible_90d` flags. Every retention rate filters its denominator to organizations whose paid-conversion date has reached the selected horizon at the shared observation date. The Revenue detail page reports `Modeled NRR (no expansion events)` with the same maturity rule; expansion and contraction are unavailable, so the output remains a retained-MRR proxy rather than production NRR.

## Churn Prioritization

The churn-risk score is a transparent rules-based prioritization tool. It combines subscription state, 7-day activation, eligible 60-day retention, and days since the last product event. Accounts that have not reached 60 days receive no failed-retention penalty, and MRR exposure uses current MRR only. It is not a predictive churn model and should be validated against observed churn outcomes before operational use.
