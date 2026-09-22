# Analysis Findings

## Lifecycle Funnel

The acquisition-to-retention funnel across 2,500 accounts exposes two primary leakage points:

| Stage | Accounts | Rate |
|---|---|---|
| Signups | 2,500 | 100% |
| Workspace Created | 1,615 | 65% |
| Activated | 1,106 | 44% |
| Trial Started | 738 | 30% |
| Paid Customers | 766 | 31% |
| Retained 60D | ~716 | ~93.5% of eligible |

**Key observation:** 35% of signups never create a workspace. Among accounts that do create a workspace, 68% go on to activate. The largest volume drop happens at the very first onboarding step — workspace creation — making it the highest-leverage stage for product improvement.

The gap between Trial Started (738) and Paid Customers (766) reflects accounts that converted directly to paid without a trial record, consistent with enterprise and direct-purchase paths in the subscription model.

### Funnel by acquisition channel — step-to-step drill-down

The overall funnel above hides which step each channel leaks at. Segmenting by `acquisition_source` and conditioning each rate on the prior step (workspace → integration, not total signups) surfaces two different failure patterns (see `funnel_by_channel` in `app/utils/metrics.py`, mirrored in `sql/marts/mart_funnel.sql`):

| Channel | Signups | Workspace rate | Workspace→Integration | Activation rate | Activated→Paid |
|---|---|---|---|---|---|
| Organic Search | 595 | 65.7% | 39.6% | 46.6% | 41.2% |
| Product-Led | 484 | 65.3% | 40.5% | 45.7% | 35.3% |
| Paid Search | 442 | 64.3% | 34.5% | 41.9% | 40.5% |
| Referral | 371 | 61.5% | 32.5% | 40.4% | 36.0% |
| Content | 353 | 65.4% | 33.8% | 43.1% | **44.1%** |
| Partner | 255 | 64.7% | **41.8%** | **47.5%** | 39.7% |

**Diagnosis — two distinct problems, not one:**
- **Content is a UX-friction problem, not an intent problem.** Its workspace creation rate (65.4%) is essentially tied with the best channel, but workspace→integration carry-through (33.8%) is second-lowest — yet accounts from Content that do activate convert to paid at the *highest* rate of any channel (44.1%). The people are qualified; the integration step is where they get stuck. Fix: reduce integration friction for this channel (better docs, guided setup), not cut its acquisition spend.
- **Product-Led is the opposite pattern — an activation-without-monetization problem.** It has the second-highest activation rate (45.7%) but the *lowest* activated→paid rate (35.3%) of any channel. Self-serve signups activate easily but don't convert to paid as readily — activation rate alone overstates this channel's health. This echoes the broader finding below that activation lift and paid conversion must be tracked as co-primary metrics, not a single funnel number.
- **Referral is weak end-to-end** (lowest workspace rate, lowest workspace→integration, lowest activation rate) rather than bottlenecked at one step — consistent with lower-intent traffic rather than a fixable UX gap.

**Interview framing:** overall rate tells you *who* is underperforming; step-to-step tells you *where*; the activated→paid comparison tells you *why* — separating a product/UX fix (Content) from an acquisition-quality issue (Referral) from a monetization gap (Product-Led) changes who owns the fix.

---

## Activation Analysis

Activation is defined as: workspace creation + at least one qualifying key action within 7 days of signup.

Key actions: `teammate_invited`, `integration_connected`, `project_created`

Findings:
- **Overall activation rate:** 44.2%
- **Median time to activate:** 4.4 days (signup → first key action)
- **Daily active usage:** 3.8% of accounts active within last 30 days
- **60-day retention for paid accounts:** 93.5%

Activation rate by segment:
- SMB accounts show the highest activation sensitivity to the guided onboarding experiment
- Enterprise accounts activate at a lower baseline rate and show weaker response to onboarding interventions

### Which first action predicts retention best? (milestone drill-down)

*Correction: an earlier version of this doc claimed teammate invitations were "the strongest behavioral retention signal in the data." That claim was never actually tested against the data — direct testing below does not support it, so it's replaced here rather than repeated.*

Grouping accounts by whichever key action they completed **first** (not just whether they eventually did it) and comparing 60-day retention among mature, ever-paid accounts (`retention_rate()` in `app/utils/metrics.py`, mirrored in `sql/marts/mart_activation.sql`):

| First action | Accounts | Paid conversion | 60-day retention (eligible accounts) |
|---|---|---|---|
| integration_connected | 567 | 38.1% | **95.4%** |
| teammate_invited | 1,099 | 39.7% | 93.6% |
| project_created | 543 | 38.1% | 91.8% |

**Two things worth noting:**
1. `integration_connected` edges out the other two as a first-action signal, but the spread is only 3.6 percentage points on a ~93.5% base retention rate for paid accounts overall — this is a modest signal, not a dramatic one. It doesn't support a strong "prioritize X over Y" product recommendation on its own.
2. Testing the *simpler* claim — "does an account that ever invites a teammate (regardless of order) retain better than one that never does?" — shows **no difference at all**: 93.5% retention for accounts that ever invited a teammate vs. 93.5% for those that never did. The "collaboration drives retention" story does not hold up in this dataset; it looked plausible from the product events available but doesn't survive being checked.

**Interview framing:** always test a claim against the actual numbers before writing it into a findings doc — an intuitive story ("collaboration predicts retention") can fail to replicate even when it sounds right, and the milestone comparison above and the ever-invited comparison would have caught this before it reached a stakeholder deck.

### Time-to-activate: P50/P90, not the mean

Median (P50) days from signup to first key action is 6.3–7.4 days depending on signup month, with no sustained improvement or regression across the observed period — onboarding speed has been stable, consistent with this being a deterministic synthetic dataset rather than a live product with real interventions. P90 is far more volatile (48–69 days), reflecting a long tail of accounts that eventually take a key action months after signup — this is exactly why P50/P90 is used instead of the mean, which a single 90-day outlier would otherwise distort.

### Activation speed by company size

| Segment | Signups | Activation rate | P50 days to first action | P90 days |
|---|---|---|---|---|
| SMB | 1,481 | 49.3% | 6.3 | 58.7 |
| Mid-Market | 719 | 40.1% | 6.8 | 64.7 |
| Enterprise | 300 | 29.3% | **12.6** | 70.9 |

Enterprise doesn't just activate least often (29.3% vs. 49.3% for SMB) — accounts that do activate take roughly **twice as long** to get there (12.6 days P50 vs. ~6.5 days for SMB/Mid-Market). This is a new, quantified layer on top of the existing "Enterprise activates at a lower baseline rate" finding: Enterprise is not just a lower-conversion segment, it's a slower one, which supports the existing recommendation for a separate, implementation-led Enterprise onboarding path rather than just tuning the self-serve flow.

---

## Experiment Readout

**Experiment:** `onboarding_guided_v1` — guided workspace setup flow vs. existing onboarding

**Primary metric:** Account activation within 7 days of signup

| Metric | Control | Variant | Difference |
|---|---|---|---|
| Accounts | 1,212 | 1,288 | — |
| Activation rate | 34.7% | 53.3% | **+18.6 pp** |
| Paid conversion | 38.8% | 38.7% | −0.1 pp |
| 60D retention | 94.3% | 92.8% | −1.5 pp |
| p-value (z-test) | — | — | < 0.001 |

**Primary finding:** The guided onboarding flow produces a large, statistically significant activation lift (+18.6 percentage points). The result is robust: the two-proportion z-test p-value rounds to 0.0000 at four decimal places.

**Downstream caution:** Paid conversion is flat (−0.1 pp, negligible). The 60-day retention guardrail shows a small negative difference (−1.5 pp), though the absolute level for both groups remains high (above 92%).

### Formal decision: is the -1.5pp retention dip a real guardrail break, or noise?

Testing the retention guardrail with its own two-proportion z-test (`experiment_decision()` in `app/utils/metrics.py`, mirrored in `sql/marts/mart_experiment.sql`) — not just eyeballing the sign of the difference — the -1.5pp difference is **not statistically significant** (z ≈ -0.93, p ≈ 0.35), on a smaller eligible sample than the primary metric (470 control / 499 treatment accounts old enough to have reached the 60-day horizon). A fixed "any negative delta blocks shipping" rule would have flagged this as broken; testing it properly shows it's within the range of ordinary sampling noise.

**Sample-size check:** for a pre-specified 5pp minimum detectable effect (this project's standing convention — see `docs/process/03_experiment_readout.md`), the required sample is ~1,468 per variant; this experiment ran with 1,212 control / 1,288 treatment, technically under that bar. It reached significance anyway because the true effect (+18.6pp) is far larger than the 5pp MDE the experiment was sized around — a smaller true effect could plausibly have gone undetected at this sample size, but that risk didn't materialize here.

**Formal verdict: SHIP.** Primary lift is significant (p < 0.001), neither guardrail is significantly degraded, and the effect direction is consistent across segments (see below) — all three of `experiment_decision()`'s checks pass.

**Segment-level heterogeneity:**
- SMB and Mid-Market show the largest activation lifts from guided onboarding
- Enterprise shows a smaller, less certain lift
- This heterogeneity motivates a constrained rollout rather than a uniform one

**Rollout recommendation:** Deploy guided onboarding to SMB and Mid-Market segments immediately. Keep Enterprise in a separate path and continue monitoring 60-day paid retention before extending the experiment.

---

## Retention and Cohort Analysis

Retention is measured at 30, 60, and 90 days for accounts whose paid conversion date has reached each horizon as of the observation date.

| Horizon | Retention Rate |
|---|---|
| 30-Day | 100.0% |
| 60-Day | 93.5% |
| 90-Day | 87.4% |

The 30-day rate of 100% reflects the early stage of the cohort — most paid accounts in this synthetic dataset converted recently, and none have reached a 30-day churn event yet. The 60- and 90-day figures are more meaningful for planning purposes.

Cohort retention curves (by signup month) show consistent patterns across cohorts rather than a deteriorating trend, suggesting the activation and subscription mechanics are stable in the data.

### Product engagement retention — a different question than paid retention

The retention above is **logo/paid retention**: of accounts that converted to paid, is the subscription still active? It says nothing about the ~56% of signups that never convert to paid at all (see Lifecycle Funnel). A separate cut — **product engagement retention** — asks whether an account had *any* product event 30/60/90 days after signup, across every signup regardless of paid status (`engagement_retention_curve()` in `app/utils/metrics.py`, mirrored in `sql/marts/mart_engagement_retention.sql`; day 0 excluded since signup-day activity is onboarding, not a return visit):

| Horizon | Engagement retention (all signups) | Paid retention (paid accounts only) |
|---|---|---|
| 30-Day | 87.7% | 100.0% |
| 60-Day | 51.4% | 93.5% |
| 90-Day | 52.4% | 87.4% |

**This is not a data quality problem — it's two different denominators answering two different questions**, and the gap is the finding: roughly half of all signups have gone quiet on the product by day 60, while the much smaller population that actually pays stays highly retained (93.5%). Subscription-status monitoring alone would never surface this — it only ever looks at the ~44% of signups that activated and the smaller subset that paid. Two more things worth noting:
- Engagement retention is essentially flat from D60 (51.4%) to D90 (52.4%) rather than continuing to decay — whoever is still around at day 60 tends to still be around at day 90. The steep drop happens earlier, between D30 and D60.
- This reframes the funnel/activation findings above: activation rate (44%) already told us most signups don't reach early product value, and this shows that a further, larger group disengages from the product entirely well before — or regardless of — ever becoming a paying customer.

---

## Revenue and NRR

| Metric | Value |
|---|---|
| Paid customers | 766 |
| Avg. Revenue per Account (ARPA) | $251 |
| Total active MRR (est.) | ~$192,000 |
| Modeled NRR (60-day cohort) | ~91–95% per cohort |

NRR is computed as retained MRR / beginning MRR for each 60-day-eligible cohort. Because the synthetic data does not include expansion or upsell events, the output is a retained-MRR proxy — a floor NRR — rather than a fully inclusive net retention figure. This is disclosed in the dashboard and appropriately constrains the interpretation.

Churn reasons for the 203 paid accounts that churned (recomputed from `subscriptions.churn_reason`; an earlier version listed 35/25/20/20, which did not match the data):
- Low adoption: 38.4% (78)
- Missing feature: 20.2% (41)
- Budget: 19.7% (40)
- Unrecorded: 21.7% (44)

Low adoption is the most common stated reason, ahead of budget and missing feature, reinforcing the case for improving activation as a retention lever, not just a top-of-funnel metric.

### Channel LTV — what the data supports and what it doesn't

`channel_ltv()` in `app/utils/metrics.py` (shown on the Revenue page; `sql/marts/mart_revenue.sql` mirrors it) computes LTV from observed paid subscriptions.

| Channel | Paid accounts | ARPA | Monthly churn | 24-mo LTV | 95% interval |
|---|---|---|---|---|---|
| Referral | 130 | $292 | 2.67% | $5,221 | $4,115-6,463 |
| Content | 146 | $279 | 2.95% | $4,843 | $3,882-5,782 |
| Partner | 96 | $269 | 2.94% | $4,682 | $3,704-5,698 |
| Organic Search | 246 | $239 | 2.37% | $4,421 | $3,803-5,118 |
| Product-Led | 190 | $233 | 2.83% | $4,106 | $3,388-4,853 |
| Paid Search | 161 | $222 | 2.73% | $3,950 | $3,234-4,704 |

- **Overall:** monthly churn is ~2.7% (203 churn events over ~7,500 account-months), so uncapped LTV is ~$9,300 and 24-month LTV is ~$4,500. Treating the cumulative churned share (21%) as monthly churn, as an earlier draft did, gives ~$1,200, about 8x too low.
- **Channels cannot be ranked.** Monthly churn is 2.4-3.0% in every channel; the spread in LTV comes mostly from ARPA. Resampling accounts (ARPA and churn together), all six intervals share a common range. Paid Search is lowest and Referral highest by point estimate, but that ordering is well within sampling noise, and nobody should reallocate budget on it.
- **Uncapped LTV extrapolates.** It implies 34-42 month lifetimes; the longest observed subscription is ~15 months. Prefer the capped figure. Churn is also not constant: all of it occurs in months 2-4 after paying and none after that (see Engagement and Churn below), so the constant-churn capped figure understates 24-month LTV by about 9%.
- **CAC and LTV:CAC are not computable** (no spend data). Time-to-paid is not a substitute: the median is 19-20 days for every channel. At a 3:1 target the ceilings are `max_cac` = capped LTV / 3, roughly $1,300-1,750 per paid account.

An earlier study-note claim that "paid_search converts well to paid but has the worst LTV" isn't supported either: Paid Search is mid-pack on activated-to-paid (40.5%) and its LTV is not distinguishable from the other channels.

---

## Churn Risk

Rules-based risk scoring uses four transparent signals:
1. Subscription status (churned or no subscription: +55 / +30)
2. No 7-day activation (+20)
3. Failed 60-day retention for eligible accounts (+15)
4. Days since last product event: 31–90 days (+10), 90+ days (+20)

| Segment | Accounts | Share | MRR Exposure | Avg Score |
|---|---|---|---|---|
| High | 620 | 24.8% | $0 | 76 |
| Medium | 1,112 | 44.5% | $96,627 | 44 |
| Low | 768 | 30.7% | $95,707 | 20 |

High-risk accounts carry $0 MRR because they are either churned or never converted to paid. Medium-risk accounts represent the most actionable intervention target: $96,627 in active MRR with deteriorating engagement signals that have not yet resolved into churn.

**CS action framework:**
- High risk: Proactive save play — confirm business value, address activation gap, executive check-in for paid accounts
- Medium risk: Scaled re-engagement — use-case reminder, training offer, product-adoption review
- Low risk: Lifecycle education, identify expansion signals, no immediate retention intervention needed

---

## Engagement and Churn

**About this dataset.** The core tables are synthetic and, by construction, churn in them is an independent random draw (22% of paying accounts, 30-120 days after paying) unrelated to activity, plan, size or channel; the event log holds only onboarding events. So where this section says something "does not predict churn", or that churn "falls in months 2-4", those are properties of how the data was generated, not discoveries about customers. What they demonstrate is the method: the tests that separate a real signal from tenure confounding and circular validation. (The same applies to the churn-reason mix, which the generator draws independently of everything else.) A separate, deliberately planted usage table is used below as a positive control.

### What the event data can and can't support

The event log has 5 onboarding event types and ~5 events per account (at most 13 active days in an account's whole life; nothing later than ~day 122 after signup). Only ~80 of 2,500 accounts have any event in the last 28 days of the data. So the usual engagement tiers (power = 10+ active days in the last 28, 4+ event types) are unreachable, and "recency" mostly measures how long ago an account signed up. The tiers can be *computed*, but they measure onboarding tenure, not ongoing usage; real product telemetry (API calls, sessions) would be needed.

### When churn happens

Churn is not constant over an account's life (`paid_survival_curve()` in `app/utils/metrics.py`; Churn Risk page):

| Month since paid start | Accounts at risk | Churned | Monthly hazard |
|---|---|---|---|
| 1 | 969 | 4 | 0.4% |
| 2 | 965 | 60 | 6.2% |
| 3 | 905 | 60 | 6.6% |
| 4 | 794 | 79 | 9.9% |
| 5-14 | 651 → 64 | 0 | 0.0% |

All 203 churn events fall between day 30 and day 120 after an account starts paying; survival plateaus at 78.5% and no account that got past month 4 has churned in the ~15 months observed. That is a synthetic-data property, but it is what the data says, and it means:
- **The constant-churn assumption behind `LTV = ARPA / churn` is wrong here.** A constant 2.7%/month implies 48% cumulative churn by month 24; the data shows 21% and flat. Using the Kaplan-Meier survival curve, expected paid months in the first 24 are 19.5 vs. 17.8 under constant churn, so the 24-month LTV is ~$4,890 rather than ~$4,480 (about 9% higher). The channel comparison is unaffected (same method, same conclusion: not separable), but the "implied lifetime of 34-42 months" is an artifact of averaging front-loaded churn over long-lived, never-churning exposure.
- **The actionable window is early.** Only **51 currently-paying accounts ($12,899, 6.7% of MRR)** are still inside their first four paying months; everyone else is past the point where churn occurs in this data.

### Does engagement predict churn?

Not in this data. The naive test, comparing a tier's churn as of today with today's churn status, is circular (a churned account has already stopped using the product) and confounded by tenure. A prospective test (`prospective_engagement_dataset()`) uses only events before a month-end cutoff and asks whether the account churns in the next 90 days, for accounts paying at the cutoff (4,575 account-cutoffs, 7.7% churn):

| Tenure at cutoff | Active in prior 28 days: No | Yes |
|---|---|---|
| <=60 days | 17.3% | 17.1% |
| 61-120 days | 12.0% | 13.8% |
| 121-240 days | 0.5% | 2.6% |
| 240+ days | 0.0% | n/a |
| **Unadjusted** | **4.7%** | **14.0%** |

Unadjusted, recently-active accounts churn three times as often, which is backwards; it is tenure (new accounts are both still onboarding, so "active", and inside the window where churn happens). Within a tenure band the difference is small and not in a consistent direction. Depth and activation don't separate churners either: among the 969 paying accounts, churn is 22.9% for activated vs. 19.3% for not (p = 0.17), 22.3% vs. 19.9% for 4+ vs. fewer event types (p = 0.37), and 21.5% vs. 20.7% for 7+ vs. fewer events (p = 0.76). So the "low adoption" churn reason (38% of stated reasons) can't be corroborated from behavior in this dataset.

### Positive control: does the method find a signal that is really there?

`usage_weekly.csv` is generated separately (the five core CSVs are unchanged, verified by test) with a planted signal: usage is lower for eventual churners and declines over the 3-6 weeks before churn; acquisition channel has no effect. Tiers come from weekly usage (`usage_engagement_features()` / `assign_engagement_tiers()`), validated prospectively as before (`prospective_usage_dataset()`; weekly cutoffs, paying accounts only, 955 distinct accounts, 27,686 account-week observations at a 30-day horizon):

| Tier | Observations | 30-day churn | Lift vs. overall (2.8%) |
|---|---|---|---|
| power | 4,493 | 0.5% | 0.2x |
| active | 22,948 | 3.0% | 1.1x |
| at_risk | 245 | 18.0% | 6.5x |

- **It finds the planted signal, and not just tenure.** Within tenure bands at-risk still churns at 42.9% (<60 days), 29.9% (60-120), 7.0% (120-240) vs. 4.8% / 7.8% / 0.9% for active.
- **The horizon has to match the warning's lead time.** A decline in usage is a short-lead signal, so at-risk lift falls from 6.5x (30 days) to 3.6x (60) to 2.7x (90) and the AUC of the usage trend from 0.65 to 0.56 to 0.51, while the usage *level* holds up (AUC 0.70 / 0.68 / 0.67). The earlier 90-day, monthly-cutoff test on this data was too coarse to see it.
- **The negative control stays quiet.** No channel effect was planted, and 30-day churn by channel ranges only 2.5% to 3.1%.
- **What it does and doesn't prove.** The method works when a signal exists and doesn't invent one when it doesn't. It does not show that real customers' usage predicts churn: the signal here was put there.

### The existing risk score

The rules-based churn-risk score (Churn Risk section) adds points for already having churned (+55) or having no subscription (+30), so its High segment is largely defined by the outcome it's supposed to warn about, and "days since last event" inherits the tenure confound above. It works as a prioritization list of accounts that need attention today, not as an early-warning model, and it hasn't been validated prospectively.

---

## Root Cause Analysis

*Correction: an earlier version of this section walked through "activation dropped 4pp from week 8 to week 9" with a −5.2pp rate effect and +1.2pp mix effect. Those figures were never computed from this dataset and don't reproduce: the data's ninth consecutive weekly cohort is −18.9pp vs. the eighth, and weekly swings across the year run from about −20pp to +20pp, so no single "−4pp" story can be pinned on the weekly series. Replaced below with a real, computed case.*

### Case: September → October 2025 activation drop

**Symptom:** the 7-day activation rate for accounts signing up in October 2025 was **34.0%**, down from **44.7%** in September (−10.7pp) — the largest month-over-month drop in the data (`mix_rate_decomposition()` in `app/utils/metrics.py`; mirrored in `sql/marts/mart_root_cause.sql`).

**Decomposition** (exact: rate + mix + interaction = observed change, by acquisition source):

| Component | Value | Interpretation |
|---|---|---|
| Rate effect | −10.9pp | Activation fell *within* channels |
| Mix effect | −0.2pp | Signup mix barely shifted |
| Interaction | +0.5pp | Negligible |
| **Net change** | **−10.7pp** | Rate-driven, not an acquisition shift |

Cutting by company size gives the same answer (rate −9.7pp, mix −0.4pp, interaction −0.6pp). The drop is broad rather than concentrated: Paid Search (54.1% → 27.6%) and Organic Search (53.1% → 34.0%) contribute most, and Enterprise fell furthest by size (46.2% → 14.8%, on only 26/27 accounts). Every channel except Referral (29.0% → 35.5%) moved down.

**Diagnosis:** rate-driven → not explained by *who* signed up, so the "acquisition sent lower-quality traffic" explanation is ruled out and any real cause sits in the product/onboarding experience that month.

**But: is the drop itself real?** The decomposition says where a change came from, not whether it was real, so that has to be checked first, and here it's shaky:
- Sep vs. Oct on a two-proportion test gives p = 0.027 — but this is the *largest* of 11 month-over-month comparisons, so the multiple-comparisons bar from the Bonferroni analysis applies (p < 0.05/11 ≈ 0.0045). It doesn't clear that bar.
- November rebounded to 44.5% — back to September's level — which is what noise looks like, and not what a persistent product regression looks like.

**Conclusion:** the direction of the diagnosis (rate, not mix) is well supported, but the evidence that October was a genuine regression rather than a bad-luck month is weak. The right next step is *not* an engineering escalation on this evidence alone; it's to check for an October deploy/onboarding change, and to see whether the dip recurs. If there's no deploy to point at, treat it as noise.

**Also worth knowing:** at a *weekly* grain this analysis is mostly noise — weekly cohorts are ~40–50 accounts, so weekly activation swings 10–20pp on sampling variation alone (and the final week in the data is partial, n=19). A monthly grain is used here for that reason.

**Key principle:** Always decompose before escalating (a mix-driven drop goes to the acquisition team; a rate-driven drop goes to product/engineering) — and test that the change is real before decomposing it.

---

## Business Recommendations

| Finding | Recommendation | Owner |
|---|---|---|
| Guided onboarding lifts SMB/Mid-Market activation by 18+ pp | Roll out to SMB and Mid-Market immediately | Product |
| Enterprise shows weaker and less certain activation lift | Build a separate, implementation-led enterprise onboarding path | Product + CS |
| Paid conversion is flat despite activation lift | Do not use activation lift alone as a success criterion — add paid conversion as a co-primary metric | Analytics |
| Content channel: strong start, weak integration step, best paid conversion once activated | Prioritize integration-step UX fixes (docs, guided setup) for Content-sourced traffic — do not cut spend | Product + Growth |
| Product-Led channel: highest activation rate but lowest activated→paid rate | Investigate self-serve paid-conversion prompts; activation is not the bottleneck for this channel | Growth + Sales |
| Enterprise takes ~2x longer to activate (12.6d P50) on top of a lower activation rate | Prioritize the implementation-led Enterprise onboarding path on speed, not just conversion rate | Product + CS |
| `integration_connected` is the strongest first-action retention signal, but only by 3.6pp over the alternatives — not a large enough gap to justify re-ordering onboarding around it | Do not build a product change on this alone; monitor as a secondary signal only | Analytics |
| 1,112 medium-risk accounts hold $96,627 in at-risk MRR | Run scaled re-engagement sequence; measure 60-day survival rate | Customer Success |
| Low adoption is the most common churn reason (38%) | Build in-product adoption checklist; surface next-action prompts at login | Product |
| Channel LTV spread (24-mo $4.0-5.2K) is within sampling noise; monthly churn is 2.4-3.0% in every channel | Don't shift budget between channels on LTV rank; obtain real spend data so CAC and payback can be computed, and use `max_cac` (~$1.3-1.75K at 3:1) as the ceiling to compare it against | Growth + Finance |
| All churn occurs in months 2-4 after an account starts paying; activation, depth and recent activity don't separate churners once tenure is controlled | Aim customer-success outreach at the first 120 days after conversion (currently 51 accounts, $12.9K MRR) rather than at engagement tiers; don't build tier-based churn alerts on this event data; instrument real usage (API calls, sessions) first | Customer Success + Analytics |
| Engagement retention (all signups) drops to 51% by D60 while paid retention stays at 93.5% — subscription monitoring alone misses this | Track D30/D60/D90 product engagement retention as a standing metric alongside paid retention, not just at paid accounts | Analytics + Product |

The highest-leverage actions are the two with quantified, multi-point evidence behind them: the guided-onboarding rollout to SMB/Mid-Market (+18.6pp activation, statistically significant) and a speed-focused Enterprise onboarding path (Enterprise activates least often *and* takes ~2x longer). The activation-milestone signal is real but small (3.6pp spread) and shouldn't be over-weighted relative to these.
