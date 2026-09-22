from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"
PAGES_ROOT = APP_ROOT / "pages"
sys.path.insert(0, str(APP_ROOT))


def load_page(filename: str):
    spec = importlib.util.spec_from_file_location(filename, PAGES_ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_modeled_nrr_retains_only_accounts_active_at_horizon():
    revenue_page = load_page("4_Revenue.py")
    subscriptions = pd.DataFrame(
        {
            "org_id": ["active", "churned", "later"],
            "start_date": pd.to_datetime(["2025-01-01", "2025-01-01", "2025-02-01"]),
            "end_date": pd.to_datetime([None, "2025-01-15", None]),
            "mrr_amount": [100.0, 200.0, 500.0],
        }
    )

    result = revenue_page.modeled_nrr_trend(
        subscriptions, pd.Timestamp("2025-02-15")
    ).set_index("cohort_month")

    january = result.loc[pd.Timestamp("2025-01-01")]
    assert january["beginning_mrr"] == 300.0
    assert january["nrr_30d"] == 100 / 300
    assert pd.isna(january["nrr_60d"])
    assert pd.isna(january["nrr_90d"])


def test_modeled_nrr_filters_mixed_maturity_within_a_cohort():
    revenue_page = load_page("4_Revenue.py")
    subscriptions = pd.DataFrame(
        {
            "org_id": ["mature", "immature"],
            "start_date": pd.to_datetime(["2025-01-01", "2025-01-31"]),
            "end_date": pd.to_datetime([None, None]),
            "mrr_amount": [100.0, 900.0],
        }
    )

    result = revenue_page.modeled_nrr_trend(
        subscriptions, pd.Timestamp("2025-02-15")
    ).iloc[0]

    assert result["eligible_mrr_30d"] == 100.0
    assert result["nrr_30d"] == 1.0


def test_signup_cohort_retention_groups_accounts_by_created_month():
    retention_page = load_page("3_Retention.py")
    accounts = pd.DataFrame(
        {
            "created_at": pd.to_datetime(["2025-01-02", "2025-01-31", "2025-02-01"]),
            "retained_30d": [True, False, True],
            "retained_60d": [True, False, False],
            "retained_90d": [False, False, False],
            "eligible_30d": [True, False, False],
            "eligible_60d": [True, False, False],
            "eligible_90d": [False, False, False],
        }
    )

    result = retention_page.signup_cohort_retention(accounts)
    january_30d = result.loc[(result["cohort_month"] == pd.Timestamp("2025-01-01")) & (result["day"] == 30), "retention_rate"].iloc[0]

    assert january_30d == 1.0
    assert set(result["cohort_month"]) == {pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")}


def test_segment_rates_exclude_ineligible_accounts():
    retention_page = load_page("3_Retention.py")
    accounts = pd.DataFrame(
        {
            "company_size": ["SMB", "SMB", "Enterprise"],
            "retained_30d": [True, False, False],
            "retained_60d": [True, False, False],
            "retained_90d": [False, False, False],
            "eligible_30d": [True, False, True],
            "eligible_60d": [True, False, True],
            "eligible_90d": [False, False, False],
        }
    )

    result = retention_page.segment_rates(accounts, "company_size")

    assert result.loc["SMB", "30D"] == 1.0
    assert result.loc["Enterprise", "30D"] == 0.0
    assert pd.isna(result.loc["SMB", "90D"])


def test_activation_completion_requires_workspace_and_key_action_within_seven_days():
    activation_page = load_page("2_Activation.py")
    organizations = pd.DataFrame(
        {"org_id": ["workspace_then_key", "key_then_workspace", "outside_window"], "created_at": pd.to_datetime(["2025-01-01", "2025-01-01", "2025-01-01"])}
    )
    events = pd.DataFrame(
        {
            "org_id": ["workspace_then_key", "workspace_then_key", "key_then_workspace", "key_then_workspace", "outside_window", "outside_window"],
            "event_name": ["workspace_created", "project_created", "integration_connected", "workspace_created", "workspace_created", "project_created"],
            "event_timestamp": pd.to_datetime(["2025-01-02", "2025-01-04", "2025-01-02", "2025-01-03", "2025-01-02", "2025-01-10"]),
        }
    )

    result = activation_page.activation_completion_days(events, organizations).set_index("org_id")

    assert result.loc["workspace_then_key", "days_to_activation"] == 3
    assert result.loc["key_then_workspace", "days_to_activation"] == 2
    assert "outside_window" not in result.index


def test_account_directory_sorts_by_numeric_risk_then_mrr():
    users_page = load_page("1_Users.py")
    accounts = pd.DataFrame(
        {
            "org_id": ["org_149", "org_999", "org_49"],
            "risk_segment": ["Medium", "High", "High"],
            "risk_score": [60, 80, 90],
            "current_mrr": [149.0, 999.0, 49.0],
        }
    )

    result = users_page.sort_account_directory(accounts)

    assert result["org_id"].tolist() == ["org_49", "org_999", "org_149"]
