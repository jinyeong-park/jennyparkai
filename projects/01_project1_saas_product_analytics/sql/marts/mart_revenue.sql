-- ============================================================
-- mart_revenue.sql
-- Revenue Analytics: MRR, ARPA, Trial-to-Paid, CAC Proxy, NRR
--
-- Business Question:
--   What is our MRR trend? Which plan/segment drives the most revenue?
--   What is the trial-to-paid conversion rate by cohort?
--   Which acquisition source delivers the best LTV:CAC ratio?
--
-- Tavus angle:  API usage → MRR; which developer segments generate
--               the most sustainable revenue?
-- Meta angle:   Revenue as the downstream outcome of product decisions;
--               connecting growth initiatives to monetization metrics.
-- ============================================================

-- ── Step 1: Snapshot MRR by month ─────────────────────────────────────────────
-- A subscription contributes to a month's MRR if it was active during that month.
-- Anchor to the data's observation date, NOT CURRENT_DATE(): the synthetic data
-- ends 2026-04-27, so a calendar built from today would append empty months
-- (and make every account look mature / churn look like it stopped).
DECLARE as_of_date DATE DEFAULT DATE '2026-04-27';

WITH calendar AS (
  SELECT month_start
  FROM UNNEST(
    GENERATE_DATE_ARRAY(
      DATE_TRUNC(DATE_SUB(as_of_date, INTERVAL 15 MONTH), MONTH),
      DATE_TRUNC(as_of_date, MONTH),
      INTERVAL 1 MONTH
    )
  ) AS month_start
),

mrr_snapshot AS (
  SELECT
    c.month_start,
    s.org_id,
    s.plan_type,
    o.acquisition_source,
    o.company_size,
    o.industry,
    s.mrr_amount
  FROM calendar c
  JOIN `saas-lifecycle-analytics.raw.subscriptions` s
    ON s.start_date < DATE_ADD(c.month_start, INTERVAL 1 MONTH)   -- '<=' would pull in subs starting on the 1st of NEXT month
    AND (s.end_date IS NULL OR s.end_date >= c.month_start)
    AND s.mrr_amount > 0
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
),

-- ── Step 2: Monthly MRR aggregation ───────────────────────────────────────────
monthly_mrr AS (
  SELECT
    month_start,
    plan_type,
    acquisition_source,
    company_size,
    COUNT(DISTINCT org_id)  AS active_accounts,
    SUM(mrr_amount) AS total_mrr,
    AVG(mrr_amount) AS arpa
  FROM mrr_snapshot
  GROUP BY 1, 2, 3, 4
),

-- ── Step 3: MoM MRR change ────────────────────────────────────────────────────
mrr_with_delta AS (
  SELECT
    *,
    LAG(total_mrr) OVER (
      PARTITION BY plan_type, acquisition_source, company_size
      ORDER BY month_start
    ) AS prior_month_mrr,

    total_mrr - LAG(total_mrr) OVER (
      PARTITION BY plan_type, acquisition_source, company_size
      ORDER BY month_start
    ) AS mrr_delta

  FROM monthly_mrr
),

-- ── Step 4: Trial-to-paid conversion funnel by signup cohort ──────────────────
-- Days-to-paid needs one row per org first: AVG(... MIN(s.start_date) ...) nests an
-- aggregate inside an aggregate, which BigQuery rejects and which would also
-- average across duplicated subscription rows.
first_paid AS (
  SELECT org_id, MIN(start_date) AS first_paid_date
  FROM `saas-lifecycle-analytics.raw.subscriptions`
  WHERE mrr_amount > 0
  GROUP BY org_id
),

conversion_funnel AS (
  SELECT
    DATE_TRUNC(DATE(o.created_at), MONTH)                              AS signup_cohort,
    o.acquisition_source,
    o.company_size,

    COUNT(DISTINCT o.org_id)                                           AS signups,
    COUNT(DISTINCT s.org_id)                                           AS trial_started,
    COUNT(DISTINCT CASE WHEN s.mrr_amount > 0 THEN s.org_id END)      AS paid_converted,
    COUNT(DISTINCT CASE
      WHEN s.mrr_amount > 0 AND s.status = 'active' THEN s.org_id
    END)                                                               AS currently_active,
    AVG(DATE_DIFF(fp.first_paid_date, DATE(o.created_at), DAY))        AS avg_days_to_paid

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  LEFT JOIN first_paid fp USING (org_id)
  GROUP BY 1, 2, 3
),

-- ── Step 5: LTV proxy by acquisition source ──────────────────────────────────
-- Monthly churn = churn EVENTS / account-months of EXPOSURE; a subscription that is
-- still active counts as exposure up to as_of_date (censored), not as a survivor.
--
-- Do NOT use COUNTIF(status = 'churned') / COUNT(DISTINCT org_id). That is the
-- cumulative share of accounts that ever churned (~21% here), not a monthly rate
-- (~2.7% here), and treating it as monthly understates LTV about 8x.
--
-- LTV = ARPA / monthly_churn assumes constant churn and an unbounded lifetime; the
-- implied lifetime (~35-40 months) is longer than any subscription has been
-- observed (~15), so also report a capped LTV over a fixed horizon:
--   ARPA x (1 - (1 - c)^H) / c
-- Without acquisition spend this is a value ceiling, not LTV:CAC.
paid_exposure AS (
  SELECT
    o.acquisition_source,
    s.org_id,
    s.mrr_amount,
    s.status = 'churned'                                                AS churned,
    DATE_DIFF(IF(s.status = 'churned', s.end_date, as_of_date), s.start_date, DAY) / 30.4375
                                                                        AS exposure_months
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  WHERE s.mrr_amount > 0
),

ltv_proxy AS (
  SELECT
    acquisition_source,
    COUNT(DISTINCT org_id)                                              AS paid_customers,
    AVG(mrr_amount)                                                     AS arpa,
    COUNTIF(churned)                                                    AS churn_events,
    SUM(exposure_months)                                                AS exposure_months,
    SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months))                 AS monthly_churn,
    SAFE_DIVIDE(AVG(mrr_amount), SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months)))
                                                                        AS ltv_uncapped,
    -- 24-month capped LTV
    SAFE_DIVIDE(
      AVG(mrr_amount) * (1 - POW(1 - SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months)), 24)),
      SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months))
    )                                                                   AS ltv_24m
  FROM paid_exposure
  GROUP BY 1
)

-- ── Final output: combine key revenue metrics ─────────────────────────────────
SELECT
  mwd.month_start,
  mwd.plan_type,
  mwd.acquisition_source,
  mwd.company_size,
  mwd.active_accounts,
  ROUND(mwd.total_mrr, 2) AS total_mrr,
  ROUND(mwd.arpa, 2) AS arpa,
  ROUND(mwd.prior_month_mrr, 2) AS prior_month_mrr,
  ROUND(mwd.mrr_delta, 2) AS mrr_delta,
  ROUND(
    SAFE_DIVIDE(mwd.mrr_delta, mwd.prior_month_mrr), 4
  ) AS mrr_growth_rate
FROM mrr_with_delta mwd
ORDER BY mwd.month_start DESC, mwd.total_mrr DESC;

-- ── Second output: channel LTV (run separately from the MRR trend above) ───────
-- SELECT * FROM ltv_proxy ORDER BY ltv_24m DESC;
--
-- Point estimates only. Python (`channel_ltv()` in app/utils/metrics.py, shown on
-- the Revenue page) adds bootstrap intervals over ARPA AND churn; on this data the
-- channel intervals all share a common range, so the ranking should not be read
-- as a real difference between channels.
