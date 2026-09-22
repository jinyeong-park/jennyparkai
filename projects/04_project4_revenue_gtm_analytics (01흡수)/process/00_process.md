# Revenue Intelligence — End-to-End Process Guide

> **Purpose:** A step-by-step walkthrough of the full B2B revenue analytics pipeline,
> from raw CRM and billing data through GTM funnel analysis, revenue reconciliation,
> pipeline risk monitoring, and customer health reporting.

---

## The Big Picture

```
[Data Acquisition] → [Data Cleaning] → [Intermediate Joins] → [Mart Models] → [Analysis]
      PHASE 1             PHASE 2            PHASE 3              PHASE 4        PHASE 5
```

```
Salesforce CRM        dbt staging         int_customer_        dim_account      GTM Funnel
Marketing Leads   →   FX normalization →  identity_map     →   fct_pipeline  →  Revenue
Contracts             Deduplication       int_gtm_funnel       fct_bookings     Reconciliation
Billing invoices      DQ flagging         int_revenue_         fct_revenue      Pipeline Risk
Customer Success                          lifecycle            fct_customer_    Customer Health
Product Events                                                 lifecycle
```

> **Production Implementation:** All SQL in Phases 2–4 is implemented as a runnable
> **dbt project** in [`../dbt/`](../dbt/README.md). Staging models clean the data,
> intermediate models resolve identity and build the lifecycle chain, and mart models
> produce the final analytical outputs.

---

## Phase Overview

| Phase | What Happens                                                              | dbt Models / Tools               | Deep-Dive File                                                           |
| ----- | ------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------ |
| 1     | Data Acquisition — 7 source systems, how they connect in B2B              | Seeds (`raw_*`)                  | [01_data_acquisition.md](./01_data_acquisition.md)                       |
| 2     | Data Cleaning — Dedup, FX normalization, DQ flagging in staging           | `stg_*` models                   | [02_data_cleaning_staging.md](./02_data_cleaning_staging.md)             |
| 3     | Intermediate Joins — Identity map and lifecycle chain                     | `int_*` models                   | [03_intermediate_models.md](./03_intermediate_models.md)                 |
| 4     | Mart Models — Analytical facts and dimensions                             | `dim_*`, `fct_*` models          | [04_mart_models.md](./04_mart_models.md)                                 |
| 5     | Analysis — GTM funnel, revenue reconciliation, pipeline, customer health  | Python notebooks                 | [05_analysis_findings.md](./05_analysis_findings.md)                     |

---

## Recommended Reading Order

Follow the phases in order — each phase builds on the previous one.

1. [01_data_acquisition.md](./01_data_acquisition.md) — The 7 source systems and how a real B2B data stack is structured
2. [02_data_cleaning_staging.md](./02_data_cleaning_staging.md) — What data quality issues we found and how staging models fix them
3. [03_intermediate_models.md](./03_intermediate_models.md) — How we join CRM → Marketing → Billing → CS into a unified lifecycle
4. [`../dbt/README.md`](../dbt/README.md) — Run the full dbt pipeline end-to-end
5. [04_mart_models.md](./04_mart_models.md) — The five analytical fact and dimension models
6. [05_analysis_findings.md](./05_analysis_findings.md) — Key findings across GTM, revenue, pipeline, and retention

---

## Key Terms Glossary

| Term                          | Definition                                                                                                                                                 |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GTM (Go-To-Market)**        | The strategy and systems a company uses to bring a product to customers — includes marketing, sales, and customer success                                   |
| **ARR / MRR**                 | Annual / Monthly Recurring Revenue — the predictable subscription revenue a company expects to collect each period                                          |
| **Bookings**                  | The total contract value signed in a period — a sales metric, not a revenue metric                                                                         |
| **Billings**                  | The amount invoiced to customers — may differ from bookings due to timing or billing schedules                                                              |
| **Revenue (Collected)**       | Cash actually received — the only number that appears on a cash-flow statement                                                                              |
| **Revenue Chain**             | The four-step sequence: CRM Booking → Contract Value → Billed → Collected Cash. Each step can be less than the previous one                                |
| **Revenue Reconciliation**    | The process of explaining why Bookings ≠ Contract Value ≠ Billed ≠ Collected — each gap has a business reason                                              |
| **NRR (Net Revenue Retention)** | (Starting Revenue + Expansion − Churn) / Starting Revenue. >100% means customers are growing faster than they churn                                      |
| **Pipeline**                  | All open sales opportunities with an expected close date in the future — a forward-looking revenue estimate                                                 |
| **Weighted Pipeline**         | Pipeline amount × win rate probability by stage (e.g., Negotiation × 65%) — a more realistic revenue forecast                                             |
| **Health Score**              | A composite metric (0–100) measuring customer engagement and likelihood to renew or churn                                                                   |
| **Account Identity Map**      | A model that shows, for every account, which systems (CRM, Marketing, Billing, CS) have a matching record                                                  |
| **Canonical Record**          | When duplicate records exist (e.g., two rows for the same contract_id), the canonical record is the one selected for calculations                           |
| **Orphan Opportunity**        | An opportunity in the CRM with an account_id that has no matching account record — usually a data entry error                                               |
| **is_orphan flag**            | A boolean column added in staging to mark records that cannot be joined to their parent record                                                              |
| **dbt**                       | Data Build Tool — the industry-standard framework for managing SQL transformations. Adds dependency management, tests, and documentation                    |
| **dbt seed**                  | Loads local CSV files directly into the data warehouse as tables                                                                                            |
| **FX normalization**          | Converting multi-currency billing amounts to a single reporting currency (USD) using exchange rates                                                          |
| **ELT**                       | Extract-Load-Transform — raw data is loaded first, then transformed inside the warehouse using dbt                                                          |

---

## The Core Problem This Project Solves

```
The Problem:
  The sales team reports $8.2M in closed-won bookings.
  Finance reports $6.9M in collected revenue.
  Where did $1.3M go?

  In B2B SaaS, four different numbers all get called "revenue":
    CRM Bookings      → what sales claims to have closed
    Contract Value    → what legal actually signed
    Billed Amount     → what the billing system invoiced
    Collected Cash    → what hit the bank account

  Each gap has a legitimate business reason — but if no one explains the gaps,
  different teams operate on different numbers and reach conflicting conclusions.

  On top of that:
    - 4 duplicate contract_ids with conflicting values exist in billing
    - 9 "orphan" opportunities in the CRM have no matching account
    - 12 marketing leads cannot be attributed to any account
    - Invoices arrive in USD, EUR, and GBP — all need FX normalization
```

```
The Solution:
  Step 1 — dbt staging models: flag and preserve every data quality issue
            without silently dropping records.
  Step 2 — int_customer_identity_map: show exactly which systems have data
            for each account and where the gaps are.
  Step 3 — int_revenue_lifecycle: connect CRM → Contract → Billing →
            Collected Cash into one row per opportunity with three gap columns.
  Step 4 — Analysis notebooks: quantify each gap and explain it in business terms.
```

---

## Final Results Summary

| Analysis Area       | Key Finding                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| GTM Funnel          | Lead → Closed-Won conversion rate identified by segment and lead source        |
| Revenue Chain       | ~15% gap between CRM bookings and collected cash; largest gap is at billing    |
| Pipeline Risk       | ~30% of open pipeline flagged as past-due or stale; weighted forecast built    |
| Customer Health     | NRR calculated by segment; at-risk account priority list for CS outreach       |
| Data Quality        | 4 duplicate contracts, 9 orphan opps, 12 unmatched leads — all surfaced        |

> The key insight: every gap in the revenue chain is explainable. Bookings overstate
> revenue due to discounts at signing. Contracts understate billings due to currency
> timing. Billings overstate collections due to payment failures. Building the full
> chain makes these gaps visible and manageable instead of hidden.

---

_Follow the links in the Phase Overview table to read each section in detail._
