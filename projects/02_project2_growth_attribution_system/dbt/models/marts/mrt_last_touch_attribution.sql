/*
  Model:    mrt_last_touch_attribution
  Layer:    Mart
  Upstream: int_pre_conversion_touchpoints

  Last-Touch Attribution:
  100% of conversion credit goes to the touchpoint immediately before conversion.

  Best for:    Direct-response and bottom-of-funnel performance evaluation.
               Answers "which channel closed the sale?"

  Limitation:  This is the default model used by most ad platforms — and the
               primary driver of self-attribution bias. Meta retargeting appears
               right before purchase but may have near-zero true incremental lift
               (confirmed by geo-holdout: iROAS 1.26x vs. platform-reported 3.25x).
*/

WITH sequenced AS (
    SELECT
        user_id,
        channel,
        touchpoint_ts,
        order_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY touchpoint_ts DESC  -- most recent touchpoint = rank 1
        ) AS reverse_rank
    FROM {{ ref('int_pre_conversion_touchpoints') }}
)

SELECT
    channel,
    COUNT(DISTINCT user_id)         AS attributed_conversions,
    ROUND(SUM(order_value_usd), 2)  AS attributed_revenue_usd
FROM sequenced
WHERE reverse_rank = 1               -- keep only the last touchpoint per user
GROUP BY channel
ORDER BY attributed_revenue_usd DESC
