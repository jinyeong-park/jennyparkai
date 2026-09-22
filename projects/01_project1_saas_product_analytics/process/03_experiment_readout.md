# Experiment Readout Process

## Experiment Types

This project covers two experiment structures:

**A/B (Two-Variant)** — `mart_experiment.sql`
Compares a single treatment against control. Uses two-proportion z-test. Applied to the guided onboarding experiment.

**Multivariate (A/B/C/D)** — `mart_multivariate.sql`
Compares multiple treatment variants simultaneously against a single control. Requires Bonferroni correction (or FDR adjustment) for multiple comparisons. Applied when testing multiple onboarding formats in parallel (checklist vs. video walkthrough vs. interactive demo).

## A/B Experiment: Decision Context

The guided onboarding experiment compares the existing onboarding flow with a guided experience that emphasizes workspace setup and early value-driving actions.

### Evaluation Sequence

1. Confirm randomization at the organization level and compare control versus treatment populations.
2. Measure the primary outcome: account activation within seven days.
3. Check downstream guardrail metrics: paid conversion and 60-day retention.
4. Segment results by company size (HTE analysis) to distinguish SMB, mid-market, and enterprise response.
5. Use the revenue impact model to translate activation lift into estimated incremental MRR.
6. Make a constrained rollout decision and continue measuring 60-day retention.

### Statistical Test

Two-proportion z-test (computed fully in SQL — `mart_experiment.sql`):

```
z = (p_treatment - p_control) / sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
```

Decision threshold: |z| ≥ 1.96 → p < 0.05 (two-tailed).

## Multivariate Experiment: Decision Context

When testing multiple onboarding formats simultaneously, pairwise z-tests against control create a multiple comparisons problem — running 3 tests at α=0.05 inflates the family-wise error rate to ~14%.

Implemented in `sql/marts/mart_multivariate.sql` and `bonferroni_pairwise_results()` / `simulate_multivariate_variants()` in `app/utils/metrics.py` (surfaced on the Experiments dashboard page). This project's real experiment data only has two arms, so the 3-variant split used there is a stable-hash simulation for demonstrating the correction — not a genuine multivariate result.

### Bonferroni Correction

Divide alpha by number of comparisons:

```
alpha_corrected = 0.05 / 3 = 0.0167
z_threshold = 2.394
```

Correcting isn't free: the stricter threshold raises the sample needed. For baseline 35%, 5pp MDE, 80% power, required N per variant is 1,468 at k=1, 1,778 at k=2, **1,958 at k=3 (+33%)** and 2,086 at k=4 (`required_sample_size(0.35, 0.05, alpha=0.05/k)`). Bonferroni is also conservative; Holm's step-down is uniformly more powerful with the same family-wise guarantee, and Benjamini-Hochberg (false-discovery-rate control) suits many variants.

### Per-Variant Decision Framework

| Result | Decision |
|---|---|
| |z| ≥ 2.394 AND lift > 0 | **SHIP** — significant after correction |
| 1.96 ≤ |z| < 2.394 AND lift > 0 | **ITERATE** — increase sample size to confirm |
| lift < 0 | **KILL** — underperforms control |
| |z| < 1.96 | **HOLD** — continue experiment |

### Sample Size Planning

Before launching: calculate required N to detect a minimum detectable effect (MDE) at target power. Formula in `mart_multivariate.sql`:

```sql
n_per_variant = (z_alpha + z_power)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1-p2)^2
```

For baseline 35%, MDE 5pp, 80% power: **~1,468 per variant → 5,872 total for 4 variants** (verified against both `mart_multivariate.sql`'s SQL calculator and `required_sample_size()` in `app/utils/metrics.py`; those two independently agree, and both correct an earlier "~730 per variant" figure that had been written here without actually running the formula — it was off by exactly 2x, missing the summed control+treatment variance term).

## Interpretation Guardrails

- Activation lift alone is not a sufficient launch signal — always check paid conversion and retention guardrails.
- HTE analysis is mandatory before any rollout: a positive overall effect can mask segment-level harm.
- In multivariate experiments, always apply multiple comparison correction before declaring a winner.
- Modeled revenue impact is a synthetic-data estimate — label clearly as decision support, not a forecast.
