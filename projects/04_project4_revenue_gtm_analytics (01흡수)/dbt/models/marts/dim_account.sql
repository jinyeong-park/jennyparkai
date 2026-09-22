/*
  dim_account
  ===========
  Master account dimension used in all fact models.

  Built from int_customer_identity_map — which already joins CRM, Marketing,
  Billing, and CS into a single account-level row.

  This model selects the attributes useful for slicing/filtering in reports
  and adds a pre-computed lifecycle_tier for high-level segmentation.

  Used by:
    - All fct_* models (joined on account_id)
    - Dashboard filters: segment, industry, region, revenue_model
    - Account health overview

  Grain: one row per account_id
*/

WITH identity AS (
    SELECT * FROM {{ ref('int_customer_identity_map') }}
),

accounts AS (
    SELECT
        account_id,
        account_name,
        industry,
        region,
        account_created_at
    FROM {{ ref('stg_salesforce_accounts') }}
)

SELECT
    i.account_id,
    a.account_name,
    i.segment,
    a.industry,
    a.region,
    i.revenue_model,
    i.account_status,
    a.account_created_at,

    -- System coverage
    i.is_in_crm,
    i.is_in_marketing,
    i.is_in_billing,
    i.is_in_customer_success,
    i.systems_present,

    -- Funnel position
    i.max_lifecycle_stage,

    -- Revenue signals
    i.total_bookings_usd,
    i.total_billed_usd,
    i.total_collected_usd,

    -- Health signals
    i.customer_health_score,
    i.health_tier,
    i.renewal_status,
    i.is_churned,
    i.has_expansion,
    i.expansion_amount,

    -- Lifecycle tier: high-level classification for exec dashboards
    -- Combines account_status with funnel position and billing presence
    CASE
        WHEN i.is_churned                               THEN 'Churned'
        WHEN i.account_status = 'Customer'
             AND i.is_in_billing                        THEN 'Active Customer'
        WHEN i.account_status = 'Customer'              THEN 'Customer - No Billing'
        WHEN i.total_bookings_usd > 0                   THEN 'Closed-Won Prospect'
        WHEN i.opp_count > 0                            THEN 'In Pipeline'
        WHEN i.max_lifecycle_stage IN ('SQL', 'MQL')   THEN 'Marketing Qualified'
        WHEN i.lead_count > 0                           THEN 'Lead'
        ELSE 'Account Only'
    END                                                 AS lifecycle_tier

FROM identity i
LEFT JOIN accounts a ON i.account_id = a.account_id
