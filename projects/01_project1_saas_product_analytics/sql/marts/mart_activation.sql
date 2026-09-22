-- ============================================================
-- mart_activation.sql
-- Developer Activation Analysis: Who reaches product value within 7 days?
--
-- Business Question:
--   Which onboarding paths lead to activation? How long does it take?
--   Which milestone (integration, project, teammate) is the strongest
--   predictor of downstream retention?
--
-- Tavus angle:  Integration connected = developer has working API setup
--               Project created = first video/persona generated (aha moment)
-- Meta angle:   Key action within first session = leading indicator of D7 retention
-- ============================================================

-- ── Step 1: First occurrence of each milestone per org ───────────────────────
WITH first_events AS (
  SELECT
    org_id,
    MIN(CASE WHEN event_name = 'workspace_created'    THEN event_timestamp END) AS first_workspace_ts,
    MIN(CASE WHEN event_name = 'teammate_invited'     THEN event_timestamp END) AS first_invite_ts,
    MIN(CASE WHEN event_name = 'integration_connected'THEN event_timestamp END) AS first_integration_ts,
    MIN(CASE WHEN event_name = 'project_created'      THEN event_timestamp END) AS first_project_ts,
    COUNT(DISTINCT event_name) AS distinct_events
  FROM `saas-lifecycle-analytics.raw.event_logs`
  GROUP BY 1
),

-- ── Step 2: Join org metadata + compute days-to-activate ─────────────────────
activation_base AS (
  SELECT
    o.org_id,
    o.created_at,
    o.acquisition_source,
    o.company_size,
    o.industry,

    fe.first_workspace_ts,
    fe.first_integration_ts,
    fe.first_project_ts,
    fe.first_invite_ts,
    fe.distinct_events,

    -- Days from signup to each milestone
    TIMESTAMP_DIFF(fe.first_workspace_ts,    o.created_at, HOUR) / 24.0  AS days_to_workspace,
    TIMESTAMP_DIFF(fe.first_integration_ts,  o.created_at, HOUR) / 24.0  AS days_to_integration,
    TIMESTAMP_DIFF(fe.first_project_ts,      o.created_at, HOUR) / 24.0  AS days_to_project,
    TIMESTAMP_DIFF(fe.first_invite_ts,       o.created_at, HOUR) / 24.0  AS days_to_invite,

    -- Activated = workspace + at least one key action within 7 days
    CASE
      WHEN fe.first_workspace_ts IS NOT NULL
        AND LEAST(
              COALESCE(TIMESTAMP_DIFF(fe.first_integration_ts, o.created_at, DAY), 999),
              COALESCE(TIMESTAMP_DIFF(fe.first_project_ts,     o.created_at, DAY), 999),
              COALESCE(TIMESTAMP_DIFF(fe.first_invite_ts,      o.created_at, DAY), 999)
            ) <= 7
      THEN 1 ELSE 0
    END AS activated_7d,

    -- Which milestone was hit first (primary activation driver)
    CASE
      WHEN fe.first_integration_ts IS NOT NULL
        AND TIMESTAMP_DIFF(fe.first_integration_ts, o.created_at, DAY) <= 7
        AND (fe.first_project_ts IS NULL OR fe.first_integration_ts <= fe.first_project_ts)
        AND (fe.first_invite_ts  IS NULL OR fe.first_integration_ts <= fe.first_invite_ts)
      THEN 'integration_first'
      WHEN fe.first_project_ts IS NOT NULL
        AND TIMESTAMP_DIFF(fe.first_project_ts, o.created_at, DAY) <= 7
        AND (fe.first_invite_ts IS NULL OR fe.first_project_ts <= fe.first_invite_ts)
      THEN 'project_first'
      WHEN fe.first_invite_ts IS NOT NULL
        AND TIMESTAMP_DIFF(fe.first_invite_ts, o.created_at, DAY) <= 7
      THEN 'invite_first'
      ELSE 'not_activated'
    END AS first_activation_milestone

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN first_events fe USING (org_id)
),

-- ── Step 3: Join downstream outcomes to measure milestone → retention value ───
outcomes AS (
  SELECT
    org_id,
    MAX(CASE WHEN mrr_amount > 0 THEN 1 ELSE 0 END) AS ever_paid,
    MAX(CASE WHEN status = 'active' AND mrr_amount > 0 THEN 1 ELSE 0 END) AS currently_active
  FROM `saas-lifecycle-analytics.raw.subscriptions`
  GROUP BY 1
)

-- ── Final: Activation summary by segment ──────────────────────────────────────
SELECT
  ab.acquisition_source,
  ab.company_size,
  ab.first_activation_milestone,

  COUNT(DISTINCT ab.org_id) AS orgs,
  COUNT(DISTINCT CASE WHEN ab.activated_7d = 1 THEN ab.org_id END) AS activated,

  -- P50/P90, not AVG: a handful of orgs that activate weeks or months late would
  -- otherwise inflate the mean and misrepresent the typical time-to-activate.
  APPROX_QUANTILES(CASE WHEN ab.activated_7d = 1 THEN ab.days_to_integration END, 100)[OFFSET(50)]
                                                                                AS p50_days_to_integration,
  APPROX_QUANTILES(CASE WHEN ab.activated_7d = 1 THEN ab.days_to_integration END, 100)[OFFSET(90)]
                                                                                AS p90_days_to_integration,
  APPROX_QUANTILES(CASE WHEN ab.activated_7d = 1 THEN ab.days_to_project END, 100)[OFFSET(50)]
                                                                                AS p50_days_to_project,

  -- Downstream conversion from each milestone type
  ROUND(COUNT(DISTINCT CASE WHEN o.ever_paid        = 1 THEN ab.org_id END)
        / NULLIF(COUNT(DISTINCT ab.org_id), 0), 4)                              AS paid_conversion_rate,
  -- NOTE: not maturity-gated (see mart_cohort_retention.sql for that pattern) —
  -- this divides currently-active by ever-paid regardless of how long each org
  -- has had a subscription, so young cohorts can understate true 60d retention.
  ROUND(COUNT(DISTINCT CASE WHEN o.currently_active = 1 THEN ab.org_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN o.ever_paid = 1 THEN ab.org_id END), 0), 4)
 AS retention_rate

FROM activation_base ab
LEFT JOIN outcomes o USING (org_id)
GROUP BY 1, 2, 3
ORDER BY orgs DESC;
