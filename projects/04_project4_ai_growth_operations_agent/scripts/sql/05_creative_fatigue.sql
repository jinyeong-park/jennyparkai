-- [SYNTHETIC DATA] Creative fatigue detection
-- Tablr AI Growth Operations Agent — Phase 5
-- For each creative_id, compute weekly CTR (week_num relative to dataset start)
-- Flag creatives where CTR in week 3+ drops more than 25% from peak CTR
-- Source: data/synthetic/fact_daily_performance.parquet + dim_creatives.parquet

WITH min_date AS (
    SELECT MIN(CAST(date AS DATE)) AS start_date
    FROM read_parquet('data/synthetic/fact_daily_performance.parquet')
),
daily_with_week AS (
    SELECT
        f.creative_id,
        f.channel,
        CAST(
            DATEDIFF('day', m.start_date, CAST(f.date AS DATE)) / 7
        AS INTEGER)                 AS week_num,
        f.clicks,
        f.impressions
    FROM read_parquet('data/synthetic/fact_daily_performance.parquet') f
    CROSS JOIN min_date m
),
weekly_ctr AS (
    SELECT
        creative_id,
        channel,
        week_num,
        SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0) AS ctr
    FROM daily_with_week
    GROUP BY creative_id, channel, week_num
),
peak AS (
    SELECT
        creative_id,
        MAX(ctr)                    AS peak_ctr,
        MAX_BY(week_num, ctr)       AS peak_ctr_week
    FROM weekly_ctr
    GROUP BY creative_id
),
latest AS (
    SELECT
        creative_id,
        MAX_BY(ctr, week_num)       AS latest_ctr,
        MAX(week_num)               AS latest_week
    FROM weekly_ctr
    GROUP BY creative_id
),
enriched AS (
    SELECT
        p.creative_id,
        dc.channel,
        dc.hook_type,
        p.peak_ctr_week,
        p.peak_ctr,
        l.latest_ctr,
        l.latest_week,
        ROUND((p.peak_ctr - l.latest_ctr) / NULLIF(p.peak_ctr, 0), 4) AS ctr_drop_pct,
        l.latest_week >= 3
            AND (p.peak_ctr - l.latest_ctr) / NULLIF(p.peak_ctr, 0) > 0.25  AS fatigue_flag
    FROM peak p
    JOIN latest l ON p.creative_id = l.creative_id
    JOIN read_parquet('data/synthetic/dim_creatives.parquet') dc
        ON p.creative_id = dc.creative_id
)
SELECT
    creative_id,
    channel,
    hook_type,
    peak_ctr_week,
    ROUND(peak_ctr * 100, 4)        AS peak_ctr_pct,
    ROUND(latest_ctr * 100, 4)      AS latest_ctr_pct,
    latest_week,
    ROUND(ctr_drop_pct * 100, 2)    AS ctr_drop_pct,
    fatigue_flag
FROM enriched
WHERE latest_week >= 3
ORDER BY ctr_drop_pct DESC;
