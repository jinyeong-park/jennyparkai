/*
  stg_salesforce_accounts
  ========================
  Source: raw_salesforce_accounts

  Data quality handled here:
  - Duplicate account_ids (12 pairs baked into source data)
    → Keep the most recently created record per account_id using ROW_NUMBER()
  - Standardize segment and status values
  - Add is_duplicate flag before dedup for auditability
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_salesforce_accounts') }}

),

-- Flag duplicates before removing them so the issue is auditable downstream
flagged AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY account_created_at DESC  -- keep the most recent record
        ) AS row_num,

        COUNT(*) OVER (
            PARTITION BY account_id
        ) AS duplicate_count

    FROM source

),

deduped AS (

    SELECT * FROM flagged WHERE row_num = 1

)

SELECT
    account_id,
    account_name,
    company_size,

    -- Normalize segment to a controlled vocabulary
    CASE
        WHEN segment = 'SMB'         THEN 'SMB'
        WHEN segment = 'Mid-Market'  THEN 'Mid-Market'
        WHEN segment = 'Enterprise'  THEN 'Enterprise'
        ELSE 'Unknown'
    END AS segment,

    industry,
    sales_region,
    revenue_model,
    account_created_at::DATE AS account_created_date,
    account_status,

    -- Data quality flag: was this record duplicated in the source?
    (duplicate_count > 1) AS had_duplicate_in_source

FROM deduped
