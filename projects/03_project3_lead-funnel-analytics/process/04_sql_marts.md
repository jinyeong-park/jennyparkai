# Phase 3: SQL Mart Layer

> **Core Question:** How do we transform 6 raw tables into clean, analysis-ready marts that answer real business questions?

---

## Why a Mart Layer?

```
❌ Without marts — analysts write complex joins every time:
   SELECT ...
   FROM raw_leads
   JOIN raw_routing_attempts ON ...
   JOIN raw_revenue_events ON ...
   JOIN raw_ad_performance ON ...
   WHERE ...
   GROUP BY ...
   (50+ lines, fan-out risk, inconsistent results)

✅ With marts — LookML and dashboards read one clean table:
   SELECT *
   FROM mart_campaign_performance
   (modeled at a defined grain, validated, consistent metric definitions)
   Note: not all marts are aggregated — mart_attribution is entity-level (1 row per lead)
```

---

## The 5 Marts

Order follows the business flow: ad spend → user funnel → partner routing → attribution → platform validation

| # | Mart | SQL File | Grain | Business Problem |
| - | ---- | -------- | ----- | ---------------- |
| 1 | `mart_campaign_performance` | `mart_campaign_performance.sql` | campaign × month | "C002 has a lower CPL than C001. Should we shift budget?" |
| 2 | `mart_lead_funnel` | `mart_lead_funnel.sql` | channel × vertical × month | "Lead volume went up 20% but revenue stayed flat. Where is the funnel breaking?" |
| 3 | `mart_partner_performance` | `mart_partner_performance.sql` | partner × date | "P003's acceptance rate dropped. Is it a trend or a one-day fluke?" |
| 4 | `mart_attribution` | `mart_attribution.sql` | 1 row per lead | "Which channel did users interact with first — before converting?" |
| 5 | `mart_reconciliation` | `mart_reconciliation.sql` | channel × month | "Meta claims 144 conversions. Our warehouse shows 132. Which is right?" |

---

## Mart 1: mart_campaign_performance

**File:** `sql/marts/mart_campaign_performance.sql`

### The Fan-out Problem (Critical)

This mart joins 3 tables. A naive join would inflate spend.

```
ad_performance: C001 → $300 spend (1 row)
leads:          C001 → 3 leads   (3 rows)

Naive JOIN → C001 spend appears 3 times = $900 ❌
```

**Solution: pre-aggregate each table to campaign grain before joining.**

```sql
-- Step 1: aggregate spend to campaign × month
WITH campaign_spend AS (
  SELECT
    DATE_TRUNC(performance_date, MONTH) AS month,
    campaign_id,
    SUM(spend) AS total_spend
  FROM raw_ad_performance
  GROUP BY
    month,
    campaign_id
),

-- Step 2: aggregate leads to campaign × month (separately — no join yet)
campaign_leads AS (
  SELECT
    DATE_TRUNC(DATE(submitted_at), MONTH) AS month,
    campaign_id,
    COUNT(DISTINCT lead_id) AS leads_submitted
  FROM raw_leads
  GROUP BY
    month,
    campaign_id
),

-- Step 3: aggregate revenue to campaign × month
-- revenue_events has no campaign_id — must bridge through raw_leads
-- raw_leads → campaign_id
-- revenue_events → lead_id → raw_leads → campaign_id
campaign_revenue AS (
  SELECT
    DATE_TRUNC(DATE(l.submitted_at), MONTH) AS month,
    l.campaign_id,
    SUM(r.revenue_amount) AS total_revenue
  FROM raw_leads AS l
  JOIN raw_revenue_events AS r
    ON l.lead_id = r.lead_id
  GROUP BY
    month,
    l.campaign_id
)

-- Step 4: join all 3 pre-aggregated CTEs — all at campaign × month grain (safe)
SELECT *
FROM campaign_spend AS s
LEFT JOIN campaign_leads  AS l ON s.month = l.month AND s.campaign_id = l.campaign_id
LEFT JOIN campaign_revenue AS r ON s.month = r.month AND s.campaign_id = r.campaign_id
```

> The grain stated in the mart must match every `GROUP BY` and join key.
> Omitting `month` from any CTE would silently collapse all months into one row per campaign.
> Revenue must be bridged through `raw_leads` because `revenue_events` has only `lead_id`, not `campaign_id`.

### Key Metrics

```sql
-- Traffic efficiency
ctr                   = SAFE_DIVIDE(clicks,         impressions)
cpc                   = SAFE_DIVIDE(total_spend,    clicks)

-- Lead cost
cpl                   = SAFE_DIVIDE(total_spend,    leads_submitted)
cost_per_valid_lead   = SAFE_DIVIDE(total_spend,    valid_leads)

-- Revenue
revenue_per_lead      = SAFE_DIVIDE(total_revenue,  leads_submitted)
roas                  = SAFE_DIVIDE(total_revenue,  total_spend)
roi                   = SAFE_DIVIDE(total_revenue - total_spend, total_spend)

-- Platform discrepancy
platform_overclaim_rate = SAFE_DIVIDE(platform_leads - warehouse_leads, platform_leads)
```

### What You'll Find in the Data

- Meta (C003, C004) shows `platform_overclaim_rate` of 15–40%
- Google (C001, C002) shows `platform_overclaim_rate` of 5–20%
- Lower CPL ≠ better ROAS — affiliate has low CPL but also low valid lead rate

---

## Mart 2: mart_lead_funnel

**File:** `sql/marts/mart_lead_funnel.sql`

### Logic

```
raw_quote_events  →  count sessions, quote_starts, completions per channel × vertical × month
raw_leads         →  count submitted, valid, duplicate leads per channel × vertical × month
           ↓
      LEFT JOIN on channel + insurance_vertical + month
           ↓
mart_lead_funnel (~150 rows — 5 channels × 5 verticals × 6 months, only active combos)
```

### Key Metrics

```sql
session_to_quote_rate    = SAFE_DIVIDE(quote_starts,       sessions)
quote_start_to_completion_rate = SAFE_DIVIDE(quote_completions,  quote_starts)
completion_to_lead_rate  = SAFE_DIVIDE(leads_submitted,    quote_completions)
overall_cvr              = SAFE_DIVIDE(leads_submitted,    sessions)
valid_lead_rate          = SAFE_DIVIDE(valid_leads,        leads_submitted)
duplicate_rate           = SAFE_DIVIDE(duplicate_leads,    leads_submitted)
```

### What You'll Find in the Data

- `affiliate` channel has the lowest `valid_lead_rate` (~65%)
- `google` and `organic` have the highest quality (88–92%)
- `completion_to_lead_rate` is consistent across channels — drop-off is earlier in funnel

---

## Mart 3: mart_partner_performance

**File:** `sql/marts/mart_partner_performance.sql`

### Logic

```
raw_routing_attempts  →  daily delivery + acceptance per partner
raw_revenue_events    →  daily revenue per partner
raw_partners          →  partner name + verticals (dimension join)
        ↓
   Window functions add rolling metrics
        ↓
mart_partner_performance (695 rows — 10 partners × ~70 active days each)
```

### Key Window Functions

```sql
-- 7-day rolling acceptance rate (volume-weighted — NOT AVG of daily rates)
-- Day 1: 10 leads, 8 accepted = 0.80
-- Day 2: 100 leads, 60 accepted = 0.60
-- AVG(rate) = 0.70 ❌  SUM(accepted)/SUM(delivered) = 68/110 = 0.618 ✅
--
-- RANGE vs ROWS:
-- ROWS BETWEEN 6 PRECEDING = previous 6 data rows (wrong if partner has gaps)
-- RANGE BETWEEN 6 PRECEDING on UNIX_DATE = previous 6 calendar days (correct)
-- Partners have ~70 active days out of 180 — gaps are common.
ROUND(SAFE_DIVIDE(
  SUM(leads_accepted) OVER (
    PARTITION BY partner_id
    ORDER BY UNIX_DATE(route_date)
    RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
  ),
  SUM(leads_delivered) OVER (
    PARTITION BY partner_id
    ORDER BY UNIX_DATE(route_date)
    RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
  )
), 3) AS rolling_7d_acceptance_rate

-- Cumulative leads delivered
SUM(leads_delivered) OVER (
  PARTITION BY partner_id
  ORDER BY UNIX_DATE(route_date)
)
```

### What You'll Find in the Data

- Some partners show declining rolling acceptance in Q2 → capacity constraints
- `avg_response_sec` varies widely — faster responders tend to accept more
- P009 (Liberty Mutual) consistently lowest acceptance at ~65%

---

## Mart 4: mart_attribution

**File:** `sql/marts/mart_attribution.sql`

### Logic: First Touch

```
raw_leads + raw_quote_events
        ↓
JOIN on l.quote_id = e.quote_id AND e.event_timestamp <= l.submitted_at
  (quote_id is the bridge key between leads and quote events)
        ↓
For each lead_id:
  All matching quote events at or before submitted_at are candidates
  Order by event_timestamp ASC
  QUALIFY ROW_NUMBER() = 1 → keeps only the earliest event row per lead
  e.channel on that row IS the first_touch_channel (no FIRST_VALUE needed)
        ↓
LEFT JOIN lead_revenue (pre-aggregated CTE) for revenue
        ↓
mart_attribution (1,321 rows — one per lead)
```

> Revenue is pre-aggregated to lead grain in a CTE before joining.
> Direct `LEFT JOIN raw_revenue_events` would break the one-row-per-lead grain
> if a lead has multiple revenue events.

### QUALIFY Pattern (BigQuery-specific)

```sql
-- Without QUALIFY — CTE approach (portable, works in any SQL dialect)
WITH all_events AS (
  SELECT
    l.lead_id,
    e.channel,
    e.event_timestamp,
    ROW_NUMBER() OVER (
      PARTITION BY l.lead_id
      ORDER BY e.event_timestamp ASC
    ) AS rn
  FROM raw_leads l
  JOIN raw_quote_events e
    ON  l.quote_id = e.quote_id
    AND e.event_timestamp <= l.submitted_at
)
SELECT *
FROM all_events
WHERE rn = 1

-- With QUALIFY — BigQuery only, same result in fewer lines
SELECT ...
FROM raw_leads l
JOIN raw_quote_events e
  ON  l.quote_id = e.quote_id
  AND e.event_timestamp <= l.submitted_at
QUALIFY ROW_NUMBER() OVER (PARTITION BY l.lead_id ORDER BY e.event_timestamp ASC) = 1
```

> CTE 방식은 `rn` 컬럼을 명시적으로 만들고 `WHERE`로 필터링하기 때문에 흐름이 명확하다.
> QUALIFY는 BigQuery 전용이지만 코드가 짧고 중간 컬럼 없이 바로 필터링할 수 있다.
> 이 mart의 실제 SQL은 QUALIFY를 사용한다.

### What You'll Find in the Data

- `first_touch_channel` ≠ `submitted_channel` for ~15% of leads (multi-touch journeys)
- Organic first-touch leads have higher `revenue_amount` on average
- `hours_to_submit` ranges from < 1 hour (direct) to 48+ hours (organic discovery)

---

## Mart 5: mart_reconciliation

**File:** `sql/marts/mart_reconciliation.sql`

### Logic

```
raw_ad_performance  →  platform_leads, platform_revenue per channel × month
raw_leads           →  warehouse_leads per channel × month
        ↓
FULL OUTER JOIN (keeps channels that appear in only one source)
        ↓
mart_reconciliation (30 rows — 5 channels × 6 months)
```

### The Discrepancy Formula

```sql
-- NULLIF(platform_leads, 0) in the denominator (not COALESCE):
-- For organic/direct channels, platform_leads is NULL/0 (no ad spend row).
-- COALESCE(platform_leads, 0) → SAFE_DIVIDE(x, 0) → returns 0 (misleading)
-- NULLIF(platform_leads, 0)   → SAFE_DIVIDE(x, NULL) → returns NULL (correct — no rate to report)
discrepancy_rate = SAFE_DIVIDE(
  COALESCE(platform_leads, 0) - COALESCE(warehouse_leads, 0),
  NULLIF(platform_leads, 0)
)
```

A rate of `0.25` means **25% of platform-reported conversions have no matching warehouse lead**.

This is NOT the same as "the platform overclaims by 25%":
- Platform = 100, warehouse = 75 → discrepancy_rate = 25/100 = **0.25**
- "Platform overclaims by X% relative to warehouse" = 25/75 = **0.33**

The formula divides by platform (the larger number), so it's the more conservative metric.
Use this to answer: "What share of platform conversions should I distrust?"
Organic/direct rows return `NULL` for this field — they have no platform benchmark to compare against.

A `reconciliation_status` column also flags each row:
- `matched` — both sources reported data (normal paid channels)
- `warehouse_only` — organic/direct: warehouse has leads but no ad spend row exists
- `platform_only` — platform reports leads we never received (edge case)

### Why FULL OUTER JOIN (not LEFT JOIN)

```sql
-- LEFT JOIN: only shows channels present in ad_performance
-- This hides organic/direct which have no spend but DO have warehouse leads
SELECT *
FROM platform_data p
LEFT JOIN warehouse_leads w ON p.month = w.month AND p.channel = w.channel

-- FULL OUTER JOIN: shows all channels from both sides
-- Organic shows up with platform_leads = 0, warehouse_leads = 95 → correct
SELECT *
FROM platform_data p
FULL OUTER JOIN warehouse_leads w ON p.month = w.month AND p.channel = w.channel
```

---

## Running the Marts

```bash
# Run all marts
python -c "
from google.cloud import bigquery
from pathlib import Path
client = bigquery.Client(project='insurance-lead-intelligence')
for f in sorted(Path('sql/marts').glob('*.sql')):
    sql = f.read_text()
    client.query(sql).result()
    print(f'✅ {f.name}')
"
```
