# Phase 1 — Synthetic Data Foundation

## Purpose

Generate a reproducible synthetic dataset that connects paid media activity to product activation, retention, and revenue — without access to real company data.

## Tables

| Table | Grain | Role |
|---|---|---|
| `dim_trial_accounts` | One row per trial signup | Attribution, persona, channel, subscription tier |
| `dim_creatives` | One row per creative | Hook type, format, persona, channel linkage |
| `fact_daily_performance` | One row per creative × date | Impressions, clicks, spend, trial signups |
| `fact_product_events` | One row per product event | Funnel events from trial signup to subscription |
| `fact_subscriptions` | One row per subscription | Tier, MRR, status, churn date |
| `fact_revenue_events` | One row per revenue event | MRR and expansion payments by month |

## Design Choices

- **Primary analytical unit**: restaurant owner trial account (`account_id`)
- **Random seed**: 20260913 — same seed always produces identical output
- **Channels**: META (40% budget), TikTok (25%), Google Search (20%), LinkedIn (15%)
- **Activation**: CAMPAIGN_LAUNCHED within 14 days of TRIAL_SIGNUP
- **Attribution**: 7.6% of accounts intentionally have missing attribution (is_missing_attribution=True)

## Intentional Patterns

| Pattern | Location |
|---|---|
| High CTR, low activation rate | META in fact_daily_performance |
| Creative fatigue (CTR declining) | 16 of 90 creatives in fact_daily_performance |
| Platform attribution vs blended CPAO reversal | META vs TikTok across both tables |
| Missing attribution | dim_trial_accounts.is_missing_attribution |
| Delayed conversions | fact_subscriptions.conversion_delay_days |
| Immature M6 cohorts | March 2026 signups not yet 180 days old |
| Data quality defect | 9 rows with clicks > impressions |

## Reproducibility

```bash
cd projects/04_project4_ai_growth_operations_agent
python scripts/generate_synthetic_data.py
```

Outputs 6 parquet + 6 CSV files to `data/synthetic/`. A `manifest.json` records the seed, date range, and row counts for verification.

## Key Numbers

- 2,000 restaurant owner trials over 12 weeks (2026-01-05 to 2026-03-29)
- 519 activated owners (campaign launched within 14 days) — 26.0% activation rate
- 264 subscriptions started — 13.2% trial-to-paid conversion
- $149,927 total synthetic ad spend across all channels (~$50K/month)
