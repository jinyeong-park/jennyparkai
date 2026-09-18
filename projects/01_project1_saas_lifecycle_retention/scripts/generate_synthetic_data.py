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
            if rng.random() < 0.60:
                plan = str(rng.choice(plans, p=[0.30, 0.38, 0.24, 0.08]))
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


if __name__ == "__main__":
    generate_dataset(Path(__file__).resolve().parents[1] / "data" / "raw")
