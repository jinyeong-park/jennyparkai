/*
  Model:    mrt_first_touch_attribution
  Layer:    Mart
  Upstream: int_pre_conversion_touchpoints

  First-Touch Attribution:
  100% of conversion credit goes to the earliest touchpoint in the user journey.

  Best for:    Top-of-funnel awareness measurement. Answers "which channel
               first introduced this user to the brand?"

  Limitation:  Ignores all mid- and bottom-funnel touchpoints entirely.
               Overvalues discovery channels (TikTok at 2.45x),
               undervalues intent channels (Google Paid Search at 1.95x).
*/

WITH sequenced AS (
    SELECT
        user_id,
        channel,
        touchpoint_ts,
        order_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY touchpoint_ts ASC   -- earliest touchpoint = rank 1
        ) AS touchpoint_rank
    FROM {{ ref('int_pre_conversion_touchpoints') }}
)

SELECT
    channel,
    COUNT(DISTINCT user_id)         AS attributed_conversions,
    ROUND(SUM(order_value_usd), 2)  AS attributed_revenue_usd
FROM sequenced
WHERE touchpoint_rank = 1            -- keep only the first touchpoint per user
GROUP BY channel
ORDER BY attributed_revenue_usd DESC
