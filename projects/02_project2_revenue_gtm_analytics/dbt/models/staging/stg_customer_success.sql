/*
  stg_customer_success
  =====================
  Source: raw_customer_success

  Adds health tiers and churn/expansion flags used in
  fct_customer_lifecycle and NRR calculations.
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_customer_success') }}

)

SELECT
    account_id,
    customer_health_score,
    renewal_date::DATE AS renewal_date,
    renewal_status,
    expansion_amount,
    churn_reason,

    -- Health tier classification
    -- Mirrors the thresholds used in the data generator
    CASE
        WHEN customer_health_score >= 70 THEN 'Healthy'
        WHEN customer_health_score >= 35 THEN 'Needs Attention'
        WHEN customer_health_score >  0  THEN 'At Risk'
        ELSE 'Unknown'
    END AS health_tier,

    -- Renewal flags
    renewal_status = 'Healthy'         AS is_healthy,
    renewal_status = 'At Risk'         AS is_at_risk,
    renewal_status = 'Needs Attention' AS needs_attention,
    renewal_status = 'Churned'         AS is_churned,

    -- Expansion flag
    (expansion_amount > 0)             AS has_expansion,

    -- Days until renewal (positive = upcoming, negative = overdue)
    (renewal_date::DATE - CURRENT_DATE) AS days_to_renewal

FROM source
