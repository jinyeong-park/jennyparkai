# Experiment Playbook — Tablr Growth Operations

> **SYNTHETIC** — This playbook describes operating principles for the simulated Tablr growth OS.
> All referenced experiments and metrics are synthetic, created for portfolio purposes.

---

## When to open an experiment vs. explore organically

Open a controlled experiment when you have a **specific, falsifiable hypothesis** about a single variable and when a wrong decision would cost meaningful budget or strategy time. Organic exploration (creative iteration, channel testing without controls) is acceptable when you are still discovering whether a hypothesis is worth testing. The bar for opening an experiment is: "Would I change a recurring budget allocation based on the result?" If yes, run an experiment.

## How to define the single primary variable

Every experiment must declare exactly one `variable_tested`. This is the thing you are **actually changing** between the control and treatment arms — hook type, messaging territory, creative format, or channel. If you change two things at once, you cannot attribute the difference to either. Split multi-variable ideas into sequential experiments, each isolated to one variable.

## Maturity rules

An experiment is **mature** when both arms have reached `minimum_trials_per_arm` and the `evaluation_window_days` have elapsed. Do not evaluate results before both conditions are met. Early reads on small samples produce false signals at a rate that compounds with each daily check. Mark the readout as `INSUFFICIENT_DATA` until maturity is confirmed.

## When to act vs. observe vs. pause

| Signal | Action |
|--------|--------|
| Statistically significant (|z| ≥ 1.96) **and** practically significant (|Δ| ≥ MDE) in the right direction | `SCALE_CANDIDATE` — act |
| Significant in the wrong direction | `PAUSE_CANDIDATE` — stop the losing arm |
| One type of significance only | `OBSERVE` — collect more data |
| Neither | `HOLD` — no action; experiment may need redesign |

## Guardrail metric policy

Each experiment carries one or more guardrail metrics that must not be damaged by more than **5% relative** in the treatment arm. If a treatment wins the primary metric but damages a guardrail, the recommendation is downgraded to `HOLD`. Guardrails protect downstream metrics (e.g., M1 retention) from being sacrificed for a short-term activation gain. Document all guardrail findings in the readout regardless of overall recommendation.
