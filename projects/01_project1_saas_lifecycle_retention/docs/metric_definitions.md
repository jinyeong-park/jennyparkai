# Metric Definitions

All core lifecycle metrics are calculated at the organization (account/workspace) grain unless noted otherwise. The source data is synthetic and deterministic.

| Metric | Numerator | Denominator | Grain | Caveat |
| --- | --- | --- | --- | --- |
| Signup | Organizations with a `created_at` date in the selected period | None; reported as a count | Organization | Represents an account-level signup/cohort, not every individual user signup. |
| Workspace creation rate | Organizations with a `workspace_created` event | Signup organizations | Organization | Workspace creation is an onboarding milestone, not activation. |
| Activation within 7 days | Organizations with `workspace_created` plus at least one of `teammate_invited`, `integration_connected`, or `project_created` within 7 days of signup | Signup organizations | Organization | Measures a defined early-value proxy; it does not prove long-term value. |
| Trial start rate | Organizations with a subscription record | Eligible signup organizations | Organization | In the synthetic model, a subscription record is used as the trial-start indicator; no separate trial event is available. |
| Ever-paid conversion rate | Organizations with a positive-MRR subscription record (`ever_paid`/legacy `paid_customer`) | Signup organizations, unless explicitly filtered to trial starters | Organization | This is a historical conversion fact and remains true after churn. |
| Current paid customers | Organizations with a positive-MRR subscription whose status is active at the shared observation date | Signup organizations, when displayed as a rate | Organization | Stored separately as `current_active_customer`; churned and trial-only organizations are excluded. |
| Retention at 30/60/90 days | Ever-paid organizations whose subscription remains active through the selected tenure horizon | Ever-paid organizations whose paid-conversion date is old enough to reach the horizon by the shared observation date | Organization | Excludes immature account-horizon observations. Signup-month charts group these paid-retention outcomes by acquisition cohort but keep paid conversion as the retention clock. |
| Modeled NRR | MRR retained through the selected horizon among mature subscriptions in a subscription-start cohort | Beginning MRR from subscriptions eligible for that cohort horizon | Subscription-start cohort | Immature subscription-horizon observations are omitted. No expansion or contraction events are modeled, so this is a retained-MRR proxy rather than production NRR. |
| Current MRR | Sum of positive MRR from subscriptions active at the shared observation date | None; reported as currency | Organization | `mrr_amount` preserves the latest historical subscription value; `current_mrr` is zero for churned, trial-only, and non-subscribed organizations. |
| Current ARPA | Current MRR | Number of current paid customers | Organization | Based on point-in-time synthetic MRR and not adjusted for discounts, usage, or period averages. |
| Churn risk | No single numerator; a 0-100 rules-based score from subscription state, activation, eligible 60-day retention, and activity recency | None | Organization | Immature accounts receive no failed-retention penalty. MRR at risk uses current MRR only. This remains a transparent prioritization heuristic, not a trained predictive model. |
| Experiment lift | Treatment metric rate minus control metric rate | Control metric rate for percent lift, or no denominator for percentage-point lift | Organization assignment | Primary dashboard lift is activation-rate difference in percentage points; causal interpretation assumes valid assignment and instrumentation. |

## Revenue Labeling

`Indexed Active MRR` is the overview trend: month-end active MRR snapshots indexed to the first observed month. `Modeled NRR (no expansion events)` appears only on the Revenue page, excludes immature horizon observations, and remains labeled as a synthetic retained-MRR proxy.

## Shared Observation Date

Activity recency, current subscription state, retention eligibility, active-MRR snapshots, and modeled NRR maturity all use the latest timestamp in the deterministic source tables. This prevents pages from drifting onto different as-of dates.
