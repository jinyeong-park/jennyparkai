from pathlib import Path

import pandas as pd

import hashlib

import numpy as np

from scripts.generate_synthetic_data import generate_dataset, generate_usage_dataset


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
    activation_by_org = (
        activation_events.groupby("org_id")["event_name"].nunique().ge(2).astype("boolean").rename("activated")
    )
    measured = assignments.join(activation_by_org, on="org_id").fillna({"activated": False})
    rates = measured.groupby("variant")["activated"].mean()

    assert rates["treatment"] > rates["control"]


CORE_TABLES = ["organizations", "users", "event_logs", "subscriptions", "experiment_assignments"]


def _digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_usage_generation_leaves_core_tables_untouched_and_is_deterministic(tmp_path: Path):
    generate_dataset(tmp_path, org_count=300, seed=7)
    before = {name: _digest(tmp_path / f"{name}.csv") for name in CORE_TABLES}

    first = generate_usage_dataset(tmp_path, seed=7)
    second = generate_usage_dataset(tmp_path, seed=7)

    assert {name: _digest(tmp_path / f"{name}.csv") for name in CORE_TABLES} == before
    pd.testing.assert_frame_equal(first, second)
    assert {"org_id", "week_start", "active_users", "sessions", "features_used"} == set(first.columns)


def _pre_churn_ratio(usage, organizations, subscriptions, churned: bool) -> float:
    """Median of (mean weekly sessions in the last 3 weeks) / (mean weekly sessions 7-10 weeks earlier)."""
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)]
    paid = paid.loc[paid["status"].eq("churned") == churned]
    ratios = []
    for row in paid.itertuples():
        weeks = usage.loc[usage["org_id"].eq(row.org_id)].sort_values("week_start")["sessions"].to_numpy()
        if len(weeks) < 11:
            continue
        end = len(weeks)  # churned orgs stop emitting rows at churn, so the last rows ARE the pre-churn weeks
        late, early = weeks[end - 3 : end].mean(), weeks[end - 10 : end - 6].mean()
        if early > 0:
            ratios.append(late / early)
    return float(np.median(ratios))


def test_planted_signal_churners_decline_before_churning_and_others_do_not(tmp_path: Path):
    tables = generate_dataset(tmp_path, org_count=900, seed=7)
    usage = generate_usage_dataset(tmp_path, seed=7)

    churner_ratio = _pre_churn_ratio(usage, tables["organizations"], tables["subscriptions"], churned=True)
    steady_ratio = _pre_churn_ratio(usage, tables["organizations"], tables["subscriptions"], churned=False)

    assert churner_ratio < 0.6          # steady decline into churn
    assert 0.8 < steady_ratio < 1.2     # non-churners hold steady (a minority dip temporarily)


def test_planted_signal_has_no_channel_effect_as_a_negative_control(tmp_path: Path):
    tables = generate_dataset(tmp_path, org_count=1200, seed=7)
    usage = generate_usage_dataset(tmp_path, seed=7)

    per_org = usage.groupby("org_id")["sessions"].mean().rename("mean_sessions").reset_index()
    per_org = per_org.merge(tables["organizations"][["org_id", "acquisition_source"]], on="org_id")
    values = np.log1p(per_org["mean_sessions"])
    between = per_org.assign(v=values).groupby("acquisition_source")["v"].agg(["mean", "size"])
    eta_squared = float((between["size"] * (between["mean"] - values.mean()) ** 2).sum() / ((values - values.mean()) ** 2).sum())

    assert eta_squared < 0.02  # channel explains ~none of the variation in usage
