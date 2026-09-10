/*
  int_customer_identity_map
  ==========================
  Creates a unified account-level identity map across all source systems.

  Problem this solves:
    - CRM (accounts), Marketing (leads), Billing (customer_id), and
      Customer Success all use account_id, but not every account exists
      in every system. This model creates a single row per account_id
      showing exactly where each account appears and where it is missing.

  Used by:
    - fct_pipeline, fct_revenue, fct_customer_lifecycle
    - Revenue reconciliation analysis
    - Any query that needs to know "does this account have billing? contracts? CS data?"

  Key output columns:
    - is_in_crm             → appeared in Salesforce accounts
    - is_in_marketing       → has at least one lead
    - is_in_billing         → has at least one invoice
    - is_in_customer_success→ has a CS record
    - systems_present       → count of systems (1–4), useful for completeness scoring
    - lifecycle_stage       → furthest stage reached in the GTM funnel
*/

WITH accounts AS (
    SELECT account_id, segment, revenue_model, account_status
    FROM {{ ref('stg_salesforce_accounts') }}
),

-- Aggregate leads to account level (one lead per account may have many leads)
leads_agg AS (
    SELECT
        account_id,
        COUNT(DISTINCT lead_id)         AS lead_count,
        MAX(lifecycle_stage_rank)       AS max_lifecycle_rank,
        MIN(lead_created_date)          AS first_lead_date,
        MAX(lead_created_date)          AS last_lead_date
    FROM {{ ref('stg_marketing_leads') }}
    WHERE has_account = TRUE
    GROUP BY account_id
),

-- Aggregate opportunities to account level
opps_agg AS (
    SELECT
        account_id,
        COUNT(DISTINCT opportunity_id)                              AS opp_count,
        SUM(CASE WHEN is_won  THEN 1 ELSE 0 END)                   AS won_count,
        SUM(CASE WHEN is_lost THEN 1 ELSE 0 END)                   AS lost_count,
        SUM(CASE WHEN is_open THEN 1 ELSE 0 END)                   AS open_count,
        SUM(CASE WHEN is_won  THEN amount ELSE 0 END)               AS total_won_amount,
        SUM(CASE WHEN is_open THEN amount ELSE 0 END)               AS total_open_pipeline
    FROM {{ ref('stg_salesforce_opportunities') }}
    WHERE is_orphan = FALSE
    GROUP BY account_id
),

-- Billing uses customer_id which maps to account_id
billing_agg AS (
    SELECT
        customer_id                          AS account_id,
        COUNT(DISTINCT invoice_id)           AS invoice_count,
        SUM(billing_amount_usd)              AS total_billed_usd,
        SUM(collected_amount_usd)            AS total_collected_usd,
        SUM(failed_amount_usd)               AS total_failed_usd
    FROM {{ ref('stg_billing') }}
    GROUP BY customer_id
),

-- Customer success
cs_agg AS (
    SELECT
        account_id,
        customer_health_score,
        health_tier,
        renewal_status,
        is_churned,
        has_expansion,
        expansion_amount
    FROM {{ ref('stg_customer_success') }}
)

SELECT
    a.account_id,
    a.segment,
    a.revenue_model,
    a.account_status,

    -- System presence flags
    TRUE                                AS is_in_crm,
    (l.account_id IS NOT NULL)          AS is_in_marketing,
    (b.account_id IS NOT NULL)          AS is_in_billing,
    (cs.account_id IS NOT NULL)         AS is_in_customer_success,

    -- System completeness score (how many of the 4 systems have this account)
    1
    + CASE WHEN l.account_id  IS NOT NULL THEN 1 ELSE 0 END
    + CASE WHEN b.account_id  IS NOT NULL THEN 1 ELSE 0 END
    + CASE WHEN cs.account_id IS NOT NULL THEN 1 ELSE 0 END
                                        AS systems_present,

    -- Lead metrics
    COALESCE(l.lead_count, 0)           AS lead_count,
    l.first_lead_date,
    l.last_lead_date,

    -- Furthest funnel stage reached
    CASE COALESCE(l.max_lifecycle_rank, 0)
        WHEN 4 THEN 'Converted'
        WHEN 3 THEN 'SQL'
        WHEN 2 THEN 'MQL'
        WHEN 1 THEN 'Lead'
        ELSE 'No Lead'
    END                                 AS max_lifecycle_stage,

    -- Opportunity metrics
    COALESCE(o.opp_count, 0)            AS opp_count,
    COALESCE(o.won_count, 0)            AS won_opp_count,
    COALESCE(o.open_count, 0)           AS open_opp_count,
    COALESCE(o.total_won_amount, 0)     AS total_bookings_usd,
    COALESCE(o.total_open_pipeline, 0)  AS total_open_pipeline_usd,

    -- Billing metrics
    COALESCE(b.invoice_count, 0)        AS invoice_count,
    COALESCE(b.total_billed_usd, 0)     AS total_billed_usd,
    COALESCE(b.total_collected_usd, 0)  AS total_collected_usd,
    COALESCE(b.total_failed_usd, 0)     AS total_failed_usd,

    -- Customer success metrics
    cs.customer_health_score,
    cs.health_tier,
    cs.renewal_status,
    COALESCE(cs.is_churned, FALSE)      AS is_churned,
    COALESCE(cs.has_expansion, FALSE)   AS has_expansion,
    COALESCE(cs.expansion_amount, 0)    AS expansion_amount

FROM accounts a
LEFT JOIN leads_agg   l  ON a.account_id = l.account_id
LEFT JOIN opps_agg    o  ON a.account_id = o.account_id
LEFT JOIN billing_agg b  ON a.account_id = b.account_id
LEFT JOIN cs_agg      cs ON a.account_id = cs.account_id
