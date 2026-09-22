-- ============================================================
-- mart_experiment.sql
-- A/B Experiment Analysis: Onboarding Experiment Readout
--
-- Business Question:
--   Did the guided onboarding flow increase activation?
--   Is the lift statistically significant?
--   Does the effect hold across all segments, or is there HTE?
--   Did activation gains translate to paid conversion and retention?
--
-- Meta angle:  Design and analyze multivariate experiments; synthesize results
--              to make data-informed launch decisions (ship / iterate / kill)
-- Tavus angle: Onboarding experiment → developer time-to-first-API-call impact
-- ============================================================

-- ── Step 1: Assign each org to its experiment variant ─────────────────────────
WITH assignments AS (
  SELECT
    ea.org_id,
    ea.variant,          -- 'control' or 'treatment'
    ea.eligible_segment,
    ea.assigned_at,
    o.acquisition_source,
    o.company_size
  FROM `saas-lifecycle-analytics.raw.experiment_assignments` ea
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  WHERE ea.experiment_id = 'onboarding_v2'   -- adjust to actual experiment_id
),

-- ── Step 2: Compute primary metric (7-day activation) per org ─────────────────
org_outcomes AS (
  SELECT
    o.org_id,

    -- Primary metric: activated within 7 days
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
        AND ws.first_workspace IS NOT NULL
      THEN 1 ELSE 0
    END) AS activated_7d,

    -- Guardrail metric 1: paid conversion
    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END) AS ever_paid,

    -- Guardrail metric 2: 60-day retention
    MAX(CASE
      WHEN s.mrr_amount > 0 AND s.status = 'active'
        AND DATE_ADD(s.start_date, INTERVAL 60 DAY) <= CURRENT_DATE()
      THEN 1 ELSE 0
    END) AS retained_60d,

    -- Secondary: integration connected (developer activation)
    MAX(CASE WHEN e.event_name = 'integration_connected' THEN 1 ELSE 0 END) AS integration_connected

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN (
    SELECT org_id, MIN(event_timestamp) AS first_workspace
    FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name = 'workspace_created'
    GROUP BY 1
  ) ws USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1
),

-- ── Step 3: Combine assignments with outcomes ──────────────────────────────────
experiment_data AS (
  SELECT
    a.*,
    COALESCE(o.activated_7d,         0) AS activated_7d,
    COALESCE(o.ever_paid,            0) AS ever_paid,
    COALESCE(o.retained_60d,         0) AS retained_60d,
    COALESCE(o.integration_connected,0) AS integration_connected
  FROM assignments a
  LEFT JOIN org_outcomes o USING (org_id)
),

-- ── Step 4: Variant-level aggregation ─────────────────────────────────────────
variant_summary AS (
  SELECT
    variant,
    company_size,
    COUNT(DISTINCT org_id) AS n,
    SUM(activated_7d) AS activated,
    SUM(ever_paid) AS paid,
    SUM(retained_60d) AS retained,
    SUM(integration_connected) AS integrations,

    -- Rates
    ROUND(AVG(activated_7d),         4) AS activation_rate,
    ROUND(AVG(ever_paid),            4) AS paid_rate,
    ROUND(AVG(retained_60d),         4) AS retention_rate,
    ROUND(AVG(integration_connected),4) AS integration_rate

  FROM experiment_data
  GROUP BY 1, 2
),

-- ── Step 5: Compute lift and z-score (statistical significance in SQL) ─────────
-- Two-proportion z-test:
--   p1 = treatment rate, p2 = control rate
--   pooled_p = (activated_treatment + activated_control) / (n_treatment + n_control)
--   z = (p1 - p2) / sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
control AS (
  SELECT company_size, n, activation_rate AS ctrl_rate, activated AS ctrl_activated
  FROM variant_summary WHERE variant = 'control'
),
treatment AS (
  SELECT company_size, n, activation_rate AS trt_rate, activated AS trt_activated
  FROM variant_summary WHERE variant = 'treatment'
)

SELECT
  t.company_size,
  c.n AS n_control,
  t.n AS n_treatment,
  ROUND(c.ctrl_rate, 4) AS control_activation_rate,
  ROUND(t.trt_rate, 4) AS treatment_activation_rate,
  ROUND(t.trt_rate - c.ctrl_rate, 4) AS absolute_lift,
  ROUND((t.trt_rate - c.ctrl_rate) / NULLIF(c.ctrl_rate, 0), 4) AS relative_lift,

  -- Pooled proportion for z-test
  ROUND(
    (c.ctrl_activated + t.trt_activated) / NULLIF(c.n + t.n, 0)
  , 4) AS pooled_p,

  -- Z-score (|z| > 1.96 → p < 0.05)
  ROUND(
    (t.trt_rate - c.ctrl_rate) /
    NULLIF(
      SQRT(
        ((c.ctrl_activated + t.trt_activated) / NULLIF(c.n + t.n, 0))
        * (1 - (c.ctrl_activated + t.trt_activated) / NULLIF(c.n + t.n, 0))
        * (1.0/c.n + 1.0/t.n)
      ), 0
    )
  , 3) AS z_score,

  -- Decision rule
  CASE
    WHEN ABS(
      (t.trt_rate - c.ctrl_rate) /
      NULLIF(
        SQRT(
          ((c.ctrl_activated + t.trt_activated) / NULLIF(c.n + t.n, 0))
          * (1 - (c.ctrl_activated + t.trt_activated) / NULLIF(c.n + t.n, 0))
          * (1.0/c.n + 1.0/t.n)
        ), 0
      )
    ) >= 1.96 THEN 'Statistically Significant (p < 0.05)'
    ELSE 'Not Significant'
  END AS significance

FROM control c
JOIN treatment t USING (company_size)
ORDER BY n_treatment DESC;

-- ============================================================
-- SUPPLEMENTAL: Sample size — was this experiment adequately powered?
-- "We ran this and it wasn't significant — do we need more data, or is the
--  effect just too small to matter?" Answering that requires a pre-specified
--  MDE (the smallest lift worth caring about), NOT the observed lift — using
--  the observed lift as its own target is circular: a truly null result has
--  ~0 observed lift, which would demand an absurd sample size to "detect,"
--  making every null result look under-powered no matter how much data was
--  actually collected.
--
-- Same formula as mart_multivariate.sql's sample-size calculator:
--   n = (z_alpha + z_power)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2
-- ============================================================
WITH params AS (
  SELECT
    0.35 AS baseline_rate,   -- control activation_rate from the query above
    0.05 AS mde,             -- pre-specified minimum detectable effect (5pp)
    1.96 AS z_alpha,         -- alpha = 0.05, two-tailed
    0.842 AS z_power         -- power = 0.80
)
SELECT
  baseline_rate,
  baseline_rate + mde                                                AS target_rate,
  mde                                                                 AS minimum_detectable_effect,
  CEILING(
    POW(z_alpha + z_power, 2)
    * (baseline_rate * (1 - baseline_rate) + (baseline_rate + mde) * (1 - (baseline_rate + mde)))
    / POW(mde, 2)
  )                                                                   AS required_n_per_variant
FROM params;
-- Python equivalent (uses this project's actual control rate, not a hardcoded
-- 0.35): `required_sample_size()` in app/utils/metrics.py, wrapped by
-- `experiment_decision()`, which folds this into a full SHIP/ITERATE/CONTINUE/
-- KILL verdict alongside significance and guardrail checks.
