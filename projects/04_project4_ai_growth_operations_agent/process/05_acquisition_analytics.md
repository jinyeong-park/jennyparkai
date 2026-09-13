# Phase 5 — Paid Acquisition and Creative Performance Analytics

## Purpose

Calculate media metrics correctly, surface the high-CTR/low-activation pattern, and detect creative fatigue — all from the synthetic DuckDB dataset.

## SQL Models

| File | What it answers |
|---|---|
| `sql/01_channel_scorecard.sql` | How does each channel perform on spend, CTR, CPM, trial CAC? |
| `sql/02_creative_performance.sql` | Which creatives drive trials, and at what cost? |
| `sql/03_activation_by_channel.sql` | Which channels bring owners who actually activate? |
| `sql/04_cpao_by_channel.sql` | How does trial CAC ranking compare to CPAO ranking? |
| `sql/05_creative_fatigue.sql` | Which creatives show >25% CTR decline from peak? |
| `sql/06_hook_type_analysis.sql` | Which hook type is most efficient per trial? |

## Key Findings (Synthetic Data)

**Channel scorecard:**

| Channel | Spend | Trial CAC | Activated Owners | CPAO |
|---|---|---|---|---|
| TikTok | $37K | $12 | 262 | **$143** |
| Google Search | $30K | $21 | 121 | $248 |
| META | $60K | $52 | 90 | **$666** |
| LinkedIn | $22K | — | — | — |

Total spend: ~$50K/month ($150K over 12-week simulation period).

**Key reversal**: META receives the largest budget share (40%) but produces the fewest activated owners at the highest CPAO ($666 — 4.7x worse than TikTok). TikTok's low CPM ($5 vs META's $18) means more impressions and clicks per dollar, creating a structural efficiency advantage.

**Hook type (trial CAC):**
- OUTCOME: $22 (best)
- CONTRAST: $23
- SOCIAL_PROOF: $28
- FOMO: $31
- DEMONSTRATION: $33 (highest)

**Creative fatigue**: 16 of 90 creatives (17.8%) show CTR decline >25% from peak. Most extreme: 3 Google Search creatives with >91% drop by week 12.

**Data quality findings:**
- 9 rows with clicks > impressions (flagged as ERROR)
- 152 accounts (7.6%) with missing attribution (preserved as UNKNOWN channel, not dropped)

## Weighted Metrics

All aggregated rates use SUM/SUM — not AVG of per-row ratios:
```sql
-- Correct
SUM(clicks) / NULLIF(SUM(impressions), 0) AS ctr

-- Wrong (common mistake)
AVG(clicks / impressions) AS ctr
```

## Notebooks

`notebooks/01_acquisition_analysis.ipynb` — 8-section analysis with business commentary on each finding.
