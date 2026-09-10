# dbt — Growth Attribution Pipeline

This directory contains the dbt project that powers the Multi-Touch Attribution pipeline.
It transforms three raw CSV datasets into four attribution models and a final executive comparison table.

**Why dbt?**

> Modern data pipelines follow the **ELT** pattern — Extract, Load, Transform.
> Raw data is first extracted from source systems (ad platforms, GA4, backend databases) and loaded into
> a cloud data warehouse (BigQuery, Snowflake, Redshift) as-is. The transformation step — cleaning,
> joining, and aggregating that raw data into usable tables — happens inside the warehouse using SQL.
> **dbt owns this T.** It is the industry-standard tool for managing SQL transformations in production,
> adding dependency management (`ref()`), automated data quality tests, and self-generated documentation —
> the standard tooling for analytics engineering teams.

---

## What This Pipeline Does

```
Raw CSVs (seeds)
    │
    ├── raw_ad_spend.csv          (Meta / Google / TikTok daily spend)
    ├── raw_user_touchpoints.csv  (GA4 clickstream events)
    └── raw_conversions.csv       (PostgreSQL backend orders)
    │
    ▼
[Staging]  — type casting, UTM normalization, channel name standardization
    │
    ▼
[Intermediate]  — deduplication, attribution window JOIN
    │
    ▼
[Marts]  — 4 attribution models + executive comparison table
    │
    ▼
mrt_attribution_comparison  ←  final output for dashboards and budget decisions
```

---

## Prerequisites

| Tool         | Version | Install                                      |
| ------------ | ------- | -------------------------------------------- |
| Python       | 3.8+    | [python.org](https://python.org)             |
| dbt-postgres | 1.7+    | `pip install dbt-postgres`                   |
| PostgreSQL   | 14+     | [postgresql.org](https://www.postgresql.org) |

Install dbt:

```bash
pip install dbt-postgres
```

Verify installation:

```bash
dbt --version
```

---

## Step-by-Step Setup

### Step 1 — Configure Database Connection

dbt connects to PostgreSQL through a `profiles.yml` file stored in your home directory.

```bash
# Copy the template
cp profiles.yml.example ~/.dbt/profiles.yml
```

Open `~/.dbt/profiles.yml` and fill in your PostgreSQL credentials:

```yaml
growth_attribution:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: your_postgres_username # ← change this
      password: your_postgres_password # ← change this
      port: 5432
      dbname: growth_attribution_db # ← must exist in PostgreSQL
      schema: public
      threads: 4
```

Create the database if it does not exist yet:

```bash
psql -U postgres -c "CREATE DATABASE growth_attribution_db;"
```

---

### Step 2 — Navigate to the dbt Directory

All dbt commands must be run from inside this `dbt/` folder.

```bash
cd dbt
```

---

### Step 3 — Validate the Connection

```bash
dbt debug
```

This checks that dbt can reach your PostgreSQL database.
You should see `All checks passed!` at the bottom of the output.

---

### Step 4 — Load Raw Data (Seeds)

dbt seeds load the CSV files from `../data/raw/` directly into PostgreSQL as tables.
This replaces the manual "import CSV" step you would do in a database GUI.

```bash
dbt seed
```

**What gets created in PostgreSQL:**

```
raw.raw_ad_spend
raw.raw_user_touchpoints
raw.raw_conversions
```

---

### Step 5 — Run the Models

This executes every model in the correct dependency order — dbt figures out the order automatically using the `ref()` relationships between models.

```bash
dbt run
```

**What gets created in PostgreSQL, in order:**

| Order | Schema       | Model                            | Materialization | What It Does                              |
| ----- | ------------ | -------------------------------- | --------------- | ----------------------------------------- |
| 1     | staging      | `stg_ad_spend`                   | view            | Type casts + channel name standardization |
| 2     | staging      | `stg_user_touchpoints`           | view            | UTM normalization + channel mapping       |
| 3     | staging      | `stg_conversions`                | view            | Ground-truth order data                   |
| 4     | intermediate | `int_deduped_touchpoints`        | view            | ROW_NUMBER() removes ~3% duplicate events |
| 5     | intermediate | `int_pre_conversion_touchpoints` | view            | Attribution window JOIN (90-day lookback) |
| 6     | marts        | `mrt_first_touch_attribution`    | table           | 100% credit → first touchpoint            |
| 7     | marts        | `mrt_last_touch_attribution`     | table           | 100% credit → last touchpoint             |
| 8     | marts        | `mrt_linear_attribution`         | table           | Equal credit split across all touchpoints |
| 9     | marts        | `mrt_time_decay_attribution`     | table           | Exponential decay, 7-day half-life        |
| 10    | marts        | `mrt_attribution_comparison`     | table           | All 4 models + ROAS side by side          |

To run only a specific model and everything it depends on:

```bash
dbt run --select +mrt_attribution_comparison   # the + means "and all upstream models"
```

To run only one layer at a time:

```bash
dbt run --select staging
dbt run --select intermediate
dbt run --select marts
```

---

### Step 6 — Run Data Quality Tests

dbt tests verify that the pipeline output is correct before anyone uses it.

```bash
dbt test
```

**Tests that run:**

| Test                                             | What It Checks                                           |
| ------------------------------------------------ | -------------------------------------------------------- |
| `stg_conversions.conversion_id` — unique         | No duplicate orders in the ground-truth data             |
| `int_deduped_touchpoints.event_id` — unique      | Deduplication actually worked                            |
| `stg_ad_spend.channel` — accepted_values         | Only the 3 expected paid channels exist                  |
| `stg_user_touchpoints.channel` — accepted_values | Only the 5 expected channels exist                       |
| `assert_no_post_conversion_touchpoints`          | Zero touchpoints exist after their conversion timestamp  |
| `assert_no_duplicate_event_ids`                  | Zero event_ids appear more than once after deduplication |

If any test fails, dbt prints exactly which rows violated the expectation — making the data quality issue immediately visible and debuggable.

To test only one model:

```bash
dbt test --select int_pre_conversion_touchpoints
```

---

### Step 7 — View the Final Output

Query the comparison table directly in PostgreSQL:

```sql
SELECT
    channel,
    total_spend_usd,
    first_touch_roas,
    last_touch_roas,
    linear_roas,
    time_decay_roas,
    platform_reported_roas
FROM marts.mrt_attribution_comparison
ORDER BY time_decay_roas DESC;
```

---

### Step 8 — Generate Documentation (Optional but Recommended)

dbt auto-generates an interactive documentation site from the schema YAML files and model descriptions.

```bash
dbt docs generate
dbt docs serve
```

This opens a browser at `http://localhost:8080` showing:

- Every model with its description and column definitions
- A **lineage graph** — a visual diagram of how every model connects to every other
- All test results

---

## Running Everything at Once

After the first-time setup (Steps 1–3), you can run the full pipeline in one command:

```bash
dbt seed && dbt run && dbt test
```

---

## Model Dependency Graph

```
raw_ad_spend ──────────────────────────────────────────► stg_ad_spend ──────────────────────────────────────────────────────────────────────────┐
                                                                                                                                                   │
raw_user_touchpoints ──► stg_user_touchpoints ──► int_deduped_touchpoints ──► int_pre_conversion_touchpoints ──► mrt_first_touch_attribution ──►   │
                                                                                          │                   ──► mrt_last_touch_attribution ──►   mrt_attribution_comparison
                                                                                          │                   ──► mrt_linear_attribution ──────►   │
                                                                                          │                   ──► mrt_time_decay_attribution ──►   │
                                                                                                                                                   │
raw_conversions ──────────► stg_conversions ─────────────────────────────────────────────┘                                                        │
                                                                                                                                                   │
                            stg_ad_spend ──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Simplified:

```
seeds → staging → intermediate → marts (attribution models) → mrt_attribution_comparison
```

---

## File Structure

```
dbt/
├── dbt_project.yml                               ← project config: layer materializations, schema names
├── profiles.yml.example                          ← DB connection template (copy to ~/.dbt/profiles.yml)
├── models/
│   ├── staging/
│   │   ├── stg_ad_spend.sql                      ← raw_ad_spend → typed + channel-standardized
│   │   ├── stg_user_touchpoints.sql              ← raw touchpoints → UTM normalized + channel mapped
│   │   ├── stg_conversions.sql                   ← raw orders → ground-truth revenue
│   │   └── _staging__schema.yml                  ← column tests for all staging models
│   ├── intermediate/
│   │   ├── int_deduped_touchpoints.sql            ← ROW_NUMBER() deduplication (~3% removed)
│   │   ├── int_pre_conversion_touchpoints.sql     ← JOIN + 90-day attribution window filter
│   │   └── _intermediate__schema.yml
│   └── marts/
│       ├── mrt_first_touch_attribution.sql        ← 100% credit to first touchpoint
│       ├── mrt_last_touch_attribution.sql         ← 100% credit to last touchpoint
│       ├── mrt_linear_attribution.sql             ← equal credit split
│       ├── mrt_time_decay_attribution.sql         ← exponential decay, 7-day half-life
│       ├── mrt_attribution_comparison.sql         ← all 4 models + ROAS (executive output)
│       └── _marts__schema.yml
└── tests/
    ├── assert_no_post_conversion_touchpoints.sql  ← QA: causal direction check
    └── assert_no_duplicate_event_ids.sql          ← QA: deduplication completeness check
```

---

## Common Issues

**`dbt debug` fails with connection error**
→ Make sure PostgreSQL is running: `brew services start postgresql` (macOS)
→ Confirm the database exists: `psql -U postgres -l`

**`dbt seed` fails with permission error**
→ Grant your user access: `psql -U postgres -c "GRANT ALL ON DATABASE growth_attribution_db TO your_user;"`

**`dbt run` fails on a specific model**
→ Run `dbt run --select model_name` to isolate it
→ Check `target/compiled/` for the compiled SQL dbt actually executed — useful for debugging

**Schema `raw`, `staging`, `intermediate`, or `marts` does not exist**
→ dbt creates schemas automatically on first run. If not, run:
`psql -U postgres -d growth_attribution_db -c "CREATE SCHEMA IF NOT EXISTS staging;"`
