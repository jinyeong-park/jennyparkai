"""Organization-level lifecycle metrics for retention analysis."""

from __future__ import annotations

import hashlib
import math
from statistics import NormalDist

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


def first_key_action(
    event_logs: pd.DataFrame, organizations: pd.DataFrame
) -> pd.DataFrame:
    """Return each org's first qualifying key action, unbounded by the 7-day window.

    Ties on identical timestamps (e.g. two events logged in the same batch or
    API call) break alphabetically on event_name so every org contributes
    exactly one row.
    """
    events = event_logs.merge(
        organizations[["org_id", "created_at"]], on="org_id", how="inner"
    ).copy()
    key_events = events.loc[events["event_name"].isin(KEY_ACTION_EVENTS)].copy()
    key_events["days_from_signup"] = (
        key_events["event_timestamp"] - key_events["created_at"]
    ).dt.total_seconds().div(86_400)
    key_events = key_events.loc[key_events["days_from_signup"].ge(0)]
    key_events = key_events.sort_values(["org_id", "event_timestamp", "event_name"])
    first = key_events.groupby("org_id", as_index=False).first()
    return first[["org_id", "event_name", "days_from_signup"]].rename(
        columns={"event_name": "first_action"}
    )


def milestone_retention(
    account_metrics: pd.DataFrame, first_actions: pd.DataFrame
) -> pd.DataFrame:
    """Compare downstream retention and paid conversion by an org's first key action.

    Answers "which action is the strongest activation signal" by grouping on
    whichever of teammate_invited / integration_connected / project_created an
    org completed first, not just whether it completed all of them.
    """
    merged = account_metrics.merge(
        first_actions[["org_id", "first_action"]], on="org_id", how="inner"
    )
    rows = []
    for action, group in merged.groupby("first_action"):
        rows.append(
            {
                "first_action": action,
                "orgs": len(group),
                "paid_conversion_rate": group["paid_customer"].mean(),
                "retention_60d_rate": retention_rate(group, 60),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("retention_60d_rate", ascending=False)
        .reset_index(drop=True)
    )


def time_to_activate_trend(
    account_metrics: pd.DataFrame, first_actions: pd.DataFrame, freq: str = "M"
) -> pd.DataFrame:
    """Return P50/P90 days-to-first-action by signup cohort, to see whether
    onboarding speed is improving over time.

    P50/P90 are used instead of the mean because a handful of orgs that take
    action months after signup would otherwise inflate the average and
    misrepresent the typical onboarding experience.
    """
    merged = account_metrics[["org_id", "created_at"]].merge(
        first_actions[["org_id", "days_from_signup"]], on="org_id", how="inner"
    )
    merged["signup_period"] = merged["created_at"].dt.to_period(freq).dt.start_time
    rows = []
    for period, group in merged.groupby("signup_period"):
        rows.append(
            {
                "signup_period": period,
                "activated_orgs": len(group),
                "p50_days": group["days_from_signup"].quantile(0.5),
                "p90_days": group["days_from_signup"].quantile(0.9),
            }
        )
    return pd.DataFrame(rows).sort_values("signup_period").reset_index(drop=True)


def activation_speed_by_segment(
    account_metrics: pd.DataFrame,
    first_actions: pd.DataFrame,
    dimension: str = "company_size",
) -> pd.DataFrame:
    """Return activation rate alongside P50/P90 days-to-first-action per segment.

    A segment can look healthy on activation rate alone while still taking far
    longer to get there — this pairs the two so that gap is visible.
    """
    merged = account_metrics.merge(
        first_actions[["org_id", "days_from_signup"]], on="org_id", how="left"
    )
    rows = []
    for segment, group in merged.groupby(dimension, dropna=False, observed=False):
        rows.append(
            {
                dimension: segment,
                "signups": len(group),
                "activation_rate": group["activated_7d"].mean(),
                "p50_days_to_first_action": group["days_from_signup"].quantile(0.5),
                "p90_days_to_first_action": group["days_from_signup"].quantile(0.9),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("signups", ascending=False)
        .reset_index(drop=True)
    )


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
    integration_orgs = events.loc[
        events["event_name"].eq("integration_connected"), "org_id"
    ].unique()
    last_event = events.groupby("org_id")["event_timestamp"].max()

    summary = organizations[["org_id"]].copy()
    summary["workspace_created"] = summary["org_id"].isin(workspace_orgs)
    summary["integration_connected"] = summary["org_id"].isin(integration_orgs)
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
        "integration_connected",
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
        "integration_connected",
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


def engagement_retention_curve(
    organizations: pd.DataFrame, event_logs: pd.DataFrame, as_of_date: pd.Timestamp
) -> pd.DataFrame:
    """Return D30/D60/D90 product-engagement retention by signup cohort.

    This is a different question than `signup_cohort_retention` / `retention_rate`,
    which measure whether a *paid* subscription is still active. This measures
    whether an org had *any* product event in the day-1..30 / 31..60 / 61..90
    windows after signup, across every signup regardless of paid status — the
    classic stickiness cut. Day 0 is excluded because signup-day activity is
    onboarding, not a return visit. Cohorts that haven't reached a horizon yet
    are excluded from that horizon's denominator (maturity gating), matching the
    convention used for paid retention elsewhere in this module.
    """
    events = event_logs.merge(
        organizations[["org_id", "created_at"]], on="org_id", how="inner"
    ).copy()
    events["days_since_signup"] = (
        events["event_timestamp"] - events["created_at"]
    ).dt.total_seconds().div(86_400)

    windows = {"retention_d30": (1, 30), "retention_d60": (31, 60), "retention_d90": (61, 90)}
    active_orgs = {
        column: set(
            events.loc[
                events["days_since_signup"].between(low, high, inclusive="both"), "org_id"
            ]
        )
        for column, (low, high) in windows.items()
    }

    cohorts = organizations[["org_id", "created_at"]].copy()
    cohorts["cohort_month"] = cohorts["created_at"].dt.to_period("M").dt.to_timestamp()

    rows = []
    for cohort_month, group in cohorts.groupby("cohort_month"):
        row = {"cohort_month": cohort_month, "cohort_size": len(group)}
        for column, (_, high) in windows.items():
            mature = (cohort_month + pd.Timedelta(days=high)) <= as_of_date
            row[column] = (
                float(group["org_id"].isin(active_orgs[column]).mean()) if mature else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cohort_month").reset_index(drop=True)


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


def funnel_by_channel(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Return step-to-step lifecycle conversion by acquisition channel.

    Each rate is conditioned on the prior step's reached population (e.g.
    integration is divided by workspace-created accounts, not total signups),
    so a channel's weakest step stays visible even when its top-of-funnel
    volume looks healthy.
    """
    rows = []
    for source, accounts in account_metrics.groupby(
        "acquisition_source", dropna=False, observed=False
    ):
        signups = len(accounts)
        workspace_count = int(accounts["workspace_created"].sum())
        integration_count = int(accounts["integration_connected"].sum())
        activated_count = int(accounts["activated_7d"].sum())
        paid_count = int(accounts.loc[accounts["activated_7d"], "paid_customer"].sum())
        rows.append(
            {
                "acquisition_source": source,
                "signups": signups,
                "workspace_rate": workspace_count / signups if signups else float("nan"),
                "workspace_to_integration_rate": (
                    integration_count / workspace_count if workspace_count else float("nan")
                ),
                "activation_rate": activated_count / signups if signups else float("nan"),
                "activated_to_paid_rate": (
                    paid_count / activated_count if activated_count else float("nan")
                ),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("signups", ascending=False)
        .reset_index(drop=True)
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


def two_proportion_p_value(
    control_successes: int, control_total: int, treatment_successes: int, treatment_total: int
) -> float:
    """Two-tailed p-value for a two-proportion z-test."""
    if control_total == 0 or treatment_total == 0:
        return 1.0
    pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
    standard_error = (
        pooled * (1 - pooled) * (1 / control_total + 1 / treatment_total)
    ) ** 0.5
    if standard_error == 0:
        return 1.0
    z_score = (
        treatment_successes / treatment_total - control_successes / control_total
    ) / standard_error
    return 2 * (1 - NormalDist().cdf(abs(z_score)))


def required_sample_size(
    baseline_rate: float, mde: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Required N per variant to detect `mde` off a `baseline_rate`, at `power`.

    n = (z_alpha + z_power)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2

    Matches the formula in `sql/marts/mart_multivariate.sql`'s sample-size
    calculator so the Python and SQL answers agree.
    """
    if mde == 0:
        raise ValueError("mde must be non-zero")
    treatment_rate = baseline_rate + mde
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_power = NormalDist().inv_cdf(power)
    variance_sum = baseline_rate * (1 - baseline_rate) + treatment_rate * (1 - treatment_rate)
    return math.ceil((z_alpha + z_power) ** 2 * variance_sum / (mde**2))


def experiment_decision(
    account_metrics: pd.DataFrame,
    mde: float = 0.05,
    retention_guardrail_period: int = 60,
    hte_dimension: str = "company_size",
    alpha: float = 0.05,
    power: float = 0.8,
) -> dict:
    """Synthesize a SHIP / ITERATE / CONTINUE / KILL verdict from the primary
    metric's significance, sample-size adequacy, and guardrail checks.

    Decision tree (matches the framework in `docs/process/03_experiment_readout.md`):
      significant lift, guardrails hold      -> SHIP
      significant lift, a guardrail degraded -> ITERATE
      not significant, under-powered         -> CONTINUE (keep collecting)
      not significant, adequately powered    -> KILL (effect is negligible)

    `mde` is the smallest lift worth caring about, decided in advance (default
    5pp, matching this project's convention elsewhere) — power is evaluated
    against that pre-specified threshold, not against whatever lift happened
    to be observed. Using the observed lift as its own target would be
    circular: a truly null result has ~0 observed lift, which would demand an
    absurdly large sample to "detect," making every null result look
    under-powered regardless of how much data was actually collected.

    A guardrail counts as "degraded" only if treatment is *significantly*
    worse than control on that metric (its own two-proportion test), not just
    numerically lower — a small negative delta on a small eligible sample is
    often noise, and treating it as a hard cutoff would kill experiments over
    noise. `harmful_segment` is reported separately as a caveat, not folded
    into the verdict itself, since a positive-overall/negative-in-one-segment
    result calls for a targeted rollout conversation, not a binary verdict.
    """
    control = account_metrics.loc[account_metrics["variant"].eq("control")]
    treatment = account_metrics.loc[account_metrics["variant"].eq("treatment")]
    control_n, treatment_n = len(control), len(treatment)

    control_rate = control["activated_7d"].mean()
    treatment_rate = treatment["activated_7d"].mean()
    lift = treatment_rate - control_rate
    p_value = two_proportion_p_value(
        int(control["activated_7d"].sum()),
        control_n,
        int(treatment["activated_7d"].sum()),
        treatment_n,
    )
    significant = p_value < alpha

    required_n = required_sample_size(control_rate, mde, alpha=alpha, power=power)
    adequately_powered = min(control_n, treatment_n) >= required_n

    paid_delta = treatment["paid_customer"].mean() - control["paid_customer"].mean()
    paid_p = two_proportion_p_value(
        int(control["paid_customer"].sum()),
        control_n,
        int(treatment["paid_customer"].sum()),
        treatment_n,
    )
    paid_guardrail_broken = paid_delta < 0 and paid_p < alpha

    eligible_col = f"eligible_{retention_guardrail_period}d"
    retained_col = f"retained_{retention_guardrail_period}d"
    control_eligible = control.loc[control[eligible_col]]
    treatment_eligible = treatment.loc[treatment[eligible_col]]
    retention_delta = None
    retention_guardrail_broken = False
    if len(control_eligible) and len(treatment_eligible):
        retention_delta = (
            treatment_eligible[retained_col].mean() - control_eligible[retained_col].mean()
        )
        retention_p = two_proportion_p_value(
            int(control_eligible[retained_col].sum()),
            len(control_eligible),
            int(treatment_eligible[retained_col].sum()),
            len(treatment_eligible),
        )
        retention_guardrail_broken = retention_delta < 0 and retention_p < alpha

    guardrails_ok = not paid_guardrail_broken and not retention_guardrail_broken

    hte = (
        account_metrics.groupby([hte_dimension, "variant"], observed=False)["activated_7d"]
        .mean()
        .unstack("variant")
    )
    harmful_segment = (
        bool((hte["treatment"] - hte["control"]).lt(0).any())
        if {"control", "treatment"}.issubset(hte.columns)
        else False
    )

    if significant:
        verdict = "SHIP" if guardrails_ok else "ITERATE"
    else:
        verdict = "CONTINUE" if not adequately_powered else "KILL"

    return {
        "verdict": verdict,
        "lift": lift,
        "p_value": p_value,
        "significant": significant,
        "control_n": control_n,
        "treatment_n": treatment_n,
        "required_n_per_variant": required_n,
        "adequately_powered": adequately_powered,
        "paid_guardrail_broken": paid_guardrail_broken,
        "retention_delta": retention_delta,
        "retention_guardrail_broken": retention_guardrail_broken,
        "harmful_segment": harmful_segment,
    }


def simulate_multivariate_variants(account_metrics: pd.DataFrame) -> pd.DataFrame:
    """Split the treatment arm into 3 illustrative sub-variants via a stable hash of org_id.

    This project's real experiment data only has two arms (control/treatment)
    — there is no genuine multivariate assignment to analyze. This mirrors
    `sql/marts/mart_multivariate.sql`'s own simulation (there via
    FARM_FINGERPRINT/MOD(3) in BigQuery) so the multiple-comparisons workflow
    in `bonferroni_pairwise_results()` has a dataset to run against. It is not
    a real experiment result — it exists for the methodology only, and is
    labeled as such wherever it's shown.
    """
    labels = ["v1_guided_checklist", "v2_video_walkthrough", "v3_interactive_demo"]
    result = account_metrics.copy()
    treatment_mask = result["variant"].eq("treatment")
    bucket = result.loc[treatment_mask, "org_id"].map(
        lambda org_id: int(hashlib.md5(org_id.encode()).hexdigest(), 16) % 3
    )
    result["mv_variant"] = result["variant"]
    result.loc[treatment_mask, "mv_variant"] = bucket.map(dict(enumerate(labels)))
    return result


def bonferroni_pairwise_results(
    account_metrics_with_mv_variant: pd.DataFrame,
    metric_col: str = "activated_7d",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Pairwise-test each treatment sub-variant against control, with and
    without Bonferroni correction for the multiple-comparisons problem.

    Running k independent tests at alpha=0.05 each inflates the family-wise
    false-positive rate to 1-(1-alpha)^k — with k=3, that's ~14%, not 5%.
    Bonferroni divides alpha by k so the corrected threshold controls the
    family-wise rate back down to alpha. Expects a `mv_variant` column from
    `simulate_multivariate_variants()`.
    """
    control = account_metrics_with_mv_variant.loc[
        account_metrics_with_mv_variant["mv_variant"].eq("control")
    ]
    control_n = len(control)
    control_successes = int(control[metric_col].sum())
    control_rate = control[metric_col].mean()

    treatment_variants = sorted(
        variant
        for variant in account_metrics_with_mv_variant["mv_variant"].unique()
        if variant != "control"
    )
    k = len(treatment_variants)
    adjusted_alpha = alpha / k if k else alpha
    z_threshold_uncorrected = NormalDist().inv_cdf(1 - alpha / 2)
    z_threshold_bonferroni = NormalDist().inv_cdf(1 - adjusted_alpha / 2)

    rows = []
    for variant in treatment_variants:
        group = account_metrics_with_mv_variant.loc[
            account_metrics_with_mv_variant["mv_variant"].eq(variant)
        ]
        n = len(group)
        successes = int(group[metric_col].sum())
        rate = group[metric_col].mean()
        lift = rate - control_rate

        pooled = (control_successes + successes) / (control_n + n)
        standard_error = (pooled * (1 - pooled) * (1 / control_n + 1 / n)) ** 0.5
        z_score = (rate - control_rate) / standard_error if standard_error else 0.0

        significant_uncorrected = abs(z_score) >= z_threshold_uncorrected
        significant_bonferroni = abs(z_score) >= z_threshold_bonferroni

        if significant_bonferroni and lift > 0:
            decision = "SHIP"
        elif significant_uncorrected and not significant_bonferroni and lift > 0:
            decision = "ITERATE"
        elif lift < 0:
            decision = "KILL"
        else:
            decision = "HOLD"

        rows.append(
            {
                "variant": variant,
                "n": n,
                "control_rate": control_rate,
                "treatment_rate": rate,
                "lift": lift,
                "z_score": z_score,
                "significant_uncorrected": significant_uncorrected,
                "significant_bonferroni": significant_bonferroni,
                "decision": decision,
            }
        )

    return (
        pd.DataFrame(rows)
        .assign(adjusted_alpha=adjusted_alpha, z_threshold_bonferroni=z_threshold_bonferroni)
        .sort_values("z_score", ascending=False)
        .reset_index(drop=True)
    )


def mix_rate_decomposition(
    account_metrics: pd.DataFrame,
    segment_col: str,
    prior_period: pd.Timestamp,
    current_period: pd.Timestamp,
    freq: str = "M",
    metric_col: str = "activated_7d",
) -> pd.DataFrame:
    """Decompose a period-over-period change in an overall rate into rate, mix,
    and interaction effects per segment.

    overall rate = sum over segments of (mix x rate), so the total change is
    exactly the sum of three terms per segment:
      rate effect        = (cur_rate - prior_rate) x prior_mix   (segment got better/worse)
      mix effect         = (cur_mix  - prior_mix)  x (prior_rate - prior_overall_rate)
      interaction effect = (cur_mix  - prior_mix)  x (cur_rate - prior_rate)

    The mix effect is centered on the prior overall rate. The uncentered form
    (`Δmix x prior_rate`) has the same total, because the mix shifts sum to
    zero, but it is misleading per segment: a low-activating channel that
    grows its share drags the overall rate down, yet uncentered it shows a
    *positive* contribution simply because its rate is above zero. Centered,
    a segment's mix effect is negative exactly when it gained share while
    activating below average (or lost share while activating above it).

    The two-term form (rate + mix only) is a first-order approximation that
    silently drops the interaction term, so its "total" doesn't reconcile to
    the actual change whenever both rate and mix moved. Keeping it explicit
    makes the decomposition sum exactly.

    A segment present in only one period has no rate for the other period; its
    missing rate is filled with the observed one so the segment counts as a
    pure mix effect (a new/departed channel), rather than producing a NaN that
    drops its contribution from the total.
    """
    cohorts = account_metrics.assign(
        period=account_metrics["created_at"].dt.to_period(freq).dt.start_time
    )
    prior_period, current_period = pd.Timestamp(prior_period), pd.Timestamp(current_period)

    def _period_table(period: pd.Timestamp) -> pd.DataFrame:
        frame = cohorts.loc[cohorts["period"].eq(period)]
        table = frame.groupby(segment_col, observed=True).agg(
            signups=("org_id", "size"), rate=(metric_col, "mean")
        )
        table["mix"] = table["signups"] / table["signups"].sum() if len(table) else 0.0
        return table

    prior, current = _period_table(prior_period), _period_table(current_period)
    joined = prior.add_prefix("prior_").join(current.add_prefix("cur_"), how="outer")
    joined[["prior_signups", "cur_signups", "prior_mix", "cur_mix"]] = joined[
        ["prior_signups", "cur_signups", "prior_mix", "cur_mix"]
    ].fillna(0)
    joined["prior_rate"] = joined["prior_rate"].fillna(joined["cur_rate"])
    joined["cur_rate"] = joined["cur_rate"].fillna(joined["prior_rate"])

    rate_delta = joined["cur_rate"] - joined["prior_rate"]
    mix_delta = joined["cur_mix"] - joined["prior_mix"]
    prior_overall_rate = (joined["prior_mix"] * joined["prior_rate"]).sum()
    joined["rate_effect"] = rate_delta * joined["prior_mix"]
    joined["mix_effect"] = mix_delta * (joined["prior_rate"] - prior_overall_rate)
    joined["interaction_effect"] = mix_delta * rate_delta
    joined["total_contribution"] = (
        joined["rate_effect"] + joined["mix_effect"] + joined["interaction_effect"]
    )
    return joined.reset_index().sort_values(
        "total_contribution", key=lambda values: values.abs(), ascending=False
    ).reset_index(drop=True)


def summarize_decomposition(decomposition: pd.DataFrame) -> dict:
    """Roll segment-level effects up to the overall change and a diagnosis.

    The diagnosis compares the rate effect against everything attributable to
    who showed up (mix + interaction), since those point at different owners:
    product/UX for rate, acquisition for mix.
    """
    rate = float(decomposition["rate_effect"].sum())
    mix = float(decomposition["mix_effect"].sum())
    interaction = float(decomposition["interaction_effect"].sum())
    if abs(rate) > abs(mix + interaction):
        diagnosis = "Rate-driven (product/UX issue)"
    elif abs(mix + interaction) > abs(rate):
        diagnosis = "Mix-driven (acquisition shift)"
    else:
        diagnosis = "Mixed"
    return {
        "rate_effect": rate,
        "mix_effect": mix,
        "interaction_effect": interaction,
        "total_change": rate + mix + interaction,
        "diagnosis": diagnosis,
    }


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


def channel_ltv(
    subscriptions: pd.DataFrame,
    organizations: pd.DataFrame,
    as_of_date: pd.Timestamp,
    dimension: str = "acquisition_source",
    horizon_months: int = 24,
    target_ltv_to_cac: float = 3.0,
    bootstrap_samples: int = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """LTV proxy per segment from observed paid subscriptions, with uncertainty.

    Monthly churn is churn events divided by account-months of exposure, so
    subscriptions still active at `as_of_date` count as censored exposure rather
    than as survivors or churners. Dividing the *cumulative* churned share by
    account count instead (a common shortcut) is not a monthly rate at all: it
    is roughly the observation window's worth of churn, so it overstates monthly
    churn several-fold and understates LTV by the same factor.

    LTV = ARPA / monthly_churn assumes a constant hazard and an unbounded
    lifetime, and the implied lifetime (1 / churn) can be far longer than
    anything actually observed. Check the first assumption with
    `paid_survival_curve()`: on this project's data churn is front-loaded (none
    after month 4), so a constant-churn LTV understates the 24-month figure. `ltv_capped` truncates to `horizon_months`:
    ARPA x (1 - (1-c)^H) / c.

    Intervals come from resampling paid accounts with replacement and
    recomputing ARPA *and* churn each time, so both sources of uncertainty are
    included. (Propagating churn alone, with ARPA held fixed, badly understates
    the spread: ARPA varies a lot across accounts.)

    There is no acquisition-cost data, so CAC and LTV:CAC cannot be computed;
    `max_cac` is the most that could be spent per account while still hitting
    `target_ltv_to_cac` on the capped LTV: a budget ceiling, not a CAC.
    """
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)].merge(
        organizations[["org_id", dimension]], on="org_id", how="inner"
    )
    paid = paid.assign(
        churned=paid["status"].eq("churned"),
        exposure_end=paid["end_date"].where(paid["status"].eq("churned"), as_of_date),
    )
    paid["exposure_months"] = (
        paid["exposure_end"] - paid["start_date"]
    ).dt.days.clip(lower=0) / 30.4375

    def _capped(arpa, churn):
        with np.errstate(divide="ignore", invalid="ignore"):
            value = arpa * (1 - (1 - churn) ** horizon_months) / churn
        return np.where(churn > 0, value, np.nan)

    rng = np.random.default_rng(seed)
    rows = []
    for segment, group in paid.groupby(dimension, observed=True):
        mrr = group["mrr_amount"].to_numpy(dtype=float)
        churned = group["churned"].to_numpy(dtype=float)
        exposure = group["exposure_months"].to_numpy(dtype=float)
        n = len(group)
        events, total_exposure, arpa = churned.sum(), exposure.sum(), mrr.mean()
        churn = events / total_exposure if total_exposure else float("nan")

        draws = rng.integers(0, n, size=(bootstrap_samples, n))
        b_arpa = mrr[draws].mean(axis=1)
        b_churn = churned[draws].sum(axis=1) / exposure[draws].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            b_ltv = np.where(b_churn > 0, b_arpa / b_churn, np.nan)
        b_capped = _capped(b_arpa, b_churn)

        def _interval(values):
            if np.isnan(values).all():
                return float("nan"), float("nan")
            low, high = np.nanpercentile(values, [2.5, 97.5])
            return float(low), float(high)

        ltv_low, ltv_high = _interval(b_ltv)
        capped_low, capped_high = _interval(b_capped)
        capped = float(_capped(arpa, churn)) if churn and churn == churn else float("nan")
        rows.append(
            {
                dimension: segment,
                "paid_accounts": n,
                "arpa": float(arpa),
                "churn_events": int(events),
                "exposure_months": float(total_exposure),
                "monthly_churn": churn,
                "lifetime_months": 1 / churn if churn and churn == churn else float("nan"),
                "ltv": arpa / churn if churn and churn == churn else float("nan"),
                "ltv_low": ltv_low,
                "ltv_high": ltv_high,
                "ltv_capped": capped,
                "ltv_capped_low": capped_low,
                "ltv_capped_high": capped_high,
                "max_cac": capped / target_ltv_to_cac,
            }
        )
    return pd.DataFrame(rows).sort_values("ltv", ascending=False).reset_index(drop=True)


def paid_survival_curve(
    subscriptions: pd.DataFrame, as_of_date: pd.Timestamp, max_months: int = 24
) -> pd.DataFrame:
    """Kaplan-Meier survival and per-month churn hazard by months since paid start.

    Answers "is churn actually constant over an account's life?", the assumption
    behind `LTV = ARPA / monthly_churn`. Still-active subscriptions are censored
    at `as_of_date`. `hazard` is churn events / accounts at risk in that month,
    counting an account as at risk only if it was observed for the whole month or
    churned in it (so a partially-observed month does not dilute the rate).
    """
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)].copy()
    paid["churned"] = paid["status"].eq("churned")
    end = paid["end_date"].where(paid["churned"], as_of_date)
    paid["life_months"] = (end - paid["start_date"]).dt.days.clip(lower=0) / 30.4375

    survival = 1.0
    rows = []
    for month in range(1, max_months + 1):
        low, high = month - 1, month
        observed_full = paid["life_months"].ge(high)
        churned_in = paid["churned"] & paid["life_months"].ge(low) & paid["life_months"].lt(high)
        at_risk = int((observed_full | churned_in).sum())
        events = int(churned_in.sum())
        hazard = events / at_risk if at_risk else float("nan")
        if hazard == hazard:
            survival *= 1 - hazard
        rows.append(
            {
                "month_since_paid": month,
                "at_risk": at_risk,
                "churned": events,
                "hazard": hazard,
                "survival": survival if at_risk else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def prospective_engagement_dataset(
    event_logs: pd.DataFrame,
    organizations: pd.DataFrame,
    subscriptions: pd.DataFrame,
    as_of_date: pd.Timestamp,
    cutoffs: list[pd.Timestamp],
    horizon_days: int = 90,
    lookback_days: int = 28,
) -> pd.DataFrame:
    """One row per (paid-active account, cutoff): behavior BEFORE the cutoff, churn AFTER it.

    Validating an engagement tier by comparing its churn rate as of today is
    circular: an account that has already churned has stopped using the product,
    so "inactive" is partly an outcome, not a warning. Here features use only
    events up to the cutoff and the outcome is churn in the next `horizon_days`,
    for accounts still paying at the cutoff. Cutoffs whose horizon runs past
    `as_of_date` are dropped so no outcome is censored.
    """
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)].merge(
        organizations[["org_id", "created_at"]], on="org_id", how="inner"
    )
    frames = []
    for cutoff in cutoffs:
        cutoff = pd.Timestamp(cutoff)
        horizon_end = cutoff + pd.Timedelta(days=horizon_days)
        if horizon_end > as_of_date:
            continue
        active = paid.loc[
            paid["start_date"].le(cutoff)
            & (paid["end_date"].isna() | paid["end_date"].gt(cutoff))
        ].copy()
        seen = event_logs.loc[event_logs["event_timestamp"].le(cutoff)]
        by_org = seen.groupby("org_id")
        features = pd.DataFrame(
            {
                "last_event": by_org["event_timestamp"].max(),
                "distinct_event_types": by_org["event_name"].nunique(),
                "total_events": by_org.size(),
            }
        )
        recent = seen.loc[seen["event_timestamp"].gt(cutoff - pd.Timedelta(days=lookback_days))]
        features["active_days_recent"] = recent.groupby("org_id")["event_timestamp"].apply(
            lambda stamps: stamps.dt.date.nunique()
        )
        active = active.merge(features, left_on="org_id", right_index=True, how="left")
        active[["active_days_recent", "distinct_event_types", "total_events"]] = active[
            ["active_days_recent", "distinct_event_types", "total_events"]
        ].fillna(0)
        active["days_since_last_event"] = (cutoff - active["last_event"]).dt.days
        active["tenure_days"] = (cutoff - active["created_at"]).dt.days
        active["days_since_paid_start"] = (cutoff - active["start_date"]).dt.days
        active["churned_within_horizon"] = (
            active["status"].eq("churned") & active["end_date"].le(horizon_end)
        )
        active["cutoff"] = cutoff
        frames.append(active)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def usage_engagement_features(
    usage: pd.DataFrame,
    cutoff: pd.Timestamp,
    recent_weeks: int = 4,
    prior_weeks: int = 4,
) -> pd.DataFrame:
    """Frequency, depth, recency and trend per org from weekly usage, using only
    weeks that had fully ended by `cutoff`.

    recent = the latest `recent_weeks` full weeks; prior = the `prior_weeks`
    before that. `trend_ratio` = recent sessions / prior sessions (NaN when the
    prior window is empty) and is the "went quiet" signal a static usage level
    can't see.
    """
    cutoff = pd.Timestamp(cutoff)
    last_full = cutoff - pd.Timedelta(days=7)
    last_full = (last_full - pd.Timedelta(days=last_full.weekday())).normalize()
    weeks = [last_full - pd.Timedelta(weeks=i) for i in range(recent_weeks + prior_weeks)]
    recent, prior = weeks[:recent_weeks], weeks[recent_weeks:]

    window = usage.loc[usage["week_start"].isin(weeks)]
    sessions = window.pivot_table(index="org_id", columns="week_start", values="sessions", aggfunc="sum")
    sessions = sessions.reindex(columns=weeks).fillna(0)
    depth = window.pivot_table(index="org_id", columns="week_start", values="features_used", aggfunc="max")
    depth = depth.reindex(columns=recent)

    features = pd.DataFrame(index=sessions.index)
    features["recent_sessions"] = sessions[recent].sum(axis=1)
    features["prior_sessions"] = sessions[prior].sum(axis=1)
    features["active_weeks_recent"] = sessions[recent].gt(0).sum(axis=1)
    features["features_used"] = depth.mean(axis=1).fillna(0)
    active_weeks = sessions.gt(0)
    features["weeks_since_active"] = active_weeks.apply(
        lambda row: next((i for i, week in enumerate(weeks) if row[week]), len(weeks)), axis=1
    )
    features["trend_ratio"] = features["recent_sessions"] / features["prior_sessions"].where(
        features["prior_sessions"].gt(0)
    )
    return features


def assign_engagement_tiers(
    features: pd.DataFrame,
    power_quantile: float = 0.8,
    min_features_for_power: float = 3.0,
    at_risk_prior_min: float = 12.0,
    at_risk_ratio: float = 0.5,
) -> pd.Series:
    """Tier each org: dormant, at_risk, power or active.

    - dormant: no sessions in the recent window
    - at_risk: real usage before (`prior_sessions >= at_risk_prior_min`) AND recent
      usage at most `at_risk_ratio` of it. This is "used to be engaged, has gone
      quiet", and needs the prior window; a brand-new account with little usage is
      simply active/low, not at risk.
    - power: recent sessions in the top `1 - power_quantile` of the population passed in
      and broad feature use
    - active: everyone else with recent usage

    The power cut is relative to the population provided (e.g. paying accounts at one
    cutoff), so it never looks at churn.
    """
    power_cut = features["recent_sessions"].quantile(power_quantile)
    tier = pd.Series("active", index=features.index)
    tier[
        features["recent_sessions"].ge(power_cut)
        & features["features_used"].ge(min_features_for_power)
    ] = "power"
    tier[
        features["prior_sessions"].ge(at_risk_prior_min)
        & features["recent_sessions"].le(at_risk_ratio * features["prior_sessions"])
    ] = "at_risk"
    tier[features["recent_sessions"].eq(0)] = "dormant"
    return tier


def prospective_usage_dataset(
    usage: pd.DataFrame,
    organizations: pd.DataFrame,
    subscriptions: pd.DataFrame,
    as_of_date: pd.Timestamp,
    cutoffs: list[pd.Timestamp],
    horizon_days: int = 30,
) -> pd.DataFrame:
    """One row per (paying account, cutoff): usage features and tier from data before
    the cutoff, and whether the account churns within `horizon_days` after it.

    A decline-based warning has a short lead time (weeks, not months), so the horizon
    must match: the same tier that shows a large lift at 30 days is nearly invisible
    at 90. Cutoffs whose horizon runs past `as_of_date` are dropped. Cutoffs that are
    a week apart reuse the same accounts, so treat counts as observations, not as
    independent accounts.
    """
    paid = subscriptions.loc[subscriptions["mrr_amount"].gt(0)].merge(
        organizations[["org_id", "created_at", "acquisition_source", "company_size"]],
        on="org_id",
        how="inner",
    )
    frames = []
    for cutoff in cutoffs:
        cutoff = pd.Timestamp(cutoff)
        horizon_end = cutoff + pd.Timedelta(days=horizon_days)
        if horizon_end > as_of_date:
            continue
        active = paid.loc[
            paid["start_date"].le(cutoff)
            & (paid["end_date"].isna() | paid["end_date"].gt(cutoff))
        ].copy()
        features = usage_engagement_features(usage, cutoff).reindex(active["org_id"])
        features = features.fillna(
            {"recent_sessions": 0, "prior_sessions": 0, "active_weeks_recent": 0, "features_used": 0, "weeks_since_active": 8}
        )
        features["tier"] = assign_engagement_tiers(features)
        active = active.merge(features, left_on="org_id", right_index=True, how="left")
        active["tenure_days"] = (cutoff - active["created_at"]).dt.days
        active["churned_within_horizon"] = (
            active["status"].eq("churned") & active["end_date"].le(horizon_end)
        )
        active["cutoff"] = cutoff
        frames.append(active)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def auc_score(outcome: pd.Series, score: pd.Series) -> float:
    """Probability a random churner scores higher than a random non-churner (0.5 = no signal).

    Rank-based (Mann-Whitney), ties get average ranks, missing scores are dropped.
    """
    frame = pd.DataFrame({"outcome": outcome.astype(bool), "score": score}).dropna()
    positives = int(frame["outcome"].sum())
    negatives = len(frame) - positives
    if positives == 0 or negatives == 0:
        return float("nan")
    ranks = frame["score"].rank()
    return float((ranks[frame["outcome"]].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def churn_by_feature(
    dataset: pd.DataFrame, feature_col: str, stratify_col: str | None = None
) -> pd.DataFrame:
    """Churn rate by a feature, optionally within strata of a confounder.

    Tenure drives both "recently active" (new accounts are still onboarding) and
    churn (it happens early in an account's life), so an unstratified comparison
    can show engagement *raising* churn. Comparing within tenure strata removes
    that.
    """
    group_cols = [stratify_col, feature_col] if stratify_col else [feature_col]
    table = (
        dataset.groupby(group_cols, observed=True)["churned_within_horizon"]
        .agg(observations="size", churn_rate="mean")
        .reset_index()
    )
    return table


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
