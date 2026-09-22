# Lifecycle Metrics

## Account Lifecycle

```text
Signup → Workspace Created → Activated → Trial Started → Paid Customer → Retained 30/60/90 Days
                                                                               ↓
                                                                        Expansion (plan upgrade)
```

The dashboard rolls user events and subscription records to one account-level record. This allows product, growth, and customer-success stakeholders to compare lifecycle outcomes by company size, acquisition source, plan, cohort, and onboarding variant.

## Activation Definition

An account is activated when it creates a workspace and completes at least one qualifying key action within seven days of signup:

- `teammate_invited`
- `integration_connected` — primary developer activation signal (API/SDK working)
- `project_created` — primary creator activation signal (first output generated)

Workspace creation alone is an onboarding milestone, not activation. The distinction prevents the funnel from treating a partially configured account as one that has reached product value.

## Revenue, Retention, and Expansion

The overview reports `Indexed Active MRR` using month-end active-MRR snapshots indexed to the first observed month. Current paid customers, current MRR, and current ARPA exclude churned and trial-only accounts while preserving ever-paid conversion as a separate historical fact.

Paid retention uses explicit `eligible_30d`, `eligible_60d`, and `eligible_90d` flags. Every retention rate filters its denominator to organizations whose paid-conversion date has reached the selected horizon at the shared observation date.

**NRR (Net Revenue Retention)** is computed as:

```
NRR = (Beginning MRR + Expansion MRR - Contraction MRR - Churn MRR) / Beginning MRR
```

The dashboard reports `Modeled NRR` as a retained-MRR proxy. In the SQL layer (`mart_revenue.sql`), expansion MRR is calculated from accounts with sequential subscription records where `mrr_amount` increases — representing plan upgrades. Full production NRR requires a dedicated `subscription_changes` table with event-level upgrade/downgrade records.

**Revenue metric definitions:**

| Metric | Definition | SQL Source |
|---|---|---|
| MRR | Sum of active subscription `mrr_amount` at month-end snapshot | `mart_revenue.sql` |
| ARPA | MRR / active paid accounts | `mart_revenue.sql` |
| Expansion MRR | MRR increase from existing accounts (plan upgrades) | `mart_revenue.sql` |
| Churn MRR | MRR lost from accounts that cancelled | `mart_revenue.sql` |
| NRR proxy | Retained MRR / beginning MRR per 60-day cohort | `mart_cohort_retention.sql` |
| Monthly churn | Churn events / account-months of exposure (active subs count as censored exposure) | `mart_revenue.sql`, `channel_ltv()` |
| LTV proxy | ARPA / monthly churn, also reported capped to a fixed horizon (default 24 months) | `mart_revenue.sql`, `channel_ltv()` |
| Max affordable CAC | Capped LTV / target LTV:CAC ratio (a budget ceiling; there is no spend data) | `channel_ltv()` |

## CAC and LTV

There is no acquisition-spend data, so **CAC and LTV:CAC cannot be computed** and this project does not pretend to. An earlier version used "time-to-paid x ARPA" as a relative CAC proxy; that is not a cost, and on this data it carries no signal either: median days from signup to first paid subscription is 19-20 for every channel.

What the data does support is the LTV side, and the *inverse* question: given a target ratio (say 3:1), what is the most that could be spent per account? That is `max_cac` = capped LTV / target ratio.

Two definitional traps, both fixed:
- **Churn is events per account-month of exposure, not the cumulative churned share.** `COUNTIF(status = 'churned') / COUNT(DISTINCT org_id)` is ~21% here because it covers the whole observation window; the monthly rate is ~2.7%. Using the former as "monthly churn" understates LTV about 8x.
- **`ARPA / churn` implies a ~35-40 month lifetime, but no subscription has been observed longer than ~15 months.** Report a capped LTV alongside it, and don't read the uncapped figure as an observation.

Churn is not actually constant: on this data every churn event falls in months 2-4 after an account starts paying and none after (`paid_survival_curve()`), so the constant-churn LTV understates 24-month LTV by ~9%.

Intervals come from resampling paid accounts (ARPA and churn together). On this data every channel's 24-month LTV interval shares a common range, so a channel ranking should not drive budget allocation.

## Root Cause Analysis Framework

When a metric moves period-over-period, the change decomposes into three components per segment:

- **Rate effect** `(cur_rate - prior_rate) x prior_mix`: segment-level activation rates changed (product/UX regression or improvement)
- **Mix effect** `(cur_mix - prior_mix) x (prior_rate - prior_overall_rate)`: the population mix shifted (more Enterprise this period = lower overall rate, even if individual rates are unchanged)
  Centered on the prior overall rate so each segment's sign is interpretable: a low-activating channel that grows its share is negative. (Uncentered `Δmix x prior_rate` has the same total but shows that same channel as a positive contributor.)
- **Interaction effect** `(cur_mix - prior_mix) x (cur_rate - prior_rate)`: segments where both moved at once. Dropping it (the common two-term form) makes the total only approximately reconcile to the observed change; keeping it makes the three sum exactly.

`mart_root_cause.sql` and `mix_rate_decomposition()` in `app/utils/metrics.py` implement this. The supplemental funnel query identifies which specific step broke (workspace → integration drop vs. integration → project drop). A decomposition attributes a change; it doesn't prove the change was real — test it first, and note that the largest of many period-over-period moves is a multiple-comparisons pick.

## Churn Prioritization

The churn-risk score is a transparent rules-based prioritization tool. It combines subscription state, 7-day activation, eligible 60-day retention, and days since the last product event. Accounts that have not reached 60 days receive no failed-retention penalty, and MRR exposure uses current MRR only. It is not a predictive churn model and should be validated against observed churn outcomes before operational use.
