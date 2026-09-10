/*
  stg_salesforce_opportunities
  =============================
  Source: raw_salesforce_opportunities

  Data quality handled here:
  - 9 orphan opportunities (account_id = 'ACC_ORPHAN_*') → flagged, not dropped
    These are included so downstream models can report on unmatched pipeline
  - Add pipeline health signals as calculated fields:
      days_open, days_past_due, is_stale, is_at_risk
  - Normalize opportunity stage to a controlled vocabulary
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_salesforce_opportunities') }}

)

SELECT
    opportunity_id,
    account_id,
    owner_id,
    created_at::DATE          AS opportunity_created_date,
    expected_close_date::DATE AS expected_close_date,
    actual_close_date::DATE   AS actual_close_date,
    last_activity_at::DATE    AS last_activity_date,

    -- Normalize stage
    CASE opportunity_stage
        WHEN 'Prospecting'  THEN 'Prospecting'
        WHEN 'Qualification'THEN 'Qualification'
        WHEN 'Proposal'     THEN 'Proposal'
        WHEN 'Negotiation'  THEN 'Negotiation'
        WHEN 'Closed-Won'   THEN 'Closed-Won'
        WHEN 'Closed-Lost'  THEN 'Closed-Lost'
        ELSE 'Unknown'
    END AS opportunity_stage,

    -- Stage ordering for funnel analysis
    CASE opportunity_stage
        WHEN 'Prospecting'   THEN 1
        WHEN 'Qualification' THEN 2
        WHEN 'Proposal'      THEN 3
        WHEN 'Negotiation'   THEN 4
        WHEN 'Closed-Won'    THEN 5
        WHEN 'Closed-Lost'   THEN 5
        ELSE 0
    END AS stage_order,

    amount,
    sales_region,
    segment,
    revenue_model,
    lead_source,
    close_date_changes,

    -- Status flags
    opportunity_stage IN ('Closed-Won', 'Closed-Lost') AS is_closed,
    opportunity_stage = 'Closed-Won'                   AS is_won,
    opportunity_stage = 'Closed-Lost'                  AS is_lost,
    opportunity_stage NOT IN ('Closed-Won','Closed-Lost') AS is_open,

    -- Pipeline health signals (calculated relative to expected close date)
    -- Using CURRENT_DATE in production; for this dataset we use the data end date
    GREATEST(0,
        CURRENT_DATE - expected_close_date::DATE
    )                                                   AS days_past_due,

    CURRENT_DATE - created_at::DATE                     AS days_open,

    CURRENT_DATE - last_activity_at::DATE               AS days_since_last_activity,

    -- At-risk flags for pipeline_analysis.py and fct_pipeline
    (opportunity_stage NOT IN ('Closed-Won','Closed-Lost')
        AND expected_close_date::DATE < CURRENT_DATE)   AS is_past_due,

    (CURRENT_DATE - last_activity_at::DATE > 60
        AND opportunity_stage NOT IN ('Closed-Won','Closed-Lost'))
                                                        AS is_stale,

    (close_date_changes >= 2)                           AS has_repeated_slip,

    -- Data quality flag
    account_id LIKE 'ACC_ORPHAN%'                       AS is_orphan

FROM source
