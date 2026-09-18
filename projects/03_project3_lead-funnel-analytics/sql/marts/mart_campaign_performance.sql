-- ============================================================
-- mart_campaign_performance
-- Grain: one row per campaign_id + month
-- Shows spend, leads, revenue, CPL, ROAS
-- Source: raw_ad_performance + raw_leads + raw_revenue_events
-- Key: pre-aggregate each table to campaign grain BEFORE joining
--      to prevent spend fan-out
-- ============================================================
--
-- BUSINESS PROBLEM
-- --------------------------------------------------------
-- "Campaign C002 has a lower CPL than C001. Should we shift
--  budget to C002?"
--
-- CPL alone is misleading. A campaign can have a low CPL but
-- produce leads that are mostly invalid, never get accepted
-- by partners, and generate zero revenue.
--
-- This mart connects spend → leads → revenue in one place
-- so you can compare CPL AND revenue per lead AND ROAS
-- for each campaign.
--
-- Key questions answered:
--   1. Which campaign delivers the best revenue per lead?
--   2. Which campaign has the worst valid lead rate
--      (cheap leads that don't convert)?
--   3. How much is each platform overclaiming vs warehouse?
--      (platform_reported_leads vs warehouse leads)
--   4. What is the true ROAS when using verified revenue,
--      not platform-reported revenue?
--
-- Critical SQL pattern:
--   Pre-aggregate spend, leads, and revenue to campaign grain
--   SEPARATELY before joining — prevents spend fan-out.
-- ============================================================

CREATE OR REPLACE TABLE `insurance-lead-intelligence.insurance_analytics_marts.mart_campaign_performance`
AS

-- Step 1: Aggregate spend to campaign + month level
WITH campaign_spend AS (
  SELECT
    DATE_TRUNC(performance_date, MONTH)       AS month,
    campaign_id,
    channel,
    insurance_vertical,
    SUM(spend)                                AS total_spend,
    SUM(impressions)                          AS impressions,
    SUM(clicks)                               AS clicks,
    SUM(platform_reported_leads)              AS platform_leads,
    SUM(platform_reported_conversions)        AS platform_conversions,
    SUM(platform_reported_revenue)            AS platform_revenue
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_ad_performance`
  GROUP BY 1, 2, 3, 4
),

-- Step 2: Aggregate leads to campaign + month level
campaign_leads AS (
  SELECT
    DATE_TRUNC(DATE(submitted_at), MONTH)     AS month,
    campaign_id,
    COUNT(DISTINCT lead_id)                   AS leads_submitted,
    COUNT(DISTINCT CASE WHEN is_valid    = TRUE THEN lead_id END) AS valid_leads,
    COUNT(DISTINCT CASE WHEN is_duplicate = TRUE THEN lead_id END) AS duplicate_leads
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
  GROUP BY 1, 2
),

-- Step 3: Aggregate revenue to campaign + month (via leads join)
campaign_revenue AS (
  SELECT
    DATE_TRUNC(DATE(l.submitted_at), MONTH)   AS month,
    l.campaign_id,
    SUM(r.revenue_amount)                     AS total_revenue,
    COUNT(DISTINCT r.revenue_event_id)        AS revenue_events
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads` l
  JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events` r
    ON l.lead_id = r.lead_id
  GROUP BY 1, 2
)

-- Step 4: Join pre-aggregated tables (no fan-out risk)
SELECT
  s.month,
  s.campaign_id,
  s.channel,
  s.insurance_vertical,

  -- Spend & traffic
  ROUND(s.total_spend, 2)                                         AS total_spend,
  s.impressions,
  s.clicks,
  ROUND(SAFE_DIVIDE(s.clicks, s.impressions), 4)                  AS ctr,
  ROUND(SAFE_DIVIDE(s.total_spend, s.clicks), 2)                  AS cpc,

  -- Platform vs warehouse
  s.platform_leads                                                AS platform_reported_leads,
  COALESCE(l.leads_submitted, 0)                                  AS warehouse_leads,
  ROUND(SAFE_DIVIDE(
    s.platform_leads - COALESCE(l.leads_submitted, 0),
    s.platform_leads
  ), 3)                                                           AS platform_overclaim_rate,

  -- Lead quality
  COALESCE(l.valid_leads, 0)                                      AS valid_leads,
  COALESCE(l.duplicate_leads, 0)                                  AS duplicate_leads,
  ROUND(SAFE_DIVIDE(l.valid_leads, l.leads_submitted), 3)         AS valid_lead_rate,

  -- Revenue
  ROUND(COALESCE(r.total_revenue, 0), 2)                          AS total_revenue,

  -- Key metrics
  ROUND(SAFE_DIVIDE(s.total_spend, l.leads_submitted), 2)         AS cpl,
  ROUND(SAFE_DIVIDE(s.total_spend, l.valid_leads), 2)             AS cost_per_valid_lead,
  ROUND(SAFE_DIVIDE(r.total_revenue, l.leads_submitted), 2)       AS revenue_per_lead,
  ROUND(SAFE_DIVIDE(r.total_revenue, s.total_spend), 3)           AS roas,
  ROUND(SAFE_DIVIDE(r.total_revenue - s.total_spend,
                    s.total_spend), 3)                            AS roi

FROM campaign_spend s
LEFT JOIN campaign_leads  l ON s.month = l.month AND s.campaign_id = l.campaign_id
LEFT JOIN campaign_revenue r ON s.month = r.month AND s.campaign_id = r.campaign_id
ORDER BY s.month, s.channel, s.campaign_id;
