# Phase 3: Data Exploration

> **Core Question:** Before writing a single mart, what do we actually have in the raw tables — and where are the traps?

Real-world workflow: raw tables land in BigQuery (via Fivetran/Airbyte or a load script).
An analyst explores them before touching mart SQL.
Skipping this step causes bugs that are hard to find later.

---

## Why Explore First

```
❌ Write mart → get wrong numbers → debug for hours → find the data issue
✅ Explore first → find the issue → write mart correctly the first time
```

Things you find during exploration:
- Join keys that don't match across tables
- Unexpected NULLs in critical columns
- Grain assumptions that turn out to be wrong
- Channels or verticals not present in one source but present in another
- Date range mismatches between tables

### Exploration Steps at a Glance

| Step | What You Check | Why It Matters |
| ---- | -------------- | -------------- |
| 1. Schema Inspection | Tables exist, row counts, column names and types | Catches load failures before any mart is written; surfaces format surprises (timestamp vs. string) |
| 2. NULL Checks | NULLs in JOIN keys, GROUP BY columns, and metric columns | NULLs in JOIN keys silently drop rows; NULLs in metrics silently undercount aggregates |
| 3. Value Distributions | Distinct values in categorical columns (channel, vertical, status) | Prevents using values that don't exist in the data in GROUP BY logic or downstream descriptions |
| 4. Date Range Checks | Min/max date per table across all sources | Mismatched ranges cause silent row loss when tables are joined on date |
| 5. Grain Validation | Whether each table is truly one row per expected key | Wrong grain assumption makes COUNT(*) and SUM() wrong across every metric that depends on it |
| 6. Join Key Validation | Whether foreign keys in one table exist in the joined table | Orphaned records change the required JOIN type (LEFT vs FULL OUTER) and can silently drop revenue |
| 7. Business Metric Preview | Quick spot-check of key rates against known benchmarks | If numbers look wrong here, something is broken upstream — better to find it now than after building 5 marts |

---

## Step 1: Schema Inspection

What columns exist, what types did BigQuery infer?

```sql
-- Row counts for all 6 raw tables
SELECT 'raw_ad_performance' AS tbl, COUNT(*) AS rows
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance`

UNION ALL

SELECT 'raw_quote_events', COUNT(*)
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_quote_events`

UNION ALL

SELECT 'raw_leads', COUNT(*)
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`

UNION ALL

SELECT 'raw_routing_attempts', COUNT(*)
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`

UNION ALL

SELECT 'raw_revenue_events', COUNT(*)
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events`

UNION ALL

SELECT 'raw_partners', COUNT(*)
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_partners`;
```

**Sample output:**

| tbl | rows |
| --- | ---- |
| raw_ad_performance | 905 |
| raw_quote_events | 17,261 |
| raw_leads | 1,321 |
| raw_routing_attempts | 1,135 |
| raw_revenue_events | 731 |
| raw_partners | 10 |

Sample rows from each table:

```sql
SELECT *
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
LIMIT 5;

SELECT *
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`
LIMIT 5;

SELECT *
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events`
LIMIT 5;
```

**Sample output (raw_leads):**

| lead_id | campaign_id | submitted_at | channel | insurance_vertical | state | is_valid | is_duplicate | quality_score | rejection_reason |
| ------- | ----------- | ------------ | ------- | ------------------ | ----- | -------- | ------------ | ------------- | ---------------- |
| L000001 | C001 | 2025-01-02 08:14:22 | google | auto | CA | true | false | 0.91 | |
| L000002 | C003 | 2025-01-02 09:33:05 | meta | home | TX | false | false | 0.44 | low_quality |
| L000003 | C006 | 2025-01-02 11:02:47 | organic | health | NY | true | false | 0.87 | |
| L000004 | C001 | 2025-01-02 13:45:10 | google | auto | FL | true | false | 0.79 | |
| L000005 | C002 | 2025-01-02 15:20:33 | meta | life | IL | false | true | 0.38 | duplicate |

**A note on `is_duplicate` and `quality_score`:**

These columns are calculated by the application layer at the time of lead submission — not derived later in the warehouse. When a lead is submitted, the backend API runs validation in real time before routing begins.

- **`is_duplicate`** — checked against existing leads in the transactional DB using phone number, email, or a combination of identifying fields within a rolling window (e.g., 30 days). If a match is found, the flag is set to `true` and the lead is not routed.

- **`quality_score`** — a 0–1 score computed by a rule-based or ML scoring system at submission time. Signals that typically lower the score include invalid phone format, disposable email domain, VPN/proxy IP, unusually fast form completion (bot behavior), or repeated submissions from the same IP. A lead with `quality_score < 0.5` is typically flagged as invalid and not routed to partners.

Both values arrive in `raw_leads` as pre-computed columns — the warehouse treats them as source-of-truth inputs, not derived fields.

**Sample output (raw_routing_attempts):**

| routing_attempt_id | lead_id | partner_id | response_status | routed_at | response_time_sec |
| ------------------ | ------- | ---------- | --------------- | --------- | ----------------- |
| R000001 | L000001 | P002 | accepted | 2025-01-02 08:15:04 | 1.3 |
| R000002 | L000004 | P001 | rejected | 2025-01-02 13:46:01 | 2.1 |
| R000003 | L000004 | P004 | accepted | 2025-01-02 13:46:08 | 0.9 |
| R000004 | L000006 | P003 | no_response | 2025-01-02 16:02:55 | 30.0 |
| R000005 | L000009 | P007 | capacity_exceeded | 2025-01-02 17:11:42 | 0.4 |

---

## Step 2: NULL Checks

Critical columns should not have unexpected NULLs.

```sql
SELECT
  COUNTIF(lead_id IS NULL)            AS null_lead_id,
  COUNTIF(campaign_id IS NULL)        AS null_campaign_id,
  COUNTIF(submitted_at IS NULL)       AS null_submitted_at,
  COUNTIF(channel IS NULL)            AS null_channel,
  COUNTIF(insurance_vertical IS NULL) AS null_vertical,
  COUNTIF(is_valid IS NULL)           AS null_is_valid,
  COUNT(*)                            AS total_rows
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`;
```

**Sample output:**

| null_lead_id | null_campaign_id | null_submitted_at | null_channel | null_vertical | null_is_valid | total_rows |
| ------------ | ---------------- | ----------------- | ------------ | ------------- | ------------- | ---------- |
| 0 | 0 | 0 | 0 | 0 | 0 | 1,321 |

```sql
SELECT
  COUNTIF(routing_attempt_id IS NULL) AS null_attempt_id,
  COUNTIF(lead_id IS NULL)            AS null_lead_id,
  COUNTIF(partner_id IS NULL)         AS null_partner_id,
  COUNTIF(response_status IS NULL)    AS null_response_status,
  COUNTIF(routed_at IS NULL)          AS null_routed_at,
  COUNT(*)                            AS total_rows
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`;
```

**Sample output:**

| null_attempt_id | null_lead_id | null_partner_id | null_response_status | null_routed_at | total_rows |
| --------------- | ------------ | --------------- | -------------------- | -------------- | ---------- |
| 0 | 0 | 0 | 0 | 0 | 1,135 |

**What we found:**
- All key columns non-null ✅
- `rejection_reason` is empty string (not NULL) when lead is valid — this is expected

---

## Step 3: Value Distributions

Understand what's in each categorical column before using it in GROUP BY.

```sql
-- Channel distribution in raw_leads
SELECT
  channel,
  COUNT(*)                                              AS leads,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3)           AS share
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
GROUP BY channel
ORDER BY leads DESC;
```

**Sample output:**

| channel | leads | share |
| ------- | ----- | ----- |
| google | 410 | 0.310 |
| meta | 318 | 0.241 |
| affiliate | 275 | 0.208 |
| organic | 198 | 0.150 |
| direct | 120 | 0.091 |

```sql
-- Insurance vertical distribution
SELECT
  insurance_vertical,
  COUNT(*) AS leads
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
GROUP BY insurance_vertical
ORDER BY leads DESC;
```

**Sample output:**

| insurance_vertical | leads |
| ------------------ | ----- |
| auto | 497 |
| home | 382 |
| health | 263 |
| life | 179 |

```sql
-- Response status distribution in routing attempts
SELECT
  response_status,
  COUNT(*) AS attempts,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS share
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`
GROUP BY response_status
ORDER BY attempts DESC;
```

**Sample output:**

| response_status | attempts | share |
| --------------- | -------- | ----- |
| accepted | 681 | 0.600 |
| rejected | 238 | 0.210 |
| no_response | 136 | 0.120 |
| capacity_exceeded | 80 | 0.070 |

**What we found:**
- Channels present: google, meta, affiliate, organic, direct — no "email" channel
- Verticals present: auto, home, health, life — no "renters"
- Response statuses: accepted, rejected, no_response, capacity_exceeded

> This step prevents writing LookML descriptions with channels/verticals that don't exist in the data.

---

## Step 4: Date Range Checks

Confirm all tables cover the same period. Mismatches cause empty joins.

```sql
SELECT
  'raw_ad_performance' AS tbl,
  MIN(performance_date) AS min_date,
  MAX(performance_date) AS max_date
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance`

UNION ALL

SELECT
  'raw_leads',
  MIN(DATE(submitted_at)),
  MAX(DATE(submitted_at))
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`

UNION ALL

SELECT
  'raw_routing_attempts',
  MIN(DATE(routed_at)),
  MAX(DATE(routed_at))
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`

UNION ALL

SELECT
  'raw_revenue_events',
  MIN(DATE(revenue_timestamp)),
  MAX(DATE(revenue_timestamp))
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events`;
```

**Sample output:**

| tbl | min_date | max_date |
| --- | -------- | -------- |
| raw_ad_performance | 2025-01-01 | 2025-06-30 |
| raw_leads | 2025-01-01 | 2025-06-30 |
| raw_routing_attempts | 2025-01-01 | 2025-06-30 |
| raw_revenue_events | 2025-01-02 | 2025-06-30 |

**What we found:** All tables span 2025-01-01 → 2025-06-30 ✅

---

## Step 5: Grain Validation

Confirm each table's grain matches the assumption before writing mart logic.

```sql
-- Is raw_leads truly 1 row per lead_id?
SELECT
  lead_id,
  COUNT(*) AS row_count
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
GROUP BY lead_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows returned
```

**Sample output:**

| lead_id | row_count |
| ------- | --------- |
| *(0 rows)* | |

```sql
-- Is raw_ad_performance 1 row per campaign × date?
SELECT
  campaign_id,
  performance_date,
  COUNT(*) AS row_count
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance`
GROUP BY campaign_id, performance_date
HAVING COUNT(*) > 1;
-- Expected: 0 rows returned
```

**Sample output:**

| campaign_id | performance_date | row_count |
| ----------- | ---------------- | --------- |
| *(0 rows)* | | |

```sql
-- Can one lead have multiple routing attempts? (affects fan-out analysis)
SELECT
  lead_id,
  COUNT(DISTINCT routing_attempt_id) AS attempts,
  COUNT(DISTINCT partner_id)         AS partners_tried
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`
GROUP BY lead_id
ORDER BY attempts DESC
LIMIT 10;
```

**Sample output:**

| lead_id | attempts | partners_tried |
| ------- | -------- | -------------- |
| L000312 | 3 | 3 |
| L000087 | 3 | 3 |
| L000541 | 2 | 2 |
| L000204 | 2 | 2 |
| L000733 | 2 | 2 |
| L000019 | 1 | 1 |
| L000022 | 1 | 1 |
| L000025 | 1 | 1 |
| ... | ... | ... |

**What we found:**
- `raw_leads`: 1 row per lead ✅ — safe to use COUNT(DISTINCT lead_id)
- `raw_ad_performance`: 1 row per campaign × date ✅
- Routing: most leads get 1 attempt; a subset gets 2–3 before acceptance
  → This confirms **fan-out risk** when joining ad_performance → leads → routing

---

## Step 6: Join Key Validation

Check that foreign keys actually match across tables before writing JOIN logic.

```sql
-- Are there leads whose campaign_id doesn't exist in ad_performance?
SELECT
  l.campaign_id,
  COUNT(*) AS orphaned_leads
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads` l
LEFT JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance` a
  USING (campaign_id)
WHERE a.campaign_id IS NULL
GROUP BY l.campaign_id;
```

**Sample output:**

| campaign_id | orphaned_leads |
| ----------- | -------------- |
| C006 | 198 |
| C007 | 120 |

> C006 = organic, C007 = direct — these channels have no ad spend, so no ad_performance rows exist. Not a data error; requires FULL OUTER JOIN in mart_reconciliation.

```sql
-- Are there routing attempts whose lead_id doesn't exist in raw_leads?
SELECT COUNT(*) AS orphaned_attempts
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts` r
LEFT JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_leads` l
  USING (lead_id)
WHERE l.lead_id IS NULL;
```

**Sample output:**

| orphaned_attempts |
| ----------------- |
| 0 |

```sql
-- Are there revenue events whose lead_id has no matching routing attempt?
SELECT COUNT(*) AS unmatched_revenue
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events` rev
LEFT JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts` r
  USING (lead_id)
WHERE r.lead_id IS NULL;
```

**Sample output:**

| unmatched_revenue |
| ----------------- |
| 0 |

**What we found:**
- organic/direct leads have campaign_id = C006/C007 but those channels have no ad_performance rows
  → FULL OUTER JOIN (not LEFT JOIN) needed in mart_reconciliation ✅
- All routing attempt lead_ids exist in raw_leads ✅
- All revenue event lead_ids have corresponding routing attempts ✅

---

## Step 7: Business Metric Preview

Quick sanity check of key metrics before building marts. If these numbers look wrong, something is off upstream.

```sql
-- Valid lead rate by channel (should match CHANNEL_QUALITY config)
SELECT
  channel,
  COUNT(*)                                                         AS total_leads,
  COUNTIF(is_valid = TRUE)                                         AS valid_leads,
  ROUND(SAFE_DIVIDE(COUNTIF(is_valid = TRUE), COUNT(*)), 3)        AS valid_lead_rate
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
GROUP BY channel
ORDER BY valid_lead_rate DESC;
-- Expected: organic ~0.92, google ~0.88, direct ~0.90, meta ~0.72, affiliate ~0.65
```

**Sample output:**

| channel | total_leads | valid_leads | valid_lead_rate |
| ------- | ----------- | ----------- | --------------- |
| organic | 198 | 182 | 0.919 |
| direct | 120 | 108 | 0.900 |
| google | 410 | 361 | 0.880 |
| meta | 318 | 229 | 0.720 |
| affiliate | 275 | 179 | 0.651 |

```sql
-- Partner acceptance rate (should match PARTNER_ACCEPTANCE config)
SELECT
  partner_id,
  COUNT(DISTINCT routing_attempt_id)                                    AS delivered,
  COUNT(DISTINCT CASE WHEN response_status = 'accepted'
                      THEN routing_attempt_id END)                      AS accepted,
  ROUND(SAFE_DIVIDE(
    COUNT(DISTINCT CASE WHEN response_status = 'accepted'
                        THEN routing_attempt_id END),
    COUNT(DISTINCT routing_attempt_id)
  ), 2)                                                                  AS acceptance_rate
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`
GROUP BY partner_id
ORDER BY acceptance_rate DESC;
-- Expected: P004 ~0.85, P002 ~0.82, P001 ~0.78, P009 ~0.65
```

**Sample output:**

| partner_id | delivered | accepted | acceptance_rate |
| ---------- | --------- | -------- | --------------- |
| P004 | 148 | 126 | 0.85 |
| P002 | 134 | 110 | 0.82 |
| P001 | 121 | 94 | 0.78 |
| P006 | 98 | 72 | 0.73 |
| P008 | 112 | 80 | 0.71 |
| P003 | 127 | 88 | 0.69 |
| P009 | 89 | 58 | 0.65 |
| ... | ... | ... | ... |

```sql
-- Fan-out test: does naive JOIN inflate spend?
-- ad_performance has 1 row per campaign × date
-- leads has N rows per campaign
-- Direct join → spend × N duplicated
SELECT
  a.campaign_id,
  COUNT(DISTINCT a.performance_date) AS ad_rows,
  COUNT(DISTINCT l.lead_id)          AS lead_rows,
  SUM(a.spend)                       AS correct_spend,
  SUM(a.spend) * COUNT(DISTINCT l.lead_id)
    / COUNT(DISTINCT a.performance_date) AS fanout_spend
FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance` a
JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_leads` l
  USING (campaign_id)
GROUP BY a.campaign_id
ORDER BY a.campaign_id;
-- fanout_spend >> correct_spend confirms why pre-aggregation is required
```

**Sample output:**

| campaign_id | ad_rows | lead_rows | correct_spend | fanout_spend |
| ----------- | ------- | --------- | ------------- | ------------ |
| C001 | 181 | 210 | 54,320 | 63,019 |
| C002 | 181 | 198 | 48,750 | 53,315 |
| C003 | 181 | 166 | 39,200 | 35,937 |
| C004 | 181 | 143 | 31,880 | 25,192 |
| C005 | 181 | 83 | 22,440 | 10,282 |

> `fanout_spend` diverges from `correct_spend` as soon as `lead_rows ≠ ad_rows`. This confirms that naively joining ad_performance → leads inflates spend. Solution: pre-aggregate each source to campaign × month separately before joining.

---

## Findings Summary

| Finding | Impact on Mart Design |
| ------- | --------------------- |
| organic/direct have no ad_performance rows | mart_reconciliation needs FULL OUTER JOIN |
| One lead can have 2–3 routing attempts | mart_partner_performance must use routing grain, not lead grain |
| revenue_events has partner_id | direct join to routing is not required for revenue attribution |
| campaign_id grain in ad_performance ≠ lead grain in raw_leads | pre-aggregate both to campaign × month before joining (fan-out prevention) |
| All join keys validated | no orphaned records — data integrity confirmed |
| Channels: google, meta, affiliate, organic, direct | no "email" channel — update any downstream descriptions |
| Verticals: auto, home, health, life | no "renters" vertical |

These findings directly shaped the mart design decisions in [Phase 4: SQL Marts](./04_sql_marts.md).
