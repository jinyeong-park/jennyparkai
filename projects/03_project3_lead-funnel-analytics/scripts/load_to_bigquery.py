"""
Insurance Lead Intelligence — BigQuery Loader
Uploads all raw CSVs from data/raw/ to BigQuery raw dataset.

Run: python scripts/load_to_bigquery.py
Requires: pip install google-cloud-bigquery
Auth: gcloud auth application-default login
"""

from google.cloud import bigquery
from google.cloud.bigquery import SchemaField as F
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

PROJECT_ID = "insurance-lead-intelligence"
DATASET    = "insurance_analytics_raw"
DATA_DIR   = Path(__file__).parent.parent / "data" / "raw"

# ─── Schemas ──────────────────────────────────────────────────────────────────

SCHEMAS = {
    "raw_partners": [
        F("partner_id",             "STRING",    "REQUIRED"),
        F("partner_name",           "STRING",    "NULLABLE"),
        F("insurance_verticals",    "STRING",    "NULLABLE"),  # pipe-delimited
        F("accepted_states",        "STRING",    "NULLABLE"),  # pipe-delimited
        F("active_status",          "STRING",    "NULLABLE"),
        F("minimum_quality_score",  "INT64",     "NULLABLE"),
        F("daily_lead_capacity",    "INT64",     "NULLABLE"),
        F("pricing_model",          "STRING",    "NULLABLE"),
        F("base_payout",            "FLOAT64",   "NULLABLE"),
        F("created_at",             "DATE",      "NULLABLE"),
    ],

    "raw_ad_performance": [
        F("performance_date",               "DATE",    "REQUIRED"),
        F("channel",                        "STRING",  "NULLABLE"),
        F("campaign_id",                    "STRING",  "NULLABLE"),
        F("insurance_vertical",             "STRING",  "NULLABLE"),
        F("state",                          "STRING",  "NULLABLE"),
        F("spend",                          "FLOAT64", "NULLABLE"),
        F("impressions",                    "INT64",   "NULLABLE"),
        F("clicks",                         "INT64",   "NULLABLE"),
        F("platform_reported_leads",        "INT64",   "NULLABLE"),
        F("platform_reported_conversions",  "INT64",   "NULLABLE"),
        F("platform_reported_revenue",      "FLOAT64", "NULLABLE"),
    ],

    "raw_quote_events": [
        F("event_id",           "STRING",    "REQUIRED"),
        F("customer_id",        "STRING",    "NULLABLE"),
        F("session_id",         "STRING",    "NULLABLE"),
        F("quote_id",           "STRING",    "NULLABLE"),
        F("event_timestamp",    "TIMESTAMP", "NULLABLE"),
        F("event_name",         "STRING",    "NULLABLE"),
        F("channel",            "STRING",    "NULLABLE"),
        F("campaign_id",        "STRING",    "NULLABLE"),
        F("utm_source",         "STRING",    "NULLABLE"),
        F("utm_medium",         "STRING",    "NULLABLE"),
        F("utm_campaign",       "STRING",    "NULLABLE"),
        F("device_type",        "STRING",    "NULLABLE"),
        F("insurance_vertical", "STRING",    "NULLABLE"),
        F("state",              "STRING",    "NULLABLE"),
    ],

    "raw_leads": [
        F("lead_id",            "STRING",    "REQUIRED"),
        F("quote_id",           "STRING",    "NULLABLE"),
        F("customer_id",        "STRING",    "NULLABLE"),
        F("campaign_id",        "STRING",    "NULLABLE"),
        F("channel",            "STRING",    "NULLABLE"),
        F("submitted_at",       "TIMESTAMP", "NULLABLE"),
        F("insurance_vertical", "STRING",    "NULLABLE"),
        F("state",              "STRING",    "NULLABLE"),
        F("device_type",        "STRING",    "NULLABLE"),
        F("lead_quality_score", "INT64",     "NULLABLE"),
        F("is_valid",           "BOOLEAN",   "NULLABLE"),
        F("is_duplicate",       "BOOLEAN",   "NULLABLE"),
        F("is_test_lead",       "BOOLEAN",   "NULLABLE"),
        F("is_suspected_fraud", "BOOLEAN",   "NULLABLE"),
        F("rejection_reason",   "STRING",    "NULLABLE"),
        F("lead_status",        "STRING",    "NULLABLE"),
    ],

    "raw_routing_attempts": [
        F("routing_attempt_id", "STRING",    "REQUIRED"),
        F("lead_id",            "STRING",    "NULLABLE"),
        F("partner_id",         "STRING",    "NULLABLE"),
        F("routed_at",          "TIMESTAMP", "NULLABLE"),
        F("routing_priority",   "INT64",     "NULLABLE"),
        F("bid_amount",         "FLOAT64",   "NULLABLE"),
        F("delivery_status",    "STRING",    "NULLABLE"),
        F("response_status",    "STRING",    "NULLABLE"),
        F("response_timestamp", "TIMESTAMP", "NULLABLE"),
        F("rejection_reason",   "STRING",    "NULLABLE"),
    ],

    "raw_revenue_events": [
        F("revenue_event_id",   "STRING",    "REQUIRED"),
        F("lead_id",            "STRING",    "NULLABLE"),
        F("partner_id",         "STRING",    "NULLABLE"),
        F("revenue_timestamp",  "TIMESTAMP", "NULLABLE"),
        F("revenue_type",       "STRING",    "NULLABLE"),
        F("revenue_amount",     "FLOAT64",   "NULLABLE"),
        F("transaction_status", "STRING",    "NULLABLE"),
    ],
}

# Partition config: which field to partition by
PARTITION_FIELDS = {
    "raw_ad_performance":   "performance_date",
    "raw_quote_events":     "event_timestamp",
    "raw_leads":            "submitted_at",
    "raw_routing_attempts": "routed_at",
    "raw_revenue_events":   "revenue_timestamp",
}

# ─── Loader ───────────────────────────────────────────────────────────────────

def load_table(client, table_name):
    csv_path = DATA_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        print(f"  ⚠️  {csv_path} not found — skipping")
        return

    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMAS[table_name],
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        null_marker="",
    )

    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_ref, job_config=job_config)

    job.result()  # Wait for completion

    table = client.get_table(table_ref)
    print(f"  ✅  {table_name:30s}  {table.num_rows:>6,} rows loaded")


def main():
    print(f"\n🔧  Loading to BigQuery")
    print(f"    Project : {PROJECT_ID}")
    print(f"    Dataset : {DATASET}\n")

    client = bigquery.Client(project=PROJECT_ID)

    # Create dataset if it doesn't exist
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)
    print(f"  📦  Dataset '{DATASET}' ready\n")

    for table_name in SCHEMAS:
        load_table(client, table_name)

    print("\n✅  All tables loaded.\n")
    print("Next step:")
    print(f"  BigQuery console → {PROJECT_ID} → {DATASET}")
    print("  Run sql/staging/*.sql to build staging layer\n")


if __name__ == "__main__":
    main()
