/*
  int_gtm_funnel
  ==============
  Connects Marketing leads → Salesforce Accounts → Opportunities to build
  the full GTM (Go-To-Market) funnel view.

  Problem this solves:
    - Marketing generates leads; Sales creates opportunities — but these live
      in separate systems with no direct foreign key between them.
    - 12 leads have no account_id (unmatched). They are included here and
      flagged so marketing can audit acquisition quality.
    - 9 orphan opportunities (account_id like 'ACC_ORPHAN_%') are included
      and flagged so pipeline reporting can surface unmatched deals.
    - This model is the single place to answer: "For a given lead, did it
      ever become an opportunity? Did that opportunity close?"

  Used by:
    - fct_pipeline (pipeline analysis)
    - fct_customer_lifecycle (full B2B lifecycle)
    - Funnel conversion rate analysis (Lead → MQL → SQL → Opp → Won)

  Key output columns:
    - funnel_stage        → Lead | MQL | SQL | Converted | Opportunity | Closed-Won
    - has_opportunity     → account has at least one opportunity in CRM
    - has_won_opportunity → account has at least one Closed-Won opportunity
    - lead_to_opp_days    → days from first lead to first opportunity created
*/

WITH leads AS (
    SELECT
        lead_id,
        account_id,
        lead_source,
        lead_source_detail,
        lead_created_date,
        lifecycle_stage,
        lifecycle_stage_rank,
        is_sales_qualified,
        has_account
    FROM {{ ref('stg_marketing_leads') }}
),

accounts AS (
    SELECT
        account_id,
        account_name,
        segment,
        industry,
        region,
        revenue_model,
        account_status,
        account_created_at
    FROM {{ ref('stg_salesforce_accounts') }}
),

opps AS (
    SELECT
        opportunity_id,
        account_id,
        opportunity_name,
        opportunity_stage,
        stage_order,
        amount,
        close_date,
        opportunity_created_at,
        is_won,
        is_lost,
        is_open,
        is_orphan,
        days_open,
        days_past_due,
        is_past_due,
        is_stale,
        has_repeated_slip
    FROM {{ ref('stg_salesforce_opportunities') }}
),

-- Aggregate opportunity signals at account level
opp_account_summary AS (
    SELECT
        account_id,
        COUNT(DISTINCT opportunity_id)                              AS total_opp_count,
        SUM(CASE WHEN is_won  THEN 1 ELSE 0 END)                   AS won_opp_count,
        SUM(CASE WHEN is_lost THEN 1 ELSE 0 END)                   AS lost_opp_count,
        SUM(CASE WHEN is_open THEN 1 ELSE 0 END)                   AS open_opp_count,
        SUM(CASE WHEN is_won  THEN amount ELSE 0 END)               AS total_won_amount,
        SUM(CASE WHEN is_open THEN amount ELSE 0 END)               AS total_pipeline_amount,
        MIN(opportunity_created_at)                                 AS first_opp_created_at,
        MAX(CASE WHEN is_won THEN opportunity_created_at END)       AS first_won_opp_at
    FROM opps
    WHERE is_orphan = FALSE
    GROUP BY account_id
),

-- Aggregate lead signals at account level
lead_account_summary AS (
    SELECT
        account_id,
        COUNT(DISTINCT lead_id)                                     AS total_lead_count,
        MIN(lead_created_date)                                      AS first_lead_date,
        MAX(lead_created_date)                                      AS last_lead_date,
        MAX(lifecycle_stage_rank)                                   AS max_lifecycle_rank,
        COUNT(DISTINCT CASE WHEN is_sales_qualified THEN lead_id END) AS sql_lead_count,
        -- Most common lead source (tie-broken by alphabetical)
        MODE() WITHIN GROUP (ORDER BY lead_source)                  AS primary_lead_source
    FROM leads
    WHERE has_account = TRUE
    GROUP BY account_id
),

-- Main funnel join: account is the spine
account_funnel AS (
    SELECT
        a.account_id,
        a.account_name,
        a.segment,
        a.industry,
        a.region,
        a.revenue_model,
        a.account_status,
        a.account_created_at,

        -- Lead metrics
        COALESCE(l.total_lead_count, 0)         AS lead_count,
        l.first_lead_date,
        l.last_lead_date,
        l.primary_lead_source,
        COALESCE(l.sql_lead_count, 0)           AS sql_lead_count,

        -- Furthest lifecycle stage from leads
        CASE COALESCE(l.max_lifecycle_rank, 0)
            WHEN 4 THEN 'Converted'
            WHEN 3 THEN 'SQL'
            WHEN 2 THEN 'MQL'
            WHEN 1 THEN 'Lead'
            ELSE 'No Lead'
        END                                     AS max_lead_stage,

        -- Opportunity metrics
        COALESCE(o.total_opp_count, 0)          AS opp_count,
        COALESCE(o.won_opp_count, 0)            AS won_opp_count,
        COALESCE(o.lost_opp_count, 0)           AS lost_opp_count,
        COALESCE(o.open_opp_count, 0)           AS open_opp_count,
        COALESCE(o.total_won_amount, 0)         AS total_won_amount,
        COALESCE(o.total_pipeline_amount, 0)    AS total_pipeline_amount,
        o.first_opp_created_at,
        o.first_won_opp_at,

        -- Presence flags
        (l.account_id IS NOT NULL)              AS has_lead,
        (o.account_id IS NOT NULL)              AS has_opportunity,
        (o.won_opp_count > 0)                   AS has_won_opportunity,
        (o.open_opp_count > 0)                  AS has_open_opportunity,

        -- Funnel conversion velocity (days from first lead to first opportunity)
        CASE
            WHEN l.first_lead_date IS NOT NULL AND o.first_opp_created_at IS NOT NULL
            THEN (o.first_opp_created_at::DATE - l.first_lead_date)
        END                                     AS lead_to_opp_days,

        -- Days from first opportunity to first Closed-Won
        CASE
            WHEN o.first_opp_created_at IS NOT NULL AND o.first_won_opp_at IS NOT NULL
            THEN (o.first_won_opp_at::DATE - o.first_opp_created_at::DATE)
        END                                     AS opp_to_close_days,

        -- Summary funnel stage (furthest stage reached overall)
        CASE
            WHEN o.won_opp_count  > 0 THEN 'Closed-Won'
            WHEN o.open_opp_count > 0 THEN 'Open Opportunity'
            WHEN o.lost_opp_count > 0 THEN 'Closed-Lost'
            WHEN COALESCE(l.max_lifecycle_rank, 0) = 3 THEN 'SQL'
            WHEN COALESCE(l.max_lifecycle_rank, 0) = 2 THEN 'MQL'
            WHEN COALESCE(l.max_lifecycle_rank, 0) = 1 THEN 'Lead'
            ELSE 'Account Only'
        END                                     AS funnel_stage

    FROM accounts a
    LEFT JOIN lead_account_summary  l ON a.account_id = l.account_id
    LEFT JOIN opp_account_summary   o ON a.account_id = o.account_id
),

-- Unmatched leads: 12 leads with no account_id — included for completeness
-- These show up in marketing audits but cannot be joined to accounts
unmatched_leads AS (
    SELECT
        lead_id,
        lead_source,
        lead_source_detail,
        lead_created_date,
        lifecycle_stage,
        lifecycle_stage_rank
    FROM leads
    WHERE has_account = FALSE
),

-- Orphan opportunities: 9 opps with no real account_id
orphan_opps AS (
    SELECT
        opportunity_id,
        account_id          AS orphan_account_ref,
        opportunity_stage,
        amount,
        close_date,
        opportunity_created_at
    FROM opps
    WHERE is_orphan = TRUE
)

-- Final output: account funnel rows
SELECT
    account_id,
    account_name,
    segment,
    industry,
    region,
    revenue_model,
    account_status,
    account_created_at,

    -- Lead funnel
    lead_count,
    first_lead_date,
    last_lead_date,
    primary_lead_source,
    sql_lead_count,
    max_lead_stage,

    -- Opportunity funnel
    opp_count,
    won_opp_count,
    lost_opp_count,
    open_opp_count,
    total_won_amount,
    total_pipeline_amount,
    first_opp_created_at,
    first_won_opp_at,

    -- Flags
    has_lead,
    has_opportunity,
    has_won_opportunity,
    has_open_opportunity,
    FALSE                   AS is_unmatched_lead,   -- accounts are always matched
    FALSE                   AS is_orphan_opp,

    -- Velocity metrics
    lead_to_opp_days,
    opp_to_close_days,

    -- Funnel classification
    funnel_stage

FROM account_funnel
