"""Reproducibility tests: running the generator twice with the same seed
must produce identical outputs.

These tests run the generator in-process twice and compare row counts and
key column values. They do not write to disk — they use temporary directories.

Run: pytest tests/data/test_reproducibility.py -v
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helper: import generate_synthetic_data as a module without executing main()
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "generate_synthetic_data.py"


def _load_generator_module():
    """Dynamically load the generator script as a Python module."""
    spec = importlib.util.spec_from_file_location("gen_synthetic", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_generation(tmp_dir: Path) -> dict[str, pd.DataFrame]:
    """Run the full generation pipeline and return DataFrames (not saved to disk)."""
    mod = _load_generator_module()
    rng = np.random.default_rng(mod.RANDOM_SEED)

    dim_creatives = mod.build_creative_dimension(rng)
    daily_perf = mod.generate_daily_performance(dim_creatives, rng)
    trial_accounts = mod.generate_trial_accounts(daily_perf, dim_creatives, rng)
    product_events = mod.generate_product_events(trial_accounts, rng)
    subscriptions = mod.generate_subscriptions(trial_accounts, product_events, rng)
    revenue_events = mod.generate_revenue_events(subscriptions, rng)

    return {
        "dim_creatives": dim_creatives,
        "fact_daily_performance": daily_perf,
        "dim_trial_accounts": trial_accounts,
        "fact_product_events": product_events,
        "fact_subscriptions": subscriptions,
        "fact_revenue_events": revenue_events,
    }


# ---------------------------------------------------------------------------
# Fixtures: run twice with captured stdout suppressed
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def run_a(tmp_path_factory) -> dict[str, pd.DataFrame]:
    tmp = tmp_path_factory.mktemp("run_a")
    return _run_generation(tmp)


@pytest.fixture(scope="module")
def run_b(tmp_path_factory) -> dict[str, pd.DataFrame]:
    tmp = tmp_path_factory.mktemp("run_b")
    return _run_generation(tmp)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("table_name", [
    "dim_creatives",
    "fact_daily_performance",
    "dim_trial_accounts",
    "fact_product_events",
    "fact_subscriptions",
    "fact_revenue_events",
])
def test_row_counts_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
    table_name: str,
) -> None:
    """Both runs must produce the same number of rows for every table."""
    count_a = len(run_a[table_name])
    count_b = len(run_b[table_name])
    assert count_a == count_b, (
        f"{table_name}: run A has {count_a} rows, run B has {count_b} rows. "
        "Generation is not reproducible — check rng state."
    )


def test_trial_account_ids_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
) -> None:
    """First 10 account IDs (by signup date) must be identical across runs."""
    ids_a = run_a["dim_trial_accounts"].sort_values("signup_date").head(10)["account_id"].tolist()
    ids_b = run_b["dim_trial_accounts"].sort_values("signup_date").head(10)["account_id"].tolist()
    assert ids_a == ids_b, (
        f"First 10 account IDs differ between runs:\n  A: {ids_a}\n  B: {ids_b}"
    )


def test_total_spend_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
) -> None:
    """Total spend across all rows must be identical (within floating-point rounding)."""
    spend_a = run_a["fact_daily_performance"]["spend_usd"].sum()
    spend_b = run_b["fact_daily_performance"]["spend_usd"].sum()
    assert abs(spend_a - spend_b) < 0.01, (
        f"Total spend differs: run A = {spend_a:.2f}, run B = {spend_b:.2f}."
    )


def test_subscription_count_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
) -> None:
    count_a = len(run_a["fact_subscriptions"])
    count_b = len(run_b["fact_subscriptions"])
    assert count_a == count_b, (
        f"Subscription counts differ: run A = {count_a}, run B = {count_b}."
    )


def test_creative_ids_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
) -> None:
    ids_a = sorted(run_a["dim_creatives"]["creative_id"].tolist())
    ids_b = sorted(run_b["dim_creatives"]["creative_id"].tolist())
    assert ids_a == ids_b, "Creative IDs differ between runs."


def test_missing_attribution_count_identical(
    run_a: dict[str, pd.DataFrame],
    run_b: dict[str, pd.DataFrame],
) -> None:
    miss_a = run_a["dim_trial_accounts"]["is_missing_attribution"].sum()
    miss_b = run_b["dim_trial_accounts"]["is_missing_attribution"].sum()
    assert miss_a == miss_b, (
        f"Missing attribution counts differ: run A = {miss_a}, run B = {miss_b}."
    )
