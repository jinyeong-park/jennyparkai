-- ============================================================
-- mart_funnel.sql
-- PLG Lifecycle Funnel: Signup → Workspace → Activated → Paid → Retained
--
-- Business Question:
--   Where does the lifecycle leak? Which step has the biggest drop-off,
--   and how does it differ by acquisition source and company size?
--
-- Tavus angle:  Developer signs up → integrates SDK → generates first video → converts to paid
-- Meta angle:   User discovers feature → takes key action → engages consistently → retained
-- ============================================================

-- ── Step 1: Tag each org with the lifecycle stages it reached ──────────────────
WITH org_events AS (
  SELECT
    o.org_id,
    o.created_at AS signup_date,
    o.acquisition_source,
    o.company_size,
    o.industry,
    o.region,

    -- Onboarding milestone: workspace created
    MAX(CASE WHEN e.event_name = 'workspace_created'   THEN 1 ELSE 0 END) AS workspace_created,

    -- Activation milestones (any one within 7 days = activated)
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited', 'integration_connected', 'project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END) AS activated_7d,

    -- Key developer action: connected integration (SDK/API setup)
    MAX(CASE WHEN e.event_name = 'integration_connected' THEN 1 ELSE 0 END) AS integration_connected,

    -- Key creator action: first project (first video/persona generated)
    MAX(CASE WHEN e.event_name = 'project_created'       THEN 1 ELSE 0 END) AS project_created

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e
    ON o.org_id = e.org_id
  GROUP BY 1, 2, 3, 4, 5, 6
),

-- ── Step 2: Join subscription data to tag paid conversion ─────────────────────
org_subscriptions AS (
  SELECT
    org_id,
    MAX(CASE WHEN mrr_amount > 0 THEN 1 ELSE 0 END) AS ever_paid,
    MAX(CASE WHEN status = 'active' AND mrr_amount > 0 THEN 1 ELSE 0 END)  AS currently_active,
    MIN(CASE WHEN mrr_amount > 0 THEN start_date END) AS paid_start_date
  FROM `saas-lifecycle-analytics.raw.subscriptions`
  GROUP BY 1
),

-- ── Step 3: Build full org-level lifecycle record ─────────────────────────────
lifecycle AS (
  SELECT
    oe.*,
    COALESCE(os.ever_paid, 0) AS ever_paid,
    COALESCE(os.currently_active, 0) AS currently_active,
    os.paid_start_date
  FROM org_events oe
  LEFT JOIN org_subscriptions os USING (org_id)
)

-- ── Step 4: Aggregate funnel by segment ───────────────────────────────────────
SELECT
  acquisition_source,
  company_size,

  COUNT(DISTINCT org_id) AS signups,
  COUNT(DISTINCT CASE WHEN workspace_created  = 1 THEN org_id END) AS workspace_created,
  COUNT(DISTINCT CASE WHEN integration_connected = 1 THEN org_id END) AS integration_connected,
  COUNT(DISTINCT CASE WHEN activated_7d       = 1 THEN org_id END) AS activated_7d,
  COUNT(DISTINCT CASE WHEN ever_paid          = 1 THEN org_id END) AS paid_converted,
  COUNT(DISTINCT CASE WHEN currently_active   = 1 THEN org_id END) AS currently_retained,

  -- Step-to-step conversion rates
  ROUND(COUNT(DISTINCT CASE WHEN workspace_created    = 1 THEN org_id END)
        / NULLIF(COUNT(DISTINCT org_id), 0), 4) AS workspace_rate,
  ROUND(COUNT(DISTINCT CASE WHEN integration_connected= 1 THEN org_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN workspace_created = 1 THEN org_id END), 0), 4)
 AS integration_rate,
  ROUND(COUNT(DISTINCT CASE WHEN activated_7d         = 1 THEN org_id END)
        / NULLIF(COUNT(DISTINCT org_id), 0), 4) AS activation_rate,
  ROUND(COUNT(DISTINCT CASE WHEN ever_paid            = 1 THEN org_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN activated_7d = 1 THEN org_id END), 0), 4)
 AS activated_to_paid_rate,
  ROUND(COUNT(DISTINCT CASE WHEN currently_active     = 1 THEN org_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN ever_paid   = 1 THEN org_id END), 0), 4)
 AS paid_retention_rate

FROM lifecycle
GROUP BY 1, 2
ORDER BY signups DESC;
