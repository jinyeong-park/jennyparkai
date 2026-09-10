/*
  Model:    mrt_attribution_comparison
  Layer:    Mart
  Upstream: All four attribution mart models + stg_ad_spend

  Executive comparison table: consolidates all four attribution models with
  channel spend to compute ROAS under each model side by side.

  This is the primary output for budget reallocation decisions.
  Key insight: channels where platform_roas >> time_decay_roas indicate
  high organic cannibalization — the channel claims credit for conversions
  that would have happened without the ad (confirmed by geo-holdout in Phase 4).

  Channel join note: stg_ad_spend only covers paid channels (Meta, Google, TikTok).
  Attribution models may include Google_Organic and Email_CRM — those will
  have NULL spend and ROAS in this table, which is expected.
*/

WITH spend AS (
    SELECT
        channel,
        SUM(spend_usd)                        AS total_spend_usd,
        SUM(platform_reported_conversions)    AS total_platform_conversions
    FROM {{ ref('stg_ad_spend') }}
    GROUP BY channel
),

first_touch AS (
    SELECT channel, attributed_revenue_usd AS first_touch_revenue
    FROM {{ ref('mrt_first_touch_attribution') }}
),

last_touch AS (
    SELECT channel, attributed_revenue_usd AS last_touch_revenue
    FROM {{ ref('mrt_last_touch_attribution') }}
),

linear AS (
    SELECT channel, attributed_revenue_usd AS linear_revenue
    FROM {{ ref('mrt_linear_attribution') }}
),

time_decay AS (
    SELECT channel, attributed_revenue_usd AS time_decay_revenue
    FROM {{ ref('mrt_time_decay_attribution') }}
)

SELECT
    s.channel,
    ROUND(s.total_spend_usd, 2)                                                   AS total_spend_usd,
    s.total_platform_conversions,

    -- Revenue attributed by each model
    ROUND(COALESCE(ft.first_touch_revenue, 0), 2)                                 AS first_touch_revenue,
    ROUND(COALESCE(lt.last_touch_revenue, 0), 2)                                  AS last_touch_revenue,
    ROUND(COALESCE(l.linear_revenue, 0), 2)                                       AS linear_revenue,
    ROUND(COALESCE(td.time_decay_revenue, 0), 2)                                  AS time_decay_revenue,

    -- ROAS by model (attributed_revenue / spend)
    ROUND(COALESCE(ft.first_touch_revenue, 0) / NULLIF(s.total_spend_usd, 0), 2) AS first_touch_roas,
    ROUND(COALESCE(lt.last_touch_revenue, 0)  / NULLIF(s.total_spend_usd, 0), 2) AS last_touch_roas,
    ROUND(COALESCE(l.linear_revenue, 0)        / NULLIF(s.total_spend_usd, 0), 2) AS linear_roas,
    ROUND(COALESCE(td.time_decay_revenue, 0)   / NULLIF(s.total_spend_usd, 0), 2) AS time_decay_roas,

    -- Platform-reported ROAS (for bias comparison; assumes avg order value = $160)
    ROUND(
        (s.total_platform_conversions * 160.0) / NULLIF(s.total_spend_usd, 0), 2
    )                                                                              AS platform_reported_roas

FROM spend s
LEFT JOIN first_touch ft ON s.channel = ft.channel
LEFT JOIN last_touch  lt ON s.channel = lt.channel
LEFT JOIN linear      l  ON s.channel = l.channel
LEFT JOIN time_decay  td ON s.channel = td.channel
ORDER BY time_decay_roas DESC NULLS LAST
