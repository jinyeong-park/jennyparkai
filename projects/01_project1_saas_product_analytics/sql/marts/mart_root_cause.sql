-- ============================================================
-- mart_root_cause.sql
-- Root Cause Analysis: Why Did a Key Metric Move?
--
-- Business Question:
--   Activation rate dropped 4pp week-over-week. Is this a real product
--   regression, or did the user mix change (more Enterprise, harder to activate)?
--
-- Technique: Mix-shift decomposition (constant-mix vs. observed)
--   If the population mix stayed the same but rates changed → rate effect (product issue)
--   If rates stayed the same but mix changed → mix effect (acquisition change)
--   True change = rate effect + mix effect + interaction effect (exact)
--
-- Data Analyst III / San Jose angle: "Root-cause analysis and identifying
--   why key metrics move" — explicit job requirement
-- Meta angle: "Understand trends in user behavior to influence growth strategy"
-- ============================================================

-- ── Step 1: Weekly activation rate by segment ─────────────────────────────────
WITH weekly_segments AS (
  SELECT
    DATE_TRUNC(DATE(o.created_at), WEEK) AS week_start,
    o.company_size,
    o.acquisition_source,
    COUNT(DISTINCT o.org_id) AS signups,

    COUNT(DISTINCT CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN o.org_id
    END) AS activated

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1, 2, 3
),

-- ── Step 2: Compute overall weekly rate and segment mix ───────────────────────
weekly_totals AS (
  SELECT
    week_start,
    SUM(signups) AS total_signups,
    SUM(activated) AS total_activated,
    SUM(activated) / NULLIF(SUM(signups), 0) AS overall_activation_rate
  FROM weekly_segments
  GROUP BY 1
),

-- ── Step 3: Pick the two periods to compare ──────────────────────────────────
-- Compare the two most recent COMPLETE periods. The newest week is usually
-- partial (only some days of signups), so ranking naively by week_start DESC
-- compares a full week against a handful of orgs and manufactures a "drop".
-- Weekly cohorts here are also small (~40-50 orgs), so segment-level weekly
-- rates swing 10-20pp on noise alone; a monthly grain (freq="M" in the Python
-- version) is far steadier. Swap the DATE_TRUNC unit to compare months.
week_labels AS (
  SELECT
    week_start,
    ROW_NUMBER() OVER (ORDER BY week_start DESC) AS week_rank
  FROM weekly_totals
  WHERE total_signups >= 30   -- crude completeness guard: skip a partial trailing week
),

-- Mix is computed within each period BEFORE joining, so a segment missing in
-- one period can't distort the other period's shares.
current_week_segments AS (
  SELECT
    ws.company_size, ws.acquisition_source, ws.signups, ws.activated,
    SAFE_DIVIDE(ws.activated, ws.signups)                        AS rate,
    SAFE_DIVIDE(ws.signups, SUM(ws.signups) OVER ())             AS mix
  FROM weekly_segments ws
  JOIN week_labels wl USING (week_start)
  WHERE wl.week_rank = 1
),

prior_week_segments AS (
  SELECT
    ws.company_size, ws.acquisition_source, ws.signups, ws.activated,
    SAFE_DIVIDE(ws.activated, ws.signups)                        AS rate,
    SAFE_DIVIDE(ws.signups, SUM(ws.signups) OVER ())             AS mix
  FROM weekly_segments ws
  JOIN week_labels wl USING (week_start)
  WHERE wl.week_rank = 2
),

-- ── Step 4: Exact rate / mix / interaction decomposition ─────────────────────
--   rate effect        = (cur_rate - prior_rate) x prior_mix
--   mix effect         = (cur_mix  - prior_mix)  x (prior_rate - prior_overall_rate)
--   interaction effect = (cur_mix  - prior_mix)  x (cur_rate - prior_rate)
-- The first two alone are a first-order approximation: they omit the
-- interaction term, so they only sum to the true change when rate OR mix
-- (not both) moved. With all three, SUM(total_contribution) equals the
-- actual change in the overall rate exactly.
--
-- The mix effect is centered on the prior OVERALL rate. Uncentered
-- (Δmix x prior_rate) has the same total, because mix shifts sum to zero, but
-- per segment it is misleading: a low-activating channel that grows its share
-- drags the overall rate down, yet uncentered it shows a POSITIVE number just
-- because its rate is above zero. Centered, it is negative exactly when a
-- segment gained share while activating below average.
--
-- A segment present in only one period has no rate for the other; fill it with
-- the observed rate so it counts as a pure mix effect instead of a NULL that
-- silently drops its contribution from the SUM.
joined AS (
  SELECT
    COALESCE(c.company_size, p.company_size)               AS company_size,
    COALESCE(c.acquisition_source, p.acquisition_source)   AS acquisition_source,
    COALESCE(p.mix, 0)                                     AS prior_mix,
    COALESCE(c.mix, 0)                                     AS cur_mix,
    COALESCE(p.rate, c.rate)                               AS prior_rate,
    COALESCE(c.rate, p.rate)                               AS cur_rate
  FROM current_week_segments c
  FULL OUTER JOIN prior_week_segments p
    USING (company_size, acquisition_source)
),

decomposition AS (
  SELECT
    *,
    (cur_rate - prior_rate) * prior_mix                    AS rate_effect,
    (cur_mix - prior_mix)
      * (prior_rate - SUM(prior_mix * prior_rate) OVER ()) AS mix_effect,
    (cur_mix - prior_mix) * (cur_rate - prior_rate)        AS interaction_effect
  FROM joined
)

-- ── Final: Segment breakdown (SUM(total_contribution) = overall change) ──────
SELECT
  company_size,
  acquisition_source,
  ROUND(prior_rate, 4)                                          AS prior_activation_rate,
  ROUND(cur_rate, 4)                                            AS current_activation_rate,
  ROUND(prior_mix, 4)                                           AS prior_mix,
  ROUND(cur_mix, 4)                                             AS current_mix,
  ROUND(rate_effect, 4)                                         AS rate_effect_contribution,
  ROUND(mix_effect, 4)                                          AS mix_effect_contribution,
  ROUND(interaction_effect, 4)                                  AS interaction_contribution,
  ROUND(rate_effect + mix_effect + interaction_effect, 4)       AS total_contribution,
  CASE
    WHEN ABS(rate_effect) > ABS(mix_effect + interaction_effect) THEN 'Rate-driven (product/UX issue)'
    WHEN ABS(mix_effect + interaction_effect) > ABS(rate_effect) THEN 'Mix-driven (acquisition channel shift)'
    ELSE 'Mixed'
  END AS diagnosis

FROM decomposition
ORDER BY ABS(rate_effect + mix_effect + interaction_effect) DESC;

-- Python equivalent, on this project's data: `mix_rate_decomposition()` /
-- `summarize_decomposition()` in app/utils/metrics.py (monthly grain), shown on
-- the Activation dashboard page. NB: a decomposition says WHERE a change came
-- from, not whether it was real — test the change itself first (two-proportion
-- test), and remember the "biggest drop" among many periods is a
-- multiple-comparisons pick.

-- ============================================================
-- SUPPLEMENTAL: Metric decomposition by funnel stage
-- "The activation rate dropped — which step broke?"
-- ============================================================

WITH weekly_funnel AS (
  SELECT
    DATE_TRUNC(DATE(o.created_at), WEEK) AS week_start,
    COUNT(DISTINCT o.org_id) AS signups,
    COUNT(DISTINCT CASE WHEN e1.org_id IS NOT NULL THEN o.org_id END) AS workspace_created,
    COUNT(DISTINCT CASE WHEN e2.org_id IS NOT NULL THEN o.org_id END) AS integration_connected,
    COUNT(DISTINCT CASE WHEN act.org_id IS NOT NULL THEN o.org_id END) AS activated

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN (
    SELECT DISTINCT org_id FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name = 'workspace_created'
  ) e1 USING (org_id)
  LEFT JOIN (
    SELECT DISTINCT org_id FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name = 'integration_connected'
  ) e2 USING (org_id)
  LEFT JOIN (
    -- Same 7-day window as the activation definition everywhere else; without
    -- it, "activated" here meant "ever took a key action", which inflates the
    -- rate and won't reconcile with the decomposition above.
    SELECT e.org_id
    FROM `saas-lifecycle-analytics.raw.event_logs` e
    JOIN `saas-lifecycle-analytics.raw.organizations` org USING (org_id)
    WHERE e.event_name IN ('teammate_invited','integration_connected','project_created')
      AND TIMESTAMP_DIFF(e.event_timestamp, org.created_at, DAY) <= 7
    GROUP BY e.org_id
  ) act USING (org_id)
  GROUP BY 1
)

SELECT
  week_start,
  signups,
  ROUND(workspace_created / NULLIF(signups, 0), 3) AS workspace_rate,
  ROUND(integration_connected / NULLIF(workspace_created, 0), 3) AS workspace_to_integration_rate,
  ROUND(activated / NULLIF(signups, 0), 3) AS overall_activation_rate,

  -- WoW delta for each step
  LAG(ROUND(workspace_created / NULLIF(signups, 0), 3)) OVER (ORDER BY week_start)
 AS prior_workspace_rate,
  LAG(ROUND(activated / NULLIF(signups, 0), 3)) OVER (ORDER BY week_start)
 AS prior_activation_rate,

  ROUND(
    activated / NULLIF(signups, 0)
    - LAG(activated / NULLIF(signups, 0)) OVER (ORDER BY week_start)
  , 3) AS activation_wow_delta

FROM weekly_funnel
ORDER BY week_start DESC;
