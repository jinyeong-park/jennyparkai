# Python — Geo-Holdout Incrementality Analysis

This directory contains the Python scripts for Phase 4 of the Growth Attribution pipeline.

---

## Files

| File | Purpose |
|------|---------|
| `generate_synthetic_data.py` | Generates the three raw CSV datasets in `data/raw/` |
| `geo_holdout_experiment.py` | Runs the Geo-Holdout incrementality analysis and produces charts |

---

## Why Python Here, Not dbt?

dbt handles data cleaning and SQL-based attribution (Phases 2–3) inside the database.
Python takes over for Phase 4 because geo-holdout analysis requires:

- **Statistical testing** — two-proportion z-test (`scipy.stats`)
- **Array math** — population-weighted rate calculations (`numpy`)
- **Visualization** — charts that communicate results to stakeholders (`matplotlib`, `seaborn`)

These are not practical in SQL alone.

---

## Setup

```bash
pip install pandas numpy scipy matplotlib seaborn
```

---

## Step 1 — Generate Synthetic Data

Only needed once (or when you want to regenerate the raw CSVs).

```bash
cd python
python generate_synthetic_data.py
```

Creates in `data/raw/`:
- `raw_user_touchpoints.csv` — GA4-style clickstream events (~30,000+ rows)
- `raw_conversions.csv` — backend order records (~4,500 rows)
- `raw_ad_spend.csv` — daily ad spend by channel and DMA (~27,000 rows)

The script bakes the geo-holdout experiment directly into the data:
- Meta ads are set to $0 spend in the 10 control DMAs during June 2026
- Multi-channel users in control DMAs are never assigned a Meta touchpoint in June

---

## Step 2 — Run the Geo-Holdout Analysis

```bash
cd python
python geo_holdout_experiment.py
```

**What it does:**

1. Loads `raw_conversions.csv`, `raw_user_touchpoints.csv`, and `raw_ad_spend.csv`
2. Splits the 50 DMAs into Control (10 markets, Meta OFF) and Treatment (40 markets, Meta ON)
3. Filters to the experiment window: June 2026
4. Builds a DMA-level population proxy from unique user counts
5. Calculates incremental lift: actual conversions − expected organic baseline
6. Runs a two-proportion z-test for statistical significance
7. Computes true incremental ROAS and compares it to Meta's self-reported ROAS
8. Saves a four-panel chart to `geo_holdout_results.png`

**Expected output (printed to console):**

```
── Incrementality Results ──────────────────────────────
  Baseline conversion rate (control DMAs):  ~3.4%
  Incremental lift:                         ~5-6%
  Organic share:                            ~94%
  True Incremental ROAS:                    ~1.26x
  Platform-reported ROAS (Meta):            3.25x

── Statistical Significance Test ───────────────────────
  P-value:  < 0.05
  Significant at 95%: True
```

---

## Experiment Design

| Parameter | Value |
|-----------|-------|
| Total DMAs | 50 U.S. markets |
| Control DMAs | 10 (Meta ads paused for 30 days) |
| Treatment DMAs | 40 (Meta ads running as normal) |
| Test period | June 2026 |
| Channel tested | Meta Paid Social (retargeting) |
| Statistical test | Two-proportion z-test (α = 0.05) |

**Control DMAs (Meta ads OFF in June):**
SAN_FRANCISCO, NEW_YORK, CHICAGO, LOS_ANGELES, DALLAS,
SEATTLE, AUSTIN, ATLANTA, BOSTON, DENVER

---

## Key Finding

Meta's platform-reported ROAS was **3.25x**.
The geo-holdout reveals the true incremental ROAS was **~1.26x**.

Over 90% of Meta-attributed conversions happened organically — these users would have
converted through Organic Search or Direct navigation even without seeing a Meta ad.

→ See [process/05_marketing_insights.md](../process/05_marketing_insights.md) for the budget reallocation decision.
