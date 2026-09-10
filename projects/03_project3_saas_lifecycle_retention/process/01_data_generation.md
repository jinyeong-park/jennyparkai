# Data Generation

## Purpose

The project uses deterministic synthetic lifecycle data so every regenerated output is stable and reviewable. The generator uses a fixed random seed and writes source-like CSV tables to `data/raw/`.

## Tables

| Table | Grain | Role in analysis |
| --- | --- | --- |
| `organizations` | One row per account/workspace | Company segment, source, region, and signup cohort |
| `users` | One row per user | Account membership and signup context |
| `event_logs` | One row per product event | Activation behaviors, engagement, and product usage |
| `subscriptions` | One row per subscription | Plan, MRR, paid status, and cancellation timing |
| `experiment_assignments` | One row per account assignment | Guided onboarding control/treatment comparison |

## Design Choices

The organization is the primary analytical unit because activation, subscription value, and retention are account-level outcomes. Treatment probabilities intentionally produce stronger early activation for SMB and mid-market accounts than for enterprise accounts, creating a realistic segmentation question for the experiment readout.

## Reproducibility

Run `python scripts/generate_synthetic_data.py` from the project directory to regenerate the same dataset. Generated CSVs are source inputs for the dashboard and are not manually edited.
