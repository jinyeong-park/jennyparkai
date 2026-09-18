# Phase 2: Data Cleaning with SQL

> **Core Question:** How do we remove noise from raw data so that downstream attribution models produce reliable results?

> **dbt Implementation:** The SQL patterns described in this document are implemented as runnable dbt models in [`../dbt/`](../dbt/README.md).
>
> | Cleaning Step | dbt Model |
> |---------------|-----------|
> | UTM normalization + channel mapping | `models/staging/stg_user_touchpoints.sql` |
> | Duplicate event removal | `models/intermediate/int_deduped_touchpoints.sql` |
> | Attribution window JOIN | `models/intermediate/int_pre_conversion_touchpoints.sql` |
> | Data quality checks | `tests/assert_no_post_conversion_touchpoints.sql`, `tests/assert_no_duplicate_event_ids.sql` |

---

## Why Data Cleaning Is the Most Important Phase

> "Garbage in, garbage out."
> The most sophisticated attribution model will produce wrong answers if the input data contains errors.

Specific problems that uncleaned data causes in this project:

- UTM case differences cause the same channel to appear as two separate channels in `GROUP BY` queries (`Google_Search` and `google_search` aggregate separately)
- Duplicate events inflate touchpoint counts, which distorts attribution weights
- Including post-conversion touchpoints reverses the causal direction — an ad click recorded after a purchase cannot logically have driven that purchase

---

## The Three Cleaning Problems to Solve

### Problem 1: UTM Case Inconsistency

**Root cause:** Marketers manually type UTM parameters into campaign URLs, leading to inconsistent capitalization across campaigns.

```
Raw data contains a mix of:
  utm_campaign = "Q1_Prospecting"
  utm_campaign = "q1_prospecting"
  utm_campaign = "Q1_PROSPECTING"
  → All three represent the same campaign, but SQL treats them as distinct values
```

**Fix: Apply `LOWER()` and `TRIM()` to all UTM fields, and normalize channel names with `CASE WHEN`**

```sql
SELECT
    event_id,
    user_id,
    timestamp,
    LOWER(TRIM(utm_source))   AS utm_source,
    LOWER(TRIM(utm_medium))   AS utm_medium,
    LOWER(TRIM(utm_campaign)) AS utm_campaign,
    CASE
        WHEN LOWER(TRIM(channel)) IN ('meta_paid_social', 'meta', 'facebook')
            THEN 'Meta_Paid_Social'
        WHEN LOWER(TRIM(channel)) IN ('google_search', 'google', 'google paid search')
            THEN 'Google_Search'
        WHEN LOWER(TRIM(channel)) IN ('tiktok_ads', 'tiktok', 'tik tok')
            THEN 'TikTok_Ads'
        ELSE INITCAP(TRIM(channel))
    END AS channel_clean,
    dma_code
FROM raw_user_touchpoints;
```

**Verification — confirm the channel count dropped to exactly 3:**

```sql
-- Before cleaning
SELECT channel, COUNT(*) FROM raw_user_touchpoints GROUP BY 1 ORDER BY 2 DESC;

-- After cleaning (should show exactly 3 rows: Meta_Paid_Social, Google_Search, TikTok_Ads)
SELECT channel_clean, COUNT(*) FROM standardized GROUP BY 1;
```

---

### Problem 2: Duplicate Events

**Root cause:** Users rapidly double-click an ad or page refresh triggers a second tag fire. Network retries can also cause duplicate event submissions.

```
Example in raw data:
  event_id: E001, user_id: U123, timestamp: 2026-03-15 14:23:11, channel: Google_Search
  event_id: E002, user_id: U123, timestamp: 2026-03-15 14:23:11, channel: Google_Search
  → Identical touchpoint recorded twice (approximately 3% of all rows)
```

**Fix: Use `ROW_NUMBER()` window function to keep only the first record per unique combination**

```sql
WITH ranked_touchpoints AS (
    SELECT
        event_id,
        user_id,
        timestamp,
        channel_clean AS channel,
        dma_code,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, timestamp, channel_clean  -- define "duplicate"
            ORDER BY event_id ASC                           -- keep the earliest event_id
        ) AS row_num
    FROM standardized   -- output from Step 1 above
)
SELECT
    event_id,
    user_id,
    timestamp,
    channel,
    dma_code
FROM ranked_touchpoints
WHERE row_num = 1;   -- retain only the first record; all others are duplicates
```

**What `ROW_NUMBER()` is doing here:**

- `PARTITION BY user_id, timestamp, channel_clean` — groups rows that share the same user, time, and channel (these are duplicates)
- `ORDER BY event_id ASC` — within each group, rank the rows starting from the lowest event_id
- `WHERE row_num = 1` — keep only rank 1; everything else is a duplicate and gets discarded

**Verification — check the percentage of rows removed:**

```sql
SELECT
    total_before,
    total_after,
    ROUND((1 - total_after::NUMERIC / total_before) * 100, 2) AS pct_removed
FROM
    (SELECT COUNT(*) AS total_before FROM raw_user_touchpoints) a,
    (SELECT COUNT(*) AS total_after  FROM deduped_touchpoints)  b;
-- Expected: approximately 3% removed
```

---

### Problem 3: Post-Conversion Touchpoints

**Root cause:** Retargeting ads continue to serve after a user has already converted. If a user clicks a Meta ad two hours after purchasing, that click should not receive attribution credit.

```
Scenario:
  User U456 completes a purchase on 2026-03-20 at 10:00 AM
  User U456 clicks a Meta retargeting ad on 2026-03-20 at 2:00 PM
  → Including this post-purchase click in attribution implies the ad drove a purchase that already happened
```

**Fix: Apply a time boundary condition in the JOIN between touchpoints and conversions**

```sql
SELECT
    t.user_id,
    t.event_id,
    t.channel,
    t.timestamp           AS touchpoint_ts,
    c.conversion_id,
    c.converted_at        AS conversion_ts,
    c.order_value_usd
FROM deduped_touchpoints t
INNER JOIN raw_conversions c
    ON t.user_id = c.user_id
WHERE t.timestamp <= c.converted_at                          -- touchpoint must occur BEFORE conversion
    AND t.timestamp >= c.converted_at - INTERVAL '90 days'  -- attribution window: 90-day lookback
```

**What is an Attribution Window?**

> The attribution window defines how far back in time to look for touchpoints that might have influenced a conversion.
> Common windows: 7 days (short-term direct response), 30 days (standard), 90 days (longer consideration cycles).
> This project uses a 90-day window to capture the full research-to-purchase journey.

---

## Full Cleaning Pipeline (Chained CTEs)

```sql
WITH

-- Step 1: Standardize UTM fields and normalize channel names
standardized AS (
    SELECT
        event_id,
        user_id,
        timestamp,
        LOWER(TRIM(utm_source))   AS utm_source,
        LOWER(TRIM(utm_medium))   AS utm_medium,
        LOWER(TRIM(utm_campaign)) AS utm_campaign,
        CASE
            WHEN LOWER(TRIM(channel)) IN ('meta_paid_social', 'meta', 'facebook')
                THEN 'Meta_Paid_Social'
            WHEN LOWER(TRIM(channel)) IN ('google_search', 'google')
                THEN 'Google_Search'
            WHEN LOWER(TRIM(channel)) IN ('tiktok_ads', 'tiktok')
                THEN 'TikTok_Ads'
            ELSE INITCAP(TRIM(channel))
        END AS channel,
        dma_code
    FROM raw_user_touchpoints
),

-- Step 2: Remove duplicate events
deduped AS (
    SELECT * FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY user_id, timestamp, channel
                ORDER BY event_id ASC
            ) AS row_num
        FROM standardized
    ) t
    WHERE row_num = 1
),

-- Step 3: Join with conversions and apply attribution window
pre_conversion_touchpoints AS (
    SELECT
        t.user_id,
        t.event_id,
        t.channel,
        t.timestamp      AS touchpoint_ts,
        c.conversion_id,
        c.converted_at   AS conversion_ts,
        c.order_value_usd
    FROM deduped t
    INNER JOIN raw_conversions c
        ON t.user_id = c.user_id
    WHERE t.timestamp <= c.converted_at
        AND t.timestamp >= c.converted_at - INTERVAL '90 days'
)

-- Final cleaned and joined dataset
SELECT * FROM pre_conversion_touchpoints
ORDER BY user_id, touchpoint_ts;
```

---

## Data Quality Checklist After Cleaning

Run these checks before moving to attribution modeling. Each query should return the expected result shown.

```sql
-- 1. Confirm exactly 3 standard channel names exist
SELECT DISTINCT channel FROM pre_conversion_touchpoints;
-- Expected: Meta_Paid_Social, Google_Search, TikTok_Ads

-- 2. Confirm no touchpoints exist after the conversion timestamp
SELECT COUNT(*)
FROM pre_conversion_touchpoints
WHERE touchpoint_ts > conversion_ts;
-- Expected: 0

-- 3. Confirm no duplicate event_ids remain
SELECT event_id, COUNT(*)
FROM pre_conversion_touchpoints
GROUP BY event_id
HAVING COUNT(*) > 1;
-- Expected: 0 rows returned

-- 4. Check average touchpoints per user (should be 2–5 for a typical e-commerce funnel)
SELECT
    ROUND(AVG(touchpoint_count), 2) AS avg_touchpoints_per_user,
    MAX(touchpoint_count)            AS max_touchpoints
FROM (
    SELECT user_id, COUNT(*) AS touchpoint_count
    FROM pre_conversion_touchpoints
    GROUP BY user_id
) t;
```

---

## Key SQL Concepts Used in This Phase

| Concept                       | Why It Is Used Here                                             |
| ----------------------------- | --------------------------------------------------------------- |
| `LOWER()` / `TRIM()`          | Normalize UTM strings — removes case and whitespace noise       |
| `CASE WHEN`                   | Map variant channel names to a single canonical value           |
| `ROW_NUMBER()`                | Assign a rank within each group of duplicates                   |
| `PARTITION BY`                | Define the duplicate key: same user + timestamp + channel       |
| `INNER JOIN` with time filter | Enforce causal direction — touchpoint must precede conversion   |
| CTEs (`WITH` clauses)         | Separate each transformation step for readability and debugging |

---

## Next Step

The cleaned dataset is now ready for attribution modeling.
The next phase answers the question: across all the touchpoints that preceded a conversion, how much credit does each channel deserve?

→ [Phase 3: Attribution Modeling with SQL](./03_attribution_models_sql.md)
