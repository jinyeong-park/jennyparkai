/*
  Model:   stg_user_touchpoints
  Layer:   Staging
  Source:  data/raw/raw_user_touchpoints.csv
           Simulates GA4 BigQuery Export or Segment/Amplitude event stream.

  Transformations:
  - Cast timestamp
  - Normalize UTM fields: LOWER() + TRIM() removes case/whitespace noise from
    manually-entered campaign URL parameters
  - Rename campaign_name → utm_campaign for semantic clarity
  - Map all channel variants to 5 canonical values:
      Meta_Paid_Social | Google_Paid_Search | TikTok_Ads | Google_Organic | Email_CRM

  Note: ~3% of rows are duplicates (double-clicks, network-level tag retries).
        Deduplication is intentionally deferred to int_deduped_touchpoints
        so this staging layer remains a clean 1:1 reflection of the source.
*/

SELECT
    event_id,
    user_id,
    timestamp::TIMESTAMP                                          AS event_timestamp,
    LOWER(TRIM(utm_source))                                       AS utm_source,
    LOWER(TRIM(utm_medium))                                       AS utm_medium,
    LOWER(TRIM(campaign_name))                                    AS utm_campaign,
    CASE
        WHEN LOWER(TRIM(channel)) IN ('meta_paid_social', 'meta', 'facebook')
            THEN 'Meta_Paid_Social'
        WHEN LOWER(TRIM(channel)) IN ('google_paid_search', 'google_search', 'google paid search')
            THEN 'Google_Paid_Search'
        WHEN LOWER(TRIM(channel)) IN ('tiktok_ads', 'tiktok', 'tik tok')
            THEN 'TikTok_Ads'
        WHEN LOWER(TRIM(channel)) IN ('google_organic', 'organic search', 'organic')
            THEN 'Google_Organic'
        WHEN LOWER(TRIM(channel)) IN ('email_crm', 'email', 'crm')
            THEN 'Email_CRM'
        ELSE INITCAP(TRIM(channel))
    END                                                           AS channel,
    TRIM(dma_code)                                                AS dma_code
FROM {{ ref('raw_user_touchpoints') }}
