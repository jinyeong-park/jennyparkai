/*
  fct_revenue
  ===========
  Monthly billing-level revenue grain — one row per invoice.
  This is the lowest-level revenue fact, used for time-series revenue analysis.

  Key questions this answers:
    - What is monthly recurring revenue (MRR) trend?
    - How much revenue is collected vs. at risk vs. failed each month?
    - Which segments / regions drive the most revenue?
    - What is the rolling 12-month NRR (Net Revenue Retention)?

  NRR components surfaced in this model:
    - Starting revenue (existing customer billings)
    - Expansion revenue (has_expansion accounts)
    - Churned revenue (is_churned accounts)
    NRR = (Starting + Expansion - Churn) / Starting

  Grain: one row per invoice (billing_date × invoice_id)
  Materialized: table
*/

WITH billing AS (
    SELECT
        invoice_id,
        customer_id             AS account_id,
        contract_id,
        billing_date,
        billing_year,
        billing_month,
        billing_amount,
        currency,
        fx_rate_to_usd,
        billing_amount_usd,
        payment_status,
        is_paid,
        is_pending,
        is_failed,
        collected_amount_usd,
        at_risk_amount_usd,
        failed_amount_usd
    FROM {{ ref('stg_billing') }}
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
        is_churned,
        has_expansion,
        expansion_amount,
        health_tier,
        renewal_status
    FROM {{ ref('dim_account') }}
),

contracts AS (
    SELECT
        contract_id,
        opportunity_id,
        contract_status,
        contract_term_months,
        monthly_contract_value
    FROM {{ ref('stg_contracts') }}
    WHERE is_canonical_record = TRUE
)

SELECT
    b.invoice_id,
    b.account_id,
    a.account_name,
    a.segment,
    a.industry,
    a.region,
    a.revenue_model,
    a.lifecycle_tier,
    a.health_tier,
    a.renewal_status,

    -- Contract link
    b.contract_id,
    c.contract_status,
    c.contract_term_months,
    c.monthly_contract_value,

    -- Time dimensions
    b.billing_date,
    b.billing_year,
    b.billing_month,

    -- Revenue amounts
    b.billing_amount,
    b.currency,
    b.fx_rate_to_usd,
    b.billing_amount_usd,

    -- Collectability breakdown
    b.payment_status,
    b.is_paid,
    b.is_pending,
    b.is_failed,
    b.collected_amount_usd,
    b.at_risk_amount_usd,
    b.failed_amount_usd,

    -- NRR classification (per invoice)
    -- Used to bucket revenue into: New, Expansion, Retained, Churned
    CASE
        WHEN a.is_churned                           THEN 'Churned'
        WHEN a.has_expansion AND a.is_churned = FALSE THEN 'Expansion'
        ELSE 'Retained'
    END                                             AS nrr_category,

    -- Revenue type by contract model
    CASE a.revenue_model
        WHEN 'Subscription' THEN 'Recurring'
        WHEN 'Usage-Based'  THEN 'Variable'
        WHEN 'One-Time'     THEN 'Non-Recurring'
        ELSE 'Other'
    END                                             AS revenue_type,

    -- Risk flag: invoice is billable but at risk of not being collected
    (b.is_pending OR b.is_failed)                   AS is_revenue_at_risk

FROM billing b
LEFT JOIN accounts  a ON b.account_id  = a.account_id
LEFT JOIN contracts c ON b.contract_id = c.contract_id
