# Phase 1: Raw Data Generation

> **Core Question:** What data does an insurance lead marketplace actually produce, and how do we simulate it realistically?

---

## Why Synthetic Data

A real insurance lead platform generates data across 6+ separate systems:

```
Google Ads API      → ad spend, impressions, clicks, platform conversions
Meta Ads API        → same (but overclaims conversions by 15–40%)
Website (Segment)   → quote funnel events
Lead System (CRM)   → lead submissions, validation, quality scores
Routing Platform    → partner matching, delivery, responses
Partner Systems     → acceptance, rejection reasons
Revenue System      → confirmed payouts
```

This project uses **synthetic data** that reproduces the key patterns and edge cases without real customer data.

---

## What Was Generated

### Script
`scripts/generate_synthetic_data.py`

### Output Files

| File | Rows | Period |
| ---- | ---- | ------ |
| `raw_partners.csv` | 10 | static |
| `raw_ad_performance.csv` | 905 | Jan–Jun 2025 |
| `raw_quote_events.csv` | 17,261 | Jan–Jun 2025 |
| `raw_leads.csv` | 1,321 | Jan–Jun 2025 |
| `raw_routing_attempts.csv` | 1,135 | Jan–Jun 2025 |
| `raw_revenue_events.csv` | 731 | Jan–Jun 2025 |

---

## Key Design Decisions

### 1. Campaigns & Channels

```python
CAMPAIGNS = [
    C001 → google    → auto insurance   → CA, TX, FL focus
    C002 → google    → home insurance   → NY, PA, OH focus
    C003 → meta      → auto insurance   → CA, TX, GA focus
    C004 → meta      → health insurance → FL, NC, IL focus
    C005 → affiliate → life insurance   → MI, OH, NY focus
    C006 → organic   → auto insurance   → all states
    C007 → direct    → home insurance   → all states
]
```

### 2. Realistic Lead Quality by Channel

Different channels produce different quality leads — this is the core business insight.

```python
CHANNEL_QUALITY = {
    "google":    0.88,   # High intent search → 88% valid
    "meta":      0.72,   # Social audience → 72% valid
    "affiliate": 0.65,   # Lower quality publishers → 65% valid
    "organic":   0.92,   # High intent organic → 92% valid
    "direct":    0.90,   # Direct visit → 90% valid
}
```

### 3. Platform Overclaim (Meta > Google)

Meta's platform reports 15–40% more conversions than actually land in the warehouse.
Google overclaims by 5–20%. This is a real-world reconciliation problem.

```python
overclaim = random.uniform(1.15, 1.40)  # meta
overclaim = random.uniform(1.05, 1.20)  # google
```

### 4. Funnel Drop-off at Each Stage

Not every visitor completes every funnel step.

```
landing_page_view          100% enter
quote_started              60% proceed
contact_info_completed     75% of above
insurance_details_completed 72% of above
quote_completed            85% of above
lead_submitted             80% of above
```

Overall session-to-lead conversion ≈ 22% — realistic for insurance.

### 5. Partner Acceptance Varies

Each partner has its own acceptance rate based on their selectivity.

| Partner | Acceptance Rate |
| ------- | --------------- |
| P002 State Farm | 82% |
| P004 BlueCross | 85% |
| P001 Progressive | 78% |
| P009 Liberty Mutual | 65% |

### 6. Edge Cases Embedded in Data

| Scenario | Rate | Why It Matters |
| -------- | ---- | -------------- |
| Duplicate leads | 6.4% | Tests deduplication logic |
| Invalid leads (low quality) | ~19% | Tests valid lead rate calc |
| Leads routed to 2–3 partners | 40% | Tests fan-out prevention |
| Revenue without accepted lead | 0% | Data integrity check |
| Leads without revenue | ~45% | Normal — not all leads monetize |

---

## How to Regenerate

```bash
python scripts/generate_synthetic_data.py
```

To change the date range, edit in the script:

```python
START_DATE = date(2025, 1, 1)
END_DATE   = date(2025, 6, 30)
```
