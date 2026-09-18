-- [SYNTHETIC DATA] Monthly cohort retention
-- For each cohort_month × channel:
--   subscribers, M1 retained, M3 retained, M6 retained (only if mature)
--
-- maturity_reference_date = '2026-09-13'
-- M1: churn_date IS NULL OR churn_date > conversion_date + 30 days
-- M3: churn_date IS NULL OR churn_date > conversion_date + 90 days
-- M6: (same logic) AND (conversion_date + 180 days <= DATE '2026-09-13')
--
-- Right-censoring: M6 is only counted for subscriptions that have been
-- observable for >= 180 days as of the maturity reference date.
-- March 2026 cohorts are NOT fully mature for M6.
-- Immature M6 cohorts are flagged via m6_eligible < subscribers.

WITH subs AS (
    SELECT
        s.subscription_id,
        s.account_id,
        CAST(s.conversion_date AS DATE)                AS conv_date,
        CAST(s.churn_date AS DATE)                     AS churn_dt,
        s.status,
        COALESCE(d.channel, 'UNKNOWN')                 AS channel,
        COALESCE(d.persona_segment, 'UNKNOWN')         AS persona_segment,
        strftime(CAST(s.conversion_date AS DATE), '%Y-%m') AS cohort_month
    FROM fact_subscriptions s
    LEFT JOIN dim_trial_accounts d ON s.account_id = d.account_id
),

cohort_retention AS (
    SELECT
        channel,
        cohort_month,
        COUNT(*)                                       AS subscribers,

        -- M1: still active OR churn happened after 30 days
        SUM(CASE
            WHEN status = 'active' OR churn_dt > conv_date + 30
            THEN 1 ELSE 0
        END)                                           AS m1_retained,

        -- M3: still active OR churn happened after 90 days
        SUM(CASE
            WHEN status = 'active' OR churn_dt > conv_date + 90
            THEN 1 ELSE 0
        END)                                           AS m3_retained,

        -- M6 retained (only for mature subscriptions)
        SUM(CASE
            WHEN (status = 'active' OR churn_dt > conv_date + 180)
                 AND conv_date + 180 <= DATE '2026-09-13'
            THEN 1 ELSE 0
        END)                                           AS m6_retained,

        -- Count of subscriptions eligible (mature) for M6 measurement
        SUM(CASE
            WHEN conv_date + 180 <= DATE '2026-09-13'
            THEN 1 ELSE 0
        END)                                           AS m6_eligible,

        -- Flag: True when all subs in cohort are M6 mature
        (SUM(CASE
            WHEN conv_date + 180 <= DATE '2026-09-13'
            THEN 1 ELSE 0
        END) = COUNT(*))                               AS cohort_m6_fully_mature
    FROM subs
    GROUP BY channel, cohort_month
)

SELECT
    channel,
    cohort_month,
    subscribers,
    m1_retained,
    m3_retained,
    m6_eligible,
    m6_retained,

    -- Rates
    m1_retained * 1.0 / NULLIF(subscribers, 0)             AS m1_rate,
    m3_retained * 1.0 / NULLIF(subscribers, 0)             AS m3_rate,
    -- M6 rate uses mature-cohort denominator only
    m6_retained * 1.0 / NULLIF(m6_eligible, 0)             AS m6_rate_mature_only,

    cohort_m6_fully_mature,

    -- Human-readable maturity warning
    CASE
        WHEN cohort_m6_fully_mature THEN 'M6 mature'
        WHEN m6_eligible = 0        THEN 'M6 immature — no eligible subs'
        ELSE 'M6 partially mature (' || m6_eligible || '/' || subscribers || ' eligible)'
    END                                                     AS m6_maturity_note

FROM cohort_retention
ORDER BY channel, cohort_month;
