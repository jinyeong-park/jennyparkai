-- [SYNTHETIC DATA] Activation funnel by channel
-- Tablr AI Growth Operations Agent — Phase 5
-- Join dim_trial_accounts with fact_product_events
-- Activation = CAMPAIGN_LAUNCHED event within 14 days of TRIAL_SIGNUP
-- Source: data/synthetic/dim_trial_accounts.parquet + fact_product_events.parquet

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
onboardings AS (
    SELECT
        account_id
    FROM read_parquet('data/synthetic/fact_product_events.parquet')
    WHERE event_type = 'ONBOARDING_COMPLETED'
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
    SELECT
        account_id,
        channel,
        is_missing_attribution
    FROM read_parquet('data/synthetic/dim_trial_accounts.parquet')
)
SELECT
    COALESCE(t.channel, 'UNKNOWN (missing attribution)')     AS channel,
    COUNT(DISTINCT t.account_id)                             AS trials,
    COUNT(DISTINCT ob.account_id)                            AS onboarding_completed,
    COUNT(DISTINCT aw.account_id)                            AS campaign_launched,
    ROUND(
        COUNT(DISTINCT ob.account_id) * 1.0
            / NULLIF(COUNT(DISTINCT t.account_id), 0),
        4
    )                                                        AS onboarding_rate,
    ROUND(
        COUNT(DISTINCT aw.account_id) * 1.0
            / NULLIF(COUNT(DISTINCT t.account_id), 0),
        4
    )                                                        AS activation_rate,
    COUNT(DISTINCT t.account_id)
        FILTER (WHERE t.is_missing_attribution)              AS missing_attribution_count,
    ROUND(
        COUNT(DISTINCT t.account_id)
            FILTER (WHERE t.is_missing_attribution) * 100.0
            / NULLIF(COUNT(DISTINCT t.account_id), 0),
        2
    )                                                        AS missing_attribution_pct
FROM trial_accts t
LEFT JOIN onboardings ob ON t.account_id = ob.account_id
LEFT JOIN activated_within_14d aw ON t.account_id = aw.account_id
GROUP BY t.channel
ORDER BY trials DESC;
