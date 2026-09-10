/*
  stg_contracts
  ==============
  Source: raw_contracts

  Data quality handled here:
  - 4 duplicate contract_ids with slightly different values (reconciliation issue)
    → Flag them; do NOT silently drop. The downstream reconciliation model explains the gap.
  - Calculate contract term length and monthly value
  - Add contract health flags
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_contracts') }}

),

flagged AS (

    SELECT
        *,
        COUNT(*) OVER (PARTITION BY contract_id) AS duplicate_count,

        -- If duplicated, rank by contract_value DESC to identify the canonical record
        ROW_NUMBER() OVER (
            PARTITION BY contract_id
            ORDER BY contract_value DESC
        ) AS dup_row_num

    FROM source

)

SELECT
    contract_id,
    account_id,
    opportunity_id,
    contract_date::DATE  AS contract_date,
    start_date::DATE     AS contract_start_date,
    end_date::DATE       AS contract_end_date,
    contract_value,
    revenue_model,
    contract_status,

    -- Contract term in days and months
    (end_date::DATE - start_date::DATE)         AS contract_term_days,
    (end_date::DATE - start_date::DATE) / 30.0  AS contract_term_months,

    -- Monthly recurring value (for subscription analysis)
    CASE
        WHEN (end_date::DATE - start_date::DATE) > 0
        THEN ROUND(contract_value / ((end_date::DATE - start_date::DATE) / 30.0), 2)
        ELSE contract_value
    END AS monthly_contract_value,

    -- Contract health
    contract_status = 'Active'    AS is_active,
    contract_status = 'Cancelled' AS is_cancelled,
    contract_status = 'Amended'   AS is_amended,

    -- Is this contract currently in its term?
    (CURRENT_DATE BETWEEN start_date::DATE AND end_date::DATE) AS is_in_term,

    -- Data quality flags
    (duplicate_count > 1)  AS has_duplicate_contract_id,
    (dup_row_num = 1)      AS is_canonical_record  -- TRUE for the record we keep in reconciliation

FROM flagged
