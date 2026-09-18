-- ============================================================
-- mart_lead_funnel
-- Grain: one row per channel + insurance_vertical + month
-- Shows funnel conversion at each stage
-- Source: raw_quote_events + raw_leads
-- ============================================================
--
-- BUSINESS PROBLEM
-- --------------------------------------------------------
-- "Lead volume went up 20% last month, but revenue stayed flat.
--  Why?"
--
-- This mart answers that question by breaking the funnel into
-- measurable stages. A volume increase without revenue growth
-- usually means drop-off is happening AFTER submission —
-- either in validation (duplicate/invalid leads) or in
-- partner routing (low acceptance rate).
--
-- Key questions answered:
--   1. At which funnel stage do most users drop off?
--   2. Which channel has the worst valid lead rate?
--   3. Is the duplicate rate increasing month-over-month?
--   4. Does a high session-to-quote rate translate to
--      a high lead submission rate?
-- ============================================================

CREATE OR REPLACE TABLE `insurance-lead-intelligence.insurance_analytics_marts.mart_lead_funnel`
AS

WITH sessions AS (
  SELECT
    DATE_TRUNC(DATE(event_timestamp), MONTH)  AS month,
    channel,
    insurance_vertical,
    COUNT(DISTINCT session_id)                AS sessions,
    COUNT(DISTINCT CASE WHEN event_name = 'quote_started'
                        THEN session_id END)  AS quote_starts,
    COUNT(DISTINCT CASE WHEN event_name = 'quote_completed'
                        THEN session_id END)  AS quote_completions,
    COUNT(DISTINCT CASE WHEN event_name = 'lead_submitted'
                        THEN session_id END)  AS sessions_with_lead
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_quote_events`
  GROUP BY 1, 2, 3
),

leads AS (
  SELECT
    DATE_TRUNC(DATE(submitted_at), MONTH)     AS month,
    channel,
    insurance_vertical,
    COUNT(DISTINCT lead_id)                   AS leads_submitted,
    COUNT(DISTINCT CASE WHEN is_valid  = TRUE THEN lead_id END) AS valid_leads,
    COUNT(DISTINCT CASE WHEN is_duplicate = TRUE THEN lead_id END) AS duplicate_leads
  FROM `insurance-lead-intelligence.insurance_analytics_raw.raw_leads`
  GROUP BY 1, 2, 3
)

SELECT
  s.month,
  s.channel,
  s.insurance_vertical,

  -- Volume
  s.sessions,
  s.quote_starts,
  s.quote_completions,
  l.leads_submitted,
  l.valid_leads,
  l.duplicate_leads,

  -- Stage-to-stage conversion rates
  ROUND(SAFE_DIVIDE(s.quote_starts,       s.sessions),          3) AS session_to_quote_rate,
  ROUND(SAFE_DIVIDE(s.quote_completions,  s.quote_starts),      3) AS quote_start_to_completion_rate,
  ROUND(SAFE_DIVIDE(l.leads_submitted,    s.quote_completions), 3) AS completion_to_lead_rate,

  -- Overall funnel
  ROUND(SAFE_DIVIDE(l.leads_submitted,    s.sessions),          3) AS overall_cvr,

  -- Lead quality
  ROUND(SAFE_DIVIDE(l.valid_leads,        l.leads_submitted),   3) AS valid_lead_rate,
  ROUND(SAFE_DIVIDE(l.duplicate_leads,    l.leads_submitted),   3) AS duplicate_rate

FROM sessions s
LEFT JOIN leads l
  ON  s.month              = l.month
  AND s.channel            = l.channel
  AND s.insurance_vertical = l.insurance_vertical
ORDER BY s.month, s.channel, s.insurance_vertical;
