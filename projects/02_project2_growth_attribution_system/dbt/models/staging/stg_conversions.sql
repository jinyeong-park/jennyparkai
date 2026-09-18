/*
  Model:   stg_conversions
  Layer:   Staging
  Source:  data/raw/raw_conversions.csv
           Simulates CDC replication from a production PostgreSQL orders table
           (via Debezium or Airflow DAG) or Shopify Webhook → ETL pipeline.

  This is the ground-truth dataset.
  All ROAS calculations and attribution models are anchored to order_value_usd
  from this table — independent of any ad platform's self-reported conversion claims.

  Transformations:
  - Cast timestamp and numeric types
  - Select and rename relevant columns
*/

SELECT
    conversion_id,
    user_id,
    order_id,
    converted_at::TIMESTAMP   AS converted_at,
    order_value_usd::NUMERIC  AS order_value_usd,
    TRIM(dma_code)            AS dma_code
FROM {{ ref('raw_conversions') }}
