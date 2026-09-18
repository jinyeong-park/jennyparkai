# Acquisition Baseline Report
**[SYNTHETIC DATA — Tablr portfolio simulation]**
**Period:** 2026-01-05 to 2026-03-29 (12 weeks)
**Date generated:** 2026-09-13
**Total spend:** $149,927 | **Total impressions:** ~4,800,000 | **Total trial signups:** 2,000

---

## Channel Scorecard

| Channel | Spend | Trial Signups | Trial CAC | Activated Owners | CPAO | Obs LTV | LTV:CAC | Policy |
|---------|-------|--------------|-----------|-----------------|------|---------|---------|--------|
| TIKTOK | $37,490 | ~1,005 | $12 | 262 | $143 | $291 | 2.03x | SCALE_CANDIDATE |
| GOOGLE_SEARCH | $29,978 | ~1,428 | $21 | 121 | $248 | $238 | 0.96x | OBSERVE |
| META | $59,974 | ~379 | $52 | 90 | $666 | $318 | 0.48x | HOLD |
| LINKEDIN | $22,485 | 0 | — | 0 | — | — | — | INSUFFICIENT_DATA |

*Activated Owners = accounts that completed CAMPAIGN_LAUNCHED within 14 days of trial signup (first-party attribution, missing-attribution accounts excluded). CPAO = spend / activated owners.*
*All CTR, CPM, CPC figures use weighted aggregation: SUM(clicks)/SUM(impressions), not an average of per-row rates.*

---

## Creative Hook Type Analysis

| Hook Type | Impressions | Clicks | CTR | Spend | Trial Signups | Trial CAC |
|-----------|-------------|--------|-----|-------|--------------|-----------|
| FEAR_OF_MISSING_OUT | 1,702,114 | 40,780 | 2.40% | $301,101 | 1,258 | $239.35 |
| OUTCOME | 2,516,193 | 58,114 | 2.31% | $427,416 | 1,699 | $251.57 |
| CONTRAST | 3,028,030 | 59,945 | 1.98% | $342,938 | 1,586 | $216.23 |
| SOCIAL_PROOF | 2,612,802 | 48,028 | 1.84% | $258,644 | 1,129 | $229.09 |
| DEMONSTRATION | 2,264,253 | 37,814 | 1.67% | $248,813 | 842 | $295.50 |

---

## Key Findings

### 1. TikTok has the lowest Trial CAC and the lowest CPAO — and the only LTV:CAC above 1.0x

TikTok delivered trial signups at $12 CAC and activated owners at $143 CPAO — the best efficiency on both metrics. META spent $59,974 (the highest single channel) but produced only 90 activated owners at a $666 CPAO — 4.7x more expensive than TikTok. Google Search sits between the two: $248 CPAO with a LTV:CAC of 0.96x (OBSERVE). The channel ranking by trial CAC and by CPAO is consistent — TikTok wins on both — but the absolute gap is large: TikTok's CPAO is 4.7x lower than META and 1.7x lower than Google Search, confirming that platform-reported trial signups significantly understate the quality differences between channels.

### 2. LinkedIn shows zero trial signups in platform data — no CPAO can be calculated

LinkedIn spent $80,164 over 12 weeks and registered 0 trial signups in fact_daily_performance. Its CPM ($122.54) and CPC ($17.44) are the highest of any channel. LinkedIn's attributed trial accounts exist only through first-party data (dim_trial_accounts has LinkedIn accounts), but the volume is too small to compute a reliable CPAO. LinkedIn spend appears misallocated to a brand-awareness motion without a conversion mechanism. **This is a descriptive observation, not a causal claim** — LinkedIn may be producing pipeline at a different funnel stage not captured here.

### 3. CONTRAST hook drives the lowest trial CAC; DEMONSTRATION drives the highest

CONTRAST creatives converted trials at $216.23 CAC — 37% cheaper than DEMONSTRATION ($295.50). FEAR_OF_MISSING_OUT achieved the highest CTR (2.40%) but did not produce the lowest CAC, indicating that top-of-funnel engagement and conversion intent are not tightly coupled. OUTCOME and CONTRAST hooks together account for the majority of trial volume (3,285 of 6,514 signups, 50.4%).

### 4. Creative fatigue is present: 16 of 90 creatives show >25% CTR decline from peak

Fatigue is most severe in three Google Search creatives (cr_google_026_001/002/003), each showing >91% CTR drop from their week-6 peak to week 12. A META creative (cr_meta_002_001) dropped 52.1% from a week-1 peak. TikTok's cr_tiktok_014_001 dropped 44.3% from its week-8 peak. Fatigue analysis is based solely on CTR trend — it is correlational, not causal; budget shifts, seasonality, and audience overlap could also explain CTR decline.

### 5. 2 creatives flagged as high-CTR / low-activation

Two creatives sit in the top quartile for CTR and the bottom quartile for activation rate (CAMPAIGN_LAUNCHED within 14 days). These creatives likely generate strong initial curiosity but fail to attract the subset of restaurant owners who complete setup and launch a marketing campaign. The most productive next investigation would be landing page alignment and onboarding flow by creative source.

---

## Data Quality Notes

| Check | Severity | Count | Note |
|-------|----------|-------|------|
| Missing attribution | WARNING | 152 (7.6%) | Channel unknown; all 152 map to NULL channel in dim_trial_accounts |
| Clicks > impressions | ERROR | 9 rows | Mathematically invalid; likely deduplication or reporting-window mismatch |
| LinkedIn trial signups | INFO | 0 | Intentional synthetic pattern — LinkedIn has no conversion path in this model |
| Negative spend / impressions | INFO | 0 | Clean |
| Duplicate account IDs | INFO | 0 | Clean |
| Orphaned product events | INFO | 0 | Full referential integrity |
| Zero spend with positive clicks | INFO | 0 | Clean |

The 7.6% missing attribution rate is a meaningful gap. If the missing 152 accounts skew toward any channel, blended CPAO figures understate or overstate individual channel efficiency.

---

## Limitations

1. **All data is synthetic.** Patterns were deliberately designed into the simulation (LinkedIn zero conversions, creative fatigue curves, missing attribution rate). Findings confirm the analysis pipeline detects what was planted — not real market dynamics.

2. **CPAO excludes missing-attribution accounts.** The 152 accounts with no channel assignment are excluded from the CPAO denominator. Including them at a blended rate would lower all channel CPAOs by roughly 7.6%.

3. **Activation window is 14 days from signup.** Owners who launched a campaign after day 14 are counted as non-activated. Extending the window would increase activation counts and lower CPAO across all channels.

4. **No revenue or LTV data is incorporated in this report.** CPAO measures funnel depth, not return on spend. A channel with higher CPAO but higher average LTV could still be the most efficient investment.

5. **Creative fatigue is measured by CTR only.** Spend shifts, audience refresh, and external seasonality were not controlled for. CTR decline should be validated against frequency and reach data before a creative is paused.

6. **LinkedIn CPAO cannot be computed** because fact_daily_performance records 0 trial signups for LinkedIn. First-party data (dim_trial_accounts) includes some LinkedIn-attributed accounts, but the counts are insufficient for a reliable metric.
