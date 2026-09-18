-- [SYNTHETIC DATA] Performance by hook_type
-- Tablr AI Growth Operations Agent — Phase 5
-- Join fact_daily_performance with dim_creatives on creative_id
-- Metrics by hook_type: impressions, clicks, CTR, spend, trial_signups, trial_CAC
-- Weighted CTR aggregation: SUM(clicks)/SUM(impressions), not AVG of per-row ratios
-- Source: data/synthetic/fact_daily_performance.parquet + dim_creatives.parquet

SELECT
    dc.hook_type,
    SUM(f.impressions)                                                  AS impressions,
    SUM(f.clicks)                                                       AS clicks,
    ROUND(SUM(f.spend_usd), 2)                                         AS spend_usd,
    SUM(f.trial_signups)                                                AS trial_signups,
    ROUND(
        SUM(f.clicks) * 1.0 / NULLIF(SUM(f.impressions), 0),
        6
    )                                                                   AS ctr,
    ROUND(
        SUM(f.clicks) * 100.0 / NULLIF(SUM(f.impressions), 0),
        4
    )                                                                   AS ctr_pct,
    ROUND(
        SUM(f.spend_usd) * 1000.0 / NULLIF(SUM(f.impressions), 0),
        2
    )                                                                   AS cpm_usd,
    ROUND(
        SUM(f.spend_usd) / NULLIF(SUM(f.clicks), 0),
        2
    )                                                                   AS cpc_usd,
    ROUND(
        SUM(f.spend_usd) / NULLIF(SUM(f.trial_signups), 0),
        2
    )                                                                   AS trial_cac_usd
FROM read_parquet('data/synthetic/fact_daily_performance.parquet') f
JOIN read_parquet('data/synthetic/dim_creatives.parquet') dc
    ON f.creative_id = dc.creative_id
GROUP BY dc.hook_type
ORDER BY ctr DESC;
