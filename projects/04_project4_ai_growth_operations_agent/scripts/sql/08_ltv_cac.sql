-- [SYNTHETIC DATA] LTV:CAC and payback by channel
--
-- observed_ltv = SUM(revenue_events.amount_usd) per subscriber, averaged by channel
-- cpao         = SUM(spend) / COUNT(activated_owners) per channel
-- ltv_cac      = observed_avg_ltv / cpao
-- payback_months = cpao / avg_monthly_price
--
-- Both trial_CAC ranking and CPAO ranking are shown to highlight reversal:
-- a channel that looks cheap by trial_CAC may be expensive by CPAO
-- (i.e., it drives many signups but few who reach the activation milestone).
--
-- Activation = CAMPAIGN_LAUNCHED within 14 days of TRIAL_SIGNUP
-- Maturity note: Observed LTV covers only ~2-3 months of revenue (short simulation).

WITH

-- Step 1: Activated owners per channel
trial_dates AS (
    SELECT account_id, CAST(event_timestamp AS DATE) AS signup_date
    FROM fact_product_events
    WHERE event_type = 'TRIAL_SIGNUP'
),
campaign_launches AS (
    SELECT account_id, CAST(event_timestamp AS DATE) AS launch_date
    FROM fact_product_events
    WHERE event_type = 'CAMPAIGN_LAUNCHED'
),
activated AS (
    SELECT DISTINCT t.account_id
    FROM trial_dates t
    JOIN campaign_launches c ON t.account_id = c.account_id
    WHERE c.launch_date - t.signup_date <= 14
),
activated_by_channel AS (
    SELECT
        COALESCE(d.channel, 'UNKNOWN') AS channel,
        COUNT(DISTINCT a.account_id)   AS activated_owners
    FROM activated a
    LEFT JOIN dim_trial_accounts d ON a.account_id = d.account_id
    GROUP BY COALESCE(d.channel, 'UNKNOWN')
),

-- Step 2: Media spend and trial CAC per channel
channel_spend AS (
    SELECT
        channel,
        SUM(spend_usd)    AS total_spend,
        SUM(trial_signups) AS total_trials
    FROM fact_daily_performance
    GROUP BY channel
),

-- Step 3: CPAO and trial CAC
channel_efficiency AS (
    SELECT
        cs.channel,
        cs.total_spend,
        cs.total_trials,
        ac.activated_owners,
        cs.total_spend / NULLIF(cs.total_trials, 0)       AS trial_cac,
        cs.total_spend / NULLIF(ac.activated_owners, 0)   AS cpao
    FROM channel_spend cs
    LEFT JOIN activated_by_channel ac ON cs.channel = ac.channel
),

-- Step 4: Observed LTV per subscriber (account-level revenue sum)
account_revenue AS (
    SELECT account_id, SUM(amount_usd) AS total_rev
    FROM fact_revenue_events
    GROUP BY account_id
),
subscriber_ltv AS (
    SELECT
        COALESCE(d.channel, 'UNKNOWN')   AS channel,
        COUNT(DISTINCT s.account_id)     AS subscribers,
        AVG(s.monthly_price_usd)         AS avg_monthly_price_usd,
        AVG(COALESCE(r.total_rev, 0))    AS observed_avg_ltv_usd,
        SUM(CASE WHEN s.status = 'churned' THEN 1 ELSE 0 END) * 1.0
            / NULLIF(COUNT(*), 0)        AS estimated_churn_rate
    FROM fact_subscriptions s
    LEFT JOIN dim_trial_accounts d ON s.account_id = d.account_id
    LEFT JOIN account_revenue r    ON s.account_id = r.account_id
    GROUP BY COALESCE(d.channel, 'UNKNOWN')
),

-- Step 5: Projected LTV = avg_monthly_price / churn_rate (constant churn model)
ltv_projected AS (
    SELECT
        channel,
        subscribers,
        avg_monthly_price_usd,
        observed_avg_ltv_usd,
        estimated_churn_rate,
        avg_monthly_price_usd / NULLIF(estimated_churn_rate, 0) AS projected_ltv_usd
    FROM subscriber_ltv
),

-- Step 6: Rankings
trial_cac_ranked AS (
    SELECT channel, trial_cac,
           ROW_NUMBER() OVER (ORDER BY trial_cac ASC)  AS trial_cac_rank  -- lower is better
    FROM channel_efficiency
    WHERE trial_cac IS NOT NULL
),
cpao_ranked AS (
    SELECT channel, cpao,
           ROW_NUMBER() OVER (ORDER BY cpao ASC)       AS cpao_rank        -- lower is better
    FROM channel_efficiency
    WHERE cpao IS NOT NULL
),
ltv_ranked AS (
    SELECT channel, observed_avg_ltv_usd,
           ROW_NUMBER() OVER (ORDER BY observed_avg_ltv_usd DESC) AS ltv_rank  -- higher is better
    FROM ltv_projected
    WHERE observed_avg_ltv_usd IS NOT NULL
)

-- Final output: channel efficiency × LTV with ranking comparison
SELECT
    lp.channel,
    lp.subscribers,
    lp.avg_monthly_price_usd,
    lp.observed_avg_ltv_usd,
    lp.estimated_churn_rate,
    lp.projected_ltv_usd,
    ce.total_spend,
    ce.total_trials,
    ce.activated_owners,
    ce.trial_cac,
    ce.cpao,

    -- LTV:CAC ratios
    lp.observed_avg_ltv_usd / NULLIF(ce.cpao, 0)     AS ltv_cac_observed,
    lp.projected_ltv_usd    / NULLIF(ce.cpao, 0)     AS ltv_cac_projected,

    -- Payback
    ce.cpao / NULLIF(lp.avg_monthly_price_usd, 0)    AS payback_months,

    -- Rankings
    tr.trial_cac_rank,
    cr.cpao_rank,
    lr.ltv_rank,

    -- Ranking reversal flag (trial_CAC rank vs CPAO rank)
    CASE
        WHEN tr.trial_cac_rank != cr.cpao_rank THEN TRUE
        ELSE FALSE
    END                                               AS trial_vs_cpao_reversal,

    -- Ranking reversal flag (CPAO rank vs LTV rank)
    CASE
        WHEN cr.cpao_rank != lr.ltv_rank THEN TRUE
        ELSE FALSE
    END                                               AS cpao_vs_ltv_reversal,

    -- Data provenance
    'SYNTHETIC'                                       AS data_origin,
    'Observed LTV covers ~2-3 months only (short simulation)'
                                                      AS ltv_observation_note

FROM ltv_projected lp
LEFT JOIN channel_efficiency ce  ON lp.channel = ce.channel
LEFT JOIN trial_cac_ranked   tr  ON lp.channel = tr.channel
LEFT JOIN cpao_ranked        cr  ON lp.channel = cr.channel
LEFT JOIN ltv_ranked         lr  ON lp.channel = lr.channel
ORDER BY lp.observed_avg_ltv_usd DESC;
