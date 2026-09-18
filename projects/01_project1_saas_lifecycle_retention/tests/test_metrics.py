from pathlib import Path

import pandas as pd

from app.utils.data_loader import load_tables
from app.utils.metrics import (
    activation_completion_days,
    build_account_metrics,
    churn_risk_segments,
    experiment_summary,
    lifecycle_funnel,
    retention_rate,
    retention_curve,
    revenue_trend,
    targeted_rollout_impact,
)
from scripts.generate_synthetic_data import generate_dataset


def _account_metric_tables() -> dict[str, pd.DataFrame]:
    organizations = pd.DataFrame(
        {
            "org_id": ["org_old", "org_recent", "org_churned"],
            "created_at": pd.to_datetime(["2024-12-01", "2025-01-01", "2025-01-01"]),
            "company_size": ["SMB", "SMB", "SMB"],
            "acquisition_source": ["Organic", "Organic", "Organic"],
            "region": ["North America", "North America", "North America"],
        }
    )
    return {
        "organizations": organizations,
        "users": pd.DataFrame(),
        "event_logs": pd.DataFrame(
            {
                "org_id": ["org_old"],
                "event_name": ["signup_completed"],
                "event_timestamp": pd.to_datetime(["2025-04-01"]),
            }
        ),
        "subscriptions": pd.DataFrame(
            {
                "org_id": ["org_old", "org_recent", "org_churned"],
                "mrr_amount": [149.0, 149.0, 399.0],
                "plan_type": ["Growth", "Growth", "Business"],
                "start_date": pd.to_datetime(["2025-01-01", "2025-03-15", "2025-01-01"]),
                "end_date": pd.to_datetime([None, None, "2025-02-15"]),
                "status": ["active", "active", "churned"],
            }
        ),
        "experiment_assignments": pd.DataFrame(
            {"org_id": ["org_old", "org_recent", "org_churned"], "variant": ["control", "control", "treatment"]}
        ),
    }


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


def test_retention_requires_observed_subscription_horizon():
    metrics = build_account_metrics(_account_metric_tables()).set_index("org_id")

    assert metrics.loc["org_old", ["retained_30d", "retained_60d", "retained_90d"]].all()
    assert metrics.loc["org_old", ["eligible_30d", "eligible_60d", "eligible_90d"]].all()
    assert not metrics.loc["org_recent", "retained_30d"]
    assert not metrics.loc["org_recent", "eligible_30d"]
    assert metrics.loc["org_churned", "retained_30d"]
    assert metrics.loc["org_churned", "eligible_60d"]
    assert not metrics.loc["org_churned", "retained_60d"]


def test_subscription_flags_and_mrr_remain_factual_without_activation():
    metrics = build_account_metrics(_account_metric_tables()).set_index("org_id")

    assert not metrics.loc["org_recent", "activated_7d"]
    assert metrics.loc["org_recent", "trial_started"]
    assert metrics.loc["org_recent", "paid_customer"]
    assert metrics.loc["org_recent", "mrr_amount"] == 149.0


def test_activation_requires_workspace_plus_key_action_within_seven_days():
    organizations = pd.DataFrame(
        {
            "org_id": ["workspace_teammate", "keys_without_workspace"],
            "created_at": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "company_size": ["SMB", "SMB"],
            "acquisition_source": ["Organic", "Organic"],
            "region": ["North America", "North America"],
        }
    )
    events = pd.DataFrame(
        {
            "org_id": [
                "workspace_teammate",
                "workspace_teammate",
                "keys_without_workspace",
                "keys_without_workspace",
            ],
            "event_name": [
                "workspace_created",
                "teammate_invited",
                "integration_connected",
                "project_created",
            ],
            "event_timestamp": pd.to_datetime(
                ["2025-01-02", "2025-01-05", "2025-01-02", "2025-01-03"]
            ),
        }
    )
    tables = {
        "organizations": organizations,
        "users": pd.DataFrame(),
        "event_logs": events,
        "subscriptions": pd.DataFrame(
            columns=["org_id", "mrr_amount", "plan_type", "start_date", "end_date", "status"]
        ),
        "experiment_assignments": pd.DataFrame(
            {
                "org_id": organizations["org_id"],
                "variant": ["control", "treatment"],
            }
        ),
    }

    metrics = build_account_metrics(tables).set_index("org_id")
    completion = activation_completion_days(events, organizations).set_index("org_id")

    assert metrics.loc["workspace_teammate", "activated_7d"]
    assert completion.loc["workspace_teammate", "days_to_activation"] == 4
    assert not metrics.loc["keys_without_workspace", "activated_7d"]
    assert "keys_without_workspace" not in completion.index


def test_retention_aggregates_exclude_ineligible_accounts():
    accounts = pd.DataFrame(
        {
            "org_id": ["control_retained", "control_immature", "treatment_churned", "treatment_immature"],
            "variant": ["control", "control", "treatment", "treatment"],
            "activated_7d": [True, False, True, False],
            "paid_customer": [True, False, True, False],
            "eligible_30d": [True, False, True, False],
            "eligible_60d": [True, False, True, False],
            "eligible_90d": [False, False, False, False],
            "retained_30d": [True, False, False, False],
            "retained_60d": [True, False, False, False],
            "retained_90d": [False, False, False, False],
        }
    )

    curve = retention_curve(accounts).set_index("day")
    experiment = experiment_summary(accounts).set_index("variant")

    assert retention_rate(accounts, 60) == 0.5
    assert curve.loc[60, "eligible_accounts"] == 2
    assert curve.loc[60, "retention_rate"] == 0.5
    assert experiment.loc["control", "retention_60d_rate"] == 1.0
    assert experiment.loc["treatment", "retention_60d_rate"] == 0.0


def test_ineligible_retention_does_not_increase_risk_score():
    metrics = build_account_metrics(_account_metric_tables()).set_index("org_id")

    assert not metrics.loc["org_recent", "eligible_60d"]
    assert metrics.loc["org_recent", "risk_score"] == 40


def test_current_revenue_separates_churned_and_trial_accounts():
    tables = _account_metric_tables()
    tables["organizations"] = pd.concat(
        [
            tables["organizations"],
            pd.DataFrame(
                {
                    "org_id": ["org_trial"],
                    "created_at": pd.to_datetime(["2025-03-20"]),
                    "company_size": ["SMB"],
                    "acquisition_source": ["Organic"],
                    "region": ["North America"],
                }
            ),
        ],
        ignore_index=True,
    )
    tables["subscriptions"] = pd.concat(
        [
            tables["subscriptions"],
            pd.DataFrame(
                {
                    "org_id": ["org_trial"],
                    "mrr_amount": [0.0],
                    "plan_type": ["Growth"],
                    "start_date": pd.to_datetime(["2025-03-20"]),
                    "end_date": pd.to_datetime([None]),
                    "status": ["trialing"],
                }
            ),
        ],
        ignore_index=True,
    )
    tables["experiment_assignments"] = pd.concat(
        [
            tables["experiment_assignments"],
            pd.DataFrame({"org_id": ["org_trial"], "variant": ["control"]}),
        ],
        ignore_index=True,
    )

    metrics = build_account_metrics(tables).set_index("org_id")

    assert metrics.loc["org_churned", "ever_paid"]
    assert not metrics.loc["org_churned", "current_active_customer"]
    assert metrics.loc["org_churned", "mrr_amount"] == 399.0
    assert metrics.loc["org_churned", "current_mrr"] == 0.0
    assert metrics.loc["org_trial", "trial_started"]
    assert not metrics.loc["org_trial", "ever_paid"]
    assert not metrics.loc["org_trial", "current_active_customer"]
    assert metrics.loc["org_trial", "current_mrr"] == 0.0


def test_revenue_trend_uses_active_mrr_snapshots():
    trend = revenue_trend(build_account_metrics(_account_metric_tables()))

    january = trend.loc[trend["month"].eq(pd.Timestamp("2025-01-01"))].iloc[0]
    february = trend.loc[trend["month"].eq(pd.Timestamp("2025-02-01"))].iloc[0]
    march = trend.loc[trend["month"].eq(pd.Timestamp("2025-03-01"))].iloc[0]

    assert january["mrr_amount"] == 548.0
    assert february["mrr_amount"] == 149.0
    assert march["mrr_amount"] == 298.0


def test_churn_risk_mrr_uses_current_active_mrr():
    metrics = build_account_metrics(_account_metric_tables())
    risk = churn_risk_segments(metrics)

    assert risk["mrr_at_risk"].sum() == metrics["current_mrr"].sum()
    assert risk["mrr_at_risk"].sum() == 298.0


def test_targeted_rollout_uses_segment_specific_inputs_and_excludes_enterprise():
    accounts = pd.DataFrame(
        {
            "org_id": [f"org_{index}" for index in range(12)],
            "company_size": ["SMB"] * 4 + ["Mid-Market"] * 4 + ["Enterprise"] * 4,
            "variant": ["control", "control", "treatment", "treatment"] * 3,
            "activated_7d": [False, False, True, False, False, True, True, True, False, False, True, True],
            "current_active_customer": [False, False, True, False, False, True, True, True, False, False, True, True],
            "current_mrr": [0.0, 0.0, 100.0, 0.0, 0.0, 200.0, 200.0, 200.0, 0.0, 0.0, 999.0, 999.0],
        }
    )

    result = targeted_rollout_impact(accounts)

    assert result["company_size"].tolist() == ["SMB", "Mid-Market"]
    assert result["eligible_accounts"].tolist() == [4, 4]
    assert result.loc[result["company_size"].eq("SMB"), "activation_lift"].iloc[0] == 0.5
    assert result.loc[result["company_size"].eq("Mid-Market"), "activation_lift"].iloc[0] == 0.5
    assert result["estimated_incremental_mrr"].sum() == 600.0
