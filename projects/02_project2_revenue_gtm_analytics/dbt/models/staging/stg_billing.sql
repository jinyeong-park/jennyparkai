/*
  stg_billing
  ============
  Source: raw_billing

  Data quality handled here:
  - Multi-currency (USD / EUR / GBP) → normalize to USD using static FX rates
    In production this would use a live FX rates table
  - Payment status breakdown → add boolean flags for easy filtering
  - Small amount mismatches vs contracts are preserved (not corrected here)
    The reconciliation model explains the gap
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_billing') }}

),

-- Static FX rates (approximate as of 2025)
-- In production: JOIN to a dim_fx_rates table keyed on billing_date
fx_normalized AS (

    SELECT
        *,
        CASE currency
            WHEN 'USD' THEN 1.00
            WHEN 'EUR' THEN 1.08
            WHEN 'GBP' THEN 1.27
            ELSE 1.00
        END AS fx_rate_to_usd

    FROM source

)

SELECT
    invoice_id,
    customer_id,      -- this is account_id in the billing system
    contract_id,
    billing_date::DATE AS billing_date,
    EXTRACT(YEAR  FROM billing_date::DATE)::INT AS billing_year,
    EXTRACT(MONTH FROM billing_date::DATE)::INT AS billing_month,

    billing_amount,
    currency,
    fx_rate_to_usd,
    ROUND(billing_amount * fx_rate_to_usd, 2) AS billing_amount_usd,

    payment_status,

    -- Payment flags
    payment_status = 'Paid'    AS is_paid,
    payment_status = 'Pending' AS is_pending,
    payment_status = 'Failed'  AS is_failed,

    -- Revenue collectability
    CASE payment_status
        WHEN 'Paid'    THEN ROUND(billing_amount * fx_rate_to_usd, 2)
        ELSE 0
    END AS collected_amount_usd,

    CASE payment_status
        WHEN 'Pending' THEN ROUND(billing_amount * fx_rate_to_usd, 2)
        ELSE 0
    END AS at_risk_amount_usd,

    CASE payment_status
        WHEN 'Failed'  THEN ROUND(billing_amount * fx_rate_to_usd, 2)
        ELSE 0
    END AS failed_amount_usd

FROM fx_normalized
