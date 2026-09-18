-- [SYNTHETIC DATA] Channel-level media scorecard
-- Tablr AI Growth Operations Agent — Phase 5
-- Metrics: impressions, clicks, spend, CTR, CPM, CPC, trial_signups, trial_CAC
-- Weighted aggregation: SUM(clicks)/SUM(impressions), not AVG of per-row ratios
-- Zero denominators handled with NULLIF
-- Source: data/synthetic/fact_daily_performance.parquet

SELECT
    channel,
    SUM(impressions)                                                    AS impressions,
    SUM(clicks)                                                         AS clicks,
    ROUND(SUM(spend_usd), 2)                                           AS spend_usd,
    SUM(trial_signups)                                                  AS trial_signups,
    ROUND(
        SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0),
        6
    )                                                                   AS ctr,
    ROUND(
        SUM(spend_usd) * 1000.0 / NULLIF(SUM(impressions), 0),
        2
    )                                                                   AS cpm_usd,
    ROUND(
        SUM(spend_usd) / NULLIF(SUM(clicks), 0),
        2
    )                                                                   AS cpc_usd,
    ROUND(
        SUM(spend_usd) / NULLIF(SUM(trial_signups), 0),
        2
    )                                                                   AS trial_cac_usd
FROM read_parquet('data/synthetic/fact_daily_performance.parquet')
GROUP BY channel
ORDER BY spend_usd DESC;
