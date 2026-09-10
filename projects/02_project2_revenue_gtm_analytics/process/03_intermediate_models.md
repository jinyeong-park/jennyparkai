# Phase 3: Intermediate Models

> **Purpose:** Join cleaned staging tables into unified analytical views that represent
> real business objects — the account identity map, the GTM funnel, and the revenue lifecycle chain.

---

## Why Intermediate Models Exist

Staging models give us clean, type-cast versions of individual source tables.
But business questions require joining multiple sources:

> "How many of our accounts have a marketing lead AND an opportunity AND billing data?"

> "For a won deal, what was the gap between the CRM booking amount and the cash we actually collected?"

These require multi-table joins with careful handling of:
- Different naming conventions (`customer_id` in billing = `account_id` in CRM)
- Missing records (not every account has a CS health score)
- Duplicate records that would multiply rows on join (deduped contracts)

The intermediate layer solves these once, centrally. Downstream mart models can then trust the joins are correct.

---

## The Three Intermediate Models

```
stg_salesforce_accounts ─┐
stg_marketing_leads     ─┼──→ int_customer_identity_map  (one row per account: all 4 systems)
stg_billing             ─┤
stg_customer_success    ─┘

stg_salesforce_accounts ─┐
stg_marketing_leads     ─┼──→ int_gtm_funnel             (one row per account: lead → opp funnel)
stg_salesforce_opps     ─┘

stg_salesforce_opps     ─┐
stg_contracts           ─┼──→ int_revenue_lifecycle       (one row per won opp: booking → cash)
stg_billing             ─┘
```

---

## `int_customer_identity_map`

### What it does

Creates one row per `account_id` showing the account's presence across all four systems:

```
account_id | is_in_crm | is_in_marketing | is_in_billing | is_in_customer_success | systems_present
ACC_00001  |   TRUE    |      TRUE       |     TRUE      |          TRUE          |       4
ACC_00234  |   TRUE    |      FALSE      |     TRUE      |          FALSE         |       2
ACC_00456  |   TRUE    |      TRUE       |     FALSE     |          FALSE         |       2
```

### Why `systems_present` matters

A `systems_present = 1` account (CRM only) is a prospect with no marketing, billing, or CS engagement. A `systems_present = 4` account is a fully engaged customer. Segmenting by this number immediately reveals the coverage gaps in your data.

### The join structure

```sql
FROM accounts a                              -- CRM is the spine (all accounts start here)
LEFT JOIN leads_agg    l ON a.account_id = l.account_id   -- some accounts have no leads
LEFT JOIN opps_agg     o ON a.account_id = o.account_id   -- some accounts have no opps
LEFT JOIN billing_agg  b ON a.account_id = b.account_id   -- billing uses customer_id
LEFT JOIN cs_agg      cs ON a.account_id = cs.account_id  -- some accounts have no CS data
```

**Why `LEFT JOIN` everywhere:** Every account that exists in Salesforce should appear in the output, even if it has no billing record yet (a new prospect) or no CS record (hasn't onboarded). `INNER JOIN` would silently drop those accounts.

### Pre-aggregating before joining

Notice that leads, opps, and billing are each aggregated into account-level summaries before joining:

```sql
-- leads_agg: one row per account_id
SELECT account_id,
    COUNT(DISTINCT lead_id)   AS lead_count,
    MAX(lifecycle_stage_rank) AS max_lifecycle_rank,
    MIN(lead_created_date)    AS first_lead_date
FROM stg_marketing_leads
WHERE has_account = TRUE  -- exclude the 12 unmatched leads
GROUP BY account_id

-- Then LEFT JOIN this to accounts — safe, no row multiplication
```

**Why this pattern matters:** If you join leads to accounts without aggregating first, and an account has 5 leads, you get 5 rows for that account. Every metric you try to sum after that double-counts. Always aggregate to the join grain first.

---

## `int_gtm_funnel`

### What it does

Connects the Marketing funnel (leads) to the Sales funnel (opportunities) at the account level, enabling end-to-end conversion analysis.

```
Account → Has Lead? → Lead Stage → Has Opportunity? → Won? → funnel_stage
```

### The `funnel_stage` classification

```sql
CASE
    WHEN won_opp_count  > 0 THEN 'Closed-Won'
    WHEN open_opp_count > 0 THEN 'Open Opportunity'
    WHEN lost_opp_count > 0 THEN 'Closed-Lost'
    WHEN max_lifecycle_rank = 3 THEN 'SQL'
    WHEN max_lifecycle_rank = 2 THEN 'MQL'
    WHEN max_lifecycle_rank = 1 THEN 'Lead'
    ELSE 'Account Only'
END AS funnel_stage
```

This gives every account exactly one stage label — the furthest they have progressed. This single column powers the funnel waterfall chart in the analysis notebook.

### Velocity metrics

```sql
-- Days from first marketing touch to first sales opportunity
(first_opp_created_at::DATE - first_lead_date) AS lead_to_opp_days,

-- Days from first opportunity created to first Closed-Won
(first_won_opp_at::DATE - first_opp_created_at::DATE) AS opp_to_close_days
```

These are NULL for accounts that haven't reached the next stage — that is expected and correct. The analysis notebook filters `WHERE lead_to_opp_days IS NOT NULL` before computing medians.

### What this model deliberately excludes

- **Unmatched leads** (12 records with `has_account = FALSE`): They exist in staging but cannot be joined to an account. They are excluded from this model's aggregation and tracked separately.
- **Orphan opportunities** (9 records with `is_orphan = TRUE`): Similarly excluded from account-level rollups. The `WHERE is_orphan = FALSE` filter in `opps_agg` handles this.

---

## `int_revenue_lifecycle`

### What it does

Builds the revenue chain from CRM booking to collected cash — one row per closed-won opportunity:

```
Opportunity (won) → Contract (canonical) → Billing invoices (aggregated) → Gap columns
```

### The three gap columns

This model's most important output is the three gap columns that power revenue reconciliation:

```sql
-- Gap 1: CRM booking vs. contract signing
-- Positive = discount was given at contract execution
crm_booking_amount - contract_value AS booking_to_contract_gap,

-- Gap 2: Contract vs. what was billed
-- Positive = billing hasn't caught up to contract (timing issue)
contract_value - total_billed_usd   AS contract_to_billing_gap,

-- Gap 3: Billed vs. collected
-- Positive = outstanding receivables (pending + failed payments)
total_billed_usd - total_collected_usd AS billing_to_collected_gap
```

**Each gap has a business owner:**
- Gap 1 → Finance / Sales Ops (discount approval process)
- Gap 2 → Billing / Revenue Ops (billing schedule alignment)
- Gap 3 → Collections / Finance (payment failure follow-up)

### The canonical contract filter

```sql
FROM stg_contracts
WHERE is_canonical_record = TRUE  -- drops the duplicate rows we flagged in staging
```

Without this filter, 4 contracts would appear twice. The revenue lifecycle join would then double-count those deals' billed and collected amounts.

### What `revenue_stage` tells you

```sql
CASE
    WHEN has_collected_revenue THEN 'Collected'
    WHEN has_billing           THEN 'Billed'
    WHEN has_contract          THEN 'Contracted'
    ELSE 'Booking Only'
END AS revenue_stage
```

This single column answers "how far through the revenue recognition process has this deal progressed?" A deal stuck at 'Booking Only' means sales closed it but no contract was ever signed — that is a serious process failure worth flagging.

---

## How Intermediate Models Relate to Each Other

The three intermediate models are independent — they do not `ref()` each other. Each builds from staging directly. They converge in `fct_customer_lifecycle`:

```
int_customer_identity_map  ──┐
int_gtm_funnel             ──┼──→ fct_customer_lifecycle  (full B2B lifecycle per account)
int_revenue_lifecycle      ──┘
```

This design choice keeps each intermediate model focused and testable independently. If `int_gtm_funnel` is wrong, only the GTM-related marts break — not the revenue models.

---

## Schema Tests for Intermediate Models

Defined in `_intermediate__schema.yml`:

| Model | Test | Why |
|-------|------|-----|
| `int_customer_identity_map` | `unique(account_id)` | Confirms the dedup worked — no double-counting |
| `int_gtm_funnel` | `unique(account_id)` | One funnel row per account |
| `int_gtm_funnel` | `accepted_values(funnel_stage)` | Guards against new stage values from Salesforce |
| `int_revenue_lifecycle` | `unique(opportunity_id)` | One revenue chain row per won deal |
| `int_revenue_lifecycle` | `not_null(crm_booking_amount)` | Every won deal must have an amount |

---

_Next: [04_mart_models.md](./04_mart_models.md) — How the five mart models expose these intermediate outputs to analysts and dashboards._
