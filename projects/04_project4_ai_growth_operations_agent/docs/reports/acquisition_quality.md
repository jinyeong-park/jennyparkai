# Acquisition Quality Report
**[SYNTHETIC DATA — Tablr portfolio simulation]**
**Period:** 2026-01-05 to 2026-03-29 | **Maturity reference:** 2026-09-13

---

## Activation Funnel

Over 12 acquisition weeks (W02–W13 2026), 2,000 trial signups entered the funnel.

| Metric | Count | Rate |
|---|---|---|
| Trial signups | 2,000 | — |
| Onboarding completed | ~826 | 41.3% |
| Campaign launched (≤14 days) | 519 | **26.0%** |
| Subscription started | 264 | 13.2% |

**Activation** is defined as launching a marketing campaign within 14 days of trial signup — the moment a restaurant owner reaches tangible product value. All 519 campaign launches qualify under this window. Activation-to-subscription conversion is ~50.9% (264 / 519), indicating that reaching the activation milestone is a strong predictor of conversion.

Weekly cohort activation rates are stable across the 12-week window (range: 23%–28%), with no material decay visible in the synthetic data. 11 of 12 cohort weeks are M6-mature as of the reference date.

---

## Retention by Channel

Retention is measured at the subscription level using three windows: M1 (30 days), M3 (90 days), M6 (180 days). M6 rates are reported only for subscriptions where `conversion_date + 180 ≤ 2026-09-13`. All M6 cohorts carry an immature warning because April–May 2026 conversions are not yet fully mature.

| Channel | Subscribers | M1 Rate | M3 Rate | M6 Rate (mature subs) | Warning |
|---|---|---|---|---|---|
| TIKTOK | ~60 | **79.9%** | **57.6%** | **37.5%** | Partial |
| GOOGLE_SEARCH | ~91 | 85.0% | 55.9% | 42.9% | Partial |
| META | ~86 | 82.5% | 55.0% | 45.0% | Partial |
| UNKNOWN | ~27 | 81.1% | 47.2% | 30.8% | Partial |

TIKTOK leads on all three retention windows despite the smallest subscriber count. UNKNOWN (missing-attribution accounts) shows the weakest M3 and M6 retention. Retention is monotonically declining across windows for all channels (M1 > M3 > M6), consistent with expected churn behavior.

---

## LTV:CAC Analysis

**Observed LTV** = sum of actual revenue events per subscriber account, averaged by channel.
**Projected LTV** = avg monthly price / estimated monthly churn rate (constant-churn assumption — simplified model).
**CPAO** = total paid spend / activated owners (campaign launched ≤14 days of trial).

| Channel | CPAO | Avg Monthly Price | Observed LTV | LTV:CAC (Obs) | Policy |
|---|---|---|---|---|---|
| TIKTOK | $143 | $182 | $291 | **2.03x** | SCALE_CANDIDATE |
| GOOGLE_SEARCH | $248 | $176 | $238 | 0.96x | OBSERVE |
| META | $666 | $172 | $318 | 0.48x | HOLD |
| UNKNOWN | — | $193 | — | — | — |

Observed LTV:CAC ratios below 1.0x reflect the 2–3 month revenue observation window — the data does not capture steady-state LTV. Projected LTV ratios remain below 1.0x, which is expected for a SaaS product in early cohort maturation. Payback periods assume constant churn; real payback improves as early-month churn falls.

---

## Key Insight: Ranking Reversal

**META's CPAO is 4.7x higher than TikTok's, despite receiving the most budget.**

META received $59,974 — the largest single channel allocation — but produced only 90 activated owners at a $666 CPAO. TikTok received $37,490 and produced 262 activated owners at $143 CPAO. META's trial CAC ($52) is also higher than TikTok's ($12), so the reversal story here is not trial CAC vs CPAO — it is the overall magnitude of META's inefficiency at every funnel stage.

TikTok's LTV:CAC of 2.03x is the only channel exceeding the 1.0x SCALE_CANDIDATE threshold. META's 0.48x falls below the 0.50x OBSERVE band, placing it squarely in HOLD. A decision based solely on channel familiarity or budget inertia would sustain META allocation; adding activation and LTV:CAC data shifts the picture decisively toward TikTok.

---

## Budget Recommendation Summary

For a $150,000/month budget (realistic for a Series A startup at ~$6M ARR) with 10% exploration reserve:

| Channel | Recommended | Pct | Expected Activated Owners |
|---|---|---|---|
| TIKTOK | $75,363 | 55.8% | 527 |
| GOOGLE_SEARCH | $43,455 | 32.2% | 175 |
| META | $16,182 | 12.0% | 24 |
| LINKEDIN (exploration) | $7,500 | 5.0% | — |
| UNKNOWN/Attribution fix | $7,500 | 5.0% | — |

TIKTOK receives the largest efficiency allocation due to its lowest CPAO ($143) and the only LTV:CAC above the 1.0x SCALE_CANDIDATE threshold. LINKEDIN is held at exploration with no performance history in the data. The 10% exploration reserve ($15,000) is split equally between LINKEDIN and the unattributed bucket, which represents a channel measurement problem, not a channel allocation decision.

---

## Limitations

- **Observed LTV covers only 2–3 months of revenue** (simulation runs Jan–Mar 2026; most revenue events are at month_num 0 and 1)
- **M6 rates for April–May 2026 cohorts are not yet mature** as of the reference date; all M6 rates are computed on a subset of subscribers
- **Projected LTV uses a constant-churn-rate model** — it does not account for early-period churn being higher than steady-state
- **CPAO is not a causal metric** — channels differ in audience composition, creative quality, and targeting; CPAO differences may reflect audience mix, not channel efficiency
- **Missing attribution (152 accounts / 7.6% of trials)** reduces the precision of channel-level comparisons; UNKNOWN shows the weakest retention, suggesting self-selection into organic/direct rather than a channel quality issue
- **Synthetic data was designed to show these patterns**; real data will show messier signals with higher variance and less clean ranking differentials
