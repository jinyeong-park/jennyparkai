# How to get this marketing data in the real world?

In a real-world enterprise environment, Data Analysts and Growth Marketers rarely download these files manually by clicking export buttons on ad platform dashboards every day.

Instead, automated ETL/ELT pipelines (such as **Fivetran**, **Airbyte**(ETL Tools), or **Apache Airflow**) sync raw data into a Cloud Data Warehouse (**BigQuery**, **Snowflake**, or **Redshift**). Analysts then write SQL queries within the warehouse to transform and export the datasets as CSV files.

### **1. raw_ad_spend.csv (Ad Platform Cost & Performance Data)**

#### **🏢 Real-World Pipeline & Source**

- **Source:** Reporting APIs of ad platforms (Meta Ads Manager, Google Ads API, TikTok Ads Manager API).
- **Automated Pipeline:** An ETL connector (e.g., Fivetran or Airbyte) calls the APIs every night (typically around 2 AM) to ingest daily aggregate metrics—Spend, Impressions, Clicks, and Platform-Reported Conversions—sliced by Campaign and DMA into the Data Warehouse.

#### **💻 How Analysts Extract CSVs in Practice**

- **Data Warehouse Users (SQL):**  
  Analysts query the aggregated ad spend table in BigQuery or Snowflake and export the results.  
  SQL
  ```
  -- Extracting daily spend from Snowflake/BigQuery
  SELECT
   ad_date AS date,
   channel,
   dma_code,
   spend_usd AS daily_spend_usd,
   reported_conversions AS platform_reported_conversions
  FROM marketing_db.daily_ad_spend_aggregated
  WHERE ad_date BETWEEN '2026-01-01' AND '2026-06-30'
  ORDER BY 1, 2;
  ```

```
  After executing the query in the Web Console, they click **"Download Results as CSV"** or export to cloud storage.

- **Non-SQL / Marketer Workflow:**
  Marketers navigate to BI tools (Looker, Tableau, Redash, or Google Looker Studio) and click **Export to CSV** on the underlying data table widget.

### **2. raw_user_touchpoints.csv (Web & App User Event Logs)**

#### **🏢 Real-World Pipeline & Source**

- **Source:** Product Analytics & CDPs (Google Analytics 4, Amplitude, Mixpanel, Segment, or RudderStack).
- **Automated Pipeline:** Front-end tracking SDKs and Google Tag Manager (GTM) capture click and session events.
  - **GA4 BigQuery Export:** GA4 streams raw event data into daily partitioned tables (events_YYYYMMDD) automatically.
  - **Segment / Amplitude:** Events are streamed directly into Snowflake/BigQuery event schema tables.

#### **💻 How Analysts Extract CSVs in Practice**

- **Extracting from GA4 Raw BigQuery Tables:**
  SQL
  \-- Querying raw event logs for session touchpoints
  SELECT
   event_id,
   user_pseudo_id AS user_id,
   TIMESTAMP_MICROS(event_timestamp) AS timestamp,
   traffic_source.source AS utm_source,
   traffic_source.medium AS utm_medium,
   traffic_source.name AS campaign_name,
   geo.metro AS dma_code
  FROM \`your\-project.analytics_123456789.events\_\*\`
  WHERE \_TABLE_SUFFIX BETWEEN '20260101' AND '20260630'
   AND event_name \= 'session_start'

  Because touchpoint logs can reach gigabytes or terabytes, analysts usually export the query results directly to **Google Cloud Storage (GCS)** or **AWS S3** before downloading the CSV locally.

### **3. raw_conversions.csv (Backend Order & Transaction Data)**

#### **🏢 Real-World Pipeline & Source**

- **Source:** Production Databases (PostgreSQL, MySQL) or E-commerce platforms (Shopify, Stripe).
- **Automated Pipeline:**
  - Production DBs use Change Data Capture (CDC via Debezium) or Airflow DAGs to replicate order tables to the Data Warehouse read-replica.
  - E-commerce platforms sync order records using native Webhooks or API connectors.

#### **💻 How Analysts Extract CSVs in Practice**

- **Extracting Completed Orders via SQL Client (DBeaver, DataGrip, Metabase):**
  SQL
  \-- Extracting completed backend orders
  SELECT
   order_uuid AS conversion_id,
   user_id,
   order_id,
   created_at AS converted_at,
   total_amount_usd AS order_value_usd,
   shipping_dma AS dma_code
  FROM production_db.orders
  WHERE status \= 'COMPLETED'
   AND created_at \>= '2026-01-01' AND created_at \< '2026-07-01';

  The analyst runs this query and chooses **Export Data \-\> CSV Format**.

### **💡 Real-World Data Realities vs. Our Synthetic Dataset**

| Feature                 | Real-World Scenario                                                           | Our Dataset Reflection                                             |
| :---------------------- | :---------------------------------------------------------------------------- | :----------------------------------------------------------------- |
| **UTM Noise**           | Case sensitivity issues (Q1_prospecting vs q1_prospecting) due to human error | **Reflected** (Requires SQL LOWER() & CASE WHEN cleaning)          |
| **Tracker Duplication** | Double-firing tags caused by rapid double-clicks or page refreshes            | **Reflected** (3% duplicate rate; fixed using ROW_NUMBER())        |
| **Over-reporting**      | Meta and Google both claiming credit for the same conversion                  | **Reflected** (Self-reported conversions \> Actual DW conversions) |
| **Geo Tracking**        | IP-to-DMA mapping noise and location inaccuracies                             | **Reflected** (Structured 50 unique US city DMAs)                  |
```
