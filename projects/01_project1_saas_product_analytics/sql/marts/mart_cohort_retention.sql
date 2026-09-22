-- ============================================================
-- mart_cohort_retention.sql
-- Monthly Cohort Retention: D30 / D60 / D90
--
-- Business Question:
--   Of users who paid in a given month, what fraction are still
--   active at 30, 60, and 90 days? How does retention differ
--   by activation status and acquisition source?
--
-- Tavus angle:  Are developers who integrated the API staying engaged?
--               Do API-first accounts retain better than product-first?
-- Meta angle:   Long-term retention as the ultimate signal of product-market fit.
--               Which cohorts show meaningful improvement over time?
-- ============================================================

-- ── Step 1: Define paid cohort (month of first paid subscription) ─────────────
WITH paid_cohorts AS (
  SELECT
    s.org_id,
    DATE_TRUNC(s.start_date, MONTH)  AS cohort_month,
    s.start_date AS paid_start_date,
    s.end_date,
    s.status,
    s.mrr_amount
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  WHERE s.mrr_amount > 0
  QUALIFY ROW_NUMBER() OVER (PARTITION BY s.org_id ORDER BY s.start_date) = 1
  -- Take only first paid subscription per org
),

-- ── Step 2: Tag activation status for each paid org ───────────────────────────
activation_tag AS (
  SELECT
    o.org_id,
    o.acquisition_source,
    o.company_size,
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
        AND fe_ws.first_workspace IS NOT NULL
      THEN 1 ELSE 0
    END) AS activated_7d
  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN (
    SELECT org_id, MIN(event_timestamp) AS first_workspace
    FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name = 'workspace_created'
    GROUP BY 1
  ) fe_ws USING (org_id)
  GROUP BY 1, 2, 3
),

-- ── Step 3: Observe retention at 30/60/90-day horizons ────────────────────────
-- An account is "retained at 30d" if its subscription is still active
-- 30 days after paid_start_date (end_date is null or > start+30)
retention_flags AS (
  SELECT
    pc.org_id,
    pc.cohort_month,
    pc.paid_start_date,
    pc.mrr_amount,
    at.activated_7d,
    at.acquisition_source,
    at.company_size,

    -- Retention = subscription still active at horizon
    CASE
      WHEN pc.end_date IS NULL OR pc.end_date > DATE_ADD(pc.paid_start_date, INTERVAL 30 DAY)
      THEN 1 ELSE 0
    END AS retained_30d,

    CASE
      WHEN DATE_ADD(pc.paid_start_date, INTERVAL 60 DAY) <= CURRENT_DATE()   -- maturity check
        AND (pc.end_date IS NULL OR pc.end_date > DATE_ADD(pc.paid_start_date, INTERVAL 60 DAY))
      THEN 1
      WHEN DATE_ADD(pc.paid_start_date, INTERVAL 60 DAY) > CURRENT_DATE()
      THEN NULL   -- immature cohort: exclude from denominator
      ELSE 0
    END AS retained_60d,

    CASE
      WHEN DATE_ADD(pc.paid_start_date, INTERVAL 90 DAY) <= CURRENT_DATE()
        AND (pc.end_date IS NULL OR pc.end_date > DATE_ADD(pc.paid_start_date, INTERVAL 90 DAY))
      THEN 1
      WHEN DATE_ADD(pc.paid_start_date, INTERVAL 90 DAY) > CURRENT_DATE()
      THEN NULL
      ELSE 0
    END AS retained_90d

  FROM paid_cohorts pc
  LEFT JOIN activation_tag at USING (org_id)
)

-- ── Final: Cohort retention matrix ────────────────────────────────────────────
SELECT
  cohort_month,
  acquisition_source,
  company_size,
  activated_7d,

  COUNT(DISTINCT org_id) AS cohort_size,
  SUM(mrr_amount) AS beginning_mrr,

  -- 30-day retention (all cohorts mature enough)
  ROUND(AVG(retained_30d), 4) AS retention_30d,

  -- 60-day retention (exclude immature cohorts via COUNT on non-null)
  ROUND(COUNTIF(retained_60d = 1) / NULLIF(COUNTIF(retained_60d IS NOT NULL), 0), 4)
 AS retention_60d,

  -- 90-day retention
  ROUND(COUNTIF(retained_90d = 1) / NULLIF(COUNTIF(retained_90d IS NOT NULL), 0), 4)
 AS retention_90d,

  -- NRR proxy: retained MRR / beginning MRR at 60d horizon
  ROUND(SUM(CASE WHEN retained_60d = 1 THEN mrr_amount ELSE 0 END)
        / NULLIF(SUM(CASE WHEN retained_60d IS NOT NULL THEN mrr_amount ELSE 0 END), 0), 4)
 AS nrr_60d_proxy

FROM retention_flags
GROUP BY 1, 2, 3, 4
ORDER BY cohort_month DESC, cohort_size DESC;
