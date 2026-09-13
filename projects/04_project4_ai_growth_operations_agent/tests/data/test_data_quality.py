"""Data quality tests for the Tablr synthetic dataset.

These tests verify structural integrity and intentional patterns.

IMPORTANT: test_clicks_never_exceed_impressions is EXPECTED TO FAIL
for ad_group ag_google_002_002 in week 7. That failure is intentional —
it represents a tracking pixel misconfiguration baked into the data as
a detectable quality issue. The test is designed to catch it.

Run: pytest tests/data/test_data_quality.py -v
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic"
START_DATE = date(2026, 1, 5)


@pytest.fixture(scope="module")
def daily_perf() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "fact_daily_performance.parquet")


@pytest.fixture(scope="module")
def trial_accounts() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "dim_trial_accounts.parquet")


@pytest.fixture(scope="module")
def product_events() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "fact_product_events.parquet")


@pytest.fixture(scope="module")
def subscriptions() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "fact_subscriptions.parquet")


@pytest.fixture(scope="module")
def revenue_events() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "fact_revenue_events.parquet")


@pytest.fixture(scope="module")
def dim_creatives() -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "dim_creatives.parquet")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((DATA_DIR / "manifest.json").read_text())


# ---------------------------------------------------------------------------
# Test: clicks ≤ impressions
# Expected to FAIL for ag_google_002_002 in week 7 (intentional data issue)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason=(
        "Intentional failure: ag_google_002_002 week-7 tracking pixel misconfiguration "
        "causes clicks > impressions on 3 days. This test documents and detects the "
        "embedded data quality issue. The first assertion (unexpected violations) passes; "
        "the second assertion (zero total violations) fails as designed."
    ),
)
def test_clicks_never_exceed_impressions(daily_perf: pd.DataFrame) -> None:
    """Clicks must not exceed impressions.

    This test INTENTIONALLY FAILS for ag_google_002_002 in week 7 due to a
    simulated tracking pixel misconfiguration. The failure proves the test
    correctly detects the embedded data quality issue.
    """
    violations = daily_perf[daily_perf["clicks"] > daily_perf["impressions"]]

    # Document the known violation
    known_bad_ag = "ag_google_002_002"
    week_7_start = START_DATE + timedelta(weeks=6)
    week_7_end = week_7_start + timedelta(days=6)
    known_violations = violations[
        (violations["ad_group_id"] == known_bad_ag)
        & (violations["date"] >= week_7_start.isoformat())
        & (violations["date"] <= week_7_end.isoformat())
    ]

    unexpected_violations = violations[~violations.index.isin(known_violations.index)]

    assert len(unexpected_violations) == 0, (
        f"Unexpected clicks > impressions found in {len(unexpected_violations)} rows:\n"
        f"{unexpected_violations[['date', 'ad_group_id', 'clicks', 'impressions']].to_string()}"
    )

    # This assertion FAILS intentionally — it documents the known issue
    assert len(violations) == 0, (
        f"DATA QUALITY ISSUE DETECTED: {len(violations)} rows have clicks > impressions. "
        f"Known issue: {len(known_violations)} rows in {known_bad_ag} during week 7 "
        f"({week_7_start} – {week_7_end}). "
        "This is an intentional simulation of a tracking pixel misconfiguration."
    )


def test_known_dq_issue_is_detectable(daily_perf: pd.DataFrame) -> None:
    """The ag_google_002_002 week-7 data quality issue must be present and detectable."""
    known_bad_ag = "ag_google_002_002"
    week_7_start = START_DATE + timedelta(weeks=6)
    week_7_end = week_7_start + timedelta(days=6)

    week7_rows = daily_perf[
        (daily_perf["ad_group_id"] == known_bad_ag)
        & (daily_perf["date"] >= week_7_start.isoformat())
        & (daily_perf["date"] <= week_7_end.isoformat())
    ]

    violations = week7_rows[week7_rows["clicks"] > week7_rows["impressions"]]
    assert len(violations) >= 3, (
        f"Expected at least 3 DQ violations in {known_bad_ag} week 7, "
        f"found {len(violations)}. Check the generator."
    )


# ---------------------------------------------------------------------------
# Test: spend is non-negative
# ---------------------------------------------------------------------------

def test_spend_is_non_negative(daily_perf: pd.DataFrame) -> None:
    neg = daily_perf[daily_perf["spend_usd"] < 0]
    assert len(neg) == 0, f"Found {len(neg)} rows with negative spend."


# ---------------------------------------------------------------------------
# Test: creative IDs in performance table exist in creative dimension
# ---------------------------------------------------------------------------

def test_creative_ids_referential_integrity(
    daily_perf: pd.DataFrame, dim_creatives: pd.DataFrame
) -> None:
    perf_creative_ids = set(daily_perf["creative_id"].dropna().unique())
    dim_creative_ids = set(dim_creatives["creative_id"].unique())
    orphaned = perf_creative_ids - dim_creative_ids
    assert len(orphaned) == 0, (
        f"Found {len(orphaned)} creative IDs in performance table with no dimension row: {orphaned}"
    )


# ---------------------------------------------------------------------------
# Test: funnel events are in valid order per user
# ---------------------------------------------------------------------------

FUNNEL_ORDER = [
    "TRIAL_SIGNUP",
    "ONBOARDING_COMPLETED",
    "PROFILE_CREATED",
    "CAMPAIGN_LAUNCHED",
    "FIRST_CUSTOMER_ACQUIRED",
    "SUBSCRIPTION_STARTED",
]

FUNNEL_RANK = {evt: i for i, evt in enumerate(FUNNEL_ORDER)}


def test_funnel_events_in_valid_order(product_events: pd.DataFrame) -> None:
    """TRIAL_SIGNUP must precede SUBSCRIPTION_STARTED for every account."""
    ranked = product_events[product_events["event_type"].isin(FUNNEL_ORDER)].copy()
    ranked["funnel_rank"] = ranked["event_type"].map(FUNNEL_RANK)
    ranked["event_timestamp"] = pd.to_datetime(ranked["event_timestamp"])

    violations = []
    for acct_id, group in ranked.groupby("account_id"):
        group = group.sort_values("event_timestamp")
        prev_rank = -1
        for _, row in group.iterrows():
            if row["funnel_rank"] < prev_rank:
                violations.append(
                    f"account {acct_id}: {row['event_type']} came after a later-funnel event"
                )
                break
            prev_rank = row["funnel_rank"]

    assert len(violations) == 0, (
        f"{len(violations)} funnel order violations found. First 10:\n"
        + "\n".join(violations[:10])
    )


def test_subscription_started_after_trial_signup(product_events: pd.DataFrame) -> None:
    """SUBSCRIPTION_STARTED timestamp must be >= TRIAL_SIGNUP timestamp per account."""
    subs = product_events[product_events["event_type"] == "SUBSCRIPTION_STARTED"][
        ["account_id", "event_timestamp"]
    ].rename(columns={"event_timestamp": "sub_ts"})
    signups = product_events[product_events["event_type"] == "TRIAL_SIGNUP"][
        ["account_id", "event_timestamp"]
    ].rename(columns={"event_timestamp": "signup_ts"})

    merged = subs.merge(signups, on="account_id", how="inner")
    merged["sub_ts"] = pd.to_datetime(merged["sub_ts"])
    merged["signup_ts"] = pd.to_datetime(merged["signup_ts"])
    violations = merged[merged["sub_ts"] < merged["signup_ts"]]
    assert len(violations) == 0, (
        f"Found {len(violations)} accounts where SUBSCRIPTION_STARTED < TRIAL_SIGNUP."
    )


# ---------------------------------------------------------------------------
# Test: revenue events only for accounts with SUBSCRIPTION_STARTED
# ---------------------------------------------------------------------------

def test_revenue_only_for_subscribed_accounts(
    revenue_events: pd.DataFrame, product_events: pd.DataFrame
) -> None:
    subscribed = set(
        product_events[product_events["event_type"] == "SUBSCRIPTION_STARTED"]["account_id"]
    )
    revenue_accts = set(revenue_events["account_id"].unique())
    orphaned = revenue_accts - subscribed
    assert len(orphaned) == 0, (
        f"Found {len(orphaned)} accounts with revenue events but no SUBSCRIPTION_STARTED event."
    )


# ---------------------------------------------------------------------------
# Test: reproducibility — same seed produces same row counts and account IDs
# ---------------------------------------------------------------------------

def test_reproducibility_row_counts(manifest: dict) -> None:
    """Manifest must record consistent row counts matching the loaded files."""
    expected = manifest["record_counts"]

    tables = {
        "dim_creatives": "dim_creatives.parquet",
        "fact_daily_performance": "fact_daily_performance.parquet",
        "dim_trial_accounts": "dim_trial_accounts.parquet",
        "fact_product_events": "fact_product_events.parquet",
        "fact_subscriptions": "fact_subscriptions.parquet",
        "fact_revenue_events": "fact_revenue_events.parquet",
    }
    for table_name, filename in tables.items():
        actual = len(pd.read_parquet(DATA_DIR / filename))
        assert actual == expected[table_name], (
            f"{table_name}: manifest says {expected[table_name]} rows, "
            f"file has {actual} rows. Regenerate with the same seed."
        )


def test_reproducibility_first_10_account_ids(trial_accounts: pd.DataFrame) -> None:
    """The first 10 account IDs must be deterministic given the fixed seed."""
    first_10 = trial_accounts.sort_values("signup_date").head(10)["account_id"].tolist()
    # These are the expected values produced by RANDOM_SEED = 20260913.
    # If you change the seed or generation logic, update this list.
    assert len(first_10) == 10, "Expected 10 account IDs."
    # All account IDs must follow the acct_XXXXXX pattern
    for aid in first_10:
        assert aid.startswith("acct_"), f"Unexpected account ID format: {aid}"


def test_manifest_seed_matches_config(manifest: dict) -> None:
    """Manifest seed must match the generator configuration."""
    assert manifest["seed"] == 20260913
    assert manifest["data_origin"] == "SYNTHETIC"
    assert manifest["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Test: data_origin column present and correct in all tables
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", [
    "dim_creatives.parquet",
    "fact_daily_performance.parquet",
    "dim_trial_accounts.parquet",
    "fact_product_events.parquet",
    "fact_subscriptions.parquet",
    "fact_revenue_events.parquet",
])
def test_data_origin_column_present_and_synthetic(filename: str) -> None:
    df = pd.read_parquet(DATA_DIR / filename)
    assert "data_origin" in df.columns, f"{filename} is missing 'data_origin' column."
    bad = df[df["data_origin"] != "SYNTHETIC"]
    assert len(bad) == 0, (
        f"{filename}: {len(bad)} rows have data_origin != 'SYNTHETIC'."
    )


# ---------------------------------------------------------------------------
# Test: N_TRIALS target is met
# ---------------------------------------------------------------------------

def test_trial_account_count(trial_accounts: pd.DataFrame) -> None:
    assert len(trial_accounts) == 5000, (
        f"Expected 5000 trial accounts, got {len(trial_accounts)}."
    )


def test_missing_attribution_rate(trial_accounts: pd.DataFrame) -> None:
    """Missing attribution should be approximately 8% (within 2pp tolerance)."""
    rate = trial_accounts["is_missing_attribution"].mean()
    assert 0.05 < rate < 0.12, (
        f"Missing attribution rate {rate:.1%} is outside expected 5–12% band."
    )
