# Phase 4: Mart Models

> **Purpose:** Expose intermediate model outputs as clean, dashboard-ready analytical tables.
> Marts are the models that analysts, BI tools, and Streamlit dashboards query directly.

---

## Mart Layer Design Principles

Mart models (`dim_*` and `fct_*`) follow the dimensional modeling convention:

- **`dim_*` (Dimensions):** Descriptive attributes about an entity. Used for filtering and grouping. Updated slowly. One row per entity.
- **`fct_*` (Facts):** Measurable business events or snapshots. Used for aggregation. Can have many rows per entity over time.

```
dim_account          → "What do we know about this account?"
fct_pipeline         → "What are all the open deals right now?"
fct_bookings         → "What revenue did we close and how much of it was collected?"
fct_revenue          → "How much billing did we generate each month?"
fct_customer_lifecycle → "What is each account's complete end-to-end journey?"
```

All five marts are **materialized as tables** (`+materialized: table`), meaning dbt writes the full result to the database on each run. This makes dashboard queries fast since they hit a pre-computed table, not a view that re-runs the joins on each query.

---

## `dim_account` — Master Account Dimension

**Grain:** One row per `account_id`

**Source:** `int_customer_identity_map` + `stg_salesforce_accounts`

**Key purpose:** Every `fct_*` model joins to `dim_account` on `account_id` to get segment, industry, region, and the pre-computed `lifecycle_tier`.

### `lifecycle_tier` — The Executive Segmentation Column

```sql
CASE
    WHEN is_churned                              THEN 'Churned'
    WHEN account_status = 'Customer'
         AND is_in_billing                       THEN 'Active Customer'
    WHEN account_status = 'Customer'             THEN 'Customer - No Billing'
    WHEN total_bookings_usd > 0                  THEN 'Closed-Won Prospect'
    WHEN opp_count > 0                           THEN 'In Pipeline'
    WHEN max_lead_stage IN ('SQL', 'MQL')        THEN 'Marketing Qualified'
    WHEN lead_count > 0                          THEN 'Lead'
    ELSE 'Account Only'
END AS lifecycle_tier
```

This single column allows an exec dashboard to slice the entire account base by business stage without joining to multiple tables. It is computed once in `dim_account` and reused everywhere.

**Used by:** All `fct_*` models, all dashboard filters

---

## `fct_pipeline` — Open Pipeline Snapshot

**Grain:** One row per open opportunity

**Source:** `stg_salesforce_opportunities` + `dim_account`

**Materialized as:** Table (point-in-time snapshot as of each dbt run)

### Risk Classification

```sql
CASE
    WHEN has_repeated_slip AND is_past_due  THEN 'High Risk'
    WHEN is_past_due OR is_stale            THEN 'Medium Risk'
    ELSE 'On Track'
END AS pipeline_risk
```

- **High Risk:** Past due AND the close date has already slipped multiple times — highest probability of not closing
- **Medium Risk:** Either past due OR stale — needs attention
- **On Track:** No risk signals

### Weighted Pipeline

```sql
-- Stage-based win rate × amount
CASE opportunity_stage
    WHEN 'Prospecting'   THEN 0.05
    WHEN 'Qualification' THEN 0.15
    WHEN 'Proposal'      THEN 0.35
    WHEN 'Negotiation'   THEN 0.65
    ELSE 0.10
END AS stage_win_rate,

ROUND(amount * stage_win_rate, 2) AS weighted_pipeline_amount
```

The difference between `pipeline_amount` (raw) and `weighted_pipeline_amount` is the key input to the revenue forecast. A pipeline with a lot of early-stage deals will have a large raw number but a small weighted number.

**Key metric this enables:**
```
Pipeline Coverage Ratio = Total Open Pipeline / Quarterly Revenue Target
Weighted Coverage Ratio = Weighted Pipeline / Quarterly Revenue Target
```

A VP of Sales wants the weighted coverage ratio to be at least 3× — meaning 3× the target in weighted pipeline to reliably hit the number.

**Used by:** Pipeline dashboard page, weekly pipeline reviews

---

## `fct_bookings` — Revenue Chain Reconciliation

**Grain:** One row per closed-won opportunity

**Source:** `int_revenue_lifecycle` + `dim_account`

**Key purpose:** The "revenue reconciliation" model. Shows every Closed-Won deal alongside its contract value, billed amount, and collected cash — plus the three gap columns.

### Revenue Chain at a Glance

```
For each won opportunity:

  crm_booking_amount     = $50,000  (what sales recorded)
  contract_value         = $47,500  (what legal signed — 5% discount)
  total_billed_usd       = $47,500  (billing matches contract)
  total_collected_usd    = $39,583  (10/12 months paid so far)

  booking_to_contract_gap  = $2,500   → discount given at signing
  contract_to_billing_gap  = $0       → no billing gap
  billing_to_collected_gap = $7,917   → 2 months of invoices still outstanding
  cash_collection_rate     = 79.2%    → expected to reach 100% as invoices clear
```

### `discount_tier` Classification

```sql
-- Expressed as % of booking amount
WHEN gap / crm_booking_amount > 0.15 THEN 'Heavy Discount (>15%)'
WHEN gap / crm_booking_amount > 0.05 THEN 'Moderate Discount (5-15%)'
WHEN gap / crm_booking_amount > 0    THEN 'Minor Discount (<5%)'
WHEN gap < 0                         THEN 'Contract Exceeds Booking'  -- rare, usually data error
ELSE 'No Discount'
```

**Used by:** Revenue reconciliation analysis, finance reporting

---

## `fct_revenue` — Monthly Billing Fact

**Grain:** One row per invoice

**Source:** `stg_billing` + `dim_account` + `stg_contracts`

**Key purpose:** The lowest-grain revenue table. Enables MRR trending, NRR calculation, and payment failure analysis at monthly intervals.

### NRR Category

Each invoice row is tagged with its account's NRR classification:

```sql
CASE
    WHEN is_churned                        THEN 'Churned'
    WHEN has_expansion AND NOT is_churned  THEN 'Expansion'
    ELSE 'Retained'
END AS nrr_category
```

**Why at invoice grain:** To compute rolling 12-month NRR, you need monthly revenue by NRR category. Having it at the invoice level lets you aggregate to any month-year period without pre-computation.

**NRR formula from this table:**
```sql
SELECT
    billing_year,
    billing_month,
    SUM(CASE WHEN nrr_category = 'Retained'  THEN collected_amount_usd END) AS retained_rev,
    SUM(CASE WHEN nrr_category = 'Expansion' THEN collected_amount_usd END) AS expansion_rev,
    SUM(CASE WHEN nrr_category = 'Churned'   THEN collected_amount_usd END) AS churned_rev
FROM fct_revenue
GROUP BY 1, 2
-- Then calculate NRR = (prior_retained + expansion) / prior_retained
```

**Used by:** MRR dashboard, NRR calculation, payment failure reporting

---

## `fct_customer_lifecycle` — Full B2B Journey

**Grain:** One row per `account_id`

**Source:** `dim_account` + `int_gtm_funnel` + `int_revenue_lifecycle` (aggregated)

**Key purpose:** The single model to answer "what happened to this account end-to-end?" Brings together every stage from first lead through retention status into one row.

### `lifecycle_completeness` — Sortable Stage Ranking

```sql
CASE
    WHEN is_churned                              THEN '6 - Churned'
    WHEN has_expansion                           THEN '5 - Expansion'
    WHEN total_collected_usd > 0                 THEN '4 - Paying Customer'
    WHEN has_any_contract                        THEN '3 - Contracted'
    WHEN has_won_opportunity                     THEN '2 - Closed-Won'
    WHEN has_opportunity                         THEN '1 - In Pipeline'
    ELSE '0 - Pre-Pipeline'
END AS lifecycle_completeness
```

The numeric prefix makes this column sortable. A query like `ORDER BY lifecycle_completeness DESC` correctly places fully expanded customers at the top and unengaged accounts at the bottom.

### Key velocity metric: `lead_to_close_days`

```sql
(first_close_date - first_lead_date) AS lead_to_close_days
```

This is the end-to-end B2B sales cycle: from the first marketing touch to the first Closed-Won. Segmenting this by `segment` reveals whether Enterprise deals actually take longer than SMB (they almost always do, but by how much?).

**Used by:** Customer lifecycle dashboard, retention analysis, CS outreach prioritization

---

## How the Five Models Relate

```
                        dim_account
                        (master attrs)
                             │
            ┌────────────────┼────────────────────────┐
            │                │                        │
       fct_pipeline    fct_bookings             fct_revenue
       (open deals)    (won deals,              (monthly
                        rev chain)               invoices)
                             │
                   fct_customer_lifecycle
                   (full journey per account)
```

`fct_customer_lifecycle` is the only mart that consumes other intermediate models directly. All others go staging → dim_account → join at the mart level.

---

## Materialization Summary

| Model | Materialization | Reason |
|-------|-----------------|--------|
| `dim_account` | table | Joined by every other mart — needs to be fast |
| `fct_pipeline` | table | Point-in-time snapshot; refreshed on each run |
| `fct_bookings` | table | Historical data; stable once deals are closed |
| `fct_revenue` | table | High-query frequency for MRR reporting |
| `fct_customer_lifecycle` | table | Multi-source join; expensive to re-compute on every query |

Staging and intermediate models are materialized as **views** — they run on-demand when the mart tables are refreshed, not stored separately.

---

_Next: [05_analysis_findings.md](./05_analysis_findings.md) — Key analytical findings from querying these mart models._
