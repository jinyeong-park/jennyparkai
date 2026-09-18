# Insurance Lead Intelligence — End-to-End Process Guide

> **Purpose:** A step-by-step walkthrough of the complete analytics pipeline — from raw data generation to Looker dashboards.

---

## The Big Picture

```
[Raw Data] → [BigQuery Load] → [Exploration] → [SQL Marts] → [LookML] → [Looker Dashboard]
  PHASE 1       PHASE 2          PHASE 3          PHASE 4      PHASE 5        PHASE 6
```

```
Python script     load_to_bigquery.py    Explore raw       mart_*.sql       view.lkml       5 Dashboards
Generate 6 CSV →  Upload to BQ raw   →  tables in BQ   →  Transform    →   Semantic    →   Lead Funnel
(6 months data)   insurance_analytics_   NULL checks        to mart layer    layer           Campaign
                  raw dataset            grain/join         (aggregated)     model.lkml      Partner
                                         validation                          explore.lkml    Attribution
                                                                                             Reconciliation
```

---

## Phase Overview

| Phase | What Happens | Files | Deep-Dive |
| ----- | ------------ | ----- | --------- |
| 1 | Raw data generation — synthetic insurance lead data with realistic patterns | `scripts/generate_synthetic_data.py` | [01_raw_data_generation.md](./01_raw_data_generation.md) |
| 2 | BigQuery load — CSV → BQ raw tables with schema | `scripts/load_to_bigquery.py` | [02_bigquery_load.md](./02_bigquery_load.md) |
| 3 | Data exploration — NULL checks, grain/join validation, distribution checks before writing any SQL | BigQuery console | [03_data_exploration.md](./03_data_exploration.md) |
| 4 | SQL mart layer — aggregate raw tables into analytics marts | `sql/marts/*.sql` | [04_sql_marts.md](./04_sql_marts.md) |
| 5 | LookML semantic layer — define metrics, dimensions, joins | `looker/views/*.view.lkml` | [05_lookml.md](./05_lookml.md) |
| 6 | Looker dashboards — funnel, campaign, partner, attribution | Looker UI | [06_looker_dashboards.md](./06_looker_dashboards.md) |

---

## Recommended Reading Order

1. [01_raw_data_generation.md](./01_raw_data_generation.md) — What data was generated and why
2. [02_bigquery_load.md](./02_bigquery_load.md) — How raw CSVs land in BigQuery
3. [03_data_exploration.md](./03_data_exploration.md) — Exploring raw tables before writing any mart SQL
4. [04_sql_marts.md](./04_sql_marts.md) — SQL transformation logic (the core analytics work)
5. [05_lookml.md](./05_lookml.md) — LookML semantic layer design
6. [06_looker_dashboards.md](./06_looker_dashboards.md) — Dashboard design and business questions answered

---

## Business Model

This project models a **performance-based insurance lead generation company** — a middleman that sits between ad platforms and insurance carriers.

**How the money flows:**

```
Ad Platforms          Lead Gen Company          Insurance Partners
(Google, Meta)             (us)                 (Progressive, GEICO...)

Spend $50 CPL   →   Collect lead data   →   Sell lead for $80–120
                     Validate quality        Exclusive: one partner only
                     Route to partners       Partner pays on acceptance
```

**Revenue model:**
- Buy leads from paid channels at a certain CPL
- Sell each valid lead to an insurance partner at a fixed payout rate
- Profit = partner payout − acquisition cost
- Only accepted leads generate revenue — rejected, timed-out, or capacity-exceeded leads are pure cost

**Lead routing — how it works:**

A submitted lead is routed to insurance partners one at a time in priority order (payout, acceptance rate, capacity). Each attempt is recorded separately. The loop stops as soon as one partner accepts.

```
Lead submitted
    ↓
Partner 1 → rejected        ← attempt 1 recorded
    ↓
Partner 2 → no_response     ← attempt 2 recorded
    ↓
Partner 3 → accepted        ← attempt 3 recorded → revenue event created
```

This is an **exclusive lead** model — once accepted, the lead is not sent to any other partner. The partner gets no competition; in return, payout rates are higher than shared-lead marketplaces.

**Lead distribution models — how the industry works:**

| Model | How It Works | Payout | Consumer Experience |
| ----- | ------------ | ------ | ------------------- |
| **Exclusive** (this project) | One partner at a time, loop stops on acceptance | High ($80–120) | One company contacts them |
| **Shared** | Full lead sent to multiple partners simultaneously | Low ($10–30) | Multiple companies contact them |
| **Ping-Post** | Step 1 (Ping): partial lead sent to all partners for blind bidding. Step 2 (Post): full lead sold to top 1–3 bidders | Medium, auction-based | 1–3 companies contact them |

**Ping-Post in detail** — the most common model in the market today:

```
Step 1 — Ping (partial data only):
    Lead gen company → broadcasts {state, vertical, age_range} to all partners
    Partners respond with a bid price within ~1 second

Step 2 — Post (full data):
    Lead gen company sells full lead to highest bidder(s)
    Partners who didn't win get nothing
```

Ping-Post became dominant because it maximizes revenue per lead for the seller while giving partners price control. The tradeoff is consumer experience — shared/ping-post leads often result in 5–10 calls and texts to the consumer within minutes, which drove TCPA regulatory pressure in the US.

**Why acceptance rate is the core operational metric:**

If a partner's acceptance rate drops, leads keep getting routed to them, fail, and must be retried with other partners — increasing latency, burning capacity, and sometimes resulting in no acceptance at all (wasted acquisition cost). Monitoring acceptance rate by partner is how ops teams catch capacity issues, coverage changes, or quality mismatches before they damage revenue.

---

## The Business Problem This Project Solves

A performance marketing company buys insurance leads across Google, Meta, and affiliate channels.

The core problem:

```
Marketing Platform
Reports 144 conversions at $8,795 revenue
         ↓
Warehouse
Records 132 submitted leads
         ↓
Validation
Rejects 28 as duplicates or low quality
         ↓
Partner Routing
Only 64 leads get accepted
         ↓
Verified Revenue
= $3,200  (not $8,795)
```

**If you optimize toward platform-reported metrics, you waste budget.**

This project builds the analytics layer that connects acquisition → submission → validation → routing → acceptance → revenue.

---

## Data Model at a Glance

```
raw_ad_performance ──→ (campaign_id) ──┐
                                       ↓
raw_quote_events ──→ (quote_id) ──→ raw_leads ──→ (lead_id) ──→ raw_routing_attempts
                                                                        │
                                         raw_revenue_events ←── (lead_id)
                                                │
                                    raw_partners ──→ (partner_id) ────┘
```

| Table | Grain | Key Metric |
| ----- | ----- | ---------- |
| `raw_ad_performance` | 1 row per campaign × date | spend, platform leads |
| `raw_quote_events` | 1 row per event | funnel stage |
| `raw_leads` | 1 row per lead | valid, duplicate, quality score |
| `raw_routing_attempts` | 1 row per lead × partner attempt | acceptance rate |
| `raw_partners` | 1 row per partner | capacity, payout |
| `raw_revenue_events` | 1 row per revenue event | revenue amount |

---

## Key Terms

| Term | Definition |
| ---- | ---------- |
| **CPL** | Cost Per Lead = Spend ÷ Submitted Leads |
| **Valid Lead Rate** | Valid Leads ÷ Submitted Leads |
| **Acceptance Rate** | Accepted Leads ÷ Delivered Leads |
| **Revenue per Lead** | Total Revenue ÷ Submitted Leads |
| **ROAS** | Revenue ÷ Marketing Spend |
| **Platform Overclaim** | (Platform Leads − Warehouse Leads) ÷ Platform Leads |
| **First Touch** | The first marketing channel a user interacted with before submitting |
| **Fan-out** | When a join duplicates rows — e.g. one campaign joined to 3 leads inflates spend 3× |
| **Routing Attempt** | One try to deliver a lead to one partner |
| **Rolling 7d Rate** | Volume-weighted acceptance rate over the last 7 calendar days: SUM(accepted) ÷ SUM(delivered) in the window — not AVG of daily rates |
