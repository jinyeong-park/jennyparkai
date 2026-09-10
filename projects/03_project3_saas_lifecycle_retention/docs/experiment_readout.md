# Guided Onboarding Experiment Readout

## Recommendation

Roll out guided onboarding to SMB and mid-market accounts. Keep enterprise accounts on a separate onboarding path, where implementation complexity and stakeholder needs can be addressed with a tailored experience. Monitor 60-day retention before a broad rollout.

## Why This Decision Is Targeted

The experiment is designed to improve early activation through workspace setup prompts and qualifying product actions. The synthetic design intentionally represents stronger treatment responsiveness for SMB and mid-market accounts than for enterprise accounts. A segment-specific rollout captures the expected early-value benefit without assuming a single onboarding flow fits every customer.

## Measurement Plan

Track activation within 7 days as the primary rollout metric. Pair it with workspace creation, trial start, paid conversion, support-ticket creation, cancellation, and 30/60-day retention as downstream and guardrail measures. Review results by company size, acquisition source, and onboarding variant.

Do not declare broad rollout success from activation alone. Continue measuring the eligible cohorts until each reaches the 60-day retention horizon, then compare treatment and control retention alongside retained MRR. Because expansion and contraction are not included in the synthetic source data, `Modeled NRR (no expansion events)` is directional only.

## Interview Positioning

This recommendation shows a product analytics decision pattern: define the primary metric, inspect segment heterogeneity, retain downstream guardrails, and scale only after durable retention evidence is available.
