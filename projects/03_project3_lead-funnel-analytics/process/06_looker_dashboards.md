# Phase 5: Looker Dashboards

> **Core Question:** Which dashboards answer the actual business questions, and how should they be structured?

---

## Dashboard Design Principles

Each dashboard answers **one business question** for **one audience**.

```
❌ One giant dashboard with 30 tiles
✅ Five focused dashboards, each with 8-12 tiles
```

Layout rule:
```
[Row 1] KPI summary tiles      ← the answer
[Row 2] Trend over time        ← is it getting better or worse?
[Row 3] Segment breakdown      ← where is the problem?
[Row 4] Detail table           ← drill into specifics
```

---

## Dashboard 1: Lead Funnel

**Audience:** Marketing + Product  
**Business question:** Where are users dropping out of the quote funnel?

### KPI Tiles (Row 1)
- Sessions
- Quote Start Rate
- Overall CVR (session → lead)
- Valid Lead Rate
- Duplicate Rate

### Charts (Rows 2–3)
- Funnel bar chart: Sessions → Quote Starts → Completions → Leads
- Stage conversion rate by channel (grouped bar)
- Valid lead rate trend by month

### Detail Table (Row 4)
- Channel × Vertical × Month: all funnel metrics

### Global Filters
- Date range
- Channel
- Insurance vertical
- State

---

## Dashboard 2: Campaign Performance

**Audience:** Marketing team  
**Business question:** Which campaigns deliver the best revenue per lead, and are we optimizing toward the right metrics?

### KPI Tiles (Row 1)
- Total Spend
- Warehouse Leads (vs Platform Leads)
- Valid Leads
- CPL
- Revenue per Lead
- ROAS

### Charts (Rows 2–3)
- CPL vs Revenue per Lead scatter (each campaign = one dot)
- Platform leads vs Warehouse leads by channel (bar — shows overclaim)
- Spend and revenue trend by month

### Detail Table (Row 4)
- Campaign × Month: spend, leads, valid rate, CPL, revenue, ROAS, platform overclaim %

### Key Insight to Surface
> Meta's platform reports 25–38% more conversions than the warehouse records.
> Optimizing toward platform ROAS overinvests in Meta.

---

## Dashboard 3: Partner Performance

**Audience:** Partner management + Operations  
**Business question:** Which partners are accepting fewer leads, and is it a trend or a one-time event?

### KPI Tiles (Row 1)
- Total Leads Delivered
- Accepted
- Overall Acceptance Rate
- 7-Day Rolling Acceptance Rate
- Revenue per Delivered Lead
- Avg Response Time (seconds)

### Charts (Rows 2–3)
- Acceptance rate trend by partner (line chart — 7d rolling)
- Partner comparison bar: acceptance rate + revenue per lead
- Rejection reason breakdown (pie or bar)

### Detail Table (Row 4)
- Partner × Date: delivered, accepted, rejected, response time, daily revenue

### Key Insight to Surface
> P009 (Liberty Mutual) consistently accepts only ~65% of leads.
> P004 (BlueCross) accepts 85% and has the highest revenue per lead.
> → Consider increasing routing priority for P004.

---

## Dashboard 4: Attribution & Reconciliation

**Audience:** Marketing analytics + Finance  
**Business question:** How much are platforms overclaiming, and which first-touch channels actually drive revenue?

### KPI Tiles (Row 1)
- Platform Reported Leads
- Warehouse Leads
- Platform Overclaim Rate
- First-Touch: % by Channel
- Revenue per First-Touch Lead (by channel)

### Charts (Rows 2–3)
- Platform vs Warehouse leads by channel (side-by-side bars)
- First-touch channel distribution (donut)
- Avg revenue by first-touch channel (bar)
- Avg hours to submit by first-touch channel

### Detail Table (Row 4)
- Channel × Month: platform leads, warehouse leads, discrepancy, overclaim %

### Key Insight to Surface
> Meta platform overclaims by 28% on average.
> Organic first-touch leads monetize at $52 vs Meta first-touch at $38.
> → Attribution shifts budget toward google + organic when using warehouse data.

---

## Dashboard 5: Executive KPI

**Audience:** Leadership  
**Business question:** Are we growing revenue efficiently?

### KPI Tiles (Row 1)
- Total Spend
- Total Revenue
- ROAS
- Leads Submitted
- Accepted Leads
- Revenue per Lead

### Charts (Rows 2–3)
- Revenue and spend trend (dual-axis line)
- ROAS by channel (bar)
- Revenue by insurance vertical (donut)

### One-line insight per tile
Each KPI tile shows: value + delta vs prior period (Looker `comparison_type: change`)

---

## Validation Checklist

Before publishing any dashboard:

| Check | How |
| ----- | --- |
| KPI tiles match BigQuery COUNT | Run validation query, compare manually |
| Filters work correctly | Apply each filter, confirm tiles update |
| Drill-downs return correct rows | Click a tile, verify the detail rows |
| No NULL values in key metrics | Confirm COALESCE is applied upstream |
| Date filter covers full range | Check min/max dates in mart tables |
| Numbers match mart_* tables | `SELECT * FROM mart_campaign_performance LIMIT 5` |

---

## Status

| Dashboard | Explore | Status |
| --------- | ------- | ------ |
| Lead Funnel | `lead_funnel` | ⏳ Build in Looker |
| Campaign Performance | `campaign_performance` | ⏳ Build in Looker |
| Partner Performance | `partner_performance` | ⏳ Build in Looker |
| Attribution | `attribution` | ⏳ Build in Looker |
| Executive KPI | `campaign_performance` | ⏳ Build in Looker |
