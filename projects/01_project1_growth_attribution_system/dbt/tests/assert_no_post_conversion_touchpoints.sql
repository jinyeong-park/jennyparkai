/*
  Singular Test: assert_no_post_conversion_touchpoints
  Target model: int_pre_conversion_touchpoints

  A touchpoint that occurred AFTER the conversion cannot have caused that conversion.
  The WHERE clause in int_pre_conversion_touchpoints should filter all such rows out.

  This test returns any violating rows — dbt fails the test if row count > 0.
  Run with: dbt test --select assert_no_post_conversion_touchpoints
*/

SELECT
    user_id,
    event_id,
    touchpoint_ts,
    conversion_ts,
    touchpoint_ts - conversion_ts AS time_after_conversion
FROM {{ ref('int_pre_conversion_touchpoints') }}
WHERE touchpoint_ts > conversion_ts
