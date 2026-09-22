"""Generate deterministic synthetic lifecycle data for the SaaS retention project."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


REFERENCE_DATE = datetime(2025, 1, 1)
EXPERIMENT_ID = "onboarding_guided_v1"


def _timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def _event_properties(properties: dict[str, object]) -> str:
    return json.dumps(properties, sort_keys=True, separators=(",", ":"))


def generate_dataset(
    output_dir: Path, org_count: int = 2500, seed: int = 42
) -> dict[str, pd.DataFrame]:
    """Create lifecycle tables and write them as CSV files to ``output_dir``."""
    if org_count < 1:
        raise ValueError("org_count must be at least 1")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    sizes = np.array(["SMB", "Mid-Market", "Enterprise"])
    industries = np.array(["Technology", "Professional Services", "Healthcare", "Education", "Financial Services", "Retail"])
    sources = np.array(["Organic Search", "Paid Search", "Content", "Referral", "Partner", "Product-Led"])
    regions = np.array(["North America", "Europe", "Asia-Pacific", "Latin America"])
    plans = np.array(["Starter", "Growth", "Business", "Enterprise"])
    plan_prices = {"Starter": 49.0, "Growth": 149.0, "Business": 399.0, "Enterprise": 999.0}

    organizations: list[dict[str, object]] = []
    assignments: list[dict[str, object]] = []
    users: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    subscriptions: list[dict[str, object]] = []
    user_number = 1
    event_number = 1
    subscription_number = 1

    for org_number in range(1, org_count + 1):
        org_id = f"org_{org_number:05d}"
        company_size = str(rng.choice(sizes, p=[0.60, 0.28, 0.12]))
        created_at = REFERENCE_DATE + timedelta(days=int(rng.integers(0, 365)))
        organizations.append(
            {
                "org_id": org_id,
                "created_at": _timestamp(created_at),
                "industry": str(rng.choice(industries)),
                "company_size": company_size,
                "acquisition_source": str(rng.choice(sources, p=[0.24, 0.18, 0.14, 0.15, 0.10, 0.19])),
                "region": str(rng.choice(regions, p=[0.52, 0.23, 0.15, 0.10])),
            }
        )

        variant = str(rng.choice(["control", "treatment"]))
        assignments.append(
            {
                "experiment_id": EXPERIMENT_ID,
                "org_id": org_id,
                "variant": variant,
                "assigned_at": _timestamp(created_at),
                "eligible_segment": company_size,
            }
        )

        user_count = int(rng.integers(1, 9))
        org_users: list[tuple[str, datetime, bool]] = []
        for user_index in range(user_count):
            user_id = f"user_{user_number:06d}"
            user_number += 1
            signup = created_at + timedelta(hours=int(rng.integers(0, 48)))
            is_admin = user_index == 0
            users.append(
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": "admin" if is_admin else str(rng.choice(["member", "viewer"], p=[0.78, 0.22])),
                    "signup_timestamp": _timestamp(signup),
                    "is_admin": is_admin,
                }
            )
            org_users.append((user_id, signup, is_admin))

        admin_id, signup, _ = org_users[0]
        lift = {"SMB": 0.18, "Mid-Market": 0.12, "Enterprise": 0.06}[company_size]
        workspace_probability = {"SMB": 0.58, "Mid-Market": 0.54, "Enterprise": 0.50}[company_size]
        workspace_probability += lift if variant == "treatment" else 0.0
        workspace_created = bool(rng.random() < workspace_probability)
        if workspace_created:
            workspace_time = signup + timedelta(hours=int(rng.integers(2, 72)))
            events.append(
                {
                    "event_id": f"event_{event_number:08d}",
                    "user_id": admin_id,
                    "org_id": org_id,
                    "event_name": "workspace_created",
                    "event_timestamp": _timestamp(workspace_time),
                    "event_properties": _event_properties({"source": "onboarding", "workspace_type": "team"}),
                }
            )
            event_number += 1

        activation_probability = {"SMB": 0.68, "Mid-Market": 0.63, "Enterprise": 0.59}[company_size]
        activation_probability += lift if variant == "treatment" else 0.0
        activated = workspace_created and bool(rng.random() < activation_probability)
        if activated:
            second_event = str(rng.choice(["integration_connected", "project_created"]))
            second_time = signup + timedelta(days=int(rng.integers(1, 7)), hours=int(rng.integers(0, 12)))
            events.append(
                {
                    "event_id": f"event_{event_number:08d}",
                    "user_id": admin_id,
                    "org_id": org_id,
                    "event_name": second_event,
                    "event_timestamp": _timestamp(second_time),
                    "event_properties": _event_properties({"source": "onboarding", "variant": variant}),
                }
            )
            event_number += 1

        # signup_completed: one-time event at signup
        events.append(
            {
                "event_id": f"event_{event_number:08d}",
                "user_id": admin_id,
                "org_id": org_id,
                "event_name": "signup_completed",
                "event_timestamp": _timestamp(signup),
                "event_properties": _event_properties({"source": "product", "variant": variant}),
            }
        )
        event_number += 1

        # Ongoing activity: project_created events after the activation window
        # (workspace_created is intentionally excluded — workspace is created once)
        if activated:
            for _ in range(int(rng.integers(1, 4))):
                ongoing_time = signup + timedelta(days=int(rng.integers(8, 121)), hours=int(rng.integers(0, 24)))
                events.append(
                    {
                        "event_id": f"event_{event_number:08d}",
                        "user_id": admin_id,
                        "org_id": org_id,
                        "event_name": "project_created",
                        "event_timestamp": _timestamp(ongoing_time),
                        "event_properties": _event_properties({"source": "product", "variant": variant}),
                    }
                )
                event_number += 1
        for user_id, user_signup, is_admin in org_users:
            if not is_admin and rng.random() < 0.65:
                event_time = user_signup + timedelta(days=int(rng.integers(0, 121)), hours=int(rng.integers(0, 24)))
                events.append(
                    {
                        "event_id": f"event_{event_number:08d}",
                        "user_id": user_id,
                        "org_id": org_id,
                        "event_name": "teammate_invited",
                        "event_timestamp": _timestamp(event_time),
                        "event_properties": _event_properties({"source": "collaboration", "invited_by_admin": True}),
                    }
                )
                event_number += 1

        # Trial: 66% of accounts start a free trial
        if rng.random() < 0.66:
            trial_start = created_at.date() + timedelta(days=int(rng.integers(1, 8)))
            trial_end = trial_start + timedelta(days=14)
            subscriptions.append(
                {
                    "subscription_id": f"sub_{subscription_number:06d}",
                    "org_id": org_id,
                    "plan_type": "Trial",
                    "mrr_amount": 0.0,
                    "start_date": trial_start.isoformat(),
                    "end_date": trial_end.isoformat(),
                    "status": "trial_ended",
                    "churn_reason": "",
                }
            )
            subscription_number += 1

            # Paid conversion: ~60% of trial starters convert to paid
            # Plan distribution is tied to company size — Enterprise accounts
            # buy higher-tier plans more often, SMB skews toward Starter/Growth.
            if rng.random() < 0.60:
                plan_probs = {
                    "SMB":         [0.55, 0.33, 0.10, 0.02],  # ARPA ≈ $136
                    "Mid-Market":  [0.20, 0.45, 0.28, 0.07],  # ARPA ≈ $259
                    "Enterprise":  [0.05, 0.20, 0.42, 0.33],  # ARPA ≈ $530
                }[company_size]
                plan = str(rng.choice(plans, p=plan_probs))
                paid_start = trial_end + timedelta(days=int(rng.integers(0, 4)))
                churned = bool(rng.random() < 0.22)
                paid_end = paid_start + timedelta(days=int(rng.integers(30, 121))) if churned else None
                subscriptions.append(
                    {
                        "subscription_id": f"sub_{subscription_number:06d}",
                        "org_id": org_id,
                        "plan_type": plan,
                        "mrr_amount": plan_prices[plan],
                        "start_date": paid_start.isoformat(),
                        "end_date": paid_end.isoformat() if paid_end else "",
                        "status": "churned" if churned else "active",
                        "churn_reason": str(rng.choice(["Low adoption", "Budget", "Missing feature", ""], p=[0.35, 0.25, 0.20, 0.20])) if churned else "",
                    }
                )
                subscription_number += 1

    tables = {
        "organizations": pd.DataFrame(organizations),
        "users": pd.DataFrame(users),
        "event_logs": pd.DataFrame(events),
        "subscriptions": pd.DataFrame(subscriptions),
        "experiment_assignments": pd.DataFrame(assignments),
    }
    for name, frame in tables.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
    return tables


USAGE_SEED_OFFSET = 1_000
USAGE_AS_OF = datetime(2026, 4, 27)


def generate_usage_dataset(
    data_dir: Path, seed: int = 42, as_of: datetime = USAGE_AS_OF
) -> pd.DataFrame:
    """Write ``usage_weekly.csv``: weekly product-usage telemetry with a PLANTED signal.

    The five core tables (see ``generate_dataset``) have no ongoing usage and their
    churn is an independent coin flip, so nothing in them can predict churn. This adds
    a separate table, generated from those tables with its own RNG stream, so the
    existing CSVs are read but never modified and every existing number stays valid.

    Planted relationships (this is a positive control, not a finding about real users):
      * usage level rises with company size, activation, being a paying customer and an
        Enterprise plan, and is lower for accounts that will eventually churn
      * accounts that churn decline steadily over the 3-6 weeks before churning
      * ~12% of non-churners have a temporary dip, so the signal is imperfect
      * accounts that never pay fade out after onboarding
      * acquisition channel has NO effect, so it works as a negative control
    Columns: org_id, week_start (Monday), active_users, sessions, features_used.
    """
    data_dir = Path(data_dir)
    organizations = pd.read_csv(data_dir / "organizations.csv", parse_dates=["created_at"])
    users = pd.read_csv(data_dir / "users.csv")
    events = pd.read_csv(data_dir / "event_logs.csv", parse_dates=["event_timestamp"])
    subscriptions = pd.read_csv(data_dir / "subscriptions.csv", parse_dates=["start_date", "end_date"])
    rng = np.random.default_rng(seed + USAGE_SEED_OFFSET)

    user_counts = users.groupby("org_id").size()
    created = organizations.set_index("org_id")["created_at"]
    key_events = events.loc[
        events["event_name"].isin(["teammate_invited", "integration_connected", "project_created"])
    ]
    early = key_events.merge(created.rename("created_at"), left_on="org_id", right_index=True)
    early = early.loc[(early["event_timestamp"] - early["created_at"]).dt.days.between(0, 7)]
    workspace_orgs = set(events.loc[events["event_name"].eq("workspace_created"), "org_id"])
    activated = set(early["org_id"]) & workspace_orgs
    paid = (
        subscriptions.loc[subscriptions["mrr_amount"].gt(0)]
        .sort_values("start_date")
        .drop_duplicates("org_id", keep="first")
        .set_index("org_id")
    )
    size_shift = {"SMB": 0.0, "Mid-Market": 0.4, "Enterprise": 0.8}

    rows: list[dict[str, object]] = []
    for org in organizations.itertuples(index=False):
        is_paid = org.org_id in paid.index
        churner = is_paid and paid.loc[org.org_id, "status"] == "churned"
        level = (
            size_shift[org.company_size]
            + 0.4 * (org.org_id in activated)
            + 0.5 * is_paid
            + 0.3 * (is_paid and paid.loc[org.org_id, "plan_type"] == "Enterprise")
            - 0.35 * churner
        )
        theta = float(np.exp(rng.normal(level, 0.6)))
        n_users = int(user_counts.get(org.org_id, 1))

        first_week = org.created_at.normalize() - pd.Timedelta(days=org.created_at.weekday())
        churn_week = None
        decline_weeks = int(rng.integers(3, 7))
        if churner:
            end = pd.Timestamp(paid.loc[org.org_id, "end_date"])
            churn_week = (end.normalize() - pd.Timedelta(days=end.weekday()) - first_week).days // 7
        dip_start, dip_len = (
            (int(rng.integers(6, 30)), int(rng.integers(3, 6)))
            if (not churner and rng.random() < 0.12)
            else (None, 0)
        )

        week = 0
        while first_week + pd.Timedelta(weeks=week) <= pd.Timestamp(as_of):
            if churn_week is not None and week >= churn_week:
                break
            if not is_paid and week > 26:
                break
            factor = np.exp(-week / 8) if not is_paid else 1.0
            if churn_week is not None and churn_week - week <= decline_weeks:
                factor *= 0.15 + 0.85 * (churn_week - week) / decline_weeks
            if dip_start is not None and dip_start <= week < dip_start + dip_len:
                factor *= 0.4
            sessions = int(rng.poisson(6 * theta * factor))
            if sessions == 0:
                active_users = features_used = 0
            else:
                active_users = min(n_users, 1 + int(rng.binomial(max(n_users - 1, 0), min(0.9, 0.15 * theta * factor))))
                features_used = min(6, 1 + int(rng.poisson(0.5 + 0.7 * np.log1p(0.5 * sessions))))
            rows.append(
                {
                    "org_id": org.org_id,
                    "week_start": (first_week + pd.Timedelta(weeks=week)).date().isoformat(),
                    "active_users": active_users,
                    "sessions": sessions,
                    "features_used": features_used,
                }
            )
            week += 1

    usage = pd.DataFrame(rows)
    usage.to_csv(data_dir / "usage_weekly.csv", index=False)
    return usage


if __name__ == "__main__":
    raw_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    generate_dataset(raw_dir)
    generate_usage_dataset(raw_dir)
