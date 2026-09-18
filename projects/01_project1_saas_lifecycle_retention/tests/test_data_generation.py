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
    activation_by_org = (
        activation_events.groupby("org_id")["event_name"].nunique().ge(2).astype("boolean").rename("activated")
    )
    measured = assignments.join(activation_by_org, on="org_id").fillna({"activated": False})
    rates = measured.groupby("variant")["activated"].mean()

    assert rates["treatment"] > rates["control"]
