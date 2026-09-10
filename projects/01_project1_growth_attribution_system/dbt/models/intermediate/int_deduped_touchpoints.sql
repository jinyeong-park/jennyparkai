/*
  Model:    int_deduped_touchpoints
  Layer:    Intermediate
  Upstream: stg_user_touchpoints

  Problem:  ~3% of touchpoint events are duplicates caused by rapid double-clicks
            or network-level tracking tag retries. Including duplicates inflates
            touchpoint counts and distorts all downstream attribution weights.

  Solution: ROW_NUMBER() partitioned by (user_id, event_timestamp, channel).
            Within each duplicate group, keeps the row with the lowest event_id.
            This is the standard SQL deduplication pattern for event-stream data.

  Result:   Removes ~3% of rows. event_id is unique after this step.
*/

WITH ranked AS (
    SELECT
        event_id,
        user_id,
        event_timestamp,
        utm_source,
        utm_medium,
        utm_campaign,
        channel,
        dma_code,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, event_timestamp, channel  -- defines "duplicate"
            ORDER BY event_id ASC                           -- keep the earliest event_id
        ) AS row_num
    FROM {{ ref('stg_user_touchpoints') }}
)

SELECT
    event_id,
    user_id,
    event_timestamp,
    utm_source,
    utm_medium,
    utm_campaign,
    channel,
    dma_code
FROM ranked
WHERE row_num = 1
