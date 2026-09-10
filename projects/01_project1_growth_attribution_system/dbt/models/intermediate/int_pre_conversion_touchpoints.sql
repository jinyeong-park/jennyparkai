/*
  Model:    int_pre_conversion_touchpoints
  Layer:    Intermediate
  Upstream: int_deduped_touchpoints, stg_conversions

  Joins deduped touchpoints with conversions to produce the core attribution dataset.
  Enforces two critical constraints:

  1. Causal direction guard:
     touchpoint_ts <= conversion_ts
     An ad click recorded AFTER a purchase cannot have caused that purchase.
     Violating this inverts causality and corrupts attribution results.

  2. Attribution window (90 days):
     touchpoint_ts >= conversion_ts - INTERVAL '90 days'
     Only touchpoints within 90 days before conversion are eligible for credit.
     Common windows: 7 days (direct response), 30 days (standard), 90 days (considered).

  This table is the direct input to all four attribution models in the marts layer.
  All paid AND organic/CRM channels are included — paid-only filtering happens in marts
  when joining with stg_ad_spend (which only covers Meta, Google, TikTok).
*/

SELECT
    t.user_id,
    t.event_id,
    t.channel,
    t.dma_code,
    t.event_timestamp                                     AS touchpoint_ts,
    c.conversion_id,
    c.converted_at                                        AS conversion_ts,
    c.order_value_usd
FROM {{ ref('int_deduped_touchpoints') }} t
INNER JOIN {{ ref('stg_conversions') }} c
    ON t.user_id = c.user_id
WHERE t.event_timestamp <= c.converted_at                            -- causal guard
    AND t.event_timestamp >= c.converted_at - INTERVAL '90 days'    -- attribution window
