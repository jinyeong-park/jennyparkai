# Phase 6 — Retention, LTV, and Budget Allocation

## Purpose

Determine which acquisition sources produce owners who stay, generate revenue, and justify further investment — and translate that into a budget allocation recommendation.

## Funnel Summary

```
2,000 trials
  → 519 activated owners (26.0%)   ← CAMPAIGN_LAUNCHED within 14 days
    → 264 subscriptions (13.2%)
      → 105 still active (39.8% of subscribers)
      → 159 churned (60.2% of subscribers)
```

## Retention by Channel (M1 / M3 / M6)

| Channel | M1 | M3 | M6 | M6 mature? |
|---|---|---|---|---|
| META | 82.5% | 55.0% | **45.0%** | Partial ⚠️ |
| Google Search | 82.0% | 59.0% | 37.7% | Partial ⚠️ |
| TikTok | 79.9% | 57.6% | **37.5%** | Partial ⚠️ |

⚠️ March 2026 cohorts not yet 180 days old as of 2026-09-13 — excluded from final M6 calculation.

## LTV:CAC by Channel

| Channel | CPAO | Observed LTV | LTV:CAC | Payback |
|---|---|---|---|---|
| TikTok | $143 | $291 | **2.03x** | <1 month |
| Google Search | $248 | $238 | 0.96x | ~1 month |
| META | $666 | $318 | **0.48x** | 2.1 months |

**Double reversal**: META receives 40% of budget (highest share) → worst CPAO → worst LTV:CAC. TikTok's structural CPM advantage ($5 vs META's $18) drives the unit economics reversal.

**Note**: Observed LTV covers only 2–3 months of revenue (short simulation window). Projected LTV uses `monthly_price / monthly_churn_rate` with explicit assumption notes.

## Budget Allocation ($150K total, 10% exploration reserve)

| Channel | Allocation | % | Logic |
|---|---|---|---|
| TikTok | $75,363 | 55.8% | Best CPAO (4.7x better than META) |
| Google Search | $43,455 | 32.2% | Mid efficiency, LTV:CAC ~1.0x |
| META | $16,182 | 12.0% | Worst CPAO, min-capped at 10% |
| LinkedIn + Unknown | $7,500 each | 10% total | Exploration reserve — no conversion history |

Allocation method: `1/CPAO` weighting, with per-channel min (10%) and max (60%) constraints. `RECOMMEND_ONLY=True` — this is a decision input, not an automated action.

## SQL Models

| File | Purpose |
|---|---|
| `sql/07_cohort_retention.sql` | Monthly cohort × channel retention with M6 maturity flags |
| `sql/08_ltv_cac.sql` | Observed LTV, CPAO, LTV:CAC, payback by channel |

## Artifacts

`notebooks/02_retention_ltv.ipynb` — 7-section analysis (cohorts, retention, LTV, LTV:CAC, budget allocation, key findings).

`examples/budget_recommendation.json` — actual output from `allocate_budget()` for the $150K scenario.
