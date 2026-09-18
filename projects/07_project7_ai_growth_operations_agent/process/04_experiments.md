# Phase 4 — Experiment Registry and Measurement Engine

## Purpose

Register creative experiments with explicit hypotheses, controls, and guardrail metrics. Enforce evidence requirements before any recommendation is made.

## Experiments

| ID | Name | Variable Tested | State |
|---|---|---|---|
| exp_001 | Contrast vs Outcome hook — META, scrappy_independent | hook_type | RUNNING |
| exp_002 | Social Proof vs FOMO — META, growth_minded | messaging_territory | RUNNING |
| exp_003 | UGC Video vs Static — TikTok, new_owner | creative_format | RUNNING |
| exp_004 | LinkedIn vs META — delivery_heavy persona | channel | EVALUATING |

## State Machine

```
DRAFT → RUNNING → EVALUATING → CONCLUDED
                              → ARCHIVED
```

An experiment cannot move to CONCLUDED while immature (trials below minimum_trials_per_arm).

## Measurement Logic

Z-test for proportions — implemented manually without scipy:

```
z = (p_treatment - p_control) / sqrt(pooled_p × (1 - pooled_p) × (1/n1 + 1/n2))
```

Statistical significance threshold: |z| ≥ 1.96 (95% CI).

## Recommendation States

| State | Condition |
|---|---|
| INSUFFICIENT_DATA | Either arm below minimum_trials_per_arm |
| SCALE_CANDIDATE | Stat. + practically significant, treatment wins |
| PAUSE_CANDIDATE | Stat. + practically significant, treatment loses |
| OBSERVE | Only one type of significance met |
| HOLD | No significance in either direction |

## Guardrail Override

If the treatment wins on the primary metric but a guardrail metric degrades by more than the configured threshold (default 5% relative), the recommendation is automatically downgraded from SCALE_CANDIDATE to HOLD.

Example: exp_001 treatment wins on activation_rate but m1_retention_rate drops 6% → recommendation becomes HOLD, not SCALE_CANDIDATE.

## Artifacts

| File | Purpose |
|---|---|
| `config/experiments.yaml` | 4 registered experiments |
| `docs/experiment_playbook.md` | When to open an experiment, maturity rules, act/observe/pause policy |
| `docs/experiment_readout.md` | Filled-in readout for exp_001 (synthetic numbers) |
