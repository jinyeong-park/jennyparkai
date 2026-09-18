/*
  fct_pipeline
  ============
  Open pipeline snapshot — one row per open opportunity with account context.

  Key questions this answers:
    - What is the total open pipeline by segment / region / stage?
    - Which deals are past their close date? How many times has the date slipped?
    - Which deals have gone stale (no activity in 30+ days)?
    - What is the weighted pipeline value (amount × win rate proxy by stage)?

  Grain: one row per open opportunity
  Materialized: table (refreshed on each dbt run — point-in-time snapshot)

  Note: this model shows only OPEN opportunities. For historical closed deals
  use fct_bookings. For combined pipeline + bookings use fct_customer_lifecycle.
*/

WITH opps AS (
    SELECT
        opportunity_id,
        account_id,
        opportunity_name,
        opportunity_stage,
        stage_order,
        amount,
        close_date,
        opportunity_created_at,
        days_open,
        days_past_due,
        days_since_last_activity,
        is_past_due,
        is_stale,
        has_repeated_slip,
        close_date_changes
    FROM {{ ref('stg_salesforce_opportunities') }}
    WHERE is_open = TRUE
      AND is_orphan = FALSE
),

accounts AS (
    SELECT
        account_id,
        account_name,
        segment,
        industry,
        region,
        revenue_model,
        lifecycle_tier
    FROM {{ ref('dim_account') }}
)

SELECT
    o.opportunity_id,
    o.account_id,
    a.account_name,
    a.segment,
    a.industry,
    a.region,
    a.revenue_model,
    a.lifecycle_tier,

    o.opportunity_name,
    o.opportunity_stage,
    o.stage_order,
    o.amount                        AS pipeline_amount,
    o.close_date,
    o.opportunity_created_at,

    -- Age and activity signals
    o.days_open,
    o.days_past_due,
    o.days_since_last_activity,
    o.close_date_changes,

    -- Risk flags
    o.is_past_due,
    o.is_stale,
    o.has_repeated_slip,

    -- Composite risk level
    CASE
        WHEN o.has_repeated_slip AND o.is_past_due  THEN 'High Risk'
        WHEN o.is_past_due OR o.is_stale            THEN 'Medium Risk'
        ELSE 'On Track'
    END                             AS pipeline_risk,

    -- Stage-based win rate proxy for weighted pipeline value
    -- These are industry-typical rates; replace with your actuals
    CASE o.opportunity_stage
        WHEN 'Prospecting'   THEN 0.05
        WHEN 'Qualification' THEN 0.15
        WHEN 'Proposal'      THEN 0.35
        WHEN 'Negotiation'   THEN 0.65
        ELSE 0.10
    END                             AS stage_win_rate,

    -- Weighted pipeline (amount × stage win rate)
    ROUND(
        o.amount * CASE o.opportunity_stage
            WHEN 'Prospecting'   THEN 0.05
            WHEN 'Qualification' THEN 0.15
            WHEN 'Proposal'      THEN 0.35
            WHEN 'Negotiation'   THEN 0.65
            ELSE 0.10
        END,
    2)                              AS weighted_pipeline_amount,

    CURRENT_DATE                    AS snapshot_date

FROM opps o
LEFT JOIN accounts a ON o.account_id = a.account_id
