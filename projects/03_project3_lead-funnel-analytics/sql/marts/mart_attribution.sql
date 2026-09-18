-- ============================================================
-- mart_attribution
-- Grain: one row per lead_id
-- Shows first-touch channel + hours to submit + revenue
-- Source: raw_leads + raw_quote_events + raw_revenue_events
-- ============================================================
--
-- BUSINESS PROBLEM
-- --------------------------------------------------------
-- "Google Search shows strong ROAS in the platform dashboard.
--  But is Google actually the first channel users interact
--  with — or are they coming from organic/social first?"
--
-- The channel recorded on a lead (submitted_channel) is
-- the last session before submission. But the user may have
-- first discovered the brand via Meta 3 days earlier.
--
-- First-touch attribution assigns credit to the EARLIEST
-- touchpoint — giving a different view of which channels
-- are driving awareness vs. capturing existing intent.
--
-- Key questions answered:
--   1. For leads that converted, what was their first channel?
--   2. Do first-touch organic leads monetize better than
--      first-touch paid leads?
--   3. How long does it take from first touch to submission
--      by channel? (hours_to_submit)
--   4. What % of leads had multiple touchpoints before
--      submitting? (touchpoint_count > 1)
--
-- Critical SQL pattern:
--   JOIN raw_quote_events on quote_id + event_timestamp <= submitted_at,
--   then QUALIFY ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY
--   event_timestamp ASC) = 1 keeps only the earliest event row per lead.
--   That row's channel IS the first-touch channel — no FIRST_VALUE() needed.
-- ============================================================

CREATE OR REPLACE TABLE `insurance-lead-intelligence.insurance_analytics_marts.mart_attribution`
AS

-- Step 1: First touch — earliest quote event per lead
WITH lead_first_touch AS (
  SELECT
    l.lead_id,
    l.campaign_id,
    l.channel                                 AS submitted_channel,
    l.submitted_at,
    l.insurance_vertical,
    l.state,
    l.is_valid,
    l.is_duplicate,

    -- First touch channel and campaign.
    -- QUALIFY ROW_NUMBER() = 1 (below) keeps only the earliest event row per lead,
    -- so e.channel on that row IS already the first-touch value.
    -- No FIRST_VALUE() needed — using it here would be redundant.
    e.channel                                 AS first_touch_channel,
    e.campaign_id                             AS first_touch_campaign,

    -- Time from first touch to submission (hours)
    ROUND(
      TIMESTAMP_DIFF(
        l.submitted_at,
        MIN(e.event_timestamp) OVER (PARTITION BY l.lead_id),
        MINUTE
      ) / 60.0, 1
    )                                         AS hours_to_submit,

    -- Number of touchpoints before submission
    COUNT(e.event_id) OVER (
      PARTITION BY l.lead_id
    )                                         AS touchpoint_count

  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads` l
  JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_quote_events` e
    ON  l.quote_id = e.quote_id
    AND e.event_timestamp <= l.submitted_at
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY l.lead_id
    ORDER BY e.event_timestamp ASC
  ) = 1
),

-- Step 2: Revenue per lead
-- Pre-aggregate to lead grain before joining — prevents one-row-per-lead grain
-- from breaking if a lead has multiple revenue events.
lead_revenue AS (
  SELECT
    lead_id,
    SUM(revenue_amount)   AS revenue_amount,
    COUNT(*)              AS revenue_events
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events`
  GROUP BY lead_id
)

-- Final: lead-level attribution table
SELECT
  ft.lead_id,
  ft.campaign_id,
  ft.submitted_channel,
  ft.first_touch_channel,
  ft.first_touch_campaign,
  DATE(ft.submitted_at)                       AS submitted_date,
  DATE_TRUNC(DATE(ft.submitted_at), MONTH)    AS submitted_month,
  ft.insurance_vertical,
  ft.state,
  ft.is_valid,
  ft.is_duplicate,
  ft.hours_to_submit,
  ft.touchpoint_count,

  -- Revenue
  COALESCE(r.revenue_amount, 0)               AS revenue_amount,
  COALESCE(r.revenue_events, 0)               AS revenue_events,
  (r.revenue_amount IS NOT NULL)              AS is_monetized

FROM lead_first_touch ft
LEFT JOIN lead_revenue r USING (lead_id)
ORDER BY ft.submitted_at;
