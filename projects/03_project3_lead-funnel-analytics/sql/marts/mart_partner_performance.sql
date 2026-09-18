-- ============================================================
-- mart_partner_performance
-- Grain: one row per partner_id + date
-- Shows daily acceptance rate + 7-day rolling average
-- Source: raw_routing_attempts + raw_partners + raw_revenue_events
-- ============================================================
--
-- BUSINESS PROBLEM
-- --------------------------------------------------------
-- "Partner P003's acceptance rate dropped from 71% to 45%
--  over the last two weeks. Is this a real trend or noise?"
--
-- A single day of low acceptance could be a fluke —
-- maybe the partner had a system outage. But a consistent
-- 7-day rolling decline signals a real problem:
-- capacity constraints, quality issues, or a pricing dispute.
--
-- This mart surfaces both the daily rate (volatility) and
-- the 7-day rolling rate (trend) so ops teams can tell
-- the difference.
--
-- Key questions answered:
--   1. Which partners have a declining acceptance trend?
--   2. Which partners respond fastest (avg_response_sec)?
--   3. Which partners generate the most revenue per
--      delivered lead — not just total volume?
--   4. Are any partners consistently hitting capacity
--      (capacity_exceeded rejections)?
--
-- Critical SQL pattern:
--   Window function with RANGE BETWEEN 6 PRECEDING AND
--   CURRENT ROW on ORDER BY UNIX_DATE(route_date) gives
--   a true 7-calendar-day window even when a partner has
--   no data on some days. ROWS BETWEEN would look back
--   6 rows regardless of how many days those span.
-- ============================================================

CREATE OR REPLACE TABLE `insurance-lead-intelligence.insurance_analytics_marts.mart_partner_performance`
AS

-- Step 1: Daily routing stats per partner
WITH daily_routing AS (
  SELECT
    DATE(routed_at)                           AS route_date,
    partner_id,
    COUNT(DISTINCT routing_attempt_id)        AS leads_delivered,
    COUNT(DISTINCT CASE WHEN response_status = 'accepted'
                        THEN routing_attempt_id END) AS leads_accepted,
    COUNT(DISTINCT CASE WHEN response_status = 'rejected'
                        THEN routing_attempt_id END) AS leads_rejected,
    COUNT(DISTINCT CASE WHEN response_status = 'no_response'
                        THEN routing_attempt_id END) AS no_response,
    COUNT(DISTINCT CASE WHEN response_status = 'capacity_exceeded'
                        THEN routing_attempt_id END) AS capacity_exceeded,
    AVG(TIMESTAMP_DIFF(response_timestamp, routed_at, SECOND)) AS avg_response_sec
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_routing_attempts`
  GROUP BY 1, 2
),

-- Step 2: Daily revenue per partner
daily_revenue AS (
  SELECT
    DATE(revenue_timestamp)                   AS revenue_date,
    partner_id,
    SUM(revenue_amount)                       AS daily_revenue,
    COUNT(DISTINCT revenue_event_id)          AS revenue_events
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_revenue_events`
  GROUP BY 1, 2
),

-- Step 3: Join partner metadata
with_partner AS (
  SELECT
    r.route_date,
    r.partner_id,
    p.partner_name,
    p.insurance_verticals,
    r.leads_delivered,
    r.leads_accepted,
    r.leads_rejected,
    r.no_response,
    r.capacity_exceeded,
    ROUND(r.avg_response_sec, 1)              AS avg_response_sec,
    COALESCE(rev.daily_revenue, 0)            AS daily_revenue,

    -- Daily acceptance rate
    ROUND(SAFE_DIVIDE(r.leads_accepted, r.leads_delivered), 3) AS daily_acceptance_rate,

    -- Revenue per delivered lead
    ROUND(SAFE_DIVIDE(rev.daily_revenue, r.leads_delivered), 2) AS revenue_per_delivered_lead

  FROM daily_routing r
  LEFT JOIN `insurance-lead-intelligence.insurance_analytics_raw.raw_partners` p
    USING (partner_id)
  LEFT JOIN daily_revenue rev
    ON  r.partner_id  = rev.partner_id
    AND r.route_date  = rev.revenue_date
)

-- Step 4: Add rolling window metrics
SELECT
  route_date,
  partner_id,
  partner_name,
  insurance_verticals,
  leads_delivered,
  leads_accepted,
  leads_rejected,
  no_response,
  capacity_exceeded,
  avg_response_sec,
  daily_revenue,
  daily_acceptance_rate,
  revenue_per_delivered_lead,

  -- 7-day rolling acceptance rate
  -- Volume-weighted: SUM(accepted) / SUM(delivered) over window — not AVG(rate)
  -- Uses RANGE BETWEEN 6 PRECEDING AND CURRENT ROW on UNIX_DATE so the window
  -- spans exactly 7 calendar days even when a partner has no data on some days.
  -- ROWS BETWEEN 6 PRECEDING would look back 6 rows (could be 6 weeks if gaps exist).
  ROUND(SAFE_DIVIDE(
    SUM(leads_accepted) OVER (
      PARTITION BY partner_id
      ORDER BY UNIX_DATE(route_date)
      RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
    ),
    SUM(leads_delivered) OVER (
      PARTITION BY partner_id
      ORDER BY UNIX_DATE(route_date)
      RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
    )
  ), 3)                                       AS rolling_7d_acceptance_rate,

  -- 7-day rolling revenue (calendar-day window, same RANGE logic)
  ROUND(SUM(daily_revenue) OVER (
    PARTITION BY partner_id
    ORDER BY UNIX_DATE(route_date)
    RANGE BETWEEN 6 PRECEDING AND CURRENT ROW
  ), 2)                                       AS rolling_7d_revenue,

  -- Running total leads delivered
  SUM(leads_delivered) OVER (
    PARTITION BY partner_id
    ORDER BY UNIX_DATE(route_date)
  )                                           AS cumulative_leads_delivered,

  -- Running total revenue
  ROUND(SUM(daily_revenue) OVER (
    PARTITION BY partner_id
    ORDER BY UNIX_DATE(route_date)
  ), 2)                                       AS cumulative_revenue

FROM with_partner
ORDER BY partner_id, route_date;
