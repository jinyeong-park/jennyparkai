/*
  fct_customer_lifecycle
  ======================
  Full B2B lifecycle view — one row per account showing the complete journey
  from first marketing touch through revenue collection and retention.

  This is the "single source of truth" model that connects every stage:
    Lead → MQL → SQL → Opportunity → Contract → Billing → Revenue → Retention

  Key questions this answers:
    - What is the average lead-to-close velocity by segment?
    - Which accounts are churned vs. at risk vs. healthy?
    - How does customer health correlate with expansion revenue?
    - What % of accounts have complete data across all 4 systems?

  Grain: one row per account_id
  Materialized: table
*/

WITH identity AS (
    SELECT * FROM {{ ref('int_customer_identity_map') }}
),

gtm AS (
    SELECT
        account_id,
        first_lead_date,
        last_lead_date,
        primary_lead_source,
        lead_count,
        sql_lead_count,
        max_lead_stage,
        opp_count,
        won_opp_count,
        lost_opp_count,
        open_opp_count,
        total_won_amount,
        total_pipeline_amount,
        first_opp_created_at,
        first_won_opp_at,
        has_lead,
        has_opportunity,
        has_won_opportunity,
        lead_to_opp_days,
        opp_to_close_days,
        funnel_stage
    FROM {{ ref('int_gtm_funnel') }}
),

revenue AS (
    SELECT
        account_id,
        MIN(close_date)                         AS first_close_date,
        SUM(crm_booking_amount)                 AS total_crm_bookings,
        SUM(contract_value)                     AS total_contract_value,
        SUM(total_billed_usd)                   AS total_billed_usd,
        SUM(total_collected_usd)                AS total_collected_usd,
        SUM(total_failed_usd)                   AS total_failed_usd,
        COUNT(DISTINCT contract_id)             AS contract_count,
        BOOL_OR(has_contract)                   AS has_any_contract,
        BOOL_OR(has_billing)                    AS has_any_billing,
        BOOL_OR(has_duplicate_contract_id)      AS had_duplicate_contract
    FROM {{ ref('int_revenue_lifecycle') }}
    GROUP BY account_id
),

accounts AS (
    SELECT
        account_id,
        account_name,
        segment,
        industry,
        region,
        revenue_model,
        lifecycle_tier,
        account_created_at
    FROM {{ ref('dim_account') }}
)

SELECT
    a.account_id,
    a.account_name,
    a.segment,
    a.industry,
    a.region,
    a.revenue_model,
    a.lifecycle_tier,
    a.account_created_at,

    -- System coverage (from identity map)
    i.systems_present,
    i.is_in_crm,
    i.is_in_marketing,
    i.is_in_billing,
    i.is_in_customer_success,

    -- Marketing funnel (from GTM model)
    g.lead_count,
    g.sql_lead_count,
    g.first_lead_date,
    g.last_lead_date,
    g.primary_lead_source,
    g.max_lead_stage,

    -- Opportunity metrics (from GTM model)
    g.opp_count,
    g.won_opp_count,
    g.lost_opp_count,
    g.open_opp_count,
    g.total_pipeline_amount,
    g.first_opp_created_at,
    g.first_won_opp_at,
    g.has_lead,
    g.has_opportunity,
    g.has_won_opportunity,
    g.funnel_stage,

    -- Velocity metrics
    g.lead_to_opp_days,
    g.opp_to_close_days,
    -- Full lifecycle velocity: first lead to first close
    CASE
        WHEN g.first_lead_date IS NOT NULL AND r.first_close_date IS NOT NULL
        THEN (r.first_close_date - g.first_lead_date)
    END                                         AS lead_to_close_days,

    -- Revenue chain (from lifecycle model)
    r.first_close_date,
    COALESCE(r.total_crm_bookings, 0)           AS total_crm_bookings,
    COALESCE(r.total_contract_value, 0)         AS total_contract_value,
    COALESCE(r.total_billed_usd, 0)             AS total_billed_usd,
    COALESCE(r.total_collected_usd, 0)          AS total_collected_usd,
    COALESCE(r.total_failed_usd, 0)             AS total_failed_usd,
    COALESCE(r.contract_count, 0)               AS contract_count,
    COALESCE(r.has_any_contract, FALSE)         AS has_any_contract,
    COALESCE(r.has_any_billing, FALSE)          AS has_any_billing,
    COALESCE(r.had_duplicate_contract, FALSE)   AS had_duplicate_contract,

    -- Customer success (from identity map, sourced from stg_customer_success)
    i.customer_health_score,
    i.health_tier,
    i.renewal_status,
    i.is_churned,
    i.has_expansion,
    i.expansion_amount,

    -- NRR building blocks (account-level)
    -- Aggregate monthly: (retained + expansion - churn) / starting
    CASE
        WHEN i.is_churned                       THEN 'Churned'
        WHEN i.has_expansion AND NOT i.is_churned THEN 'Expansion'
        WHEN COALESCE(r.total_collected_usd, 0) > 0 THEN 'Retained'
        ELSE 'No Revenue'
    END                                         AS nrr_category,

    -- Lifecycle completeness: how far through the B2B funnel did this account get?
    CASE
        WHEN i.is_churned                               THEN '6 - Churned'
        WHEN i.has_expansion                            THEN '5 - Expansion'
        WHEN COALESCE(r.total_collected_usd, 0) > 0    THEN '4 - Paying Customer'
        WHEN COALESCE(r.has_any_contract, FALSE)        THEN '3 - Contracted'
        WHEN g.has_won_opportunity                      THEN '2 - Closed-Won'
        WHEN g.has_opportunity                          THEN '1 - In Pipeline'
        ELSE '0 - Pre-Pipeline'
    END                                         AS lifecycle_completeness

FROM accounts a
LEFT JOIN identity i ON a.account_id = i.account_id
LEFT JOIN gtm     g ON a.account_id = g.account_id
LEFT JOIN revenue r ON a.account_id = r.account_id
