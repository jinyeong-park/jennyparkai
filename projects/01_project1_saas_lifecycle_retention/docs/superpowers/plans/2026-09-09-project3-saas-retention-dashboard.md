# Project 3 SaaS Retention Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Streamlit dashboard and synthetic data foundation for Product-Led SaaS Lifecycle & Retention Analytics.

**Architecture:** Generate deterministic account-level SaaS lifecycle data into CSV files, load it through focused utility modules, and compute dashboard-ready metrics in Python. The Streamlit app follows the Project 2 pattern with `Summary.py`, page modules, and shared `utils` for theme, data loading, and metrics.

**Tech Stack:** Python 3, pandas, numpy, scipy, plotly, Streamlit, CSV files.

**Spec:** `projects/03_project3_saas_lifecyle_retention/docs/superpowers/specs/2026-09-09-project3-saas-retention-dashboard-design.md`

## Global Constraints

- Keep all implementation inside `projects/03_project3_saas_lifecyle_retention`.
- Use a local Streamlit app as the first interactive artifact.
- Keep Hex-oriented documentation for interview positioning.
- Model dashboard styling after `03_product-led-retention-analytics.png`.
- Use deterministic synthetic data so regenerated outputs remain stable.
- Do not modify unrelated root-level or Project 2 files.

---

## File Structure

- `scripts/generate_synthetic_data.py`: creates raw CSV files for organizations, users, events, subscriptions, and experiment assignments.
- `data/raw/*.csv`: generated source-like tables.
- `app/requirements.txt`: Python dependencies for the dashboard.
- `app/Summary.py`: executive overview dashboard.
- `app/pages/*.py`: detailed lifecycle pages.
- `app/utils/data_loader.py`: loads raw CSV files and exposes typed table access.
- `app/utils/metrics.py`: computes activation, funnel, retention, experiment, revenue, and churn risk metrics.
- `app/utils/theme.py`: shared Streamlit styling and chart colors.
- `tests/test_data_generation.py`: validates generated data shape and business rules.
- `tests/test_metrics.py`: validates metric calculations against generated data.
- `process/*.md`: case-study workflow documentation.
- `docs/*.md`: metric definitions, tracking plan, and experiment readout.

---

### Task 1: Synthetic SaaS Lifecycle Data

**Files:**
- Create: `projects/03_project3_saas_lifecyle_retention/scripts/generate_synthetic_data.py`
- Create: `projects/03_project3_saas_lifecyle_retention/tests/test_data_generation.py`
- Create: `projects/03_project3_saas_lifecyle_retention/data/raw/organizations.csv`
- Create: `projects/03_project3_saas_lifecyle_retention/data/raw/users.csv`
- Create: `projects/03_project3_saas_lifecyle_retention/data/raw/event_logs.csv`
- Create: `projects/03_project3_saas_lifecyle_retention/data/raw/subscriptions.csv`
- Create: `projects/03_project3_saas_lifecyle_retention/data/raw/experiment_assignments.csv`

**Interfaces:**
- Consumes: no local project code.
- Produces: `generate_dataset(output_dir: Path, org_count: int = 2500, seed: int = 42) -> dict[str, pandas.DataFrame]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_data_generation.py`:

```python
from pathlib import Path

import pandas as pd

from scripts.generate_synthetic_data import generate_dataset


def test_generate_dataset_returns_required_tables(tmp_path: Path):
    tables = generate_dataset(tmp_path, org_count=200, seed=7)

    assert set(tables) == {
        "organizations",
        "users",
        "event_logs",
        "subscriptions",
        "experiment_assignments",
    }
    assert len(tables["organizations"]) == 200
    assert tables["users"]["org_id"].isin(tables["organizations"]["org_id"]).all()
    assert tables["event_logs"]["org_id"].isin(tables["organizations"]["org_id"]).all()


def test_generated_csvs_include_required_columns(tmp_path: Path):
    generate_dataset(tmp_path, org_count=200, seed=7)

    required_columns = {
        "organizations.csv": {"org_id", "created_at", "industry", "company_size", "acquisition_source", "region"},
        "users.csv": {"user_id", "org_id", "role", "signup_timestamp", "is_admin"},
        "event_logs.csv": {"event_id", "user_id", "org_id", "event_name", "event_timestamp", "event_properties"},
        "subscriptions.csv": {"subscription_id", "org_id", "plan_type", "mrr_amount", "start_date", "end_date", "status", "churn_reason"},
        "experiment_assignments.csv": {"experiment_id", "org_id", "variant", "assigned_at", "eligible_segment"},
    }

    for filename, columns in required_columns.items():
        frame = pd.read_csv(tmp_path / filename)
        assert columns.issubset(frame.columns)
        assert len(frame) > 0


def test_treatment_has_higher_activation_event_rate(tmp_path: Path):
    tables = generate_dataset(tmp_path, org_count=800, seed=7)
    events = tables["event_logs"]
    assignments = tables["experiment_assignments"]

    activation_events = events[events["event_name"].isin(["workspace_created", "integration_connected", "project_created"])]
    activation_by_org = activation_events.groupby("org_id")["event_name"].nunique().ge(2).rename("activated")
    measured = assignments.join(activation_by_org, on="org_id").fillna({"activated": False})
    rates = measured.groupby("variant")["activated"].mean()

    assert rates["treatment"] > rates["control"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m pytest tests/test_data_generation.py -v
```

Expected: FAIL because `scripts.generate_synthetic_data` does not exist.

- [ ] **Step 3: Implement deterministic data generation**

Create `scripts/generate_synthetic_data.py` with `generate_dataset`. Use `numpy.random.default_rng(seed)`. Generate 2,500 organizations across company size, source, industry, and region. Assign experiment variants at org level. Create 1-8 users per org, product events over 120 days, subscription rows for paid and churned accounts, and event properties as JSON strings.

Core behavior:

```python
def generate_dataset(output_dir: Path, org_count: int = 2500, seed: int = 42) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    # build organizations, assignments, users, event_logs, subscriptions
    # write each table to output_dir / f"{table_name}.csv"
    return tables
```

Use treatment probabilities that produce higher workspace creation and activation than control, with enterprise treatment lift smaller than SMB and mid-market.

- [ ] **Step 4: Run the generator**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python scripts/generate_synthetic_data.py
```

Expected: five CSV files appear in `data/raw`.

- [ ] **Step 5: Run data generation tests**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m pytest tests/test_data_generation.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add projects/03_project3_saas_lifecyle_retention/scripts/generate_synthetic_data.py projects/03_project3_saas_lifecyle_retention/tests/test_data_generation.py projects/03_project3_saas_lifecyle_retention/data/raw
git commit -m "Add project3 synthetic lifecycle data"
```

---

### Task 2: Data Loader And Metric Engine

**Files:**
- Create: `projects/03_project3_saas_lifecyle_retention/app/utils/__init__.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/utils/data_loader.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/utils/metrics.py`
- Create: `projects/03_project3_saas_lifecyle_retention/tests/test_metrics.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/requirements.txt`

**Interfaces:**
- Consumes: CSV files from `data/raw`.
- Produces:
  - `load_tables(data_dir: Path | None = None) -> dict[str, pandas.DataFrame]`
  - `build_account_metrics(tables: dict[str, pandas.DataFrame]) -> pandas.DataFrame`
  - `lifecycle_funnel(account_metrics: pandas.DataFrame) -> pandas.DataFrame`
  - `experiment_summary(account_metrics: pandas.DataFrame) -> pandas.DataFrame`
  - `retention_curve(account_metrics: pandas.DataFrame) -> pandas.DataFrame`
  - `revenue_trend(account_metrics: pandas.DataFrame) -> pandas.DataFrame`
  - `churn_risk_segments(account_metrics: pandas.DataFrame) -> pandas.DataFrame`

- [ ] **Step 1: Write failing metric tests**

Create `tests/test_metrics.py`:

```python
from pathlib import Path

from app.utils.data_loader import load_tables
from app.utils.metrics import (
    build_account_metrics,
    churn_risk_segments,
    experiment_summary,
    lifecycle_funnel,
    retention_curve,
    revenue_trend,
)
from scripts.generate_synthetic_data import generate_dataset


def test_build_account_metrics_has_lifecycle_flags(tmp_path: Path):
    generate_dataset(tmp_path, org_count=300, seed=12)
    metrics = build_account_metrics(load_tables(tmp_path))

    expected = {"org_id", "activated_7d", "trial_started", "paid_customer", "retained_30d", "retained_60d", "risk_segment", "mrr_amount"}
    assert expected.issubset(metrics.columns)
    assert metrics["activated_7d"].mean() > 0.25
    assert metrics["paid_customer"].sum() > 0


def test_lifecycle_funnel_is_ordered_and_declining(tmp_path: Path):
    generate_dataset(tmp_path, org_count=300, seed=12)
    metrics = build_account_metrics(load_tables(tmp_path))
    funnel = lifecycle_funnel(metrics)

    assert list(funnel["stage"]) == ["Signups", "Workspace Created", "Activated", "Trial Started", "Paid Customers", "Retained 60D"]
    assert funnel["accounts"].is_monotonic_decreasing


def test_experiment_summary_reports_positive_treatment_lift(tmp_path: Path):
    generate_dataset(tmp_path, org_count=600, seed=12)
    metrics = build_account_metrics(load_tables(tmp_path))
    summary = experiment_summary(metrics)

    treatment = summary.loc[summary["variant"] == "treatment"].iloc[0]
    assert treatment["activation_lift_pp"] > 0


def test_retention_revenue_and_risk_outputs_are_non_empty(tmp_path: Path):
    generate_dataset(tmp_path, org_count=300, seed=12)
    metrics = build_account_metrics(load_tables(tmp_path))

    assert len(retention_curve(metrics)) > 0
    assert len(revenue_trend(metrics)) > 0
    assert churn_risk_segments(metrics)["accounts"].sum() == len(metrics)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m pytest tests/test_metrics.py -v
```

Expected: FAIL because app utilities do not exist.

- [ ] **Step 3: Add dependencies**

Create `app/requirements.txt`:

```text
streamlit
pandas
numpy
plotly
scipy
pytest
```

- [ ] **Step 4: Implement data loader**

Create `app/utils/data_loader.py` with stable default path resolution from the project root:

```python
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_tables(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    source = data_dir or DEFAULT_DATA_DIR
    tables = {
        "organizations": pd.read_csv(source / "organizations.csv", parse_dates=["created_at"]),
        "users": pd.read_csv(source / "users.csv", parse_dates=["signup_timestamp"]),
        "event_logs": pd.read_csv(source / "event_logs.csv", parse_dates=["event_timestamp"]),
        "subscriptions": pd.read_csv(source / "subscriptions.csv", parse_dates=["start_date", "end_date"]),
        "experiment_assignments": pd.read_csv(source / "experiment_assignments.csv", parse_dates=["assigned_at"]),
    }
    return tables
```

- [ ] **Step 5: Implement metric functions**

Create `app/utils/metrics.py`. Compute org-level flags from event names and timestamps. Join organizations, assignments, and subscription status. Define risk segments from activity recency, retention, activation, and subscription state.

Required columns in `build_account_metrics`:

```python
[
    "org_id", "created_at", "company_size", "acquisition_source", "region",
    "variant", "workspace_created", "activated_7d", "trial_started",
    "paid_customer", "retained_30d", "retained_60d", "retained_90d",
    "mrr_amount", "plan_type", "status", "days_since_last_event",
    "risk_score", "risk_segment"
]
```

- [ ] **Step 6: Run metric tests**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m pytest tests/test_metrics.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add projects/03_project3_saas_lifecyle_retention/app/requirements.txt projects/03_project3_saas_lifecyle_retention/app/utils projects/03_project3_saas_lifecyle_retention/tests/test_metrics.py
git commit -m "Add project3 lifecycle metrics"
```

---

### Task 3: Streamlit Overview Dashboard

**Files:**
- Create: `projects/03_project3_saas_lifecyle_retention/app/Summary.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/utils/theme.py`

**Interfaces:**
- Consumes: `load_tables`, `build_account_metrics`, `lifecycle_funnel`, `experiment_summary`, `retention_curve`, `revenue_trend`, `churn_risk_segments`.
- Produces: runnable Streamlit executive overview page.

- [ ] **Step 1: Implement shared theme**

Create `app/utils/theme.py`:

```python
PRIMARY = "#0f4c81"
BLUE = "#2f80ed"
TEAL = "#17b8a6"
GREEN = "#22c55e"
AMBER = "#f5b942"
RED = "#ef5b5b"
INK = "#0b1f3a"
MUTED = "#5b7194"
PANEL_BG = "#ffffff"
GRID = "#dce6f4"


def inject_theme() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; max-width: 1380px;}
        [data-testid="stSidebar"] {background: #f6f9ff;}
        .metric-card {
            border: 1px solid #dce6f4;
            border-radius: 8px;
            padding: 18px 20px;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 76, 129, 0.05);
        }
        .metric-label {color: #29466f; font-size: 0.84rem; font-weight: 700;}
        .metric-value {color: #0b1f3a; font-size: 2rem; font-weight: 800; margin-top: 0.35rem;}
        .metric-delta {color: #00a67d; font-size: 0.9rem; font-weight: 700; margin-top: 0.5rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: Implement summary page**

Create `app/Summary.py` with:

- `st.set_page_config(page_title="Product-Led SaaS Retention Analytics", layout="wide")`
- Sidebar navigation labels matching the reference.
- KPI card row.
- Three-column middle section: funnel, activation metrics, cohort retention.
- Three-column bottom section: experiment performance, NRR trend, churn risk.
- Plotly charts for funnel, retention, revenue, and risk.

- [ ] **Step 3: Run import sanity check**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m py_compile app/Summary.py app/utils/theme.py app/utils/data_loader.py app/utils/metrics.py
```

Expected: PASS with no output.

- [ ] **Step 4: Launch Streamlit locally**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention/app
streamlit run Summary.py
```

Expected: app starts and prints a local URL.

- [ ] **Step 5: Commit**

```bash
git add projects/03_project3_saas_lifecyle_retention/app/Summary.py projects/03_project3_saas_lifecyle_retention/app/utils/theme.py
git commit -m "Add project3 Streamlit overview dashboard"
```

---

### Task 4: Detail Pages

**Files:**
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/1_Users.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/2_Activation.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/3_Retention.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/4_Revenue.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/5_Experiments.py`
- Create: `projects/03_project3_saas_lifecyle_retention/app/pages/6_Churn_Risk.py`

**Interfaces:**
- Consumes: data loader, metric engine, and theme from earlier tasks.
- Produces: drill-down pages for the sidebar lifecycle sections.

- [ ] **Step 1: Create Users page**

Show signup volume by acquisition source, company size, and region. Include an account table with org id, created date, segment, source, users, activation, paid customer, MRR, and risk segment.

- [ ] **Step 2: Create Activation page**

Show activation rate by company size and source, median time to activate, and early product action adoption. Include activation definition copy from the README.

- [ ] **Step 3: Create Retention page**

Show 30/60/90-day retention by activation status, source, company size, and plan. Include cohort line chart and heatmap-style table using pandas styling.

- [ ] **Step 4: Create Revenue page**

Show paid customers, ARPA, MRR, plan mix, NRR trend, and estimated incremental MRR from treatment rollout.

- [ ] **Step 5: Create Experiments page**

Show control vs treatment activation rate, lift, p-value from a two-proportion test, guardrail metrics, and segment-level treatment effect.

- [ ] **Step 6: Create Churn Risk page**

Show risk segment counts, risk drivers, at-risk account table, and recommended customer success actions.

- [ ] **Step 7: Run compile check**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m py_compile app/pages/*.py
```

Expected: PASS with no output.

- [ ] **Step 8: Commit**

```bash
git add projects/03_project3_saas_lifecyle_retention/app/pages
git commit -m "Add project3 dashboard detail pages"
```

---

### Task 5: Case Study Documentation

**Files:**
- Create: `projects/03_project3_saas_lifecyle_retention/process/00_process.md`
- Create: `projects/03_project3_saas_lifecyle_retention/process/01_data_generation.md`
- Create: `projects/03_project3_saas_lifecyle_retention/process/02_lifecycle_metrics.md`
- Create: `projects/03_project3_saas_lifecyle_retention/process/03_experiment_readout.md`
- Create: `projects/03_project3_saas_lifecyle_retention/process/04_dashboard_story.md`
- Create: `projects/03_project3_saas_lifecyle_retention/docs/metric_definitions.md`
- Create: `projects/03_project3_saas_lifecyle_retention/docs/tracking_plan.md`
- Create: `projects/03_project3_saas_lifecyle_retention/docs/experiment_readout.md`
- Modify: `projects/03_project3_saas_lifecyle_retention/README.md`

**Interfaces:**
- Consumes: dashboard outputs and metric definitions from earlier tasks.
- Produces: portfolio-ready narrative and run instructions.

- [ ] **Step 1: Create process overview**

Document the workflow:

```text
Define product question -> generate synthetic lifecycle data -> build account metrics -> analyze activation/retention/experiment results -> create stakeholder dashboard -> recommend rollout and measurement plan.
```

- [ ] **Step 2: Create metric definitions**

Define signup, workspace creation, activation within 7 days, trial start, paid conversion, retention, NRR, ARPA, churn risk, and experiment lift. Include numerator, denominator, grain, and caveats for each metric.

- [ ] **Step 3: Create tracking plan**

Document key product events and required properties:

```text
sign_up_completed, workspace_created, teammate_invited, integration_connected, project_created, dashboard_viewed, report_exported, checkout_initiated, trial_started, paid_conversion, support_ticket_created, subscription_canceled
```

- [ ] **Step 4: Create experiment readout**

Write the business recommendation: roll out guided onboarding to SMB and mid-market, keep enterprise on a separate path, and monitor 60-day retention before broad rollout.

- [ ] **Step 5: Update README**

Add a Dashboard section near the top with local run commands:

```bash
cd projects/03_project3_saas_lifecyle_retention
python scripts/generate_synthetic_data.py
cd app
pip install -r requirements.txt
streamlit run Summary.py
```

- [ ] **Step 6: Commit**

```bash
git add projects/03_project3_saas_lifecyle_retention/README.md projects/03_project3_saas_lifecyle_retention/process projects/03_project3_saas_lifecyle_retention/docs
git commit -m "Document project3 SaaS retention case study"
```

---

### Task 6: Final Verification

**Files:**
- Modify only if verification exposes a concrete issue.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified runnable project.

- [ ] **Step 1: Regenerate data**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python scripts/generate_synthetic_data.py
```

Expected: CSV files are regenerated with stable row counts.

- [ ] **Step 2: Run all tests**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m pytest tests -v
```

Expected: PASS.

- [ ] **Step 3: Compile app files**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention
python -m py_compile app/Summary.py app/pages/*.py app/utils/*.py scripts/generate_synthetic_data.py
```

Expected: PASS with no output.

- [ ] **Step 4: Start Streamlit**

Run:

```bash
cd projects/03_project3_saas_lifecyle_retention/app
streamlit run Summary.py
```

Expected: Streamlit starts and serves the dashboard locally.

- [ ] **Step 5: Commit any verification fixes**

```bash
git status --short projects/03_project3_saas_lifecyle_retention
git add projects/03_project3_saas_lifecyle_retention
git commit -m "Verify project3 retention dashboard"
```

Only commit if files changed during verification.
