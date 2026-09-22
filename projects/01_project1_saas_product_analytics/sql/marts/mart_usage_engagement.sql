-- ============================================================
-- mart_usage_engagement.sql
-- Engagement tiers from weekly usage, validated prospectively against churn
--
-- Business Question:
--   Who is engaged, who is going quiet, and does the tier actually warn us
--   about churn before it happens?
--
-- Source: `raw.usage_weekly` (org_id, week_start [Monday], active_users, sessions,
--   features_used). THIS TABLE IS SYNTHETIC WITH A PLANTED SIGNAL (usage is lower for
--   eventual churners and declines over the 3-6 weeks before churn; acquisition
--   channel has no effect). It is a positive control for the method, not a finding
--   about real customers. The five core tables have no ongoing usage and their churn
--   is an independent coin flip, so nothing in them can predict it.
--
-- Design (what makes the validation valid):
--   * Features use only weeks that had fully ended by the cutoff.
--   * The outcome is churn in the next `horizon_days`, for accounts still paying at
--     the cutoff. A "went quiet" warning has a short lead time (weeks), so the horizon
--     matters: the at-risk lift is ~6.5x at 30 days, ~3.6x at 60, ~2.7x at 90.
--   * Weekly cutoffs are pooled. An account appears at many cutoffs, so counts are
--     observations, not independent accounts.
--   * The power cut is relative to the paying population at each cutoff (80th
--     percentile of recent sessions), so tiers never look at churn.
--
-- Tier precedence: dormant > at_risk > power > active
--   dormant : no sessions in the last 4 full weeks
--   at_risk : >= 12 sessions in the 4 weeks before that AND recent <= 50% of it
--             ("used to be engaged, has gone quiet"; a new low-usage account is not at risk)
--   power   : recent sessions >= population P80 AND mean features used >= 3
--   active  : everyone else with recent usage
--
-- Python equivalent: usage_engagement_features() / assign_engagement_tiers() /
--   prospective_usage_dataset() in app/utils/metrics.py (Churn Risk page).
--   Checked against it via DuckDB: 27,686 observations at 30 days, at_risk 245 obs
--   at 18.0% churn, power 4,493 at 0.5%, active 22,948 at 3.0%.
-- ============================================================

DECLARE as_of_date DATE DEFAULT DATE '2026-04-27';
DECLARE horizon_days INT64 DEFAULT 30;

-- ── Step 1: Weekly cutoffs whose churn horizon is fully observed ──────────────
WITH cutoffs AS (
  SELECT cutoff
  FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2025-04-28', as_of_date, INTERVAL 7 DAY)) AS cutoff
  WHERE DATE_ADD(cutoff, INTERVAL horizon_days DAY) <= as_of_date
),

-- ── Step 2: Accounts paying at each cutoff ────────────────────────────────────
paying AS (
  SELECT
    c.cutoff,
    DATE_TRUNC(DATE_SUB(c.cutoff, INTERVAL 7 DAY), WEEK(MONDAY)) AS last_week,  -- latest full week
    s.org_id, s.status, s.end_date
  FROM cutoffs c
  JOIN `saas-lifecycle-analytics.raw.subscriptions` s
    ON s.mrr_amount > 0
    AND s.start_date <= c.cutoff
    AND (s.end_date IS NULL OR s.end_date > c.cutoff)
),

-- ── Step 3: Frequency, depth, and the prior-window baseline ───────────────────
-- recent = last 4 full weeks; prior = the 4 weeks before that.
features AS (
  SELECT
    p.cutoff, p.org_id, p.status, p.end_date,
    IFNULL(SUM(IF(u.week_start BETWEEN DATE_SUB(p.last_week, INTERVAL 21 DAY) AND p.last_week,
                  u.sessions, NULL)), 0)                                   AS recent_sessions,
    IFNULL(SUM(IF(u.week_start BETWEEN DATE_SUB(p.last_week, INTERVAL 49 DAY)
                                   AND DATE_SUB(p.last_week, INTERVAL 28 DAY),
                  u.sessions, NULL)), 0)                                   AS prior_sessions,
    IFNULL(AVG(IF(u.week_start BETWEEN DATE_SUB(p.last_week, INTERVAL 21 DAY) AND p.last_week,
                  u.features_used, NULL)), 0)                              AS features_used
  FROM paying p
  LEFT JOIN `saas-lifecycle-analytics.raw.usage_weekly` u
    ON u.org_id = p.org_id
    AND u.week_start BETWEEN DATE_SUB(p.last_week, INTERVAL 49 DAY) AND p.last_week  -- nothing after the cutoff
  GROUP BY 1, 2, 3, 4
),

with_cut AS (
  SELECT *, PERCENTILE_CONT(recent_sessions, 0.8) OVER (PARTITION BY cutoff) AS power_cut
  FROM features
),

-- ── Step 4: Tier + outcome ────────────────────────────────────────────────────
tiered AS (
  SELECT
    cutoff, org_id,
    CASE
      WHEN recent_sessions = 0 THEN 'dormant'
      WHEN prior_sessions >= 12 AND recent_sessions <= 0.5 * prior_sessions THEN 'at_risk'
      WHEN recent_sessions >= power_cut AND features_used >= 3 THEN 'power'
      ELSE 'active'
    END AS tier,
    (status = 'churned'
      AND end_date <= DATE_ADD(cutoff, INTERVAL horizon_days DAY)) AS churned_in_horizon
  FROM with_cut
)

-- ── Final: churn by tier ──────────────────────────────────────────────────────
SELECT
  tier,
  COUNT(*)                                                    AS observations,
  ROUND(AVG(CAST(churned_in_horizon AS INT64)), 4)            AS churn_rate,
  ROUND(SAFE_DIVIDE(AVG(CAST(churned_in_horizon AS INT64)),
        (SELECT AVG(CAST(churned_in_horizon AS INT64)) FROM tiered)), 1) AS lift_vs_overall
FROM tiered
GROUP BY tier
ORDER BY CASE tier WHEN 'power' THEN 1 WHEN 'active' THEN 2 WHEN 'at_risk' THEN 3 ELSE 4 END;
