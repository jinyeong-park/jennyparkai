# Phase 1: Data Acquisition

> **Core Question:** In a real B2B SaaS company, where does the data come from — and why does it live in 7 separate systems?

---

## Why B2B Revenue Data Is Inherently Fragmented

In a B2C e-commerce company, a single purchase event ties together the customer, the transaction, and the marketing touchpoint in one place. In B2B SaaS, the journey from "prospect" to "paying customer" spans months and involves multiple teams, each using different tools:

```
Marketing Team    →  Salesforce / HubSpot (CRM)
                  →  Marketo / HubSpot (Marketing Automation)
Sales Team        →  Salesforce Opportunities
Finance / Legal   →  DocuSign / PandaDoc (Contracts)
Billing           →  Stripe / Zuora / Chargebee (Invoicing)
Customer Success  →  Gainsight / ChurnZero (Health Scores)
Product           →  Amplitude / Mixpanel (Usage Events)
```

Each system knows one part of the story. No single system sees the full picture from lead to renewal.

**This is the problem that a Revenue Intelligence pipeline solves.**

---

## The 7 Data Sources in This Project

### Source 1: `raw_salesforce_accounts` — Company Records

**Real-world origin:** Salesforce CRM (Account object)

**Real-world pipeline:**
```
[Salesforce Account object]
        ↓
[Fivetran Salesforce connector — syncs every 6 hours]
        ↓
[Lands in warehouse as salesforce.account table]
        ↓
[dbt staging model deduplicates and normalizes]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `account_id` | Primary identifier — referenced by all other tables |
| `segment` | SMB / Mid-Market / Enterprise — the main analytical dimension |
| `industry` | Vertical (Tech, Finance, Healthcare, etc.) |
| `revenue_model` | Subscription / Usage-Based / One-Time |
| `account_status` | Prospect / Customer / Churned |

**Data quality issue in this project:** ~12 duplicate account_ids exist in the source — the same account appears twice with slightly different names. A `ROW_NUMBER()` deduplication in staging keeps the most recent record and flags the duplicates.

---

### Source 2: `raw_marketing_leads` — Inbound Lead Records

**Real-world origin:** Marketing Automation (HubSpot, Marketo) or CRM Leads object

**Real-world pipeline:**
```
[Web form submissions, content downloads, webinar signups]
        ↓
[Marketing automation platform captures the event]
[Assigns lifecycle stage: Lead → MQL → SQL → Converted]
        ↓
[Synced to data warehouse via Fivetran or native connector]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `lead_id` | Unique lead identifier |
| `account_id` | Links the lead to a company account (nullable — some leads are anonymous) |
| `lead_source` | Inbound / Outbound / Organic / Event / Referral |
| `lifecycle_stage` | Current position in the marketing funnel |

**Data quality issue:** 12 leads have a NULL `account_id` — they arrived through channels that did not capture the company. These are retained with `has_account = FALSE` for audit purposes.

---

### Source 3: `raw_salesforce_opportunities` — Sales Pipeline

**Real-world origin:** Salesforce Opportunity object

**Real-world pipeline:**
```
[Sales rep creates an opportunity in Salesforce]
[Updates stage as the deal progresses]
[Sets expected close date — this is the number every VP asks about on Monday]
        ↓
[Fivetran syncs to warehouse hourly]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `opportunity_id` | Unique deal identifier |
| `account_id` | Links to the company |
| `opportunity_stage` | Prospecting → Qualification → Proposal → Negotiation → Closed-Won/Lost |
| `amount` | Projected deal value (what the rep thinks it will close for) |
| `expected_close_date` | The date the rep expects to close — this changes frequently |
| `close_date_changes` | How many times the close date was pushed out |
| `last_activity_at` | Last time a sales action was logged against this deal |

**Data quality issue:** 9 opportunities have account_ids starting with `ACC_ORPHAN_` — they were created against accounts that no longer exist in the CRM. These are flagged with `is_orphan = TRUE`.

---

### Source 4: `raw_contracts` — Signed Legal Agreements

**Real-world origin:** DocuSign / PandaDoc / internal contract system

**Real-world pipeline:**
```
[Sales team sends contract via DocuSign]
[Customer signs → contract status updates to "Active"]
[Finance team records the contract in contract management system]
        ↓
[Synced to warehouse — often on a delay vs. CRM]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `contract_id` | Unique contract identifier |
| `opportunity_id` | Links back to the CRM opportunity |
| `contract_value` | The signed total contract value (TCV) |
| `contract_start_date` / `contract_end_date` | Contract term |
| `contract_status` | Active / Amended / Cancelled |

**Data quality issue:** 4 contract_ids appear twice with different values. This is a real occurrence in B2B — a contract gets amended and the system creates a second record instead of updating the original. Both records are retained with `is_canonical_record` flagging which one to use for calculations.

**Why this creates a revenue gap:** The `contract_value` here is what legal signed. This is often slightly different from the `amount` in Salesforce because reps sometimes quote rounded numbers, or a small discount is applied at contract execution.

---

### Source 5: `raw_billing` — Invoice Records

**Real-world origin:** Stripe, Zuora, Chargebee, or custom billing system

**Real-world pipeline:**
```
[Billing system generates monthly invoices based on contract terms]
[Invoice sent to customer via email / AP portal]
[Payment received → status updates to "Paid"]
[Failed ACH/card charge → status stays "Failed"]
        ↓
[Nightly export to warehouse via API or database replication]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `invoice_id` | Unique invoice identifier |
| `customer_id` | This is the account_id in billing system nomenclature |
| `contract_id` | Links to the contract being billed |
| `billing_amount` | Invoice amount in original currency |
| `currency` | USD / EUR / GBP |
| `payment_status` | Paid / Pending / Failed |

**Key complexity:** Billing systems often operate in the customer's local currency. Revenue analytics requires normalizing everything to USD using FX rates. In production this uses a live FX rates table; here we use static 2025 rates (EUR 1.08, GBP 1.27).

---

### Source 6: `raw_customer_success` — Health and Renewal Data

**Real-world origin:** Gainsight, ChurnZero, or Salesforce CS module

**Real-world pipeline:**
```
[CS platform aggregates product usage, support tickets, NPS scores]
[Computes a composite health score (0–100) per account]
[CS manager manually updates renewal_status]
        ↓
[Synced to warehouse via API connector]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `account_id` | Links to the CRM account |
| `customer_health_score` | Composite 0–100 score |
| `renewal_date` | When the contract comes up for renewal |
| `renewal_status` | Healthy / Needs Attention / At Risk / Churned |
| `expansion_amount` | Additional ARR from upsell/cross-sell |
| `churn_reason` | Why a churned account left |

---

### Source 7: `raw_product_events` — Usage Telemetry

**Real-world origin:** Amplitude, Mixpanel, Segment, or custom event tracking

**Real-world pipeline:**
```
[User performs action in the product (login, feature_used, report_created)]
[Client-side SDK fires event to tracking platform]
[Events stream to warehouse via Segment or custom Kafka pipeline]
        ↓
[One row per event — high-volume table, often 10M+ rows/month in production]
```

**Key fields:**
| Field | Description |
|-------|-------------|
| `user_id` | Individual user within an account |
| `account_id` | The company the user belongs to |
| `event_name` | login / workspace_created / feature_used / report_created / etc. |
| `event_timestamp` | Exact time of the action |

**How it feeds analytics:** Product events are the raw material for customer health scoring. High-value events (activation_completed, integration_connected) signal strong adoption and predict renewal. Low activity signals churn risk.

---

## How These Sources Connect

```
raw_salesforce_accounts ←── account_id ──→ raw_marketing_leads
         │                                          │
         │ account_id                               │ account_id
         ▼                                          ▼
raw_salesforce_opportunities          raw_customer_success
         │                            raw_product_events
         │ opportunity_id
         ▼
   raw_contracts
         │
         │ contract_id
         ▼
    raw_billing
```

**The central join key is `account_id`.** Every system uses it, but:
- Billing calls it `customer_id` (same value, different name)
- 12 leads don't have one (unmatched)
- 9 opportunities reference account_ids that don't exist (orphans)

The `int_customer_identity_map` model is built specifically to surface these connection gaps.

---

## Loading Data into the Pipeline

In this project, synthetic data is generated by `python/mart_simulator.py` and stored in `data/raw/` as CSV files. The dbt project loads them as seeds:

```bash
# From the dbt/ directory
dbt seed          # Loads all raw_*.csv files into the warehouse
dbt run           # Runs all staging → intermediate → mart models
dbt test          # Validates uniqueness, not_null, and accepted_values
```

**In production**, the `dbt seed` step is replaced by:
- Fivetran or Airbyte connectors that sync from the live source systems
- Data lands directly in the warehouse as raw tables
- dbt picks up from there — same models, no changes required

---

_Next: [02_data_cleaning_staging.md](./02_data_cleaning_staging.md) — How staging models clean and flag the data quality issues found in each source._
