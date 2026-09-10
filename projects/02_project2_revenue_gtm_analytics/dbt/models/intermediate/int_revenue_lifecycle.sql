/*
  int_revenue_lifecycle
  =====================
  Connects Closed-Won Opportunities → Contracts → Billing Invoices to
  build the full revenue recognition chain.

  Problem this solves:
    - CRM bookings (opportunity amount) ≠ contract value ≠ billed amount ≠ collected cash.
    - Each gap has a legitimate business explanation (discounts, FX, payment failures).
    - This model makes all four numbers comparable at the account × opportunity level
      so the reconciliation analysis can explain the deltas.

  Key data quality handling:
    - Contracts: 4 duplicate contract_ids with conflicting values exist in source.
      Only canonical records (is_canonical_record = TRUE) flow into revenue calculations.
    - Billing: Multi-currency normalized to USD. Failed/pending payments are preserved
      so we can measure cash collection risk.
    - Opportunities without contracts (common for smaller deals) are included with NULL
      contract fields — they still represent recognized bookings.

  Used by:
    - fct_revenue (monthly/annual revenue reporting)
    - fct_bookings (bookings vs billings reconciliation)
    - Revenue reconciliation analysis (explains the 4 gaps)

  Key output columns:
    - crm_booking_amount     → opportunity.amount (what sales closed)
    - contract_value         → signed contract value (what legal agreed to)
    - total_billed_usd       → invoices sent (what billing charged)
    - total_collected_usd    → payments received (actual cash)
    - booking_to_contract_gap → crm_booking_amount - contract_value
    - contract_to_billing_gap → contract_value - total_billed_usd
    - billing_to_collected_gap → total_billed_usd - total_collected_usd
*/

WITH won_opps AS (
    SELECT
        opportunity_id,
        account_id,
        opportunity_name,
        opportunity_stage,
        amount                      AS crm_booking_amount,
        close_date,
        opportunity_created_at,
        days_open                   AS days_to_close
    FROM {{ ref('stg_salesforce_opportunities') }}
    WHERE is_won = TRUE
      AND is_orphan = FALSE
),

-- Canonical contracts only — drops the 4 duplicate records
contracts AS (
    SELECT
        contract_id,
        opportunity_id,
        account_id,
        contract_status,
        contract_value,
        contract_start_date,
        contract_end_date,
        contract_term_months,
        monthly_contract_value,
        has_duplicate_contract_id,
        is_canonical_record
    FROM {{ ref('stg_contracts') }}
    WHERE is_canonical_record = TRUE
),

-- Billing aggregated to contract level for the join chain
billing_contract_agg AS (
    SELECT
        contract_id,
        COUNT(DISTINCT invoice_id)      AS invoice_count,
        MIN(billing_date)               AS first_billing_date,
        MAX(billing_date)               AS last_billing_date,
        SUM(billing_amount_usd)         AS total_billed_usd,
        SUM(collected_amount_usd)       AS total_collected_usd,
        SUM(at_risk_amount_usd)         AS total_at_risk_usd,
        SUM(failed_amount_usd)          AS total_failed_usd,

        -- Currency mix (useful for FX risk reporting)
        COUNT(DISTINCT currency)        AS currency_count,
        MODE() WITHIN GROUP (ORDER BY currency) AS primary_currency,

        -- Payment status breakdown
        SUM(CASE WHEN is_paid    THEN 1 ELSE 0 END) AS paid_invoice_count,
        SUM(CASE WHEN is_pending THEN 1 ELSE 0 END) AS pending_invoice_count,
        SUM(CASE WHEN is_failed  THEN 1 ELSE 0 END) AS failed_invoice_count
    FROM {{ ref('stg_billing') }}
    GROUP BY contract_id
),

-- Also aggregate billing directly to opportunity level
-- (some invoices link to contracts that link to opps;
--  this handles the case where billing contract_id maps to the opp)
billing_opp_agg AS (
    SELECT
        c.opportunity_id,
        SUM(b.billing_amount_usd)   AS opp_total_billed_usd,
        SUM(b.collected_amount_usd) AS opp_total_collected_usd,
        SUM(b.failed_amount_usd)    AS opp_total_failed_usd
    FROM {{ ref('stg_billing') }} b
    INNER JOIN contracts c ON b.contract_id = c.contract_id
    GROUP BY c.opportunity_id
),

-- Core join: won_opps is the spine
revenue_chain AS (
    SELECT
        o.opportunity_id,
        o.account_id,
        o.opportunity_name,
        o.crm_booking_amount,
        o.close_date,
        o.opportunity_created_at,
        o.days_to_close,

        -- Contract fields (NULL if no contract exists for this won opp)
        c.contract_id,
        c.contract_status,
        c.contract_value,
        c.contract_start_date,
        c.contract_end_date,
        c.contract_term_months,
        c.monthly_contract_value,
        c.has_duplicate_contract_id,

        -- Billing fields (NULL if no invoices exist)
        COALESCE(b.invoice_count, 0)            AS invoice_count,
        b.first_billing_date,
        b.last_billing_date,
        COALESCE(b.total_billed_usd, 0)         AS total_billed_usd,
        COALESCE(b.total_collected_usd, 0)      AS total_collected_usd,
        COALESCE(b.total_at_risk_usd, 0)        AS total_at_risk_usd,
        COALESCE(b.total_failed_usd, 0)         AS total_failed_usd,
        COALESCE(b.paid_invoice_count, 0)       AS paid_invoice_count,
        COALESCE(b.pending_invoice_count, 0)    AS pending_invoice_count,
        COALESCE(b.failed_invoice_count, 0)     AS failed_invoice_count,
        b.primary_currency,
        COALESCE(b.currency_count, 0)           AS currency_count,

        -- Presence flags
        (c.contract_id IS NOT NULL)             AS has_contract,
        (b.invoice_count > 0)                   AS has_billing,
        (b.total_collected_usd > 0)             AS has_collected_revenue

    FROM won_opps o
    LEFT JOIN contracts             c ON o.opportunity_id = c.opportunity_id
    LEFT JOIN billing_contract_agg  b ON c.contract_id    = b.contract_id
)

SELECT
    opportunity_id,
    account_id,
    opportunity_name,
    close_date,
    opportunity_created_at,
    days_to_close,

    -- The 4 revenue numbers
    crm_booking_amount,
    COALESCE(contract_value, 0)     AS contract_value,
    total_billed_usd,
    total_collected_usd,

    -- Revenue chain presence
    has_contract,
    has_billing,
    has_collected_revenue,
    has_duplicate_contract_id,

    -- Contract details
    contract_id,
    contract_status,
    contract_start_date,
    contract_end_date,
    contract_term_months,
    monthly_contract_value,

    -- Billing details
    invoice_count,
    first_billing_date,
    last_billing_date,
    total_at_risk_usd,
    total_failed_usd,
    paid_invoice_count,
    pending_invoice_count,
    failed_invoice_count,
    primary_currency,
    currency_count,

    -- Gap analysis (the reconciliation numbers)
    -- Positive gap = CRM overstated vs next stage; Negative = understated
    crm_booking_amount - COALESCE(contract_value, 0)    AS booking_to_contract_gap,
    COALESCE(contract_value, 0) - total_billed_usd      AS contract_to_billing_gap,
    total_billed_usd - total_collected_usd              AS billing_to_collected_gap,

    -- End-to-end collection rate
    CASE
        WHEN crm_booking_amount > 0
        THEN ROUND(total_collected_usd / crm_booking_amount, 4)
    END                                                 AS cash_collection_rate,

    -- Contract coverage: what % of the booking is contracted
    CASE
        WHEN crm_booking_amount > 0
        THEN ROUND(COALESCE(contract_value, 0) / crm_booking_amount, 4)
    END                                                 AS contract_coverage_rate,

    -- Revenue stage classification
    CASE
        WHEN has_collected_revenue      THEN 'Collected'
        WHEN has_billing                THEN 'Billed'
        WHEN has_contract               THEN 'Contracted'
        ELSE 'Booking Only'
    END                                                 AS revenue_stage

FROM revenue_chain
