-- [SYNTHETIC DATA] CPAO (Cost Per Activated Owner) by channel
-- Tablr AI Growth Operations Agent — Phase 5
-- CPAO = total_spend / activated_owners (where activation = CAMPAIGN_LAUNCHED within 14 days)
-- Compares: trial_CAC vs CPAO to reveal ranking reversal
-- Channels where CPAO ranking differs from trial_CAC ranking are key findings
-- Source: data/synthetic/fact_daily_performance.parquet + dim_trial_accounts.parquet
--         + fact_product_events.parquet

WITH signups AS (
    SELECT
        account_id,
        CAST(event_timestamp AS TIMESTAMP) AS signup_ts
    FROM read_parquet('data/synthetic/fact_product_events.parquet')
    WHERE event_type = 'TRIAL_SIGNUP'
),
activations AS (
    SELECT
        account_id,
        CAST(event_timestamp AS TIMESTAMP) AS activated_ts
    FROM read_parquet('data/synthetic/fact_product_events.parquet')
    WHERE event_type = 'CAMPAIGN_LAUNCHED'
),
activated_within_14d AS (
    SELECT DISTINCT s.account_id
    FROM signups s
    JOIN activations a ON s.account_id = a.account_id
    WHERE
        DATEDIFF('day', CAST(s.signup_ts AS DATE), CAST(a.activated_ts AS DATE)) >= 0
        AND DATEDIFF('day', CAST(s.signup_ts AS DATE), CAST(a.activated_ts AS DATE)) <= 14
),
trial_accts AS (
    SELECT account_id, channel
    FROM read_parquet('data/synthetic/dim_trial_accounts.parquet')
    WHERE NOT is_missing_attribution
),
activations_by_channel AS (
    SELECT
        t.channel,
        COUNT(DISTINCT t.account_id)    AS attributed_trials,
        COUNT(DISTINCT aw.account_id)   AS activated_owners
    FROM trial_accts t
    LEFT JOIN activated_within_14d aw ON t.account_id = aw.account_id
    GROUP BY t.channel
),
spend_by_channel AS (
    SELECT
        channel,
        ROUND(SUM(spend_usd), 2)        AS total_spend,
        SUM(trial_signups)              AS platform_trial_signups
    FROM read_parquet('data/synthetic/fact_daily_performance.parquet')
    GROUP BY channel
)
SELECT
    s.channel,
    s.total_spend,
    s.platform_trial_signups,
    ROUND(s.total_spend / NULLIF(s.platform_trial_signups, 0), 2) AS trial_cac_usd,
    a.attributed_trials,
    a.activated_owners,
    ROUND(s.total_spend / NULLIF(a.activated_owners, 0), 2)       AS cpao_usd,
    -- Rank columns show the reversal
    RANK() OVER (ORDER BY s.total_spend / NULLIF(s.platform_trial_signups, 0) ASC NULLS LAST) AS trial_cac_rank,
    RANK() OVER (ORDER BY s.total_spend / NULLIF(a.activated_owners, 0) ASC NULLS LAST)       AS cpao_rank
FROM spend_by_channel s
LEFT JOIN activations_by_channel a ON s.channel = a.channel
ORDER BY cpao_usd ASC NULLS LAST;
