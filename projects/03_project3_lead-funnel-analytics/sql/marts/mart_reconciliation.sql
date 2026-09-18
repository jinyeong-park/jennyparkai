-- ============================================================
-- mart_reconciliation
-- Grain: one row per channel × month
-- Compares platform-reported leads vs warehouse leads
-- Surfaces how much each channel overclaims
-- Source: raw_ad_performance + raw_leads
-- ============================================================
--
-- BUSINESS PROBLEM
-- --------------------------------------------------------
-- "Meta Ads Manager says we got 144 conversions and $8,795
--  in revenue last month. But our warehouse only shows 132
--  leads and $3,200 in verified revenue. Which number is right
--  — and why is there a gap?"
--
-- Every ad platform counts conversions differently:
--   - Different attribution windows (7-day, 28-day click)
--   - Cross-device matching errors
--   - Pixel double-firing
--   - View-through conversions (no click happened)
--   - Organic conversions claimed as paid
--
-- This mart puts both numbers side by side so you can see
-- exactly how much each channel overclaims, and use the
-- warehouse number (verified) for budget decisions.
--
-- Key questions answered:
--   1. Which channel overclaims the most?
--      (Meta typically 15-40%, Google 5-20%)
--   2. Is the overclaim rate getting worse month-over-month?
--   3. What is the verified ROAS vs platform-reported ROAS?
--   4. If we reallocated budget using warehouse data instead
--      of platform data, where would money go?
--
-- Critical SQL pattern:
--   FULL OUTER JOIN — needed because organic/direct have
--   warehouse leads but no ad spend rows. A LEFT JOIN would
--   drop those channels entirely.
-- ============================================================

CREATE OR REPLACE TABLE `insurance-lead-intelligence.insurance_analytics_marts.mart_reconciliation`
AS

WITH warehouse_leads AS (
  SELECT
    DATE_TRUNC(DATE(submitted_at), MONTH)     AS month,
    channel,
    COUNT(DISTINCT lead_id)                   AS warehouse_leads,
    COUNT(DISTINCT CASE WHEN is_valid = TRUE THEN lead_id END) AS valid_leads
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
  GROUP BY 1, 2
),

platform_data AS (
  SELECT
    DATE_TRUNC(performance_date, MONTH)       AS month,
    channel,
    SUM(platform_reported_leads)              AS platform_leads,
    SUM(platform_reported_conversions)        AS platform_conversions,
    SUM(platform_reported_revenue)            AS platform_revenue,
    SUM(spend)                                AS total_spend
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance`
  GROUP BY 1, 2
)

SELECT
  COALESCE(p.month, w.month)                  AS month,
  COALESCE(p.channel, w.channel)              AS channel,
  COALESCE(p.platform_leads, 0)               AS platform_leads,
  COALESCE(w.warehouse_leads, 0)              AS warehouse_leads,
  COALESCE(w.valid_leads, 0)                  AS valid_leads,
  COALESCE(p.platform_revenue, 0)             AS platform_revenue,
  COALESCE(p.total_spend, 0)                  AS total_spend,

  -- lead_discrepancy = platform_leads − warehouse_leads
  -- Positive means platform claims more than we recorded.
  COALESCE(p.platform_leads, 0) - COALESCE(w.warehouse_leads, 0) AS lead_discrepancy,

  -- discrepancy_rate = (platform − warehouse) / platform
  -- Interpretation: share of platform-reported conversions not reflected in the warehouse.
  -- Example: platform=100, warehouse=75 → rate=0.25 means
  --   "25% of platform conversions have no matching warehouse lead"
  -- NOTE: this is NOT the same as "platform overclaims by 25% relative to warehouse"
  --   (that would be 25/75 = 33%). Using NULLIF so organic (platform=0) returns NULL, not error.
  ROUND(SAFE_DIVIDE(
    COALESCE(p.platform_leads, 0) - COALESCE(w.warehouse_leads, 0),
    NULLIF(p.platform_leads, 0)
  ), 3)                                       AS discrepancy_rate,

  -- reconciliation_status: which sources have data for this channel × month
  -- Used to distinguish: organic (warehouse_only) vs paid channels (matched)
  CASE
    WHEN p.channel IS NULL THEN 'warehouse_only'   -- organic/direct: no ad spend row
    WHEN w.channel IS NULL THEN 'platform_only'    -- platform reports leads we never recorded
    ELSE                        'matched'           -- both sources have data (normal)
  END                                         AS reconciliation_status

FROM platform_data p
FULL OUTER JOIN warehouse_leads w
  ON p.month = w.month AND p.channel = w.channel
ORDER BY month, channel;
