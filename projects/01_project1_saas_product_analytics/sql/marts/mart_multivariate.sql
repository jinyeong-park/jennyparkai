-- ============================================================
-- mart_multivariate.sql
-- Multivariate Experiment Analysis: A/B/C/D Variant Comparison
--
-- Business Question:
--   We're testing 3 onboarding variants simultaneously. Which one wins?
--   Are any variants significantly better than control?
--   How do we account for multiple comparisons (false positives)?
--
-- Meta angle: "Experimentation experience to design multivariate tests,
--   synthesize test results and build frameworks to make data-informed
--   launch decisions" — explicit Meta requirement
--
-- Framework:
--   1. Pairwise comparison: each variant vs. control
--   2. Bonferroni correction for multiple comparisons
--   3. Segment-level HTE for winner variant
--   4. Decision framework: ship / iterate / kill per variant
--
-- Python equivalent (same variant simulation + Bonferroni logic, run against
-- this project's real dataset): `simulate_multivariate_variants()` and
-- `bonferroni_pairwise_results()` in app/utils/metrics.py, surfaced on the
-- "Multiple comparisons" section of the Experiments dashboard page.
-- ============================================================

-- ── Step 1: Simulate multivariate variants from experiment data ───────────────
-- In the real dataset, variant is 'control' or 'treatment'.
-- Here we extend the framework to A/B/C/D structure for interview demonstration.
-- In production: experiment_assignments would have variant IN ('control','v1','v2','v3')

WITH variants AS (
  SELECT
    ea.org_id,
    -- Simulate 4 variants by splitting treatment group
    CASE
      WHEN ea.variant = 'control' THEN 'control'
      WHEN ea.variant = 'treatment' AND MOD(ABS(FARM_FINGERPRINT(ea.org_id)), 3) = 0 THEN 'v1_guided_checklist'
      WHEN ea.variant = 'treatment' AND MOD(ABS(FARM_FINGERPRINT(ea.org_id)), 3) = 1 THEN 'v2_video_walkthrough'
      ELSE 'v3_interactive_demo'
    END AS variant,
    ea.eligible_segment,
    o.company_size,
    o.acquisition_source
  FROM `saas-lifecycle-analytics.raw.experiment_assignments` ea
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  WHERE ea.experiment_id = 'onboarding_v2'
),

-- ── Step 2: Compute outcomes per org ─────────────────────────────────────────
outcomes AS (
  SELECT
    v.org_id,
    v.variant,
    v.company_size,
    v.acquisition_source,

    -- Primary metric
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END) AS activated,

    -- Secondary: integration specifically (developer aha moment)
    MAX(CASE WHEN e.event_name = 'integration_connected' THEN 1 ELSE 0 END) AS integrated,

    -- Guardrail: paid conversion
    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END) AS paid

  FROM variants v
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1, 2, 3, 4
),

-- ── Step 3: Variant-level aggregation ────────────────────────────────────────
variant_agg AS (
  SELECT
    variant,
    COUNT(*) AS n,
    SUM(activated) AS activated,
    SUM(integrated) AS integrated,
    SUM(paid) AS paid,
    AVG(activated) AS activation_rate,
    AVG(integrated) AS integration_rate,
    AVG(paid) AS paid_rate
  FROM outcomes
  GROUP BY 1
),

-- ── Step 4: Control baseline ──────────────────────────────────────────────────
control_baseline AS (
  SELECT
    n AS n_ctrl,
    activated AS act_ctrl,
    activation_rate AS ctrl_rate
  FROM variant_agg
  WHERE variant = 'control'
),

-- ── Step 5: Pairwise z-test vs control with Bonferroni correction ─────────────
-- Bonferroni: divide alpha by the number of comparisons k (= treatment variants).
-- k is counted from the data, and the critical z is looked up by k, so adding a
-- variant changes the threshold automatically. (BigQuery has no inverse-normal
-- function, hence the lookup; values are two-tailed z at alpha = 0.05 / k.)
--   k=1 -> 1.960   k=2 -> 2.241   k=3 -> 2.394   k=4 -> 2.498   k=5 -> 2.576
critical_values AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS k, 1.960 AS z_bonferroni),
    STRUCT(2, 2.241), STRUCT(3, 2.394), STRUCT(4, 2.498), STRUCT(5, 2.576)
  ])
),
bonferroni AS (
  SELECT
    n.k,
    0.05 / n.k          AS adjusted_alpha,
    cv.z_bonferroni     AS z_threshold
  FROM (SELECT COUNT(*) AS k FROM variant_agg WHERE variant != 'control') n
  JOIN critical_values cv USING (k)   -- no row (=> no results) if k > 5: add a row rather than guess
),
pairwise AS (
  SELECT
    v.variant,
    v.n AS n_treatment,
    c.n_ctrl,
    ROUND(c.ctrl_rate, 4) AS control_rate,
    ROUND(v.activation_rate, 4) AS treatment_rate,
    ROUND(v.activation_rate - c.ctrl_rate, 4) AS absolute_lift,
    ROUND((v.activation_rate - c.ctrl_rate) / NULLIF(c.ctrl_rate, 0), 4) AS relative_lift,

    -- Pooled proportion
    ROUND((v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0), 4) AS pooled_p,

    -- Z-score
    ROUND(
      (v.activation_rate - c.ctrl_rate) /
      NULLIF(SQRT(
        ((v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
        * (1 - (v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
        * (1.0/v.n + 1.0/c.n_ctrl)
      ), 0)
    , 3) AS z_score,

    -- Standard alpha (no correction)
    CASE
      WHEN ABS(
        (v.activation_rate - c.ctrl_rate) /
        NULLIF(SQRT(
          ((v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
          * (1 - (v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
          * (1.0/v.n + 1.0/c.n_ctrl)
        ), 0)
      ) >= 1.96 THEN TRUE ELSE FALSE
    END AS significant_no_correction,

    -- Bonferroni-corrected (threshold comes from the bonferroni CTE, driven by k)
    CASE
      WHEN ABS(
        (v.activation_rate - c.ctrl_rate) /
        NULLIF(SQRT(
          ((v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
          * (1 - (v.activated + c.act_ctrl) / NULLIF(v.n + c.n_ctrl, 0))
          * (1.0/v.n + 1.0/c.n_ctrl)
        ), 0)
      ) >= b.z_threshold THEN TRUE ELSE FALSE
    END                                                             AS significant_bonferroni

  FROM variant_agg v
  CROSS JOIN control_baseline c
  CROSS JOIN bonferroni b
  WHERE v.variant != 'control'
)

-- ── Final: Decision framework per variant ────────────────────────────────────
SELECT
  variant,
  n_treatment,
  control_rate,
  treatment_rate,
  absolute_lift,
  CONCAT(ROUND(relative_lift * 100, 1), '%') AS relative_lift_pct,
  z_score,
  significant_no_correction,
  significant_bonferroni,

  -- Decision rule
  CASE
    WHEN significant_bonferroni AND absolute_lift > 0
      THEN 'SHIP — significant after multiple-comparison correction'
    WHEN significant_no_correction AND NOT significant_bonferroni AND absolute_lift > 0
      THEN 'ITERATE — significant without correction; increase sample size to confirm'
    WHEN absolute_lift < 0
      THEN 'KILL — treatment underperforms control'
    ELSE 'HOLD — not significant; continue experiment'
  END AS decision

FROM pairwise
ORDER BY z_score DESC;

-- ============================================================
-- SUPPLEMENTAL: Sample size calculator
-- "How many accounts do we need to detect a 5pp lift at 80% power?"
-- ============================================================
-- Given:
--   baseline_rate  = 0.35 (control activation rate)
--   minimum_detectable_effect = 0.05 (5pp lift we care about)
--   alpha = 0.05 (two-tailed, z=1.96)
--   power = 0.80 (z=0.842)
--
-- Formula: n = (z_alpha + z_power)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2

SELECT
  0.35 AS baseline_rate,
  0.40 AS target_rate,
  0.05 AS minimum_detectable_effect,
  ROUND(
    POW(1.96 + 0.842, 2)
    * (0.35 * (1 - 0.35) + 0.40 * (1 - 0.40))
    / POW(0.40 - 0.35, 2)
  , 0) AS required_n_per_variant,
  ROUND(
    POW(1.96 + 0.842, 2)
    * (0.35 * (1 - 0.35) + 0.40 * (1 - 0.40))
    / POW(0.40 - 0.35, 2)
  , 0) * 4 AS total_n_for_4_variants;
