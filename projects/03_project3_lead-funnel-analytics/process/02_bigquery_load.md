# Phase 2: BigQuery Load

> **Core Question:** How do raw CSV files get into BigQuery, and what schema decisions matter?

---

## Architecture

```
data/raw/*.csv
      ↓
scripts/load_to_bigquery.py
      ↓
BigQuery: insurance-lead-intelligence.insurance_analytics_raw
      ↓
6 raw tables, ready for SQL transformation
```

---

## Dataset Structure

```
insurance-lead-intelligence (GCP Project)
├── insurance_analytics_raw       ← raw ingestion layer (Phase 2)
│   ├── raw_partners
│   ├── raw_ad_performance
│   ├── raw_quote_events
│   ├── raw_leads
│   ├── raw_routing_attempts
│   └── raw_revenue_events
│
└── insurance_analytics_marts     ← analytics mart layer (Phase 4)
    ├── mart_lead_funnel
    ├── mart_campaign_performance
    ├── mart_partner_performance
    ├── mart_attribution
    └── mart_reconciliation
```

---

## Schema Decisions

### Why explicit schema (not autodetect)?

BigQuery's `autodetect=True` is convenient but risky in production:

| Problem                  | Example                                           |
| ------------------------ | ------------------------------------------------- |
| Strings read as integers | `lead_id = "001"` → autodetect reads as `1`       |
| Booleans read as strings | `"TRUE"` → stays as string, not BOOLEAN           |
| Timestamps misread       | `"2025-01-15 09:30:00 UTC"` → might become STRING |

For this project, `raw_leads` was loaded with autodetect after confirming the schema was clean.

### Key Type Decisions

| Column                                         | Type      | Reason                                   |
| ---------------------------------------------- | --------- | ---------------------------------------- |
| `submitted_at`, `routed_at`, `event_timestamp` | TIMESTAMP | Enables `DATE_TRUNC`, `TIMESTAMP_DIFF`   |
| `is_valid`, `is_duplicate`                     | BOOLEAN   | Enables `WHERE is_valid = TRUE` directly |
| `spend`, `revenue_amount`                      | FLOAT64   | Decimal precision for dollar amounts     |
| `lead_quality_score`                           | INT64     | Scores are whole numbers                 |
| `campaign_id`, `partner_id`                    | STRING    | IDs should always be STRING (never INT)  |

### Why campaign_id is STRING, not INT

```sql
-- ❌ If campaign_id is INT64:
WHERE campaign_id = '001'   -- fails (type mismatch)
WHERE campaign_id = 1       -- works, but loses leading zeros

-- ✅ If campaign_id is STRING:
WHERE campaign_id = 'C001'  -- always works
```

---

## Load Results

| Table                  | Rows   | Notes                          |
| ---------------------- | ------ | ------------------------------ |
| `raw_partners`         | 10     | Static dimension table         |
| `raw_ad_performance`   | 905    | 5 campaigns × ~181 days        |
| `raw_quote_events`     | 17,261 | All funnel events              |
| `raw_leads`            | 1,321  | Submitted leads                |
| `raw_routing_attempts` | 1,135  | Valid leads routed to partners |
| `raw_revenue_events`   | 731    | Accepted leads with payout     |

---

## What Was Tricky

### Partition + autodetect = 0 rows bug

When `time_partitioning` was set on the LoadJobConfig alongside `autodetect=True`, the job reported `output_rows: 905` but querying the table returned 0 rows.

**Root cause:** A partition definition applied during the load overrode the table metadata without properly committing the rows.

**Fix:** Load without time partitioning first. Partitioning can be added later via `ALTER TABLE` or by recreating the table with a `CREATE TABLE ... PARTITION BY` DDL statement.

```python
# What caused the bug
job_config.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="performance_date",
)

# Fix: remove time_partitioning from LoadJobConfig
```

---

## How to Re-run

```bash
python scripts/load_to_bigquery.py
```

Uses `WRITE_TRUNCATE` — safe to re-run, existing data is replaced.
