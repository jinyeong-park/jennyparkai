# Growth Attribution System — End-to-End Process Guide

> **Purpose:** A step-by-step walkthrough of the entire pipeline from data acquisition to marketing decisions.

---

## The Big Picture

```
[Data Acquisition] → [Data Cleaning] → [Attribution Modeling] → [Geo Experiment] → [Decision]
     PHASE 1              PHASE 2             PHASE 3               PHASE 4          PHASE 5
```

```
Ad Platform APIs      dbt staging         dbt marts             Python             Budget
(Meta / Google /  →   UTM normalization → First-Touch       →   Geo-Holdout    →   Reallocation
 TikTok)              Deduplication       Last-Touch             Experiment         ROI Reporting
GA4 / Segment         Attribution Window  Linear                 iCAC Calculation
Backend DB            (int_ models)       Time-Decay
```

> **Production Implementation:** The SQL concepts in Phases 2 and 3 are implemented as a
> runnable **dbt project** in [`../dbt/`](../dbt/README.md).
> Staging models handle cleaning, intermediate models handle joins, and mart models produce
> the four attribution outputs. See the dbt README for setup and execution instructions.

---

## Phase Overview

| Phase | What Happens                                                                | dbt Models                   | Deep-Dive File                                                 |
| ----- | --------------------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------- |
| 1     | Data Acquisition — How real companies collect ad and conversion data        | Seeds (`raw_*`)              | [01_data_acquisition.md](./01_data_acquisition.md)             |
| 2     | Data Cleaning — UTM normalization, deduplication, attribution window        | `stg_*` → `int_*`            | [02_data_cleaning_sql.md](./02_data_cleaning_sql.md)           |
| 3     | Attribution Modeling — Calculating channel-level conversion credit          | `mrt_*_attribution`          | [03_attribution_models_sql.md](./03_attribution_models_sql.md) |
| 4     | Geo-Holdout Experiment — Measuring true incremental lift with Python        | _(Python only)_              | [04_geo_holdout_python.md](./04_geo_holdout_python.md)         |
| 5     | Marketing Insights & Decisions — Interpreting results and adjusting budgets | `mrt_attribution_comparison` | [05_marketing_insights.md](./05_marketing_insights.md)         |

---

## Recommended Reading Order

Follow the phases in order — each phase builds on the previous one.

1. [01_data_acquisition.md](./01_data_acquisition.md) — Where the data comes from and how it lands in the warehouse
2. [02_data_cleaning_sql.md](./02_data_cleaning_sql.md) — UTM normalization, deduplication, attribution window filter
3. [03_attribution_models_sql.md](./03_attribution_models_sql.md) — First-Touch, Last-Touch, Linear, and Time-Decay models in SQL
4. [`../dbt/README.md`](../dbt/README.md) — Run the full pipeline end-to-end with `dbt seed && dbt run && dbt test`
5. [04_geo_holdout_python.md](./04_geo_holdout_python.md) — Geo-holdout experiment design and Python incrementality analysis
6. [05_marketing_insights.md](./05_marketing_insights.md) — Interpreting results and reallocating budget

---

## Key Terms Glossary

| Term                              | Definition                                                                                                                                                                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Attribution**                   | The process of assigning credit to marketing channels for driving a conversion                                                                                                                                                                   |
| **Multi-Touch Attribution (MTA)** | A class of models that distribute conversion credit across all touchpoints in the user journey, not just the first or last click                                                                                                                 |
| **Self-Attribution Bias**         | Each ad platform (Meta, Google) independently claims credit for the same conversion, leading to double-counting                                                                                                                                  |
| **ROAS**                          | Return on Ad Spend — revenue generated per dollar of ad spend                                                                                                                                                                                    |
| **iCAC**                          | Incremental Cost per Acquisition — cost to acquire one additional customer that would not have converted organically                                                                                                                             |
| **Geo-Holdout**                   | An experiment where ads are paused in a subset of geographic markets (control) to measure the baseline conversion rate vs. markets where ads remain active (treatment)                                                                           |
| **DMA**                           | Designated Market Area — a U.S. regional advertising market unit (e.g., NYC, LA, Chicago)                                                                                                                                                        |
| **UTM Parameters**                | Tracking tags appended to URLs that identify how users arrived at a site (utm_source, utm_medium, utm_campaign)                                                                                                                                  |
| **ETL / ELT**                     | Extract-Transform-Load — the pipeline that moves data from source systems into a data warehouse                                                                                                                                                  |
| **CDC**                           | Change Data Capture — technology that detects and replicates database changes in real time                                                                                                                                                       |
| **Attribution Window**            | The lookback period used to determine which touchpoints are eligible for attribution credit (e.g., 7-day, 30-day)                                                                                                                                |
| **dbt**                           | Data Build Tool — the industry-standard framework for managing SQL transformations in a data warehouse. Adds `ref()` dependency management, automated tests, and self-generated documentation. Used in this project to implement Phases 2 and 3. |
| **dbt seed**                      | A dbt command that loads local CSV files directly into the database as tables — replacing manual CSV imports                                                                                                                                     |
| **dbt model**                     | A single SQL file in a dbt project that defines one table or view. Models reference each other with `ref('model_name')` instead of hardcoded table names                                                                                         |

---

## The Core Problem This Project Solves

```
The Problem:
  Meta Ads Manager  reports → "We drove 350 conversions"
  Google Ads        reports → "We drove 280 conversions"
  Actual total conversions → 420

  Each platform independently claims credit for the same conversion events.
  Combined platform-reported conversions exceed real conversions by 34%.
  This inflated view leads to misallocating budget toward low-performing channels.

The Solution:
  Step 1 — SQL Multi-Touch Attribution: deduplicate touchpoints and distribute
            conversion credit across channels using verifiable clickstream data.
  Step 2 — Geo-Holdout Experiment: pause Meta ads in 10 control DMAs to measure
            how many conversions happen organically (without any Meta ad).
  Step 3 — Reallocate $100K from low-incrementality Meta retargeting
            toward high-incrementality Google Search and TikTok prospecting.
```

---

## Final Results Summary

| Channel            | Platform-Reported ROAS | True Incremental ROAS | Action Taken                                   |
| ------------------ | ---------------------- | --------------------- | ---------------------------------------------- |
| Meta Paid Social   | 3.25x                  | **1.26x**             | Budget cut — high organic cannibalization      |
| Google Paid Search | 2.80x                  | **2.65x**             | Budget increased — high incremental lift       |
| TikTok Ads         | 1.60x                  | **2.10x**             | Budget increased — strong new-user acquisition |
| Blended Total      | 2.80x                  | **1.91x**             | $100K reallocated; Blended CAC fell 14.2%      |

> Meta appeared to be the top performer based on platform reporting.
> In reality, it was the lowest-incrementality channel — over 60% of its attributed
> conversions would have happened anyway through Organic Search or Direct.

---

_Follow the links in the Phase Overview table to read each section in detail._
