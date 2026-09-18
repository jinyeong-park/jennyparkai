/*
  Model:    mrt_linear_attribution
  Layer:    Mart
  Upstream: int_pre_conversion_touchpoints

  Linear Attribution:
  Conversion credit split equally across every touchpoint in the user journey.

  Best for:    Balanced view of the full funnel. Useful as a sanity-check
               baseline between the extremes of First-Touch and Last-Touch.

  Limitation:  Treats a brief brand impression equally with a high-intent
               search click. Does not account for recency or frequency of contact.

  Mechanic:    COUNT(*) OVER (PARTITION BY user_id) computes the total number of
               touchpoints per user without collapsing rows. Each row then carries
               its proportional share: order_value_usd / total_touchpoints.
*/

SELECT
    channel,
    COUNT(DISTINCT user_id)                                       AS users_touched,
    ROUND(SUM(order_value_usd / total_touchpoints_per_user), 2)  AS attributed_revenue_usd
FROM (
    SELECT
        user_id,
        channel,
        order_value_usd,
        COUNT(*) OVER (PARTITION BY user_id) AS total_touchpoints_per_user
    FROM {{ ref('int_pre_conversion_touchpoints') }}
) t
GROUP BY channel
ORDER BY attributed_revenue_usd DESC
