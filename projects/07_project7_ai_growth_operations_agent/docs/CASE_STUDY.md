# Tablr AI Growth Operations Agent — Case Study

**[SYNTHETIC DATA — Tablr portfolio simulation]**
*All numbers, companies, and user data are entirely simulated. No real Tablr product exists.*

---

## 1. Business Problem

Tablr is a fictional B2B SaaS product that helps independent restaurant owners run digital marketing campaigns. The growth team faces a compound problem common to early-stage B2B SaaS: trial-to-activation is low (26.0%), attribution gaps make channel efficiency opaque (7.6% missing), and creative fatigue is eroding paid media performance without a systematic early-warning system. Budget allocation decisions are being made on trial CAC — a proxy metric that masks downstream activation quality — rather than Cost per Activated Owner (CPAO), the true signal of acquired value.

The goal of this project was to design and simulate an AI growth operations agent that could: (1) identify the trial CAC / CPAO reversal story across channels, (2) detect creative fatigue before budget is wasted, (3) run A/B experiment governance with statistical guardrails, and (4) output auditable, human-approved recommendations — not autonomous budget changes.

---

## 2. Audience and Growth Hypotheses

Five ICPs were defined based on restaurant owner archetype:

- **scrappy_independent** — skeptical of new tools; responds to contrast/before-after messaging
- **growth_minded** — evidence-driven; responds to peer social proof
- **delivery_heavy** — operationally focused; high delivery platform dependency; LinkedIn addressable
- **multi_location** — scale-minded; highest monthly price tier; longest payback window
- **new_owner** — in early launch phase; needs fast wins; UGC-style content resonates

Channel strategy: TikTok and META for top-of-funnel volume (scrappy, growth-minded, new_owner), Google Search for high-intent capture (multi_location), LinkedIn for precision delivery-heavy targeting despite 3-4x higher CPM.

---

## 3. Measurement Strategy

**Why CPAO instead of trial CAC?**

Trial CAC measures spend per person who starts a trial. It is cheap to optimize: acquire curious browsers. CPAO (Cost per Activated Owner) measures spend per person who actually launched a Tablr marketing campaign within 14 days of signup. This is the true activation gate — an owner who never launches a campaign cannot convert to a paid subscription.

The critical discovery: META has a higher trial CAC ($52) than TikTok ($12), and an even larger CPAO gap ($666 vs $143). META was acquiring more expensive-to-click and harder-to-activate users. Optimizing on trial CAC alone would have continued spending on META — exactly the wrong decision.

Dashboard design: every page surfaces CPAO as the primary efficiency metric, with trial CAC as context only.

---

## 4. Creative Strategy

Sixteen creative briefs were developed across six hook type categories:

| Hook Type | Trial CAC (synthetic) | Rationale |
|---|---|---|
| CONTRAST | $216 | Before/after framing for skeptics |
| OUTCOME | $234 | Revenue result focus |
| SOCIAL_PROOF | $241 | Peer restaurant success |
| DEMONSTRATION | $258 | Dashboard setup walkthrough |
| FOMO | $271 | Competitor urgency |
| PROBLEM_AGITATE | $289 | Pain point amplification |

CONTRAST hooks consistently outperformed on trial CAC across channels, particularly for the scrappy_independent persona on META. This informed the exp_001 experiment design.

Fatigue detection: 16 out of 90 creatives (17.8%) showed >25% CTR drop from peak with at least 4 weeks of data. These were flagged for creative refresh rather than budget reallocation — the creative, not the channel, was the variable to fix.

---

## 5. Experiment Design

Four experiments were registered in `data/config/experiments.yaml`, each with a primary metric, guardrail metric, minimum trial threshold, and explicit arm design:

- **exp_001** (RUNNING): Hook type test on META — CONTRAST vs OUTCOME for scrappy_independent. Primary: activation_rate (MDE 3pp). Guardrail: M1 retention (MDE 5pp).
- **exp_002** (RUNNING): Messaging territory on META — SOCIAL_PROOF vs FOMO for growth_minded. Primary: activation_rate (MDE 2.5pp). Guardrail: CPAO (MDE $15).
- **exp_003** (RUNNING): Creative format on TikTok — UGC video vs static for new_owner. Primary: CTR (MDE 0.5pp). Guardrail: activation_rate (MDE 2pp). Note: the guardrail prevents optimizing for empty clicks — CTR improvement that doesn't activate owners is not progress.
- **exp_004** (EVALUATING): Channel test — LinkedIn job-title targeting vs META lookalike for delivery_heavy. Primary: CPAO (MDE $20). Guardrail: activation_rate.

Statistical methodology: two-sample z-test for proportions. 95% confidence threshold (|z| ≥ 1.96) AND practical significance (|abs_diff| ≥ MDE) both required before acting. Guardrail violations downgrade SCALE_CANDIDATE to HOLD automatically.

---

## 6. Simulated Findings — The META Reversal Story

The most compelling finding from 12 weeks of synthetic data was the inversion between trial CAC and CPAO across channels:

| Channel | Trial CAC | CPAO | LTV:CAC | Decision |
|---|---|---|---|---|
| TikTok | $12 | $143 | 2.03x | SCALE_CANDIDATE |
| Google Search | $21 | $248 | 0.96x | OBSERVE |
| META | $52 | $666 | 0.48x | HOLD |
| LinkedIn | — | No data | — | Insufficient Data |

META's trial CAC ($52) is 4.3x higher than TikTok ($12). A naive media buyer focused only on volume would continue spending on META, but CPAO reveals a larger gap: META activated owners at $666 per — 4.7x more expensive than TikTok's $143. At a 12.9% trial-to-subscription rate, each META subscription cost well above observed LTV.

TikTok's M6 retention of 37.5% further confirmed acquired quality: TikTok-sourced owners generated more revenue per cohort. The LTV:CAC ratio of 2.03x (vs META's 0.48x) far exceeded the SCALE_CANDIDATE threshold of 1.0x.

Result: At the $150K/month scenario (realistic for a Series A startup at ~$6M ARR), the budget allocator increased TikTok to 55.8% of spend ($75,363), while META was held at 12.0% ($16,182) pending the hook type experiment (exp_001) to isolate whether the problem is channel-structural or creative-solvable.

---

## 7. Architecture — Three-Layer Decision System

```
Layer 1: Analytics Engine (Python + DuckDB + Parquet)
  └── campaign_metrics.py, retention.py, ltv.py, cohorts.py,
      creative_intelligence.py, budget_allocator.py
  └── Computes all metrics from raw synthetic parquet files

Layer 2: Deterministic Policy Engine (policy.py)
  └── Pure rule-based: if ltv_cac >= 1.0 AND m6_mature → SCALE_CANDIDATE
  └── M1 retention guardrail, M6 maturity gate, trial floor
  └── No LLM — cannot be hallucinated into wrong decisions

Layer 3: LLM Analyst Layer (narrative_agent.py)
  └── Receives policy decision + evidence dict
  └── Writes narrative rationale, tradeoff, risk, next experiment hypothesis
  └── CANNOT change the recommendation state
  └── Output: channel_recommendations.json with immutable audit trail
```

The 3-layer design ensures that LLM reasoning is additive (narrative context) not substitutive (decision authority). Policy rules are transparent, auditable, and reproducible.

---

## 8. Safety and Governance

**RECOMMEND_ONLY=True** is enforced at every layer:

- Budget allocator returns `AllocationResult(recommend_only=True)` — no API call to ad platforms
- Policy engine writes to JSON — no campaign mutations
- Every state transition is logged to an immutable audit trail with actor, timestamp, and rationale
- The Streamlit dashboard shows review buttons (APPROVE / REJECT / REQUEST REVISION) in disabled state — display only
- The LLM agent's `recommend_only=True` flag is validated before output is surfaced

Audit trail entries distinguish between `policy_engine` actor (sets recommendation state) and `llm_agent` actor (writes narrative only, state unchanged). This provides a clear chain of custody.

---

## 9. Limitations

- All data is **synthetic** — generated by `scripts/generate_synthetic_data.py`. No real restaurant owners, campaigns, or revenue data.
- **12-week observation window** (Jan 5 – Mar 29, 2026) is too short for reliable M6 retention or projected LTV. March 2026 cohorts are not yet M6-mature.
- **No real API integrations** — no calls to Meta Ads API, TikTok for Business, Google Ads API, or AppStore Connect.
- **Constant churn assumption** in projected LTV is unrealistic; real churn is cohort-dependent and time-decaying.
- Attribution gaps (7.6% UNKNOWN, 152 accounts) are unresolved in this simulation. A real system would require server-side attribution or probabilistic matching.
- The LLM layer uses a mock analyst — real deployment would require prompt evaluation and output quality monitoring.

---

## 10. Next Experiment

Based on the findings, the highest-leverage next experiment is:

**Hypothesis:** A SOCIAL_PROOF hook featuring verified independent restaurant owners on TikTok (authentic UGC format) will improve 14-day activation rate by 15+ percentage points versus the current CONTRAST hook control, because TikTok's algorithm rewards platform-native content and the scrappy_independent persona responds to peer validation.

- **Variable tested:** hook_type (SOCIAL_PROOF vs CONTRAST)
- **Channel:** TikTok
- **Primary metric:** cpao_usd (LOWER_IS_BETTER, MDE $30)
- **Guardrail metric:** m1_retention_rate (HIGHER_IS_BETTER, threshold > 5pp degradation)
- **Minimum trials:** 300 per arm
- **Expected outcome:** If SOCIAL_PROOF wins, blended TikTok CPAO drops below $110, and LTV:CAC improves to ~2.5x — reinforcing SCALE_CANDIDATE with high confidence.
