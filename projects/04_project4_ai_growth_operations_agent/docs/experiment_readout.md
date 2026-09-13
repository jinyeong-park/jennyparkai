# Experiment Readout: exp_001

> **[SYNTHETIC]** — All figures below are simulated for portfolio purposes.
> No real user or campaign data is referenced. DRY_RUN=true, RECOMMEND_ONLY=true.

---

## Experiment Summary

| Field | Value |
|-------|-------|
| **Experiment ID** | exp_001 |
| **Name** | Hook Type: Contrast vs Outcome — META, scrappy_independent |
| **State** | RUNNING |
| **Variable Tested** | hook_type |
| **Primary Metric** | activation_rate (HIGHER_IS_BETTER) |
| **MDE** | 0.03 (3 percentage points) |
| **Evaluation Window** | 14 days |
| **Minimum Trials / Arm** | 200 |
| **Start Date** | 2026-01-12 |
| **Data Origin** | SYNTHETIC |

## Hypothesis

> A contrast hook (before/after framing) will drive higher activation rate than an outcome hook for scrappy independent owners who are skeptical of new tools.

---

## Arm Results

| Arm | Type | Trials | Activations | Activation Rate | Spend (USD) | CPAO |
|-----|------|--------|-------------|-----------------|-------------|------|
| exp_001_ctrl — Outcome hook | Control | 284 | 64 | 22.5% | $4,260 | $66.56 |
| exp_001_trt — Contrast hook | Treatment | 271 | 76 | 28.0% | $4,065 | $53.49 |

---

## Statistical Comparison

| Metric | Value |
|--------|-------|
| Absolute difference (treatment − control) | +5.5 pp |
| Relative difference | +24.4% |
| Pooled p | 0.252 |
| z-score | 2.41 |
| Statistically significant (95% CI)? | **Yes** (|z| = 2.41 ≥ 1.96) |
| Practically significant (≥ MDE 3 pp)? | **Yes** (5.5 pp ≥ 3 pp) |

---

## Guardrail Check: m1_retention_rate

| Arm | M1 Retention Rate |
|-----|-------------------|
| Control | 61.0% |
| Treatment | 63.5% |
| Relative difference | +4.1% |
| Guardrail threshold | >-5% relative |
| Guardrail damaged? | **No** |

The contrast hook treatment does not damage M1 retention. Owners who activate through the contrast hook retain at a slightly higher rate in the first month, consistent with the hypothesis that skeptics who convert on a more honest framing are higher-quality activations.

---

## Recommendation

**SCALE_CANDIDATE**

The contrast hook (before/after framing) shows a statistically significant and practically significant improvement in activation rate for the scrappy_independent persona on META. The treatment outperforms the control by 5.5 percentage points (relative: +24.4%) with a z-score of 2.41. The guardrail metric (M1 retention) is unharmed. CPAO improves from $66.56 to $53.49 — a $13 reduction per activated owner.

**Recommended next step:** Shift 70% of scrappy_independent META budget to contrast hook creative while opening a follow-on experiment to test contrast hook variants (problem framing vs. transformation narrative).

---

## Notes

- Both arms reached the minimum trial threshold (200) before this readout.
- The 14-day evaluation window has elapsed from the start date.
- Activation is defined as launching a marketing campaign within 14 days of trial signup.
- All figures are synthetic and generated for portfolio demonstration purposes.
- This readout was produced by the ExperimentEvaluator in RECOMMEND_ONLY mode.
