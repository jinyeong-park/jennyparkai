-- [SYNTHETIC DATA] Creative-level performance joined with dim_creatives
-- Tablr AI Growth Operations Agent — Phase 5
-- Metrics: impressions, clicks, spend, CTR, CPC, trial_signups, trial_CAC
-- Enriched with: hook_type, creative_format, persona_segment from dim_creatives
-- Sorted by spend DESC
-- Source: data/synthetic/fact_daily_performance.parquet + dim_creatives.parquet

SELECT
    f.creative_id,
    dc.channel,
    dc.hook_type,
    dc.creative_format,
    dc.persona_segment,
    SUM(f.impressions)                                                  AS impressions,
    SUM(f.clicks)                                                       AS clicks,
    ROUND(SUM(f.spend_usd), 2)                                         AS spend_usd,
    SUM(f.trial_signups)                                                AS trial_signups,
    ROUND(
        SUM(f.clicks) * 1.0 / NULLIF(SUM(f.impressions), 0),
        6
    )                                                                   AS ctr,
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
GROUP BY
    f.creative_id,
    dc.channel,
    dc.hook_type,
    dc.creative_format,
    dc.persona_segment
ORDER BY spend_usd DESC;
