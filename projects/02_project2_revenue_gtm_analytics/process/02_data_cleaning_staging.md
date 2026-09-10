# Phase 2: Data Cleaning — Staging Models

> **Core Principle:** Flag data quality issues; don't silently drop them.
> Downstream models decide what to include or exclude based on the flags.

---

## The Staging Layer Philosophy

In dbt, staging models (`stg_*`) are the first transformation layer. Their job is:

1. **Rename** columns to consistent, readable names
2. **Cast** data types (strings → dates, strings → booleans)
3. **Flag** data quality issues without dropping records
4. **Add** derived columns that are close to the source (not business logic)

What staging models do **not** do:
- Join multiple tables together (that is the intermediate layer's job)
- Apply business logic (that goes in marts)
- Filter out bad records (they are flagged, not dropped)

---

## The 5 Data Quality Issues in This Dataset

Found during the data exploration notebook (`01_data_exploration.ipynb`):

| # | Table | Issue | Count | Handling |
|---|-------|-------|-------|----------|
| 1 | `raw_salesforce_accounts` | Duplicate account_ids | ~12 accounts | `ROW_NUMBER()` dedup; `had_duplicate_in_source` flag |
| 2 | `raw_marketing_leads` | Leads with no account_id | 12 leads | `has_account = FALSE` flag; retained in staging |
| 3 | `raw_salesforce_opportunities` | Orphan opportunities (invalid account_id) | 9 opps | `is_orphan = TRUE` flag; excluded from joins |
| 4 | `raw_contracts` | Duplicate contract_ids with conflicting values | 4 IDs (8 rows) | `is_canonical_record` flag; highest value row selected |
| 5 | `raw_billing` | Multi-currency invoices | ~30% non-USD | FX normalization to USD using static rates |

---

## Staging Model Deep-Dives

### `stg_salesforce_accounts` — Deduplication

**Problem:** ~12 `account_id` values appear twice in the source, with slightly different names. This happens when sales reps create duplicate account records in Salesforce.

**Solution: `ROW_NUMBER()` window function**

```sql
WITH deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY account_created_at DESC  -- keep most recent
        ) AS row_num,
        COUNT(*) OVER (
            PARTITION BY account_id
        ) > 1 AS had_duplicate_in_source      -- audit flag
    FROM {{ ref('raw_salesforce_accounts') }}
)
SELECT * FROM deduped WHERE row_num = 1
```

**Why this matters:** If you don't deduplicate before joining, a single account appears in reports twice. Revenue numbers double-count. Conversion rates look artificially low.

**Why we keep the flag:** The `had_duplicate_in_source` column lets a data quality dashboard track how many duplicate accounts existed — useful for the Salesforce admin to go clean them up at the source.

---

### `stg_marketing_leads` — Unmatched Lead Flagging

**Problem:** 12 leads have a `NULL` `account_id`. They came through channels that did not capture the company name (e.g., an anonymous whitepaper download before the user identified themselves).

**Solution: Boolean presence flag**

```sql
SELECT
    lead_id,
    account_id,
    (account_id IS NOT NULL) AS has_account,  -- FALSE for the 12 unmatched leads
    ...
FROM {{ ref('raw_marketing_leads') }}
```

**What `lifecycle_stage_rank` adds:**

The raw `lifecycle_stage` is a string. Converting it to a numeric rank enables:
- `MAX(lifecycle_stage_rank)` to find the furthest stage per account
- Comparing stage progression across time periods

```sql
CASE lifecycle_stage
    WHEN 'Lead'      THEN 1
    WHEN 'MQL'       THEN 2
    WHEN 'SQL'       THEN 3
    WHEN 'Converted' THEN 4
    ELSE 0
END AS lifecycle_stage_rank
```

---

### `stg_salesforce_opportunities` — Pipeline Risk Signals

**Problem:** The raw table has `opportunity_stage` and `expected_close_date`, but no signals for whether a deal is overdue or has gone stale.

**Solution: Derived risk flags**

```sql
-- Is the deal past its expected close date?
(CURRENT_DATE > close_date AND is_open) AS is_past_due,

-- How many days since the rep last logged an activity?
(CURRENT_DATE - last_activity_at::DATE) AS days_since_last_activity,

-- Is the deal stale (no activity in 30 days)?
(days_since_last_activity > 30 AND is_open) AS is_stale,

-- Has the close date slipped multiple times?
(close_date_changes >= 2) AS has_repeated_slip,

-- Are orphan opps flagged?
(account_id LIKE 'ACC_ORPHAN_%') AS is_orphan
```

**Why orphans are flagged but not dropped:** The 9 orphan opportunities represent $X in pipeline value. Dropping them silently would make the pipeline report incorrect. Instead, they are flagged so:
- Pipeline reports can filter them out: `WHERE is_orphan = FALSE`
- A separate DQ alert can surface them to the RevOps team for cleanup

---

### `stg_contracts` — Duplicate Contract Resolution

**Problem:** 4 `contract_id` values appear twice. This happens when a contract is amended — some systems create a new record rather than updating the existing one.

**The complication:** The two records for the same `contract_id` often have **different values**. You cannot simply pick one arbitrarily — the choice affects revenue calculations.

**Solution: Canonical record selection**

```sql
WITH contract_dups AS (
    SELECT *,
        COUNT(*) OVER (PARTITION BY contract_id) AS duplicate_count,
        COUNT(*) OVER (PARTITION BY contract_id) > 1 AS has_duplicate_contract_id,
        ROW_NUMBER() OVER (
            PARTITION BY contract_id
            ORDER BY contract_value DESC  -- keep higher value (post-amendment is usually higher)
        ) AS dup_row_num
    FROM {{ ref('raw_contracts') }}
)
SELECT
    *,
    (dup_row_num = 1) AS is_canonical_record
FROM contract_dups
```

**How downstream models use this:**

```sql
-- In int_revenue_lifecycle and fct_bookings:
WHERE is_canonical_record = TRUE
-- This ensures each contract appears exactly once in revenue calculations
```

**Note on the choice:** Selecting the higher-value record is a reasonable default for amended contracts (amendments usually increase scope). In a real production system, you would validate this with the finance team.

---

### `stg_billing` — FX Normalization

**Problem:** Billing data contains invoices in USD, EUR, and GBP. Revenue reporting requires a single currency.

**Solution: Static FX rates → `billing_amount_usd`**

```sql
-- Step 1: Apply static FX rates
CASE currency
    WHEN 'USD' THEN 1.00
    WHEN 'EUR' THEN 1.08   -- approximate as of 2025
    WHEN 'GBP' THEN 1.27   -- approximate as of 2025
    ELSE 1.00
END AS fx_rate_to_usd,

ROUND(billing_amount * fx_rate_to_usd, 2) AS billing_amount_usd

-- Step 2: Preserve the original currency and rate for auditability
-- billing_amount (original) + currency + fx_rate_to_usd always in the table
```

**In production this would be:**

```sql
-- Join to a live FX rates dimension table keyed on billing_date
JOIN dim_fx_rates ON
    billing.billing_date = fx.rate_date
    AND billing.currency = fx.from_currency
    AND fx.to_currency = 'USD'
```

**Payment collectability flags:**

```sql
-- These three columns make filtering fast in downstream models
payment_status = 'Paid'    AS is_paid,
payment_status = 'Pending' AS is_pending,
payment_status = 'Failed'  AS is_failed,

-- And revenue broken down by collectability
CASE payment_status
    WHEN 'Paid'    THEN billing_amount_usd ELSE 0
END AS collected_amount_usd,

CASE payment_status
    WHEN 'Pending' THEN billing_amount_usd ELSE 0
END AS at_risk_amount_usd,

CASE payment_status
    WHEN 'Failed'  THEN billing_amount_usd ELSE 0
END AS failed_amount_usd
```

---

### `stg_customer_success` — Health Tier Bucketing

**Problem:** The raw `customer_health_score` is a continuous number (0–100). Most business questions are categorical: "How many accounts are at risk?"

**Solution: Health tier classification**

```sql
CASE
    WHEN customer_health_score >= 70 THEN 'Healthy'
    WHEN customer_health_score >= 35 THEN 'Needs Attention'
    WHEN customer_health_score >  0  THEN 'At Risk'
    ELSE 'Unknown'
END AS health_tier
```

**Note on thresholds:** The 70 / 35 thresholds are set to match the data generator's parameters. In a real deployment, these thresholds would be calibrated against historical churn data — e.g., "Accounts that churned had an average health score of 28 six months before churn."

---

## Staging Schema Tests

Every staging model has automated tests defined in `_staging__schema.yml`:

```yaml
- name: stg_salesforce_accounts
  columns:
    - name: account_id
      tests:
        - unique          # No duplicate account_ids after dedup
        - not_null
    - name: segment
      tests:
        - accepted_values:
            values: ['SMB', 'Mid-Market', 'Enterprise', 'Unknown']
```

Running `dbt test` after `dbt run` verifies:
- All primary keys are unique and non-null
- Categorical columns only contain expected values
- Dollar amounts are non-null

---

## What Goes Into Intermediate Models

Staging models give us clean, flag-enriched versions of each source table. The next step is joining them:

| Staging output | Feeds into |
|----------------|------------|
| `stg_salesforce_accounts` | `int_customer_identity_map` (spine), `int_gtm_funnel` |
| `stg_marketing_leads` | `int_customer_identity_map`, `int_gtm_funnel` |
| `stg_salesforce_opportunities` | `int_customer_identity_map`, `int_gtm_funnel`, `int_revenue_lifecycle` |
| `stg_contracts` | `int_revenue_lifecycle` |
| `stg_billing` | `int_customer_identity_map`, `int_revenue_lifecycle`, `fct_revenue` |
| `stg_customer_success` | `int_customer_identity_map`, `dim_account` |
| `stg_product_events` | (feeds future health score model — not yet in this project) |

---

_Next: [03_intermediate_models.md](./03_intermediate_models.md) — How the three intermediate models build the account identity map and revenue lifecycle chain._
