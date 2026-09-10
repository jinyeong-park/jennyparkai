# Phase 1: Data Acquisition

> **Core Question:** How does a real company actually collect ad performance and conversion data?

---

## Why We Do Not Start With a CSV Download

Most people initially think of data acquisition as: "Log into Meta Ads Manager → Export CSV." In a production environment, this approach does not scale.

**Why manual downloads fail:**

- Daily manual exports across Meta, Google, and TikTok introduce human error and inconsistent formatting
- Data at enterprise scale reaches gigabytes or terabytes — browser-based downloads are not feasible
- Manual processes cannot support automated dashboards or real-time reporting

**How real companies do it:**

```
Ad Platform APIs  →  ETL Tool  →  Cloud Data Warehouse  →  SQL Query  →  Analysis
(Meta / Google)     (Fivetran)     (BigQuery / Snowflake)
```

---

## The Three Data Sources in This Project

### Source 1: `raw_ad_spend.csv` — Ad Platform Cost and Reported Performance

**Real-world origin:** Meta Ads Manager API, Google Ads API, TikTok Ads Manager API

**Real-world pipeline:**

```
[Meta / Google / TikTok APIs]
        ↓
[Fivetran or Airbyte calls APIs nightly (~2 AM)]
[Ingests daily aggregate metrics by Campaign and DMA]
        ↓
[Lands in marketing_db.daily_ad_spend table in BigQuery or Snowflake]
        ↓
[Data Analyst writes SQL → exports CSV]
```

**Fields included:**
| Field | Description |
|-------|-------------|
| `ad_date` | Date of the ad run |
| `channel` | Meta_Paid_Social / Google_Search / TikTok_Ads |
| `dma_code` | Designated Market Area Code (Geographic market code, U.S. advertising regions) |
| `spend_usd` | Ad spend for that day |
| `platform_reported_conversions` | Conversions claimed by the platform — **this number is inflated and is the core problem** |

**How analysts extract this in practice:**

```sql
-- Querying daily ad spend from Snowflake or BigQuery
SELECT
    ad_date                  AS date,
    channel,
    dma_code,
    spend_usd                AS daily_spend_usd,
    reported_conversions     AS platform_reported_conversions
FROM marketing_db.daily_ad_spend_aggregated
WHERE ad_date BETWEEN '2026-01-01' AND '2026-06-30'
ORDER BY 1, 2;
```

> After running the query, analysts click "Download Results as CSV" in the web console.
> Non-SQL marketers export from BI tools like Looker, Tableau, or Looker Studio.

---

### Source 2: `raw_user_touchpoints.csv` — User Clickstream and Event Logs

**Real-world origin:** Google Analytics 4 (GA4), Amplitude, Mixpanel, Segment, or RudderStack

**Why this data source matters:**

> Ad platform data reflects each platform's own perspective — they each claim credit for conversions independently.
> Clickstream data records the user's actual journey across all channels in a neutral, first-party way.
> This is the foundation for any Multi-Touch Attribution model.

**Real-world pipeline:**

```
[User clicks an ad or visits the site]
        ↓
[GA4 SDK or Google Tag Manager fires an event in the browser]
[Captures: user_id, timestamp, utm_source, utm_medium, utm_campaign, DMA from IP]
        ↓
[GA4 BigQuery Export: streams events into daily partitioned tables (events_YYYYMMDD)]
  OR
[Segment / Amplitude: streams events directly into Snowflake or BigQuery]
        ↓
[Analyst queries the raw event tables with SQL]
```

**How analysts extract this from GA4 raw tables:**

```sql
-- Querying raw session-level touchpoints from GA4 BigQuery export
SELECT
    event_id,
    user_pseudo_id                              AS user_id,
    TIMESTAMP_MICROS(event_timestamp)           AS timestamp,
    traffic_source.source                       AS utm_source,
    traffic_source.medium                       AS utm_medium,
    traffic_source.name                         AS campaign_name,
    geo.metro                                   AS dma_code
FROM `your-project.analytics_123456789.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260101' AND '20260630'
    AND event_name = 'session_start'
```

> Because touchpoint logs can be hundreds of gigabytes, analysts typically export results
> to Google Cloud Storage (GCS) or AWS S3 before downloading locally.

**Fields included:**
| Field | Description |
|-------|-------------|
| `event_id` | Unique identifier for each click or visit event |
| `user_id` | User identifier — used to JOIN with the conversions table |
| `timestamp` | When the event occurred |
| `channel` | Which channel brought the user (Meta, Google, TikTok, Organic, etc.) |
| `utm_source / utm_medium / utm_campaign` | URL tracking parameters |
| `dma_code` | User's geographic region |

**Real-world noise reflected in this dataset:**

| Noise Type             | Root Cause                                                               | Example                                                                          |
| ---------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| UTM case inconsistency | Marketers manually type UTM parameters in campaign URLs                  | `Q1_Prospecting` vs `q1_prospecting` — treated as two different campaigns in SQL |
| Duplicate events       | Users double-click rapidly or network retries cause duplicate tag fires  | Same user_id + timestamp + channel recorded twice (~3% of rows)                  |
| Signal loss (iOS 14+)  | Apple's App Tracking Transparency policy reduces consent for ad tracking | Incomplete or null user_id values for a portion of traffic                       |

---

### Source 3: `raw_conversions.csv` — Backend Order and Transaction Records

**Real-world origin:** Production databases (PostgreSQL, MySQL) or e-commerce platforms (Shopify, Stripe)

**Why this is the most critical source:**

> This is the **ground truth**.
> Regardless of what any ad platform claims, a completed order in the production database is the definitive record of a conversion.
> All ROAS calculations and Attribution models are anchored to this data.

**Real-world pipeline:**

```
[User completes a purchase]
        ↓
[Production database (PostgreSQL) records a COMPLETED order in the orders table]
        ↓
[Change Data Capture (CDC via Debezium) or Airflow DAG replicates the record to the Data Warehouse]
  OR
[Shopify Webhook → ETL connector → Data Warehouse]
        ↓
[Analyst queries the replicated orders table]
```

**How analysts extract this in practice:**

```sql
-- Extracting completed backend orders via SQL client (DBeaver, DataGrip, Metabase)
SELECT
    order_uuid       AS conversion_id,
    user_id,
    order_id,
    created_at       AS converted_at,
    total_amount_usd AS order_value_usd,
    shipping_dma     AS dma_code
FROM production_db.orders
WHERE status = 'COMPLETED'
    AND created_at >= '2026-01-01'
    AND created_at <  '2026-07-01';
```

**Fields included:**
| Field | Description |
|-------|-------------|
| `conversion_id` | Unique order identifier |
| `user_id` | Buyer identifier — used to JOIN with touchpoints |
| `converted_at` | Timestamp of purchase completion |
| `order_value_usd` | Purchase value in USD — the numerator in ROAS calculations |
| `dma_code` | Buyer's geographic region — used in the Geo-Holdout experiment |

---

## How the Three Sources Connect

```
raw_user_touchpoints  ──┐
  (JOIN on user_id)     ├──→ Attribution Analysis
raw_conversions       ──┘

raw_ad_spend          ──→ Channel-level spend rollup ──→ ROAS Calculation
  (JOIN on channel)
```

**The fundamental join logic:**

1. Link `raw_user_touchpoints` and `raw_conversions` using `user_id`
2. Include only touchpoints that occurred **before** the conversion timestamp — this ensures causal direction (ad exposure must precede purchase)
3. Roll up `raw_ad_spend` by channel and date to compute spend denominators for ROAS

---

## Synthetic Data vs. Real-World Data

The analytical methods in this project are grounded in real professional experience working on cross-channel attribution and incrementality measurement. However, the actual company data from those engagements is strictly confidential — it cannot be shared or reproduced outside of the organization's internal data infrastructure.

The datasets in `data/raw/` are therefore synthetically generated using a Python script (`generate_synthetic_data.py`) to mirror the same schema, statistical distributions, and real-world noise patterns encountered in production. This allows the full methodology to be demonstrated and reproduced publicly. Here is how the synthetic dataset compares to real data:

| Characteristic          | Real Enterprise Data                                        | This Project's Synthetic Data           |
| ----------------------- | ----------------------------------------------------------- | --------------------------------------- |
| Volume                  | Millions to billions of rows                                | ~100,000 rows (6 months)                |
| UTM noise               | Present — due to human error in campaign setup              | Reflected — requires `LOWER()` cleaning |
| Duplicate events        | 3–5% of rows                                                | Reflected — 3% duplicate rate           |
| Platform over-reporting | Platform-reported conversions often exceed actual by 30–50% | Reflected — 34% over-reporting baked in |
| Geographic data         | Hundreds of U.S. DMAs                                       | 50 structured DMAs                      |
| Cookie signal loss      | Significant since iOS 14                                    | Partially reflected                     |

---

## Loading Data into the Pipeline

In this project, the three CSV files in `data/raw/` are loaded into PostgreSQL using **dbt seeds** — a dbt command that ingests local CSV files directly into the database as tables. This replaces the manual "import CSV" step you would do in a database GUI.

```bash
dbt seed
# Creates: raw.raw_ad_spend, raw.raw_user_touchpoints, raw.raw_conversions
```

From there, dbt models handle all cleaning and transformation automatically. See [`../dbt/README.md`](../dbt/README.md) for setup and execution instructions.

---

## Next Step

With raw data in hand, it must be cleaned before any analysis can begin.
Inconsistent formats, duplicate records, and tracking noise will distort every downstream calculation.

→ [Phase 2: Data Cleaning with SQL](./02_data_cleaning_sql.md)
