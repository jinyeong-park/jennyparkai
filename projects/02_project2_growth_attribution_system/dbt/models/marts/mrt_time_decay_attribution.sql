/*
  Model:    mrt_time_decay_attribution   ← Primary model for this project
  Layer:    Mart
  Upstream: int_pre_conversion_touchpoints

  Time-Decay Attribution:
  Touchpoints closer to conversion receive exponentially more credit.

  Formula:  weight = 2^(-days_before_conversion / 7)   [7-day half-life]

    Days before conversion | Weight
    ───────────────────────┼───────
    0 days                 | 1.000
    7 days                 | 0.500
    14 days                | 0.250
    21 days                | 0.125

  Weights are normalized per user (sum = 1.0) so that total attributed revenue
  across all channels equals the actual order_value_usd for that conversion.

  Best for:   Performance marketing where recency of ad interaction is the
              strongest signal of purchase intent. Most realistic single-source
              model for bottom-of-funnel analysis.
*/

WITH decay_weights AS (
    SELECT
        user_id,
        channel,
        order_value_usd,
        touchpoint_ts,
        conversion_ts,
        -- Days elapsed between this touchpoint and the conversion
        EXTRACT(EPOCH FROM (conversion_ts - touchpoint_ts)) / 86400.0  AS days_before_conversion,
        -- Exponential decay weight: more recent = heavier weight
        POW(
            2,
            -(EXTRACT(EPOCH FROM (conversion_ts - touchpoint_ts)) / 86400.0) / 7.0
        )                                                               AS weight
    FROM {{ ref('int_pre_conversion_touchpoints') }}
),

normalized AS (
    SELECT
        user_id,
        channel,
        order_value_usd,
        weight,
        -- Sum of weights across all touchpoints for this user (normalization denominator)
        SUM(weight) OVER (PARTITION BY user_id)  AS total_weight_per_user
    FROM decay_weights
)

SELECT
    channel,
    COUNT(DISTINCT user_id)                                             AS attributed_conversions,
    ROUND(SUM(order_value_usd * (weight / total_weight_per_user)), 2)  AS attributed_revenue_usd
FROM normalized
GROUP BY channel
ORDER BY attributed_revenue_usd DESC
