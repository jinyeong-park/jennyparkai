/*
  stg_product_events
  ===================
  Source: raw_product_events

  Standardizes product usage events and adds engagement signals
  used in customer health analysis and lead scoring.
*/

WITH source AS (

    SELECT * FROM {{ ref('raw_product_events') }}

)

SELECT
    user_id,
    account_id,
    event_timestamp::TIMESTAMP AS event_timestamp,
    event_timestamp::DATE      AS event_date,
    EXTRACT(YEAR  FROM event_timestamp::DATE)::INT AS event_year,
    EXTRACT(MONTH FROM event_timestamp::DATE)::INT AS event_month,

    event_name,
    feature_name,
    active_users,
    activation_event::BOOLEAN AS is_activation_event,

    -- Engagement tier per event
    -- Used in customer health scoring: high-value events signal strong adoption
    CASE event_name
        WHEN 'activation_completed'   THEN 'High'
        WHEN 'integration_connected'  THEN 'High'
        WHEN 'workspace_created'      THEN 'High'
        WHEN 'report_created'         THEN 'Medium'
        WHEN 'invite_user'            THEN 'Medium'
        WHEN 'feature_used'           THEN 'Medium'
        WHEN 'api_call'               THEN 'Medium'
        WHEN 'login'                  THEN 'Low'
        ELSE 'Low'
    END AS engagement_tier

FROM source
