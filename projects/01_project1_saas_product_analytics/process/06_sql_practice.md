# SQL Practice — PLG Lifecycle Analytics

> **Target roles**: Tavus Growth Analyst · Meta Product Growth Analyst · Data Analyst III (SaaS)
>
> **Stack**: BigQuery · SQL (window functions, CTEs, cohort patterns, statistical tests)

---

## Business Context

This project simulates the analytics environment of an **AI-powered developer platform** — modeled after companies like Tavus that sell API-first products to developers and product teams.

**The core product**: An AI video/conversational API that lets developers embed personalized, real-time video experiences into their products.

**The business model**: Free trial → paid API plan (usage-based + seats). Revenue grows when developers integrate the API, generate their first output (aha moment), and expand usage across their team.

**The analytics challenge**: Understanding why some developers activate and scale while others drop off after signup — and using that understanding to improve onboarding, retention, and expansion.

> "This is an independent educational project. It simulates the analytics environment of an API-first B2B SaaS company and is not affiliated with Tavus or any other organization."

---

## Data Model

```
saas-lifecycle-analytics.raw.organizations
  org_id          STRING    -- account/workspace ID
  created_at      TIMESTAMP -- signup timestamp
  company_size    STRING    -- 'SMB' | 'Mid-Market' | 'Enterprise'
  industry        STRING
  acquisition_source STRING -- 'organic' | 'paid_search' | 'referral' | 'outbound'
  region          STRING

saas-lifecycle-analytics.raw.users
  user_id         STRING
  org_id          STRING    -- FK → organizations
  role            STRING    -- 'admin' | 'developer' | 'viewer'
  signup_timestamp TIMESTAMP
  is_admin        BOOLEAN

saas-lifecycle-analytics.raw.event_logs
  event_id        STRING
  user_id         STRING
  org_id          STRING
  event_name      STRING    -- see event taxonomy below
  event_timestamp TIMESTAMP
  event_properties JSON

saas-lifecycle-analytics.raw.subscriptions
  subscription_id STRING
  org_id          STRING
  plan_type       STRING    -- 'free_trial' | 'starter' | 'pro' | 'enterprise'
  mrr_amount      FLOAT     -- 0 for trial
  start_date      DATE
  end_date        DATE      -- NULL if active
  status          STRING    -- 'active' | 'churned' | 'paused'
  churn_reason    STRING

saas-lifecycle-analytics.raw.experiment_assignments
  experiment_id   STRING
  org_id          STRING
  variant         STRING    -- 'control' | 'treatment'
  assigned_at     TIMESTAMP
  eligible_segment STRING
```

### Event Taxonomy

| Event | Developer Meaning | Analytics Meaning |
|---|---|---|
| `signup_completed` | Developer creates account | Top of funnel |
| `workspace_created` | Sets up first project space | Onboarding milestone |
| `integration_connected` | SDK/API key configured | **Aha moment (developer)** |
| `project_created` | First video/persona generated | **Aha moment (creator)** |
| `teammate_invited` | Invites collaborator | Team expansion signal |

---

## Domain 1: Funnel Analysis

**Business question**: Where does the lifecycle leak? Which step has the biggest drop-off?

### 1-1. Overall lifecycle funnel

```sql
WITH funnel_stages AS (
  SELECT
    o.org_id,
    o.acquisition_source,
    o.company_size,

    -- Stage flags
    1 AS signed_up,
    MAX(CASE WHEN e.event_name = 'workspace_created' THEN 1 ELSE 0 END)        AS workspace_created,
    MAX(CASE WHEN e.event_name = 'integration_connected' THEN 1 ELSE 0 END)    AS integration_connected,
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END)                                                                         AS activated_7d,
    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END)                          AS paid_converted

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1, 2, 3
)

SELECT
  COUNT(*)                                                        AS signups,
  COUNTIF(workspace_created = 1)                                 AS workspace_created,
  COUNTIF(integration_connected = 1)                             AS integration_connected,
  COUNTIF(activated_7d = 1)                                      AS activated_7d,
  COUNTIF(paid_converted = 1)                                    AS paid_converted,

  -- Step-to-step rates
  ROUND(COUNTIF(workspace_created = 1)    / COUNT(*), 3)         AS workspace_rate,
  ROUND(COUNTIF(integration_connected=1) / NULLIF(COUNTIF(workspace_created=1),0), 3)
                                                                  AS workspace_to_integration_rate,
  ROUND(COUNTIF(activated_7d = 1)         / COUNT(*), 3)         AS overall_activation_rate,
  ROUND(COUNTIF(paid_converted = 1)       / NULLIF(COUNTIF(activated_7d=1),0), 3)
                                                                  AS activated_to_paid_rate

FROM funnel_stages;
```

**Key SQL patterns**: CASE WHEN aggregation, NULLIF for safe division, funnel step-to-step rates

**Interview talking point**: "I define each stage explicitly so the denominator is correct per step — workspace-to-integration uses workspace as denominator, not total signups."

---

### 1-2. Funnel by acquisition source (where does organic vs paid differ?)

```sql
WITH funnel_by_source AS (
  SELECT
    o.acquisition_source,
    COUNT(DISTINCT o.org_id)                                                    AS signups,
    COUNT(DISTINCT CASE WHEN e1.org_id IS NOT NULL THEN o.org_id END)          AS workspace_created,
    COUNT(DISTINCT CASE WHEN e2.org_id IS NOT NULL THEN o.org_id END)          AS integration_connected,
    COUNT(DISTINCT CASE WHEN act.org_id IS NOT NULL THEN o.org_id END)         AS activated_7d,
    COUNT(DISTINCT CASE WHEN s.mrr_amount > 0 THEN o.org_id END)              AS paid_converted

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
    SELECT org_id
    FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name IN ('teammate_invited','integration_connected','project_created')
    GROUP BY org_id
    HAVING MIN(TIMESTAMP_DIFF(event_timestamp,
      (SELECT created_at FROM `saas-lifecycle-analytics.raw.organizations` WHERE org_id = e.org_id),
      DAY)) <= 7
  ) act USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1
)

SELECT
  *,
  ROUND(paid_converted / NULLIF(signups, 0), 3)   AS overall_conversion_rate
FROM funnel_by_source
ORDER BY signups DESC;
```

### The drill-down framework: don't stop at the overall rate

Overall activation rate by channel tells you *who* is underperforming, but not *why*. Three layers, in order:

1. **Overall rate by channel** — which channel looks weak?
2. **Step-to-step rate, each conditioned on the prior step** (`workspace_to_integration_rate = integration_connected / workspace_created`, not `/ signups`) — *which specific step* is where that channel leaks?
3. **Cross-step comparison against `activated_to_paid_rate`** — once a channel's accounts clear activation, do they convert to paid as well as (or better than) other channels?

If a channel has a normal top-of-funnel rate, a weak middle step, and a strong (or best-in-class) `activated_to_paid_rate`, that's an **onboarding/UX friction** signature — the people are qualified, the product is getting in the way. If a channel is weak at every step including `activated_to_paid_rate`, that's an **acquisition-quality** signature — the traffic itself is lower-intent, and no onboarding fix will close the gap. Conflating the two leads to the wrong fix: cutting spend on a friction-limited channel, or pouring product effort into fixing a quality-limited one.

Running this against the actual project dataset surfaces both patterns at once — see `docs/process/05_analysis_findings.md → Funnel by acquisition channel` for the real numbers: one channel shows the friction signature (strong start, weak integration step, best-in-class paid conversion once activated) and another shows the quality signature (weak at every step). A third pattern also shows up that the two-bucket framework above doesn't cover — a channel that activates well but converts to paid worst, which is a monetization gap rather than an activation or acquisition problem.

**Interview talking point**: "Overall activation rate by channel hides where exactly the drop-off happens. I always condition step-to-step rates on the prior step, not total signups, so I'm not confusing a workspace-creation problem with an integration problem. Then I cross-check against downstream paid conversion — a channel that struggles to activate but converts well once it does is a friction problem, not a quality problem, and that completely changes who owns the fix: product/onboarding versus the acquisition team."

---

## Domain 2: Activation Analysis

**Business question**: Which milestone predicts the best retention? How long does it take developers to activate?

### 2-1. Time-to-activate distribution

```sql
WITH first_milestones AS (
  SELECT
    o.org_id,
    o.acquisition_source,
    o.company_size,
    o.created_at,

    MIN(CASE WHEN e.event_name = 'integration_connected'
      THEN TIMESTAMP_DIFF(e.event_timestamp, o.created_at, HOUR)
    END) AS hours_to_integration,

    MIN(CASE WHEN e.event_name = 'project_created'
      THEN TIMESTAMP_DIFF(e.event_timestamp, o.created_at, HOUR)
    END) AS hours_to_project,

    MIN(CASE WHEN e.event_name = 'teammate_invited'
      THEN TIMESTAMP_DIFF(e.event_timestamp, o.created_at, HOUR)
    END) AS hours_to_invite

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1, 2, 3, 4
)

SELECT
  acquisition_source,
  company_size,
  COUNT(*)                                                    AS orgs,
  ROUND(AVG(hours_to_integration) / 24, 1)                  AS avg_days_to_integration,
  ROUND(APPROX_QUANTILES(hours_to_integration, 100)[OFFSET(50)] / 24, 1)
                                                              AS p50_days_to_integration,
  ROUND(APPROX_QUANTILES(hours_to_integration, 100)[OFFSET(90)] / 24, 1)
                                                              AS p90_days_to_integration,
  ROUND(AVG(hours_to_project) / 24, 1)                      AS avg_days_to_project,
  ROUND(AVG(hours_to_invite) / 24, 1)                       AS avg_days_to_invite

FROM first_milestones
WHERE hours_to_integration IS NOT NULL
GROUP BY 1, 2
ORDER BY orgs DESC;
```

**Key SQL pattern**: `APPROX_QUANTILES` for percentile distribution — shows P50/P90 time-to-activate

**Interview talking point**: "Average alone is misleading — I use P50 and P90 so we can see if there's a long tail of developers who take weeks to integrate."

---

### 2-2. Milestone → downstream retention (which action predicts staying?)

```sql
-- Which first activation milestone best predicts 60-day retention?
WITH milestone_outcomes AS (
  SELECT
    o.org_id,

    -- First qualifying action within 7 days
    CASE
      WHEN MIN(CASE WHEN e.event_name = 'integration_connected'
                AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
                THEN e.event_timestamp END) IS NOT NULL
      THEN 'integration_first'
      WHEN MIN(CASE WHEN e.event_name = 'project_created'
                AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
                THEN e.event_timestamp END) IS NOT NULL
      THEN 'project_first'
      WHEN MIN(CASE WHEN e.event_name = 'teammate_invited'
                AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
                THEN e.event_timestamp END) IS NOT NULL
      THEN 'invite_first'
      ELSE 'not_activated'
    END AS first_milestone,

    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END)                      AS ever_paid,
    MAX(CASE
      WHEN s.mrr_amount > 0 AND s.status = 'active'
        AND DATE_ADD(s.start_date, INTERVAL 60 DAY) <= CURRENT_DATE()
      THEN 1 ELSE 0
    END)                                                                    AS retained_60d

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1
)

SELECT
  first_milestone,
  COUNT(*)                                                    AS orgs,
  ROUND(AVG(ever_paid), 3)                                  AS paid_conversion_rate,
  ROUND(AVG(retained_60d), 3)                               AS retention_60d_rate
FROM milestone_outcomes
GROUP BY 1
ORDER BY retention_60d_rate DESC;
```

**Data caveat**: `AVG(retained_60d)` here is taken over every org assigned to a milestone, including orgs that never paid or aren't yet 60 days mature — those count as 0, which understates true retention. The maturity-gating principle from Domain 3 below (only include accounts old enough to have reached the horizon) applies here too. Running the eligibility-gated version against this project's actual dataset gives `integration_connected` 95.4% vs. `teammate_invited` 93.6% vs. `project_created` 91.8% — see `docs/process/05_analysis_findings.md → Which first action predicts retention best?`. That page also documents a claim this project's own docs used to make ("teammate invitations are the strongest retention signal") that didn't hold up once tested directly — a useful reminder to verify a plausible-sounding story against the numbers before it goes in a findings doc or a stakeholder deck.

---

## Domain 3: Cohort Retention

**Business question**: Are later cohorts retaining better? (Are we improving?)

### 3-1. Monthly cohort retention matrix

```sql
WITH paid_cohorts AS (
  SELECT
    s.org_id,
    DATE_TRUNC(s.start_date, MONTH)  AS cohort_month,
    s.start_date                     AS paid_start_date,
    s.end_date,
    s.mrr_amount
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  WHERE s.mrr_amount > 0
  QUALIFY ROW_NUMBER() OVER (PARTITION BY s.org_id ORDER BY s.start_date) = 1
),

retention_matrix AS (
  SELECT
    cohort_month,
    COUNT(DISTINCT org_id)                                                    AS cohort_size,

    -- Retention at each horizon (exclude immature observations with NULL)
    ROUND(COUNTIF(end_date IS NULL OR end_date > DATE_ADD(paid_start_date, INTERVAL 30 DAY))
          / COUNT(*), 3)                                                     AS d30_retention,

    ROUND(
      COUNTIF(
        DATE_ADD(paid_start_date, INTERVAL 60 DAY) <= CURRENT_DATE()
        AND (end_date IS NULL OR end_date > DATE_ADD(paid_start_date, INTERVAL 60 DAY))
      )
      / NULLIF(COUNTIF(DATE_ADD(paid_start_date, INTERVAL 60 DAY) <= CURRENT_DATE()), 0)
    , 3)                                                                     AS d60_retention,

    ROUND(
      COUNTIF(
        DATE_ADD(paid_start_date, INTERVAL 90 DAY) <= CURRENT_DATE()
        AND (end_date IS NULL OR end_date > DATE_ADD(paid_start_date, INTERVAL 90 DAY))
      )
      / NULLIF(COUNTIF(DATE_ADD(paid_start_date, INTERVAL 90 DAY) <= CURRENT_DATE()), 0)
    , 3)                                                                     AS d90_retention

  FROM paid_cohorts
  GROUP BY 1
)

SELECT * FROM retention_matrix
ORDER BY cohort_month DESC;
```

**Key SQL pattern**: Maturity-gated retention — only include orgs in the denominator if enough time has passed. Avoids inflating early retention by excluding accounts that haven't had time to churn.

**Interview talking point (Meta)**: "I always gate the denominator on maturity — if a cohort signed up 30 days ago, they can't be in the 90-day retention denominator yet. Otherwise the rate looks artificially high."

---

### 3-2. Activated vs. non-activated retention comparison

```sql
WITH activation_status AS (
  SELECT
    o.org_id,
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END) AS activated_7d
  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1
),

paid_with_activation AS (
  SELECT
    s.org_id,
    DATE_TRUNC(s.start_date, MONTH) AS cohort_month,
    s.start_date,
    s.end_date,
    a.activated_7d
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  JOIN activation_status a USING (org_id)
  WHERE s.mrr_amount > 0
  QUALIFY ROW_NUMBER() OVER (PARTITION BY s.org_id ORDER BY s.start_date) = 1
)

SELECT
  activated_7d,
  COUNT(*)                                                          AS accounts,
  ROUND(COUNTIF(end_date IS NULL OR end_date > DATE_ADD(start_date, INTERVAL 30 DAY))
        / COUNT(*), 3)                                             AS d30_retention,
  ROUND(
    COUNTIF(
      DATE_ADD(start_date, INTERVAL 60 DAY) <= CURRENT_DATE()
      AND (end_date IS NULL OR end_date > DATE_ADD(start_date, INTERVAL 60 DAY))
    )
    / NULLIF(COUNTIF(DATE_ADD(start_date, INTERVAL 60 DAY) <= CURRENT_DATE()), 0)
  , 3)                                                             AS d60_retention

FROM paid_with_activation
GROUP BY 1;
```

---

### 3-3. Product engagement retention (signup cohort, not paid cohort)

**Business question**: Of everyone who signed up — not just accounts that converted to paid — is engagement retention different from paid retention?

3-1 and 3-2 above both measure **paid retention**: cohorted by paid-conversion date, asking "is the subscription still active?" That's a different question from **product engagement retention**: cohorted by *signup* date, asking "did the account have any product activity 30/60/90 days later?" — across every signup, whether or not it ever paid.

```sql
WITH cohorts AS (
  SELECT
    org_id,
    created_at,
    DATE_TRUNC(DATE(created_at), MONTH) AS cohort_month
  FROM `saas-lifecycle-analytics.raw.organizations`
),

-- Day 0 excluded — signup-day activity is onboarding, not a return visit.
activity AS (
  SELECT
    c.org_id,
    c.cohort_month,
    MAX(CASE WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 1 AND 30  THEN 1 ELSE 0 END) AS active_d30,
    MAX(CASE WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 31 AND 60 THEN 1 ELSE 0 END) AS active_d60,
    MAX(CASE WHEN TIMESTAMP_DIFF(e.event_timestamp, c.created_at, DAY) BETWEEN 61 AND 90 THEN 1 ELSE 0 END) AS active_d90
  FROM cohorts c
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1, 2
)

SELECT
  cohort_month,
  COUNT(DISTINCT org_id) AS cohort_size,
  CASE WHEN DATE_ADD(cohort_month, INTERVAL 30 DAY) <= CURRENT_DATE() THEN ROUND(AVG(active_d30), 4) END AS retention_d30,
  CASE WHEN DATE_ADD(cohort_month, INTERVAL 60 DAY) <= CURRENT_DATE() THEN ROUND(AVG(active_d60), 4) END AS retention_d60,
  CASE WHEN DATE_ADD(cohort_month, INTERVAL 90 DAY) <= CURRENT_DATE() THEN ROUND(AVG(active_d90), 4) END AS retention_d90
FROM activity
GROUP BY cohort_month
ORDER BY cohort_month DESC;
```

Full mart: `sql/marts/mart_engagement_retention.sql`. Pandas equivalent: `engagement_retention_curve()` in `app/utils/metrics.py`.

Run against this project's actual dataset, the gap between the two retention definitions is large: D60 engagement retention across **all signups** is 51.4%, versus 93.5% D60 **paid** retention (paid accounts only) — see `docs/process/05_analysis_findings.md → Product engagement retention` for the full comparison.

**Interview talking point**: "Paid retention and engagement retention answer different questions, and conflating them hides where value is actually being lost. Paid retention only ever looks at the accounts that already converted — a small, self-selected, higher-intent group — so it can look healthy even while most of the signup base has gone quiet on the product. I track both: paid retention for revenue health, engagement retention for product health. When they diverge sharply, like here, it means most of the drop-off is happening before or outside the subscription relationship, which finance-facing subscription metrics alone would never surface."

---

## Domain 4: Experiment Analysis (A/B Test)

**Business question**: Did the new guided onboarding flow increase activation? Is the lift real?

### 4-1. Primary metric lift with z-test in SQL

```sql
WITH experiment_outcomes AS (
  SELECT
    ea.org_id,
    ea.variant,
    ea.eligible_segment,
    o.company_size,
    o.acquisition_source,

    -- Primary: 7-day activation
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END) AS activated,

    -- Guardrail 1: paid conversion
    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END) AS paid,

    -- Guardrail 2: 60-day retention
    MAX(CASE
      WHEN s.mrr_amount > 0 AND s.status = 'active'
        AND DATE_ADD(s.start_date, INTERVAL 60 DAY) <= CURRENT_DATE()
      THEN 1 ELSE 0
    END) AS retained_60d

  FROM `saas-lifecycle-analytics.raw.experiment_assignments` ea
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  WHERE ea.experiment_id = 'onboarding_v2'
  GROUP BY 1, 2, 3, 4, 5
),

variant_agg AS (
  SELECT
    variant,
    COUNT(*)           AS n,
    SUM(activated)     AS activated,
    SUM(paid)          AS paid,
    SUM(retained_60d)  AS retained,
    AVG(activated)     AS activation_rate,
    AVG(paid)          AS paid_rate,
    AVG(retained_60d)  AS retention_rate
  FROM experiment_outcomes
  GROUP BY 1
),

-- Z-test: two-proportion test for statistical significance
z_test AS (
  SELECT
    MAX(CASE WHEN variant = 'control'   THEN n               END) AS n_ctrl,
    MAX(CASE WHEN variant = 'treatment' THEN n               END) AS n_trt,
    MAX(CASE WHEN variant = 'control'   THEN activation_rate END) AS rate_ctrl,
    MAX(CASE WHEN variant = 'treatment' THEN activation_rate END) AS rate_trt,
    MAX(CASE WHEN variant = 'control'   THEN activated       END) AS act_ctrl,
    MAX(CASE WHEN variant = 'treatment' THEN activated       END) AS act_trt
  FROM variant_agg
)

SELECT
  rate_ctrl                                                             AS control_rate,
  rate_trt                                                              AS treatment_rate,
  ROUND(rate_trt - rate_ctrl, 4)                                       AS absolute_lift_pp,
  ROUND((rate_trt - rate_ctrl) / NULLIF(rate_ctrl, 0), 4)             AS relative_lift,

  -- Pooled proportion
  ROUND((act_ctrl + act_trt) / NULLIF(n_ctrl + n_trt, 0), 4)         AS pooled_p,

  -- Z-score
  ROUND(
    (rate_trt - rate_ctrl) /
    SQRT(
      ((act_ctrl + act_trt) / NULLIF(n_ctrl + n_trt, 0))
      * (1 - (act_ctrl + act_trt) / NULLIF(n_ctrl + n_trt, 0))
      * (1.0/n_ctrl + 1.0/n_trt)
    )
  , 3)                                                                 AS z_score,

  CASE
    WHEN ABS(
      (rate_trt - rate_ctrl) /
      SQRT(
        ((act_ctrl + act_trt) / NULLIF(n_ctrl + n_trt, 0))
        * (1 - (act_ctrl + act_trt) / NULLIF(n_ctrl + n_trt, 0))
        * (1.0/n_ctrl + 1.0/n_trt)
      )
    ) >= 1.96 THEN 'Significant (p < 0.05)'
    ELSE 'Not Significant'
  END                                                                  AS result

FROM z_test;
```

**Key SQL pattern**: Z-test entirely in SQL — no Python needed. Z > 1.96 → p < 0.05.

**Interview talking point (Meta)**: "I compute the two-proportion z-test inline so any analyst can run it in BigQuery without switching tools. The pooled proportion is key — you use it rather than the individual rates to estimate variance under the null hypothesis."

---

### 4-2. Heterogeneous Treatment Effects (HTE) — segment-level lift

```sql
-- Does the treatment effect differ by company size?
SELECT
  company_size,
  variant,
  COUNT(*)                                AS n,
  ROUND(AVG(activated), 4)              AS activation_rate,
  ROUND(AVG(paid), 4)                   AS paid_rate

FROM (
  SELECT
    ea.org_id,
    ea.variant,
    o.company_size,
    MAX(CASE
      WHEN e.event_name IN ('teammate_invited','integration_connected','project_created')
        AND TIMESTAMP_DIFF(e.event_timestamp, o.created_at, DAY) <= 7
      THEN 1 ELSE 0
    END) AS activated,
    MAX(CASE WHEN s.mrr_amount > 0 THEN 1 ELSE 0 END) AS paid
  FROM `saas-lifecycle-analytics.raw.experiment_assignments` ea
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  WHERE ea.experiment_id = 'onboarding_v2'
  GROUP BY 1, 2, 3
)
GROUP BY 1, 2
ORDER BY company_size, variant;
```

**Interview talking point (Meta)**: "I always check for HTE after finding an overall positive lift. If SMB shows +25pp but Enterprise shows -5pp, shipping to everyone would hurt Enterprise. Meta-style experimentation looks for segment interactions before any launch decision."

---

### 4-3. Sample size — was this experiment adequately powered?

**Business question**: The lift wasn't significant — do we need more data, or is the effect just too small to matter?

Answering this needs a **pre-specified** minimum detectable effect (MDE) — the smallest lift worth caring about, decided *before* looking at results — not the lift that happened to come out of the experiment. Using the observed lift as its own target is circular: a truly null result has ~0 observed lift, which would demand an absurd sample size to "detect," making every null result look under-powered no matter how much data was actually collected.

```sql
-- n = (z_alpha + z_power)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2
WITH params AS (
  SELECT
    0.35 AS baseline_rate,   -- control rate
    0.05 AS mde,             -- pre-specified minimum detectable effect
    1.96 AS z_alpha,         -- alpha = 0.05, two-tailed
    0.842 AS z_power         -- power = 0.80
)
SELECT
  CEILING(
    POW(z_alpha + z_power, 2)
    * (baseline_rate * (1 - baseline_rate) + (baseline_rate + mde) * (1 - (baseline_rate + mde)))
    / POW(mde, 2)
  ) AS required_n_per_variant
FROM params;
```

**Data caveat — verify the formula, don't hand-copy an old result**: `docs/process/03_experiment_readout.md` used to say baseline 35% / MDE 5pp / 80% power needed "~730 per variant." Running the formula above gives **1,468** — the old figure was off by exactly 2x (it dropped the `+` term that sums both groups' variance). Both `mart_multivariate.sql`'s SQL version and `required_sample_size()` in `app/utils/metrics.py` independently agree on 1,468, and the doc has been corrected. This is the same lesson as the `raw.retention` table that didn't exist and the "teammate invitations" claim that didn't hold up: run the calculation and check it against a second implementation before writing a number down, rather than trusting that a plausible-looking figure was already verified.

**Applied to the real onboarding experiment**: it ran with 1,212 control / 1,288 treatment — technically under the 1,468-per-variant bar for a 5pp MDE. It reached significance anyway because the true effect (+18.6pp) is far larger than 5pp; a smaller true effect could plausibly have been missed at this sample size, but that risk didn't materialize here. See `docs/process/05_analysis_findings.md → Formal decision` for the full readout, including a proper significance test on the retention guardrail (not just eyeballing whether the delta is negative).

**Interview talking point**: "If a result isn't significant, the next question is whether we're under-powered or whether the effect is genuinely too small to matter — and that requires a sample-size calculation against a pre-specified MDE decided before the experiment, not the observed lift. I also don't treat a guardrail's negative delta as an automatic stop — I run the same two-proportion test on the guardrail metric itself. A small drop on a small eligible sample is often statistical noise, and a fixed threshold would kill experiments over noise as easily as it catches real regressions."

---

### 4-4. Multiple comparisons — Bonferroni correction for A/B/C/D tests

**Business question**: We tested 3 onboarding variants against control at once, not just one. Can we compare all 4 groups with the same z-test threshold?

No — running k independent significance tests at alpha=0.05 each does **not** keep the overall false-positive rate at 5%. The chance that *at least one* of k unrelated tests comes back "significant" by chance alone is `1 - (1-alpha)^k`:

```
k=1: 1 - 0.95^1 = 5.0%   (the ordinary case)
k=3: 1 - 0.95^3 = 14.3%  (nearly 3x the nominal rate)
```

**Bonferroni correction**: divide alpha by the number of comparisons before finding the critical z-value.

```sql
-- adjusted_alpha = 0.05 / k
-- k=3 -> adjusted_alpha = 0.0167 -> z_threshold = 2.394 (vs. 1.96 uncorrected)
WITH bonferroni AS (
  SELECT 3 AS k, 0.05 / 3 AS adjusted_alpha, 2.394 AS z_threshold
),
z_scores AS (
  SELECT
    t.variant,
    (t.trt_rate - c.ctrl_rate) /
      NULLIF(SQRT(((c.activated + t.activated) / NULLIF(c.n + t.n, 0))
        * (1 - (c.activated + t.activated) / NULLIF(c.n + t.n, 0))
        * (1.0/c.n + 1.0/t.n)), 0)                                AS z_score
  FROM treatments t CROSS JOIN control c
)
SELECT
  z.variant,
  ROUND(z.z_score, 3)                                             AS z_score,
  CASE
    WHEN ABS(z.z_score) >= b.z_threshold THEN 'Significant after correction'
    ELSE 'Not significant after correction'
  END                                                              AS decision
FROM z_scores z CROSS JOIN bonferroni b;
```

Full version with the decision framework (SHIP/ITERATE/KILL/HOLD per variant): `sql/marts/mart_multivariate.sql`. That mart counts `k` from the data and looks the critical z up by `k` (BigQuery has no inverse-normal function), so adding a variant updates the threshold. A first draft that writes `3 AS k, 0.05 / 3, 2.394` as three separate literals only *looks* parameterized: change k and the threshold silently stays at 2.394.

**The cost of correcting**: a stricter threshold needs more data. For baseline 35% and a 5pp MDE at 80% power, per-variant N rises from 1,468 (k=1) to 1,778 (k=2), 1,958 (k=3, +33%) and 2,086 (k=4). Deciding how many variants to test is a sample-size decision, not just a statistics footnote. Python: `bonferroni_pairwise_results()` in `app/utils/metrics.py`.

**Data caveat**: this project's real experiment data only has 2 arms (control/treatment) — there's no genuine 3-way product comparison to run. Both the SQL mart and the Python function simulate 3 sub-variants by a stable hash of `org_id` on the treatment group, purely to have something to demonstrate the correction mechanics against. Since all 3 sub-variants are random subsets of the *same* real treatment group, they all inherit the same real (huge) effect and all ship even after correction — that's an artifact of the simulation, not a finding. The methodology is what transfers to a real multivariate test, not these specific numbers.

**Interview talking point (Meta)**: "Multiple comparisons is a real risk any time you're evaluating more than one treatment variant against a single control — running each test independently at alpha=0.05 inflates the family-wise error rate to 1-(1-alpha)^k. Bonferroni is the simplest fix: divide alpha by the number of comparisons, which raises the bar for each individual test. It's conservative — it can under-power a real effect when k is large — but it's easy to explain and easy to defend in a launch review. For a large number of variants I'd consider a less conservative correction like Benjamini-Hochberg, but Bonferroni is the right default for a handful of comparisons."

---

## Domain 5: Revenue Analytics

**Business question**: Where is MRR growing? Which cohort converts fastest? What is LTV by channel?

### 5-1. MRR trend with MoM delta

```sql
WITH monthly_mrr AS (
  SELECT
    DATE_TRUNC(
      CASE WHEN s.status = 'active' THEN CURRENT_DATE() ELSE s.end_date END,
      MONTH
    )                                           AS snapshot_month,
    o.acquisition_source,
    COUNT(DISTINCT s.org_id)                   AS active_accounts,
    SUM(s.mrr_amount)                          AS total_mrr
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  WHERE s.mrr_amount > 0 AND s.status = 'active'
  GROUP BY 1, 2
)

SELECT
  snapshot_month,
  acquisition_source,
  active_accounts,
  ROUND(total_mrr, 2)                          AS total_mrr,
  ROUND(LAG(total_mrr) OVER (
    PARTITION BY acquisition_source ORDER BY snapshot_month
  ), 2)                                         AS prior_mrr,
  ROUND(total_mrr - LAG(total_mrr) OVER (
    PARTITION BY acquisition_source ORDER BY snapshot_month
  ), 2)                                         AS mrr_delta,
  ROUND(
    (total_mrr - LAG(total_mrr) OVER (PARTITION BY acquisition_source ORDER BY snapshot_month))
    / NULLIF(LAG(total_mrr) OVER (PARTITION BY acquisition_source ORDER BY snapshot_month), 0)
  , 4)                                          AS mom_growth_rate

FROM monthly_mrr
ORDER BY snapshot_month DESC, total_mrr DESC;
```

**Key SQL pattern**: `LAG()` window function for period-over-period comparison.

---

### 5-2. LTV by acquisition source (there is no CAC to divide by)

```sql
-- Monthly churn = churn EVENTS / account-months of EXPOSURE.
-- Still-active subscriptions contribute exposure up to the observation date (censored).
DECLARE as_of_date DATE DEFAULT DATE '2026-04-27';   -- the data's end, not CURRENT_DATE()

WITH paid_exposure AS (
  SELECT
    o.acquisition_source,
    s.org_id,
    s.mrr_amount,
    s.status = 'churned' AS churned,
    DATE_DIFF(IF(s.status = 'churned', s.end_date, as_of_date), s.start_date, DAY) / 30.4375
      AS exposure_months
  FROM `saas-lifecycle-analytics.raw.subscriptions` s
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
  WHERE s.mrr_amount > 0
)
SELECT
  acquisition_source,
  COUNT(DISTINCT org_id)                                           AS paid_accounts,
  ROUND(AVG(mrr_amount), 0)                                        AS arpa,
  ROUND(SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months)), 4)    AS monthly_churn,
  ROUND(SAFE_DIVIDE(AVG(mrr_amount),
        SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months))), 0)   AS ltv_uncapped,
  -- 24-month capped LTV: ARPA x (1 - (1-c)^24) / c
  ROUND(SAFE_DIVIDE(
    AVG(mrr_amount) * (1 - POW(1 - SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months)), 24)),
    SAFE_DIVIDE(COUNTIF(churned), SUM(exposure_months))), 0)       AS ltv_24m
FROM paid_exposure
GROUP BY 1
ORDER BY ltv_24m DESC;
```

**Data caveats, all found by running the numbers**

- **"Churn rate" was the cumulative churned share.** The first draft of this query used `COUNTIF(status = 'churned') / COUNT(DISTINCT org_id)` as `monthly_churn_rate`. That is ~21% here (203 of 969 paid accounts churned at some point in the window), while the actual monthly rate is ~2.7%. Treated as monthly, it understates LTV about 8x (~$1,200 vs. ~$9,300).
- **The "LTV:CAC ratio" column was not a ratio of anything.** It computed `(ARPA / churn) / (months_to_paid x ARPA)`, in which ARPA cancels out and time-to-paid is not a cost. Median days to first paid subscription is 19-20 for *every* channel, so it wasn't even a differentiating signal. Without spend data the honest outputs are LTV and `max_cac = capped LTV / target ratio`.
- **The uncapped lifetime is longer than the data.** `1 / churn` implies 34-42 months; the longest observed subscription is ~15. The 24-month capped LTV is ~$4,000-5,200 against ~$8,100-10,900 uncapped.
- **The channel ranking isn't statistically supported.** Monthly churn is 2.4-3.0% for every channel; the LTV spread comes mostly from ARPA ($222-$292). Bootstrapping accounts (ARPA and churn together), all six channels' 24-month LTV intervals share a common range (e.g., Referral ~$4.1-6.5K vs. Paid Search ~$3.2-4.7K). Holding churn alone fixed and ignoring ARPA's variance gives intervals that look separable; they aren't.

Python: `channel_ltv()` in `app/utils/metrics.py` (Revenue page). Full mart: `sql/marts/mart_revenue.sql`.

**Interview talking point**: "Without spend data I can't compute LTV:CAC, so I don't. I compute LTV from observed churn and invert the question: at a 3:1 target, what's the most we could spend per account? Churn is events per account-month of exposure, not the share of accounts that ever churned; mixing those up made my first version understate LTV eightfold. And because 1/churn implies a lifetime longer than anything we've observed, I report a capped LTV, with intervals from resampling accounts. Channels looked ranked by point estimate, but the intervals overlapped, so I wouldn't move budget on that alone."

---

## Domain 6: User Behavior & Engagement Depth

**Business question**: Who are the power users? Which behavioral signals predict churn?

### 6-1. Engagement scoring (DAU/MAU analog for B2B)

```sql
-- L28 engagement: active days in last 28 days per org
WITH org_activity AS (
  SELECT
    org_id,
    COUNT(DISTINCT DATE(event_timestamp))                              AS active_days_total,
    COUNT(DISTINCT CASE
      WHEN event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 28 DAY)
      THEN DATE(event_timestamp)
    END)                                                               AS active_days_l28,
    COUNT(DISTINCT event_name)                                         AS distinct_actions,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(event_timestamp), DAY)    AS days_since_last_event,
    COUNT(DISTINCT user_id)                                            AS engaged_users
  FROM `saas-lifecycle-analytics.raw.event_logs`
  GROUP BY 1
),

engagement_tiers AS (
  SELECT
    oa.*,
    o.acquisition_source,
    o.company_size,
    CASE
      WHEN oa.active_days_l28 >= 15 AND oa.distinct_actions >= 4
        AND oa.days_since_last_event <= 3  THEN 'power'
      WHEN oa.active_days_l28 >= 7  AND oa.distinct_actions >= 3
        AND oa.days_since_last_event <= 10 THEN 'active'
      WHEN oa.days_since_last_event <= 28  THEN 'casual'
      ELSE 'dormant'
    END AS engagement_tier
  FROM org_activity oa
  JOIN `saas-lifecycle-analytics.raw.organizations` o USING (org_id)
)

SELECT
  engagement_tier,
  acquisition_source,
  company_size,
  COUNT(*)                                  AS accounts,
  ROUND(AVG(active_days_l28), 1)          AS avg_l28_active_days,
  ROUND(AVG(distinct_actions), 1)         AS avg_distinct_actions,
  ROUND(AVG(engaged_users), 1)            AS avg_engaged_users
FROM engagement_tiers
GROUP BY 1, 2, 3
ORDER BY accounts DESC;
```

**Interview talking point (Meta)**: "I use L28 active days as a B2B analog to DAU/MAU ratio. For a developer API product, daily usage is unusual — weekly or bi-weekly engagement is healthy. The key signal is whether developers are returning consistently, not daily."

---

### 6-2. Churn signal detection (leading indicators)

```sql
-- Which behavioral patterns appear in the 14 days before churn?
WITH churned_orgs AS (
  SELECT
    org_id,
    end_date AS churn_date
  FROM `saas-lifecycle-analytics.raw.subscriptions`
  WHERE status = 'churned' AND mrr_amount > 0
),

pre_churn_behavior AS (
  SELECT
    c.org_id,
    c.churn_date,
    -- Activity in 14 days before churn
    COUNT(CASE
      WHEN e.event_timestamp BETWEEN
        TIMESTAMP_SUB(CAST(c.churn_date AS TIMESTAMP), INTERVAL 14 DAY)
        AND CAST(c.churn_date AS TIMESTAMP)
      THEN e.event_id
    END)                                                              AS events_last_14d,

    -- Activity in 15-30 days before churn (for comparison)
    COUNT(CASE
      WHEN e.event_timestamp BETWEEN
        TIMESTAMP_SUB(CAST(c.churn_date AS TIMESTAMP), INTERVAL 30 DAY)
        AND TIMESTAMP_SUB(CAST(c.churn_date AS TIMESTAMP), INTERVAL 14 DAY)
      THEN e.event_id
    END)                                                              AS events_14_30d,

    -- Last event before churn
    TIMESTAMP_DIFF(
      CAST(c.churn_date AS TIMESTAMP),
      MAX(CASE
        WHEN e.event_timestamp < CAST(c.churn_date AS TIMESTAMP)
        THEN e.event_timestamp
      END),
      DAY
    )                                                                 AS days_inactive_before_churn

  FROM churned_orgs c
  LEFT JOIN `saas-lifecycle-analytics.raw.event_logs` e USING (org_id)
  GROUP BY 1, 2
)

SELECT
  ROUND(AVG(events_last_14d), 1)             AS avg_events_last_14d_pre_churn,
  ROUND(AVG(events_14_30d), 1)              AS avg_events_15_30d_pre_churn,
  ROUND(AVG(days_inactive_before_churn), 1) AS avg_days_inactive_before_churn,
  COUNTIF(events_last_14d = 0)              AS orgs_with_zero_activity_last_14d,
  COUNT(*)                                   AS total_churned
FROM pre_churn_behavior;
```

---

### 6-3. Does engagement predict churn? (prospective test)

**Business question**: Can engagement tiers warn us about churn before it happens?

Two things make the obvious check invalid. First, **it is circular**: comparing each tier's churn rate as of today with today's churn status treats "stopped using the product" as a predictor of churn when it is partly a consequence (a churned account has already gone quiet). Second, **it is confounded by tenure**: new accounts are still onboarding, so they look "recently active", and they sit inside the window where churn happens, so activity appears to *raise* churn.

The valid design is prospective: features from events **before** a cutoff, outcome = churn in the **next** N days, for accounts still paying at the cutoff, stratified by tenure. Full query: the SUPPLEMENTAL block in `sql/marts/mart_user_behavior.sql`; Python: `prospective_engagement_dataset()` / `churn_by_feature()`.

**Data caveats, all found by running it**
- **The event log can't support the tiers.** Five onboarding event types, ~5 events per account, nothing after ~day 122. "Power = 10+ active days in the last 28" is unreachable, and measuring recency from `CURRENT_TIMESTAMP()` makes every account dormant (the data ends 2026-04-27). Only ~80 of 2,500 accounts have any event in the last 28 days of data.
- **The "at-risk" tier in the first draft wasn't at-risk.** `days_since_last_event <= 30` after failing the active thresholds catches brand-new accounts with few events. A real at-risk tier needs prior high activity *and* a recent drop.
- **The `churn_rate` denominator included accounts that never paid** (`churned / COUNT(DISTINCT org_id)` with `COALESCE(mrr, 0)`), so tiers full of unpaid accounts looked safer. Divide by paying accounts.
- **Result:** unadjusted, recently-active accounts churn 14.0% vs. 4.7% (backwards); within tenure bands the difference is small and not consistently signed (<=60 days: 17.1% vs. 17.3%; 61-120: 13.8% vs. 12.0%). Depth, activation and event volume don't separate churners (p = 0.17-0.76). All churn falls in months 2-4 after paying, so the actionable rule is tenure, not engagement. See `docs/process/05_analysis_findings.md -> Engagement and Churn`.

**Positive control.** "No signal found" is only convincing if the method *can* find one. A separate usage table with a planted signal (lower usage for eventual churners, a decline over the 3-6 weeks before churn, no channel effect) is used for that: tiers built from weekly usage (`sql/marts/mart_usage_engagement.sql`, Python `prospective_usage_dataset()`) put at-risk accounts at 18.0% 30-day churn vs. 0.5% (power) and 3.0% (active), still 3.8x to 8.9x more than active within tenure bands, while the channel negative control stays flat (2.5-3.1%). Note the horizon: a drop in usage is a short-lead warning, so the at-risk lift is 6.5x at 30 days but 2.7x at 90.

**Interview talking point**: "I don't validate an engagement tier by comparing it with today's churn status, because that's partly circular and heavily confounded by tenure. I take a snapshot at a past cutoff, build the features only from events before it, and check churn in the next 90 days within tenure bands. On our data that showed recently-active accounts churning three times as often unadjusted, which reversed once I controlled for tenure. Churn was entirely a function of months since conversion, so the recommendation was to target the first 120 days rather than to build tier-based alerts on an event log that only has onboarding events."

---

## Domain 7: Growth Recommendations (Meta angle)

**Business question**: Given all the data, which segment should we prioritize? What product change has the highest impact?

### 7-1. Opportunity sizing by segment

```sql
-- Which segments have the biggest activation gap (and thus the biggest upside)?
WITH segment_perf AS (
  SELECT
    o.acquisition_source,
    o.company_size,
    COUNT(DISTINCT o.org_id)                                                      AS signups,
    COUNT(DISTINCT CASE WHEN activated.org_id IS NOT NULL THEN o.org_id END)     AS activated,
    COUNT(DISTINCT CASE WHEN s.mrr_amount > 0 THEN o.org_id END)                AS paid,
    AVG(CASE WHEN s.mrr_amount > 0 THEN s.mrr_amount END)                        AS avg_mrr

  FROM `saas-lifecycle-analytics.raw.organizations` o
  LEFT JOIN (
    SELECT DISTINCT org_id
    FROM `saas-lifecycle-analytics.raw.event_logs`
    WHERE event_name IN ('teammate_invited','integration_connected','project_created')
    GROUP BY org_id
  ) activated USING (org_id)
  LEFT JOIN `saas-lifecycle-analytics.raw.subscriptions` s USING (org_id)
  GROUP BY 1, 2
),

-- Best-performing segment as benchmark
benchmark AS (
  SELECT MAX(activated / NULLIF(signups, 0)) AS best_activation_rate
  FROM segment_perf
)

SELECT
  sp.acquisition_source,
  sp.company_size,
  sp.signups,
  ROUND(sp.activated / NULLIF(sp.signups, 0), 3)                              AS activation_rate,
  ROUND(b.best_activation_rate, 3)                                            AS benchmark_rate,

  -- Gap to benchmark
  ROUND(b.best_activation_rate - sp.activated / NULLIF(sp.signups, 0), 3)   AS activation_gap,

  -- Incremental revenue if we closed the gap
  ROUND(
    (b.best_activation_rate - sp.activated / NULLIF(sp.signups, 0))
    * sp.signups
    * (sp.paid / NULLIF(sp.activated, 0))   -- activated-to-paid rate
    * COALESCE(sp.avg_mrr, 0)
  , 0)                                                                        AS incremental_mrr_opportunity

FROM segment_perf sp
CROSS JOIN benchmark b
ORDER BY incremental_mrr_opportunity DESC;
```

**Interview talking point (Meta)**: "This is how I translate a data finding into a product priority. If SMB organic has a 15pp activation gap versus the benchmark, and there are 500 SMB organic orgs with $80 ARPA, closing that gap is worth ~$42K MRR. That's a quantified opportunity — it gives PM/Eng a number to weigh against engineering cost."

---

### 7-2. Root cause: rate effect vs. mix effect

**Business question**: Activation rate dropped week-over-week. Is that a product problem or did the mix of who signed up change?

Overall rate = sum over segments of (mix x rate), so the change splits exactly into three terms per segment:

```
rate effect        = (cur_rate - prior_rate) x prior_mix     -> product/UX owns it
mix effect         = (cur_mix  - prior_mix)  x (prior_rate - prior_overall_rate)  -> acquisition owns it
interaction effect = (cur_mix  - prior_mix)  x (cur_rate - prior_rate)
```

Full query: `sql/marts/mart_root_cause.sql`. Three things it now does that a first draft typically doesn't:

- **Includes the interaction term.** The two-term form (rate + mix) is only a first-order approximation; it silently fails to reconcile whenever both rate and mix moved.
- **Centers the mix effect on the overall rate.** `Δmix x prior_rate` sums to the same total (mix shifts add to zero), but per segment it points the wrong way: a low-activating channel that grows its share looks like a *positive* contributor. On the two-channel example (organic 80%->50% of signups at 55%, paid_search 20%->50% at 20%) the uncentered form gives paid_search +6.0pp; centered, paid_search is -8.4pp and organic -2.1pp, still summing to -10.5pp, and now correctly names paid_search as the drag.
- **Doesn't lose new/departed segments.** With a FULL OUTER JOIN, a segment present in only one period has a NULL rate for the other, so its effect is NULL and disappears from `SUM()`. Filling the missing rate with the observed one (`COALESCE(p.rate, c.rate)`) counts it as a pure mix effect and keeps the total reconciled.
- **Doesn't compare a partial trailing period.** `ROW_NUMBER() OVER (ORDER BY week_start DESC)` picks the newest week, which is usually incomplete; comparing it to a full week manufactures a "drop".

**Data caveat**: this project's process notes used to walk through "activation dropped 4pp from week 8 to week 9" with a -5.2pp rate and +1.2pp mix effect. Those numbers were never computed from the dataset and don't reproduce. On the real data, weekly cohorts (~40-50 accounts) swing 10-20pp on sampling noise alone, so the real case is at a monthly grain: Sep -> Oct 2025 activation fell 44.7% -> 34.0% (-10.7pp), decomposing to a -10.9pp rate effect, -0.2pp mix, +0.5pp interaction: rate-driven. But that is the largest of 11 month-over-month comparisons (p = 0.027, above the Bonferroni bar of 0.0045) and November rebounded fully, so it may be noise. See `docs/process/05_analysis_findings.md -> Root Cause Analysis`.

**Interview talking point**: "When a metric drops I split it into rate, mix and interaction effects before escalating, because they have different owners: a rate effect goes to product, a mix effect to acquisition. But decomposition only says where a change came from, not whether it was real, so I test the change first, and if I picked it as the biggest of many periods I hold it to a multiple-comparisons standard. In our data the September-to-October drop was cleanly rate-driven but didn't survive that, and it rebounded the next month, so I wouldn't have sent it to engineering on that evidence alone."

---

## Interview Q&A

### Tavus-specific

**Q: "Walk me through how you'd measure whether a developer has reached the aha moment."**

A: "I define the aha moment as `integration_connected` within 7 days of signup — that's the point where a developer has working API access and has generated their first output. I then look at the downstream retention rate for accounts that hit this milestone versus those that didn't. If integration-first accounts retain at 70% vs 30% for non-activated, that's the aha moment signal. I'd then look at what's blocking integration: is it time-to-first-API-call, documentation friction, or onboarding copy?"

**Q: "How do you define activation for an API-first product?"**

A: "Activation isn't signup — it's the first moment the user gets value from the core product. For an API product like Tavus, that's the first successful API call or video generation. I use `integration_connected` as the activation gate because it requires: (1) the developer read the docs, (2) configured their environment, and (3) got a working response. Workspace creation alone is an onboarding step, not activation."

**Q: "CAC and LTV — how do you calculate these without a dedicated CAC dataset?"**

A: "I don't compute CAC or LTV:CAC without spend data — a made-up proxy would look like an answer and isn't one. I compute LTV from observed subscriptions: ARPA divided by monthly churn, where churn is churn events per account-month of exposure (active subscriptions count as censored exposure). I cap it at a fixed horizon because 1/churn can imply a lifetime longer than anything observed, and I put a bootstrap interval on it. Then I flip the question: at a 3:1 target ratio, LTV/3 is the most we could spend per account. That gives finance a ceiling to compare real CAC against, and I'd push for actual spend data from the marketing team."

---

### Meta-specific

**Q: "How do you decide whether to ship an experiment result?"**

A: "Four checks: (1) Is the primary metric significant (|z| > 1.96)? (2) Are guardrail metrics (paid conversion, retention) not harmed? (3) Does the lift hold across key segments — HTE check? (4) Is the sample size large enough that the confidence interval excludes zero meaningfully? If all four pass, I recommend ship. If primary is positive but a guardrail is degraded, I escalate to product to weigh the tradeoff. If HTE shows the treatment helps SMB but hurts Enterprise, I'd recommend a targeted rollout."

**Q: "How do you identify what's causing a metric to move?"**

A: "I start with decomposition: break the metric into its components. If activation drops 5pp, is it the workspace creation rate, the integration rate, or both? Then I check for confounders: did the user mix change (more Enterprise, harder to activate)? Did a deploy go out? I use a week-over-week comparison with segment cuts. The goal is to isolate whether it's a product change, a population change, or external. Only once I know what changed do I look for why."

**Q: "You have activation data. How do you turn it into a product recommendation?"**

A: "I quantify the opportunity first: 'If we raised SMB activation from 40% to 55% (the benchmark), we'd add $42K MRR at current ARPA and conversion rates.' Then I look at where in the funnel the drop-off happens — is it workspace creation (onboarding friction) or integration (technical friction)? That points to whether PM/design or engineering needs to act. I package it as: here's the size of the prize, here's where the leak is, here's one testable hypothesis to close it."
