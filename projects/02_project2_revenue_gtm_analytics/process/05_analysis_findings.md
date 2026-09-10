# Phase 5: Analysis & Key Findings

> **Purpose:** Translate the dbt mart models into actionable business insights
> across four analytical domains: GTM funnel, revenue reconciliation, pipeline health,
> and customer retention.

> **Source notebooks:** All findings below are produced by the four Jupyter notebooks
> in [`../python/`](../python/) using `mart_simulator.py` to replicate the dbt transformations.

---

## Analysis 1: GTM Funnel (`02_gtm_funnel_analysis.ipynb`)

**Business question:** Where does our pipeline come from, and where does it leak?

### Funnel Conversion Rates

The GTM funnel starts from all CRM accounts and measures what percentage reach each stage:

```
All Accounts → Has Lead → MQL+ → SQL+ → Has Opportunity → Closed-Won
    100%         ~X%       ~X%    ~X%       ~X%               ~X%
```

**What to look for:**
- The biggest drop-off point in the funnel identifies where to invest — marketing, SDR, or AE
- If Lead→MQL is low: top-of-funnel content quality or targeting needs work
- If SQL→Opportunity is low: handoff between marketing and sales is broken
- If Opportunity→Won is low: either deal quality is poor or AE closing skills need improvement

### Lead Source Performance

Not all lead sources produce equal quality pipeline. The analysis compares:

| Metric | Why it matters |
|--------|----------------|
| Lead volume | Reach — how many companies is this source touching? |
| SQL rate | Quality — how many leads become sales-qualified? |
| Win rate | Conversion — how many accounts with this source eventually close? |
| Avg deal size | Value — are these small or large customers? |

**Key insight pattern:** High-volume sources (Inbound, Organic) often have lower win rates but still drive the most total revenue. Referral and Event sources typically have lower volume but significantly higher win rates — each lead is pre-qualified before it enters the funnel.

### Sales Velocity by Segment

```
Median Sales Cycle by Segment:
  Enterprise:  lead_to_close_days = ~X days
  Mid-Market:  lead_to_close_days = ~X days
  SMB:         lead_to_close_days = ~X days
```

Enterprise takes longer — this is expected. The analytical value is knowing the exact median and P75 so the revenue forecast can be adjusted: "We have 15 Enterprise deals in Negotiation today; based on typical cycle length, they are likely to close in Q+1, not this quarter."

### Data Quality Impact

- **12 unmatched leads:** Cannot be attributed to an account. Marketing spend that drove these leads cannot be measured for ROI.
- **9 orphan opportunities:** $X in pipeline that cannot be tied to an account. If these are real deals, they represent a reporting gap in the VP's pipeline number.

**Action:** RevOps should investigate the orphan opportunities first — each represents pipeline that may be close to closing but is invisible to standard reports.

---

## Analysis 2: Revenue Reconciliation (`03_revenue_reconciliation.ipynb`)

**Business question:** Why does our CRM show more revenue than what we collected?

### The Four Revenue Numbers

```
Stage              Amount      % of Bookings    Gap
──────────────────────────────────────────────────────
CRM Bookings       $X,XXX,XXX    100%
Contract Value     $X,XXX,XXX    ~X%          Gap 1: ~X%
Billed (USD)       $X,XXX,XXX    ~X%          Gap 2: ~X%
Collected Cash     $X,XXX,XXX    ~X%          Gap 3: ~X%
──────────────────────────────────────────────────────
End-to-end rate                  ~X%
```

### Gap 1: Booking → Contract (Discount at Signing)

The CRM booking amount is what the sales rep entered when they marked the deal Closed-Won. The contract value is what legal actually signed. The difference is the discount.

**Typical patterns:**
- Enterprise deals carry larger discounts (more negotiation leverage)
- End-of-quarter deals carry larger discounts (reps under quota pressure)
- A `discount_tier = 'Heavy Discount (>15%)'` should trigger a review from Sales Ops

### Gap 2: Contract → Billed

In most SaaS billing models, the contract is billed monthly or quarterly — not all upfront. A 12-month contract signed on day 1 may only have 6 months billed if we are mid-contract. This gap is expected and healthy.

If this gap is unexpectedly large, it indicates a billing system delay — contracts were signed but invoices were not generated on schedule.

### Gap 3: Billed → Collected (Payment Risk)

This is the gap that Finance cares about most. Invoices have been sent but not paid.

```
Pending:  The invoice has been sent; payment is not yet due or is being processed
Failed:   The payment attempt was rejected (card failure, insufficient funds, ACH return)
```

**Action triggers:**
- High failed amount → Collections team follow-up
- High pending amount with old billing dates → Dunning sequence activation

### Duplicate Contract Impact

4 contract_ids appeared twice with different values. The `is_canonical_record` filter selects the higher-value record (post-amendment). The value difference across these 4 pairs represents the revenue that would be double-counted if the filter were not applied.

---

## Analysis 3: Pipeline Analysis (`04_pipeline_analysis.ipynb`)

**Business question:** How healthy is our current pipeline and what will we realistically close?

### Pipeline by Stage

```
Stage          Deals    Total Pipeline    Weighted Pipeline    Win Rate
────────────────────────────────────────────────────────────────────────
Prospecting     X       $X,XXX,XXX        $XXX,XXX             5%
Qualification   X       $X,XXX,XXX        $XXX,XXX            15%
Proposal        X       $X,XXX,XXX        $X,XXX,XXX          35%
Negotiation     X       $X,XXX,XXX        $X,XXX,XXX          65%
────────────────────────────────────────────────────────────────────────
Total           X       $X,XXX,XXX        $X,XXX,XXX
```

The ratio of weighted to raw pipeline is the pipeline quality indicator. A ratio below 20% means the pipeline is heavily weighted toward early stages — the quarter's number is unlikely to be hit.

### Risk Flag Summary

Three risk signals are applied independently:

| Signal | Definition | Pipeline at Risk |
|--------|------------|------------------|
| `is_past_due` | Close date has passed; deal is still open | $X,XXX,XXX |
| `is_stale` | No activity logged in 30+ days | $X,XXX,XXX |
| `has_repeated_slip` | Close date has changed ≥2 times | $X,XXX,XXX |

**High Risk = past due AND repeated slip.** These deals have been repeatedly promised to close and haven't. They should be reviewed by the VP of Sales for either a realistic re-forecast or removal from the pipeline.

### Deal Age Distribution

The histogram of `days_open` reveals whether the team has "zombie" deals — opportunities that have been sitting in the pipeline for 90+ days with no movement. These inflate the pipeline number but are unlikely to close.

**The zombie deal problem:** Sales reps often leave stale deals open because closing them as 'Lost' hurts their conversion metrics. A healthy RevOps process removes deals that have not had activity in 60+ days, or at minimum re-stages them to an earlier stage.

---

## Analysis 4: Customer Health & Retention (`05_customer_health.ipynb`)

**Business question:** Which customers are at risk of churning, and is our base growing?

### Health Score Distribution

```
Health Tier          Accounts     % of Base
──────────────────────────────────────────
Healthy (≥70)          X          ~X%
Needs Attention (35-69) X         ~X%
At Risk (<35)          X          ~X%
Unknown (0)            X          ~X%
```

**What "Needs Attention" means in practice:** These accounts are not yet at risk of churn, but they are not fully engaged. A proactive CS outreach at this stage costs less than a save-play once the account reaches "At Risk." The analysis notebook generates a priority list sorted by health score for exactly this use case.

### NRR by Segment

NRR (Net Revenue Retention) is calculated as:

```
NRR = (Starting Revenue + Expansion Revenue) / Starting Revenue
```

A number above 100% means the revenue from existing customers grew — even before counting new customer acquisitions. This is the most important growth metric for a SaaS business.

**Segment NRR comparison reveals:**
- Which segments are expanding (upsell is working)
- Which segments are contracting (churn or downsell)
- Where the CS team should focus expansion efforts

### At-Risk Account Priority List

The analysis combines two filters:
1. `health_tier IN ('At Risk', 'Needs Attention')` — low health signal
2. `total_collected_usd > 0` — account is an actual paying customer, not a prospect

The resulting list is sorted by health score (lowest first), then by `days_to_renewal` (soonest first). This gives CS managers a call list for the week: the most at-risk accounts with the most urgent renewal timelines.

### Health Score vs. Expansion Correlation

The scatter plot in the notebook tests the hypothesis: "Healthy customers expand; unhealthy customers churn."

- If the correlation is positive and significant: health score is a good leading indicator of expansion
- If the correlation is near zero: the health score model needs recalibration — it may not be capturing the right signals

---

## Cross-Analysis: The Revenue Completeness Picture

After running all four analyses, the clearest finding is about data completeness. An account can be in Salesforce (CRM) without a marketing lead, a signed contract, billing history, or a CS health score. Each missing piece represents an analytical blind spot.

The `int_customer_identity_map` model's `systems_present` column directly quantifies this:

| systems_present | What it means | Action |
|-----------------|---------------|--------|
| 4 | Complete data across all systems | No action needed |
| 3 | Missing one system | Investigate which system and why |
| 2 | Major gaps in the data | High priority for data quality review |
| 1 | CRM-only (prospect) | Expected for new leads — monitor for progression |

Segmenting revenue analysis by `systems_present` shows whether your highest-value customers have the most or least complete data. If your largest accounts are missing CS health scores, you have no early warning system for their renewal.

---

## Summary: From Numbers to Decisions

| Finding | Business Decision |
|---------|-------------------|
| Lead source X has 2× the win rate of source Y | Shift marketing budget toward source X |
| 30% of pipeline is past-due or stale | Conduct an immediate pipeline scrub; re-forecast the quarter |
| Booking → Collected gap is 15% overall, 22% for Enterprise | Review Enterprise discount approval thresholds |
| NRR for SMB segment is below 100% | CS team to prioritize SMB renewal outreach this quarter |
| X accounts have health score < 35 with renewal in 60 days | CS managers to call these accounts this week |

> The value of a unified data model is not the individual numbers — it is the ability to
> connect them. A health score drop that coincides with a billing payment failure in the
> same account is a much stronger churn signal than either one alone.
> `fct_customer_lifecycle` makes that connection visible.

---

_Return to [00_process.md](./00_process.md) for the complete phase overview._
