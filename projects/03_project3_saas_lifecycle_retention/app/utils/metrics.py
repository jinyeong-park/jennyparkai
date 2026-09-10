"""Organization-level lifecycle metrics for retention analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


KEY_ACTION_EVENTS = {"teammate_invited", "integration_connected", "project_created"}
RETENTION_PERIODS = (0, 30, 60, 90)
TARGET_ROLLOUT_SEGMENTS = ("SMB", "Mid-Market")


def _as_of_date(tables: dict[str, pd.DataFrame]) -> pd.Timestamp:
    """Use the latest source timestamp as a stable dataset observation date."""
    date_columns = (
        (tables["organizations"], "created_at"),
        (tables["event_logs"], "event_timestamp"),
        (tables["subscriptions"], "start_date"),
        (tables["subscriptions"], "end_date"),
    )
    timestamps = [
        values
        for table, column in date_columns
        if column in table
        for values in [table[column].dropna()]
        if not values.empty
    ]
    return pd.Timestamp(pd.concat(timestamps).max())


def _events_in_activation_window(
    event_logs: pd.DataFrame, organizations: pd.DataFrame
) -> pd.DataFrame:
    events = event_logs.merge(
        organizations[["org_id", "created_at"]], on="org_id", how="inner"
    ).copy()
    events["event_age_days"] = (
        events["event_timestamp"] - events["created_at"]
    ).dt.total_seconds().div(86_400)
    return events.loc[events["event_age_days"].between(0, 7, inclusive="both")]


def activation_completion_days(
    event_logs: pd.DataFrame, organizations: pd.DataFrame
) -> pd.DataFrame:
    """Return elapsed days when workspace creation and a key action are complete."""
    events = _events_in_activation_window(event_logs, organizations)
    workspace = (
        events.loc[events["event_name"].eq("workspace_created")]
        .groupby("org_id", as_index=False)["event_timestamp"]
        .min()
        .rename(columns={"event_timestamp": "workspace_at"})
    )
    key_action = (
        events.loc[events["event_name"].isin(KEY_ACTION_EVENTS)]
        .groupby("org_id", as_index=False)["event_timestamp"]
        .min()
        .rename(columns={"event_timestamp": "key_action_at"})
    )
    completed = workspace.merge(key_action, on="org_id").merge(
        organizations[["org_id", "created_at"]], on="org_id"
    )
    completed["activation_at"] = completed[["workspace_at", "key_action_at"]].max(axis=1)
    completed["days_to_activation"] = (
        completed["activation_at"] - completed["created_at"]
    ).dt.total_seconds().div(86_400)
    return completed[["org_id", "days_to_activation"]]


def _event_metrics(
    organizations: pd.DataFrame,
    event_logs: pd.DataFrame,
    as_of_date: pd.Timestamp,
) -> pd.DataFrame:
    """Summarize product activity and first-week activation at the org level."""
    events = event_logs.merge(
        organizations[["org_id", "created_at"]], on="org_id", how="inner"
    ).copy()
    activated_orgs = activation_completion_days(event_logs, organizations)["org_id"]
    workspace_orgs = events.loc[
        events["event_name"].eq("workspace_created"), "org_id"
    ].unique()
    last_event = events.groupby("org_id")["event_timestamp"].max()

    summary = organizations[["org_id"]].copy()
    summary["workspace_created"] = summary["org_id"].isin(workspace_orgs)
    summary["activated_7d"] = summary["org_id"].isin(activated_orgs)
    summary["last_event_at"] = summary["org_id"].map(last_event)
    recency = (as_of_date - summary["last_event_at"]).dt.total_seconds().div(86_400)
    summary["days_since_last_event"] = (
        np.floor(recency.clip(lower=0)).fillna(999).astype(int)
    )
    return summary


def _subscription_metrics(
    subscriptions: pd.DataFrame, as_of_date: pd.Timestamp
) -> pd.DataFrame:
    """Separate trial, paid history, current revenue, and retention eligibility."""
    columns = [
        "org_id",
        "trial_started",
        "ever_paid",
        "paid_customer",
        "current_active_customer",
        "eligible_30d",
        "eligible_60d",
        "eligible_90d",
        "retained_30d",
        "retained_60d",
        "retained_90d",
        "mrr_amount",
        "current_mrr",
        "plan_type",
        "status",
        "trial_start_date",
        "paid_conversion_date",
        "subscription_start_date",
        "subscription_end_date",
    ]
    if subscriptions.empty:
        return pd.DataFrame(columns=columns)

    latest = subscriptions.sort_values(["org_id", "start_date"]).drop_duplicates(
        "org_id", keep="last"
    ).copy()
    paid = latest["mrr_amount"].gt(0)
    active_now = (
        paid
        & latest["status"].eq("active")
        & latest["start_date"].le(as_of_date)
        & (latest["end_date"].isna() | latest["end_date"].ge(as_of_date))
    )

    result = latest[
        ["org_id", "mrr_amount", "plan_type", "status", "start_date", "end_date"]
    ].copy()
    result = result.rename(
        columns={
            "start_date": "trial_start_date",
            "end_date": "subscription_end_date",
        }
    )
    result["trial_started"] = True
    result["ever_paid"] = paid.to_numpy()
    result["paid_customer"] = result["ever_paid"]
    result["current_active_customer"] = active_now.to_numpy()
    result["current_mrr"] = result["mrr_amount"].where(active_now.to_numpy(), 0.0)
    result["paid_conversion_date"] = result["trial_start_date"].where(paid.to_numpy())
    result["subscription_start_date"] = result["paid_conversion_date"]

    for period in RETENTION_PERIODS[1:]:
        horizon = result["paid_conversion_date"] + pd.Timedelta(days=period)
        eligible = result["ever_paid"] & horizon.le(as_of_date)
        subscribed_through_horizon = result["subscription_end_date"].isna() | result[
            "subscription_end_date"
        ].ge(horizon)
        result[f"eligible_{period}d"] = eligible
        result[f"retained_{period}d"] = eligible & subscribed_through_horizon
    return result[columns]


def build_account_metrics(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build one dashboard-ready lifecycle record for every organization."""
    organizations = tables["organizations"].copy()
    assignments = (
        tables["experiment_assignments"][["org_id", "variant"]]
        .drop_duplicates("org_id")
        .copy()
    )
    as_of_date = _as_of_date(tables)
    metrics = organizations.merge(assignments, on="org_id", how="left")
    metrics = metrics.merge(
        _event_metrics(organizations, tables["event_logs"], as_of_date),
        on="org_id",
        how="left",
    )
    metrics = metrics.merge(
        _subscription_metrics(tables["subscriptions"], as_of_date),
        on="org_id",
        how="left",
    )

    boolean_columns = [
        "workspace_created",
        "activated_7d",
        "trial_started",
        "ever_paid",
        "paid_customer",
        "current_active_customer",
        "eligible_30d",
        "eligible_60d",
        "eligible_90d",
        "retained_30d",
        "retained_60d",
        "retained_90d",
    ]
    metrics[boolean_columns] = metrics[boolean_columns].apply(
        lambda column: column.astype("boolean").fillna(False).astype(bool)
    )
    metrics["mrr_amount"] = pd.to_numeric(metrics["mrr_amount"]).fillna(0.0)
    metrics["current_mrr"] = pd.to_numeric(metrics["current_mrr"]).fillna(0.0)
    metrics["plan_type"] = metrics["plan_type"].fillna("Free")
    metrics["status"] = metrics["status"].fillna("no_subscription")
    metrics["observation_date"] = as_of_date

    risk_score = np.select(
        [metrics["status"].eq("churned"), metrics["status"].eq("no_subscription")],
        [55, 30],
        default=0,
    ).astype(int)
    risk_score += np.where(~metrics["activated_7d"], 20, 0)
    risk_score += np.where(
        metrics["eligible_60d"] & ~metrics["retained_60d"], 15, 0
    )
    risk_score += np.where(metrics["days_since_last_event"].gt(90), 20, 0)
    risk_score += np.where(metrics["days_since_last_event"].between(31, 90), 10, 0)
    metrics["risk_score"] = np.clip(risk_score, 0, 100)
    metrics["risk_segment"] = pd.cut(
        metrics["risk_score"],
        bins=[-1, 34, 64, 100],
        labels=["Low", "Medium", "High"],
    ).astype(str)

    required_columns = [
        "org_id",
        "created_at",
        "company_size",
        "acquisition_source",
        "region",
        "variant",
        "workspace_created",
        "activated_7d",
        "trial_started",
        "ever_paid",
        "paid_customer",
        "current_active_customer",
        "eligible_30d",
        "eligible_60d",
        "eligible_90d",
        "retained_30d",
        "retained_60d",
        "retained_90d",
        "mrr_amount",
        "current_mrr",
        "plan_type",
        "status",
        "trial_start_date",
        "paid_conversion_date",
        "subscription_start_date",
        "subscription_end_date",
        "observation_date",
        "days_since_last_event",
        "risk_score",
        "risk_segment",
    ]
    return metrics[required_columns].sort_values("org_id").reset_index(drop=True)


def retention_rate(account_metrics: pd.DataFrame, period: int) -> float:
    """Return retention among accounts that have reached the requested horizon."""
    eligible = account_metrics[f"eligible_{period}d"].fillna(False)
    if not eligible.any():
        return float("nan")
    return float(account_metrics.loc[eligible, f"retained_{period}d"].mean())


def retention_rates_by_segment(
    account_metrics: pd.DataFrame, dimension: str
) -> pd.DataFrame:
    """Return eligible-only 30/60/90-day retention by a dashboard dimension."""
    rows = []
    for segment, accounts in account_metrics.groupby(
        dimension, dropna=False, observed=False
    ):
        row = {dimension: segment}
        row.update(
            {
                f"{period}D": retention_rate(accounts, period)
                for period in RETENTION_PERIODS[1:]
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).set_index(dimension)


def signup_cohort_retention(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Build eligible-only 0/30/60/90-day retention for signup-month cohorts."""
    cohorts = account_metrics.assign(
        cohort_month=account_metrics["created_at"].dt.to_period("M").dt.to_timestamp()
    )
    rows = []
    for cohort_month, cohort in cohorts.groupby("cohort_month"):
        rows.append(
            {
                "cohort_month": cohort_month,
                "day": 0,
                "eligible_accounts": len(cohort),
                "retention_rate": 1.0,
            }
        )
        for period in RETENTION_PERIODS[1:]:
            rows.append(
                {
                    "cohort_month": cohort_month,
                    "day": period,
                    "eligible_accounts": int(cohort[f"eligible_{period}d"].sum()),
                    "retention_rate": retention_rate(cohort, period),
                }
            )
    return pd.DataFrame(rows)


def lifecycle_funnel(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return ordered account counts for the product lifecycle funnel."""
    stage_flags = [
        ("Signups", pd.Series(True, index=account_metrics.index)),
        ("Workspace Created", account_metrics["workspace_created"]),
        ("Activated", account_metrics["activated_7d"]),
        ("Trial Started", account_metrics["trial_started"]),
        ("Paid Customers", account_metrics["paid_customer"]),
        ("Retained 60D", account_metrics["retained_60d"]),
    ]
    cumulative_eligibility = pd.Series(True, index=account_metrics.index)
    stages = []
    for stage, flag in stage_flags:
        cumulative_eligibility &= flag
        stages.append((stage, cumulative_eligibility.sum()))
    return pd.DataFrame(
        {
            "stage": [stage for stage, _ in stages],
            "accounts": [int(count) for _, count in stages],
        }
    )


def experiment_summary(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Compare activation and downstream conversion between experiment variants."""
    rows = []
    for variant, accounts in account_metrics.groupby("variant", dropna=False):
        rows.append(
            {
                "variant": variant,
                "accounts": len(accounts),
                "activation_rate": accounts["activated_7d"].mean(),
                "paid_conversion_rate": accounts["paid_customer"].mean(),
                "retention_60d_rate": retention_rate(accounts, 60),
                "retention_60d_eligible_accounts": int(accounts["eligible_60d"].sum()),
            }
        )
    summary = pd.DataFrame(rows)
    control_rate = summary.loc[summary["variant"].eq("control"), "activation_rate"]
    baseline = control_rate.iloc[0] if not control_rate.empty else 0.0
    summary["activation_lift_pp"] = (summary["activation_rate"] - baseline) * 100
    return summary


def retention_curve(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return cohort-wide retention rates with explicit horizon denominators."""
    rows = [
        {
            "day": 0,
            "accounts": len(account_metrics),
            "eligible_accounts": len(account_metrics),
            "retention_rate": 1.0 if len(account_metrics) else 0.0,
        }
    ]
    for period in RETENTION_PERIODS[1:]:
        eligible = account_metrics[f"eligible_{period}d"].fillna(False)
        rows.append(
            {
                "day": period,
                "accounts": int(
                    account_metrics.loc[eligible, f"retained_{period}d"].sum()
                ),
                "eligible_accounts": int(eligible.sum()),
                "retention_rate": retention_rate(account_metrics, period),
            }
        )
    return pd.DataFrame(rows)


def revenue_trend(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return active paid MRR snapshots at each observed month end."""
    paid = account_metrics.loc[
        account_metrics["subscription_start_date"].notna()
    ].copy()
    if paid.empty:
        return pd.DataFrame(
            columns=["month", "snapshot_date", "accounts", "paid_accounts", "mrr_amount"]
        )

    as_of_date = pd.Timestamp(paid["observation_date"].max())
    first_month = paid["subscription_start_date"].min().to_period("M")
    last_month = as_of_date.to_period("M")
    rows = []
    for period in pd.period_range(first_month, last_month, freq="M"):
        month = period.to_timestamp()
        snapshot_date = min(period.to_timestamp(how="end"), as_of_date)
        active = paid["subscription_start_date"].le(snapshot_date) & (
            paid["subscription_end_date"].isna()
            | paid["subscription_end_date"].ge(snapshot_date)
        )
        snapshot = paid.loc[active]
        rows.append(
            {
                "month": month,
                "snapshot_date": snapshot_date,
                "accounts": int(active.sum()),
                "paid_accounts": int(active.sum()),
                "mrr_amount": float(snapshot["mrr_amount"].sum()),
            }
        )
    return pd.DataFrame(rows)


def modeled_nrr_trend(
    subscriptions: pd.DataFrame, as_of_date: pd.Timestamp
) -> pd.DataFrame:
    """Calculate retained MRR only for subscriptions mature at each horizon."""
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)].copy()
    paid["cohort_month"] = paid["start_date"].dt.to_period("M").dt.to_timestamp()
    rows = []
    for cohort_month, cohort in paid.groupby("cohort_month"):
        row = {
            "cohort_month": cohort_month,
            "beginning_mrr": float(cohort["mrr_amount"].sum()),
        }
        for horizon in RETENTION_PERIODS[1:]:
            horizon_date = cohort["start_date"] + pd.Timedelta(days=horizon)
            eligible = horizon_date.le(as_of_date)
            eligible_cohort = cohort.loc[eligible]
            eligible_mrr = float(eligible_cohort["mrr_amount"].sum())
            retained = eligible_cohort.loc[
                eligible_cohort["end_date"].isna()
                | eligible_cohort["end_date"].ge(horizon_date.loc[eligible])
            ]
            row[f"eligible_mrr_{horizon}d"] = eligible_mrr
            row[f"nrr_{horizon}d"] = (
                float(retained["mrr_amount"].sum()) / eligible_mrr
                if eligible_mrr
                else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cohort_month").reset_index(drop=True)


def targeted_rollout_impact(
    account_metrics: pd.DataFrame,
    target_segments: tuple[str, ...] = TARGET_ROLLOUT_SEGMENTS,
) -> pd.DataFrame:
    """Estimate current MRR impact using segment-specific rollout inputs."""
    rows = []
    for segment in target_segments:
        accounts = account_metrics.loc[account_metrics["company_size"].eq(segment)]
        control = accounts.loc[accounts["variant"].eq("control")]
        treatment = accounts.loc[accounts["variant"].eq("treatment")]
        control_rate = control["activated_7d"].mean() if len(control) else 0.0
        treatment_rate = treatment["activated_7d"].mean() if len(treatment) else 0.0
        activation_lift = float(treatment_rate - control_rate)
        activated = accounts.loc[accounts["activated_7d"]]
        activated_to_paid = (
            float(activated["current_active_customer"].mean()) if len(activated) else 0.0
        )
        current_paid = accounts.loc[accounts["current_active_customer"]]
        arpa = float(current_paid["current_mrr"].mean()) if len(current_paid) else 0.0
        incremental_activated = activation_lift * len(accounts)
        rows.append(
            {
                "company_size": segment,
                "eligible_accounts": len(accounts),
                "activation_lift": activation_lift,
                "incremental_activated": incremental_activated,
                "activated_to_paid_rate": activated_to_paid,
                "current_arpa": arpa,
                "estimated_incremental_mrr": incremental_activated
                * activated_to_paid
                * arpa,
            }
        )
    return pd.DataFrame(rows)


def churn_risk_segments(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return the account distribution across actionable churn-risk tiers."""
    return (
        account_metrics.groupby("risk_segment", observed=False, as_index=False)
        .agg(
            accounts=("org_id", "size"),
            mrr_at_risk=("current_mrr", "sum"),
            average_risk_score=("risk_score", "mean"),
        )
        .set_index("risk_segment")
        .reindex(["High", "Medium", "Low"], fill_value=0)
        .reset_index()
    )
