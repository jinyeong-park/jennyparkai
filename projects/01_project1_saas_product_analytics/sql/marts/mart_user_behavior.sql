-- ============================================================
-- mart_user_behavior.sql
-- User Behavior & Engagement Depth
--
-- Business Question:
--   How deeply are users engaging with the product?
--   Which behavioral patterns predict long-term retention?
--   Who are the power users, and what do they do differently?
--
-- Meta angle:  Identify behavioral signals that drive long-term product growth.
--              Understand user engagement trends to prioritize product decisions.
-- Tavus angle: Which developer actions (API calls, integrations) correlate
--              with account expansion and retention?
--
-- READ THIS BEFORE TRUSTING THE TIERS ON THIS DATASET
--   * The event log holds only 5 onboarding event types and ~5 events per org
--     (max 13 active days in an org's whole life; nothing after ~day 122). A
--     "power" tier of >= 10 active days in the last 28 days is unreachable, and
--     only ~80 of 2,500 orgs have any event in the last 28 days of data.
--   * Recency is measured from the data's observation date, NOT CURRENT_TIMESTAMP():
--     the synthetic data ends 2026-04-27, so "now" would make every org dormant.
--   * Comparing a tier's churn rate as of today with today's churn status is
--     circular (a churned account has already stopped using the product) and is
--     confounded by tenure. Use the prospective test at the bottom of this file.
-- ============================================================

DECLARE as_of_date DATE DEFAULT DATE '2026-04-27';

-- ── Step 1: Per-user event summary ───────────────────────────────────────────
WITH user_events AS (
  SELECT
    u.user_id,
    u.org_id,
    u.role,
    u.signup_timestamp,

    COUNT(e.event_id) AS total_events,
    COUNT(DISTINCT e.event_name) AS distinct_event_types,
    COUNT(DISTINCT DATE(e.event_timestamp)) AS active_days,

    -- First and last event (engagement window)
    MIN(e.event_timestamp) AS first_event_ts,
    MAX(e.event_timestamp) AS last_event_ts,
    TIMESTAMP_DIFF(MAX(e.event_timestamp), MIN(e.event_timestamp), DAY) AS engagement_span_days,

    -- Event type breakdown
    COUNTIF(e.event_name = 'workspace_created') AS workspace_events,
    COUNTIF(e.event_name = 'integration_connected') AS integration_events,
    COUNTIF(e.event_name = 'project_created') AS project_events,
    COUNTIF(e.event_name = 'teammate_invited') AS invite_events,

    -- Recency (days since last event)
    TIMESTAMP_DIFF(TIMESTAMP(as_of_date), MAX(e.event_timestamp), DAY) AS days_since_last_event

  FROM `saas-lifecycle-analytics.raw.users` u
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (user_id)
  GROUP BY 1, 2, 3, 4
),

-- ── Step 2: Org-level engagement aggregation ──────────────────────────────────
org_engagement AS (
  SELECT
    org_id,
    COUNT(DISTINCT user_id) AS total_users,
    SUM(total_events) AS org_total_events,
    AVG(total_events) AS avg_events_per_user,
    MAX(active_days) AS max_active_days_any_user,
    AVG(active_days) AS avg_active_days,
    MAX(engagement_span_days) AS max_engagement_span,
    MIN(days_since_last_event) AS days_since_any_activity,
    SUM(integration_events) AS total_integrations,
    SUM(project_events) AS total_projects,
    SUM(invite_events) AS total_invites,

    -- Engagement breadth: how many distinct event types across all users
    MAX(distinct_event_types) AS max_event_types

  FROM user_events
  GROUP BY 1
),

-- ── Step 3: Engagement score (rules-based, like Meta's L7 or DAU/MAU) ─────────
-- Score = weighted combination of depth, breadth, recency
engagement_score AS (
  SELECT
    oe.*,
    o.acquisition_source,
    o.company_size,
    o.industry,

    -- Engagement tier. Caveats: (1) thresholds were written for a product with ongoing
    -- usage telemetry and are unreachable here (see header); (2) 'at_risk' below is only
    -- "recently active but below the active thresholds", which includes brand-new accounts;
    -- a true at-risk tier needs prior high activity AND a recent drop.
    CASE
      WHEN oe.avg_active_days >= 10
        AND oe.max_event_types >= 4
        AND oe.days_since_any_activity <= 7
      THEN 'power'       -- highly engaged, all milestones, recently active
      WHEN oe.avg_active_days >= 5
        AND oe.max_event_types >= 3
        AND oe.days_since_any_activity <= 14
      THEN 'active'
      WHEN oe.days_since_any_activity <= 30
      THEN 'at_risk'     -- was active but slowing
      ELSE 'dormant'
    END AS engagement_tier,

    -- L28 proxy: events in the last 28 days (DAU/MAU analog)
    -- (requires event_timestamp data; computed here as a flag approach)
    CASE
      WHEN oe.days_since_any_activity <= 28 THEN 1 ELSE 0
    END AS active_l28

  FROM org_engagement oe
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
),

-- ── Step 4: Session-level analysis (event sequences per day per user) ─────────
-- Useful for Meta-style engagement depth: how many actions per session?
session_depth AS (
  SELECT
    user_id,
    org_id,
    DATE(event_timestamp) AS session_date,
    COUNT(event_id) AS events_in_session,
    COUNT(DISTINCT event_name) AS event_types_in_session,
    MIN(event_timestamp) AS session_start,
    MAX(event_timestamp) AS session_end,
    TIMESTAMP_DIFF(MAX(event_timestamp), MIN(event_timestamp), MINUTE) AS session_duration_min
  FROM `saas-lifecycle-analytics.raw.event_logs`
  GROUP BY 1, 2, 3
)

-- ── Final: Engagement summary with outcomes ────────────────────────────────────
SELECT
  es.org_id,
  es.acquisition_source,
  es.company_size,
  es.engagement_tier,
  es.total_users,
  es.org_total_events,
  ROUND(es.avg_events_per_user, 1) AS avg_events_per_user,
  ROUND(es.avg_active_days, 1) AS avg_active_days,
  es.max_event_types,
  es.days_since_any_activity,
  es.total_integrations,
  es.total_projects,
  es.total_invites,
  es.active_l28,

  -- Downstream outcome join
  COALESCE(s.mrr_amount, 0) AS current_mrr,
  s.status AS subscription_status

FROM engagement_score es
LEFT JOIN (
  SELECT org_id, mrr_amount, status
  FROM `saas-lifecycle-analytics.raw.subscriptions`
  WHERE mrr_amount > 0
  QUALIFY ROW_NUMBER() OVER (PARTITION BY org_id ORDER BY start_date DESC) = 1
) s USING (org_id)
ORDER BY es.org_total_events DESC;

-- ============================================================
-- SUPPLEMENTAL: Does engagement predict churn? (prospective, leakage-free)
--
-- Features use only events BEFORE a cutoff; the outcome is churn in the NEXT 90 days,
-- for accounts still paying at the cutoff. Month-end cutoffs are pooled (an account
-- can appear more than once), and cutoffs whose 90-day horizon runs past the data are
-- dropped so no outcome is censored. Stratify by tenure: new accounts are both
-- "recently active" (still onboarding) and inside the window where churn happens, so
-- an unstratified comparison makes activity look like it CAUSES churn.
--
-- On this data: unadjusted 14.0% (active) vs 4.7% (inactive); within tenure bands
-- (<=60d 17.1% vs 17.3%; 61-120d 13.8% vs 12.0%) activity makes little difference.
-- Python: prospective_engagement_dataset() / churn_by_feature() in app/utils/metrics.py.
-- ============================================================
WITH cutoffs AS (
  SELECT TIMESTAMP(LAST_DAY(m)) AS cutoff
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2025-04-01', DATE '2026-04-01', INTERVAL 1 MONTH)) AS m
  WHERE DATE_ADD(LAST_DAY(m), INTERVAL 90 DAY) <= as_of_date
),

paid_active AS (
  SELECT c.cutoff, s.org_id, s.end_date, s.status, o.created_at
  FROM cutoffs c
  JOIN `saas-lifecycle-analytics.raw.subscriptions` s
    ON s.mrr_amount > 0
    AND s.start_date <= DATE(c.cutoff)
    AND (s.end_date IS NULL OR s.end_date > DATE(c.cutoff))   -- still paying at the cutoff
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
),

behavior AS (
  SELECT
    p.cutoff, p.org_id,
    COUNT(DISTINCT IF(e.event_timestamp > TIMESTAMP_SUB(p.cutoff, INTERVAL 28 DAY),
                      DATE(e.event_timestamp), NULL)) AS active_days_recent
  FROM paid_active p
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e
    ON e.org_id = p.org_id
    AND e.event_timestamp <= p.cutoff                         -- nothing after the cutoff
  GROUP BY 1, 2
),

obs AS (
  SELECT
    p.cutoff, p.org_id, b.active_days_recent,
    TIMESTAMP_DIFF(p.cutoff, p.created_at, DAY) AS tenure_days,
    (p.status = 'churned'
      AND p.end_date <= DATE_ADD(DATE(p.cutoff), INTERVAL 90 DAY)) AS churned_90d
  FROM paid_active p
  JOIN behavior b USING (cutoff, org_id)
)

SELECT
  CASE WHEN tenure_days <= 60  THEN '1: <=60d'
       WHEN tenure_days <= 120 THEN '2: 61-120d'
       WHEN tenure_days <= 240 THEN '3: 121-240d'
       ELSE '4: 240d+' END                                      AS tenure_band,
  active_days_recent > 0                                        AS active_in_prior_28d,
  COUNT(*)                                                      AS observations,
  ROUND(AVG(CAST(churned_90d AS INT64)), 4)                     AS churn_rate_90d
FROM obs
GROUP BY 1, 2
ORDER BY 1, 2;
