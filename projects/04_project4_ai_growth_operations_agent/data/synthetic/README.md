# Synthetic Dataset — Tablr Growth Simulation

**All data in this directory is synthetic. No real companies, individuals,
ad accounts, or transaction records are represented.**

## Files

| File | Description | Rows |
|------|-------------|------|
| `dim_creatives.parquet` | Creative dimension: one row per creative variant | 90 |
| `fact_daily_performance.parquet` | Daily ad delivery and funnel metrics per creative | ~7,560 |
| `dim_trial_accounts.parquet` | One row per simulated restaurant owner trial | 2,000 |
| `fact_product_events.parquet` | One row per product event per user | ~11,600 |
| `fact_subscriptions.parquet` | Subscription lifecycle per converted account | ~646 |
| `fact_revenue_events.parquet` | Monthly MRR and expansion revenue events | ~815 |
| `manifest.json` | Metadata: seed, timestamp, record counts, version |  |

CSV copies of each table are saved alongside the Parquet files for easy inspection.

## Random Seed

All data was generated with `RANDOM_SEED = 20260913`.
Running `python scripts/generate_synthetic_data.py` with this seed
always produces the same row counts and the same first 10 account IDs.

## Intentional Patterns

These patterns are deliberately encoded in the data to support realistic analysis:

1. **High CTR, low activation** (`cr_meta_001_001`): CTR = 4.5–5.5%, but only 18% of
   signups complete onboarding (vs. 42% baseline). Hook: FEAR_OF_MISSING_OUT.
   Attracts curiosity clickers, not serious restaurant owners.

2. **Lower CTR, higher LTV persona** (`COMMUNITY_FOCUSED`): CTR ~1.2% (lowest), but
   M3 retention = 78% (vs. 55% baseline) and LTV = $1,450 (vs. ~$820 baseline).
   Sticky once activated.

3. **Creative fatigue** (`cr_meta_002_001`): CTR = 3.2% in weeks 1–6, decays to 1.1%
   by week 12. Impressions stay constant (budget maintained). Frequency increases.

4. **Platform-reported winner, weak blended** (`cr_meta_003_002`): Meta ROAS = 4.2x,
   but first-party CPAO = $312 (vs. target $180). High signup volume but 22%
   activation rate.

5. **Insufficient evidence** (`cr_linkedin_001_003`): Launched in week 11.
   Only 180 total clicks — below the 300-click minimum threshold.
   State = INSUFFICIENT_DATA.

6. **Genuine winner** (`cr_tiktok_002_002`): CTR = 2.8%, activation = 61%,
   M3 retention = 72%, CPAO = $134. Strong across all metrics.

7. **Delayed conversions**: 15% of subscribers convert 7–14 days after the 14-day
   trial period ends. Modeled via `conversion_delay_days` in `fact_subscriptions`.

8. **Missing attribution**: 8% of trial signups have NULL `campaign_id` and
   `creative_id`. Direct or organic traffic that entered the funnel untracked.

9. **Data quality issue**: In week 7 (2026-02-16 to 2026-02-22), ad group
   `ag_google_002_002` has `clicks > impressions` on 3 days due to a simulated
   tracking pixel misconfiguration. Detectable by `test_data_quality.py`.

## How to Regenerate

```bash
python scripts/generate_synthetic_data.py
```

The script completes in under 60 seconds and overwrites existing files.
To change patterns, edit `CREATIVE_OVERRIDES` or `COMMUNITY_FOCUSED_OVERRIDES`
in the script and update the seed if behavior changes.

## Data Dictionary

See `data/data_dictionary.md` for column definitions, metric formulas,
attribution assumptions, and retention window logic.
