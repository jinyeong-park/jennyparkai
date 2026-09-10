/*
  Singular Test: assert_no_duplicate_event_ids
  Target model: int_deduped_touchpoints

  After ROW_NUMBER() deduplication, every event_id should appear exactly once.
  If any event_id appears more than once, the deduplication logic has a gap.

  Note: this differs from the upstream duplicate problem (same user+time+channel).
        Here we check that event_id itself — which should be globally unique —
        is not repeated in the deduped output.

  This test returns any violating rows — dbt fails the test if row count > 0.
  Run with: dbt test --select assert_no_duplicate_event_ids
*/

SELECT
    event_id,
    COUNT(*) AS occurrences
FROM {{ ref('int_deduped_touchpoints') }}
GROUP BY event_id
HAVING COUNT(*) > 1
