/*
  fct_bookings
  ============
  Bookings-to-cash reconciliation — one row per closed-won opportunity
  showing the full revenue chain from CRM booking to collected cash.

  Key questions this answers:
    - What is the total bookings number vs. what was actually contracted?
    - How much of contracted revenue has been invoiced? Collected?
    - Which deals are booked but never contracted (billing gap risk)?
    - What is the average discount between CRM amount and contract value?

  Revenue chain:
    CRM Booking → Contract → Invoice → Collected Cash
       ↓ gap          ↓ gap      ↓ gap
   (discount)   (timing/billing)  (payment failure)

  Grain: one row per closed-won opportunity
  Materialized: table
*/

WITH lifecycle AS (
    SELECT * FROM {{ ref('int_revenue_lifecycle') }}
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
    l.opportunity_id,
    l.account_id,
    a.account_name,
    a.segment,
    a.industry,
    a.region,
    a.revenue_model,
    a.lifecycle_tier,

    l.opportunity_name,
    l.close_date,
    EXTRACT(YEAR  FROM l.close_date)::INT   AS close_year,
    EXTRACT(MONTH FROM l.close_date)::INT   AS close_month,
    l.opportunity_created_at,
    l.days_to_close,

    -- The 4 revenue numbers
    l.crm_booking_amount,
    l.contract_value,
    l.total_billed_usd,
    l.total_collected_usd,

    -- Revenue gaps (positive = next stage is smaller = gap exists)
    l.booking_to_contract_gap,
    l.contract_to_billing_gap,
    l.billing_to_collected_gap,

    -- End-to-end metrics
    l.cash_collection_rate,
    l.contract_coverage_rate,
    l.revenue_stage,

    -- Contract details
    l.contract_id,
    l.contract_status,
    l.contract_start_date,
    l.contract_end_date,
    l.contract_term_months,
    l.monthly_contract_value,
    l.has_duplicate_contract_id,

    -- Billing details
    l.invoice_count,
    l.first_billing_date,
    l.last_billing_date,
    l.total_at_risk_usd,
    l.total_failed_usd,
    l.paid_invoice_count,
    l.pending_invoice_count,
    l.failed_invoice_count,
    l.primary_currency,
    l.currency_count,

    -- Presence flags
    l.has_contract,
    l.has_billing,
    l.has_collected_revenue,

    -- Discount classification (booking → contract gap as % of booking)
    CASE
        WHEN l.crm_booking_amount = 0 THEN NULL
        WHEN l.booking_to_contract_gap / l.crm_booking_amount > 0.15 THEN 'Heavy Discount (>15%)'
        WHEN l.booking_to_contract_gap / l.crm_booking_amount > 0.05 THEN 'Moderate Discount (5-15%)'
        WHEN l.booking_to_contract_gap / l.crm_booking_amount > 0    THEN 'Minor Discount (<5%)'
        WHEN l.booking_to_contract_gap < 0                           THEN 'Contract Exceeds Booking'
        ELSE 'No Discount'
    END                                                             AS discount_tier,

    -- Collection risk classification
    CASE
        WHEN NOT l.has_contract                                      THEN 'No Contract'
        WHEN l.total_failed_usd > 0 AND l.cash_collection_rate < 0.5 THEN 'High Collection Risk'
        WHEN l.total_failed_usd > 0 OR l.total_at_risk_usd > 0      THEN 'Some Collection Risk'
        WHEN l.has_collected_revenue AND l.cash_collection_rate >= 0.95 THEN 'Fully Collected'
        WHEN l.has_collected_revenue                                 THEN 'Partially Collected'
        ELSE 'Not Yet Collected'
    END                                                             AS collection_status

FROM lifecycle l
LEFT JOIN accounts a ON l.account_id = a.account_id
