/*
  stg_marketing_leads
  ====================
  Source: raw_marketing_leads

  Data quality handled here:
  - 12 leads with missing account_id → flagged with has_account = FALSE
    These are unmatched leads that cannot be linked to the CRM
  - Normalize lifecycle_stage to a consistent ordering value
  - Standardize channel names
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_marketing_leads') }}

)

SELECT
    lead_id,
    account_id,
    created_at::DATE AS lead_created_date,

    -- Normalize channel
    INITCAP(TRIM(channel))    AS channel,
    INITCAP(TRIM(lead_source)) AS lead_source,
    campaign,

    -- Normalize lifecycle stage
    CASE lifecycle_stage
        WHEN 'Lead'      THEN 'Lead'
        WHEN 'MQL'       THEN 'MQL'
        WHEN 'SQL'       THEN 'SQL'
        WHEN 'Converted' THEN 'Converted'
        ELSE 'Unknown'
    END AS lifecycle_stage,

    -- Numeric rank for funnel ordering (useful in window functions downstream)
    CASE lifecycle_stage
        WHEN 'Lead'      THEN 1
        WHEN 'MQL'       THEN 2
        WHEN 'SQL'       THEN 3
        WHEN 'Converted' THEN 4
        ELSE 0
    END AS lifecycle_stage_rank,

    segment,
    company_size,

    -- Data quality flags
    (account_id IS NOT NULL)                                    AS has_account,
    lifecycle_stage IN ('SQL', 'Converted')                     AS is_sales_qualified

FROM source
