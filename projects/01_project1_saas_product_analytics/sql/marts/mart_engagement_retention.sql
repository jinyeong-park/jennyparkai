-- ============================================================
-- mart_engagement_retention.sql
-- Product Engagement Retention: D30 / D60 / D90, by signup cohort
--
-- Business Question:
--   Of everyone who signed up in a given month — not just accounts that
--   converted to paid — what fraction had any product activity 30/60/90
--   days later? Is that different from paid/logo retention (mart_cohort_retention.sql)?
--
-- This is a different metric from mart_cohort_retention.sql, not a duplicate:
--   - mart_cohort_retention.sql: "is the subscription still active?" — cohorted
--     by paid-conversion month, denominator is paid accounts only.
--   - mart_engagement_retention.sql (this file): "did they still use the
--     product?" — cohorted by signup month, denominator is every signup.
-- A gap between the two is expected (most signups never pay), but the size of
-- the gap shows how much usage drop-off happens outside the subscription
-- relationship, which subscription-status tracking alone would never surface.
-- ============================================================

-- ── Step 1: Cohort every org by signup month ──────────────────────────────────
WITH cohorts AS (
  SELECT
    org_id,
    created_at,
    DATE_TRUNC(DATE(created_at), MONTH) AS cohort_month
  FROM `saas-lifecycle-analytics.raw.organizations`
),

-- ── Step 2: Was there any product event in each day-window after signup? ──────
-- Day 0 is excluded — signup-day activity is onboarding, not a return visit.
--   D30 window = days 1-30, D60 = days 31-60, D90 = days 61-90.
activity AS (
  SELECT
    c.org_id,
    c.cohort_month,

    MAX(CASE
      WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 1 AND 30
      THEN 1 ELSE 0
    END) AS active_d30,

    MAX(CASE
      WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 31 AND 60
      THEN 1 ELSE 0
    END) AS active_d60,

    MAX(CASE
      WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 61 AND 90
      THEN 1 ELSE 0
    END) AS active_d90

  FROM cohorts c
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1, 2
)

-- ── Final: Cohort engagement retention (maturity-gated) ────────────────────────
SELECT
  cohort_month,
  COUNT(DISTINCT org_id)                                                     AS cohort_size,

  -- Each horizon is NULL (excluded, not zero) until the cohort is old enough
  -- to have reached it — otherwise recent cohorts drag the rate down artificially.
  CASE WHEN DATE_ADD(cohort_month, INTERVAL 30 DAY) <= CURRENT_DATE()
    THEN ROUND(AVG(active_d30), 4)
  END AS retention_d30,

  CASE WHEN DATE_ADD(cohort_month, INTERVAL 60 DAY) <= CURRENT_DATE()
    THEN ROUND(AVG(active_d60), 4)
  END AS retention_d60,

  CASE WHEN DATE_ADD(cohort_month, INTERVAL 90 DAY) <= CURRENT_DATE()
    THEN ROUND(AVG(active_d90), 4)
  END AS retention_d90

FROM activity
GROUP BY cohort_month
ORDER BY cohort_month DESC;
