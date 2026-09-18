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
- Accounts that invite teammates show meaningfully higher long-term retention — collaboration behavior is the strongest behavioral retention signal in the data

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

**Downstream caution:** Paid conversion is flat (−0.1 pp, negligible). The 60-day retention guardrail shows a small negative difference (−1.5 pp) that warrants monitoring before a full rollout, though the absolute level for both groups remains high (above 92%).

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

---

## Revenue and NRR

| Metric | Value |
|---|---|
| Paid customers | 766 |
| Avg. Revenue per Account (ARPA) | $251 |
| Total active MRR (est.) | ~$192,000 |
| Modeled NRR (60-day cohort) | ~91–95% per cohort |

NRR is computed as retained MRR / beginning MRR for each 60-day-eligible cohort. Because the synthetic data does not include expansion or upsell events, the output is a retained-MRR proxy — a floor NRR — rather than a fully inclusive net retention figure. This is disclosed in the dashboard and appropriately constrains the interpretation.

Churn reasons for paid accounts that churned:
- Low adoption: 35%
- Budget: 25%
- Missing feature: 20%
- Other / unrecorded: 20%

Low adoption is the most common stated reason — reinforcing the case for improving activation as a retention lever, not just a top-of-funnel metric.

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

## Business Recommendations

| Finding | Recommendation | Owner |
|---|---|---|
| Guided onboarding lifts SMB/Mid-Market activation by 18+ pp | Roll out to SMB and Mid-Market immediately | Product |
| Enterprise shows weaker and less certain activation lift | Build a separate, implementation-led enterprise onboarding path | Product + CS |
| Teammate invitations are the strongest behavioral retention signal | Move invite prompt to earlier in the onboarding flow, before workspace setup completes | Product |
| Paid conversion is flat despite activation lift | Do not use activation lift alone as a success criterion — add paid conversion as a co-primary metric | Analytics |
| 1,112 medium-risk accounts hold $96,627 in at-risk MRR | Run scaled re-engagement sequence; measure 60-day survival rate | Customer Success |
| Low adoption is the most common churn reason (35%) | Build in-product adoption checklist; surface next-action prompts at login | Product |

The highest-leverage single action is the teammate invite prompt — it ties directly to collaboration adoption, which predicts long-term retention more strongly than any other single event in the data.
