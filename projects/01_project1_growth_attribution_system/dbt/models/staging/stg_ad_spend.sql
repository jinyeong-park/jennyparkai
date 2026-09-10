/*
  Model:   stg_ad_spend
  Layer:   Staging
  Source:  data/raw/raw_ad_spend.csv
           Simulates nightly Fivetran/Airbyte ETL from Meta, Google, TikTok Ads APIs.

  Transformations:
  - Cast date and numeric types
  - Rename columns for clarity (date → ad_date, daily_spend_usd → spend_usd)
  - Standardize channel names to match stg_user_touchpoints canonical values

  Note: platform_reported_conversions are self-reported by each ad platform.
        Due to self-attribution bias, combined platform numbers exceed actual
        backend conversions by ~34%. Do not use as ground-truth conversion data.
*/

SELECT
    date::DATE                                            AS ad_date,
    CASE
        WHEN LOWER(TRIM(channel)) = 'meta_paid_social'    THEN 'Meta_Paid_Social'
        WHEN LOWER(TRIM(channel)) = 'google_paid_search'  THEN 'Google_Paid_Search'
        WHEN LOWER(TRIM(channel)) = 'tiktok_ads'          THEN 'TikTok_Ads'
        ELSE INITCAP(TRIM(channel))
    END                                                   AS channel,
    TRIM(dma_code)                                        AS dma_code,
    daily_spend_usd::NUMERIC                              AS spend_usd,
    platform_reported_conversions::INTEGER                AS platform_reported_conversions
FROM {{ ref('raw_ad_spend') }}
