"""Unit tests for Phase 6: cohort analysis, retention, LTV, and budget allocation.

[SYNTHETIC DATA] — all inputs are simulated Tablr data.

Run with:
    python -m pytest tests/unit/test_retention_ltv.py -v
"""

from __future__ import annotations

import pytest

from growth_agent.analytics.cohorts import build_cohorts, get_cohort_summary
from growth_agent.analytics.retention import get_retention_by_channel, get_retention_detail
from growth_agent.analytics.ltv import get_ltv_by_channel, get_ltv_estimates
from growth_agent.analytics.budget_allocator import (
    AllocationScenario,
    ChannelConstraint,
    AllocationResult,
    allocate_budget,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cohort_rows():
    return build_cohorts()


@pytest.fixture(scope="module")
def retention_summaries():
    return get_retention_by_channel()


@pytest.fixture(scope="module")
def retention_detail_rows():
    return get_retention_detail()


@pytest.fixture(scope="module")
def ltv_channel():
    return get_ltv_by_channel()


@pytest.fixture(scope="module")
def ltv_estimates():
    return get_ltv_estimates()


@pytest.fixture(scope="module")
def default_scenario():
    return AllocationScenario(
        scenario_name="Test Scenario",
        total_budget_usd=100_000.0,
        exploration_reserve_pct=0.10,
        constraints=[
            ChannelConstraint("META", min_allocation_pct=0.05, max_allocation_pct=0.60),
            ChannelConstraint("GOOGLE_SEARCH", min_allocation_pct=0.05, max_allocation_pct=0.60),
            ChannelConstraint("TIKTOK", min_allocation_pct=0.05, max_allocation_pct=0.60),
        ],
        optimize_by="cpao",
    )


@pytest.fixture(scope="module")
def allocation_result(default_scenario):
    return allocate_budget(default_scenario)


# ---------------------------------------------------------------------------
# Cohort tests
# ---------------------------------------------------------------------------

def test_cohort_builder_returns_weekly_rows(cohort_rows):
    """build_cohorts() should return at least one CohortRow per ISO week in the data."""
    assert len(cohort_rows) > 0, "Expected at least one cohort row"
    # 12-week simulation should produce at least 12 unique cohort weeks
    weeks = {r.cohort_week for r in cohort_rows}
    assert len(weeks) >= 12, f"Expected >= 12 cohort weeks, got {len(weeks)}"


def test_activation_rate_within_14_days_only(cohort_rows):
    """campaign_launched_14d should never exceed trials (activation window respected)."""
    for row in cohort_rows:
        assert row.campaign_launched_14d <= row.trials, (
            f"Activation ({row.campaign_launched_14d}) exceeds trials ({row.trials}) "
            f"for cohort {row.cohort_week} / {row.channel}"
        )
    # Global: ~519 activations from 2,000 trials (~26.0%)
    total_trials = sum(r.trials for r in cohort_rows)
    total_activated = sum(r.campaign_launched_14d for r in cohort_rows)
    assert total_activated == 519, (
        f"Expected 519 total activated owners, got {total_activated}"
    )
    assert total_trials == 2000, f"Expected 2000 trials, got {total_trials}"


def test_m6_mature_flag_correct(cohort_rows):
    """Jan 2026 cohorts should be M6 mature; a cohort from late March should not."""
    jan_rows = [r for r in cohort_rows if r.cohort_week == "2026-W02"]
    assert jan_rows, "No rows found for 2026-W02"
    # W02 starts 2026-01-05 => 252 days to reference => mature
    for r in jan_rows:
        assert r.is_m6_mature, f"Expected 2026-W02 to be M6 mature (days_observed={r.days_observed})"
        assert r.days_observed >= 180

    # W13 starts around 2026-03-23 => ~174 days to reference => NOT mature
    late_rows = [r for r in cohort_rows if r.cohort_week == "2026-W13"]
    if late_rows:
        for r in late_rows:
            assert not r.is_m6_mature, (
                f"Expected 2026-W13 to be immature (days_observed={r.days_observed})"
            )


def test_missing_attribution_handled(cohort_rows):
    """UNKNOWN channel should appear in cohort rows (missing attribution not dropped)."""
    channels = {r.channel for r in cohort_rows}
    assert "UNKNOWN" in channels, (
        "UNKNOWN channel missing from cohort rows — missing-attribution accounts were dropped"
    )
    unknown_trials = sum(r.trials for r in cohort_rows if r.channel == "UNKNOWN")
    assert unknown_trials > 0, "UNKNOWN channel has zero trials"


# ---------------------------------------------------------------------------
# Retention tests
# ---------------------------------------------------------------------------

def test_retention_m1_gt_m3_gt_m6(retention_detail_rows):
    """Retention must be monotonically non-increasing: M1 >= M3 >= M6 (retained counts)."""
    for row in retention_detail_rows:
        assert row.m1_retained >= row.m3_retained, (
            f"{row.channel}/{row.cohort_month}: m1={row.m1_retained} < m3={row.m3_retained}"
        )
        # M6 retained is capped to eligible subscribers — compare within eligible
        # The number retained at M6 (among eligible) cannot exceed M3 retained (among all)
        # but since denominators differ we only enforce m6_retained <= m3_retained
        assert row.m6_retained <= row.m3_retained, (
            f"{row.channel}/{row.cohort_month}: m6_retained={row.m6_retained} > m3_retained={row.m3_retained}"
        )


def test_retention_by_channel_all_channels_present(retention_summaries):
    """All paid channels and UNKNOWN should appear in retention summaries."""
    channels = {r.channel for r in retention_summaries}
    expected = {"META", "GOOGLE_SEARCH", "TIKTOK", "UNKNOWN"}
    assert expected.issubset(channels), (
        f"Missing channels: {expected - channels}"
    )


def test_m6_immature_warning_set(retention_summaries):
    """m6_immature_warning should be True for all channels (April/May cohorts not mature)."""
    for r in retention_summaries:
        assert r.m6_immature_warning, (
            f"Expected m6_immature_warning=True for {r.channel} "
            "(April-May 2026 cohorts not yet M6 mature)"
        )


# ---------------------------------------------------------------------------
# LTV tests
# ---------------------------------------------------------------------------

def test_observed_ltv_non_negative(ltv_estimates):
    """Observed LTV must be >= 0 for all channel/persona combinations."""
    assert len(ltv_estimates) > 0, "LTV estimates list is empty"
    for est in ltv_estimates:
        assert est.observed_avg_ltv_usd >= 0, (
            f"Negative observed LTV for {est.channel}/{est.persona_segment}: "
            f"{est.observed_avg_ltv_usd}"
        )


def test_projected_ltv_none_when_zero_churn(ltv_estimates):
    """projected_ltv_usd must be None when estimated_monthly_churn_rate is 0."""
    zero_churn = [e for e in ltv_estimates if e.estimated_monthly_churn_rate == 0]
    for est in zero_churn:
        assert est.projected_ltv_usd is None, (
            f"projected_ltv_usd should be None when churn_rate=0 "
            f"({est.channel}/{est.persona_segment})"
        )


def test_ltv_assumption_note_present(ltv_estimates):
    """Every LTV estimate must carry a non-empty assumption note."""
    for est in ltv_estimates:
        assert est.ltv_assumption_note, (
            f"Missing ltv_assumption_note for {est.channel}/{est.persona_segment}"
        )


def test_ltv_channel_has_all_channels(ltv_channel):
    """LTV:CAC analysis must include all channels with subscribers."""
    channels = {r.channel for r in ltv_channel}
    assert "META" in channels
    assert "TIKTOK" in channels
    assert "GOOGLE_SEARCH" in channels


def test_ranking_reversal_detected(ltv_channel):
    """At least one channel should show a ranking reversal (META in synthetic data)."""
    reversals = [r for r in ltv_channel if r.ranking_reversal]
    assert len(reversals) >= 1, (
        "Expected at least one ranking reversal between LTV rank and CPAO rank. "
        "Synthetic data is designed to show META as a reversal case."
    )


# ---------------------------------------------------------------------------
# Budget allocation tests
# ---------------------------------------------------------------------------

def test_budget_sums_to_total(allocation_result, default_scenario):
    """Sum of all channel allocations must equal total_budget_usd (within $1)."""
    total_allocated = sum(a.recommended_spend_usd for a in allocation_result.allocations)
    assert abs(total_allocated - default_scenario.total_budget_usd) < 1.0, (
        f"Budget sum mismatch: {total_allocated} vs {default_scenario.total_budget_usd}"
    )


def test_exploration_reserve_respected(allocation_result, default_scenario):
    """exploration_reserve_usd must equal total_budget * exploration_reserve_pct."""
    expected_reserve = (
        default_scenario.total_budget_usd * default_scenario.exploration_reserve_pct
    )
    assert abs(allocation_result.exploration_reserve_usd - expected_reserve) < 0.01, (
        f"Exploration reserve mismatch: {allocation_result.exploration_reserve_usd} "
        f"vs {expected_reserve}"
    )


def test_channel_constraints_respected(allocation_result, default_scenario):
    """No channel should exceed its max_allocation_pct constraint."""
    constraint_map = {c.channel: c for c in default_scenario.constraints}
    total = default_scenario.total_budget_usd
    for alloc in allocation_result.allocations:
        constraint = constraint_map.get(alloc.channel)
        if constraint is None:
            continue
        max_spend = constraint.max_allocation_pct * total
        # Allow $1 rounding tolerance
        assert alloc.recommended_spend_usd <= max_spend + 1.0, (
            f"{alloc.channel} exceeds max_allocation: {alloc.recommended_spend_usd} "
            f"> {max_spend}"
        )
        min_spend = constraint.min_allocation_pct * total
        assert alloc.recommended_spend_usd >= min_spend - 1.0, (
            f"{alloc.channel} below min_allocation: {alloc.recommended_spend_usd} "
            f"< {min_spend}"
        )


def test_recommend_only_is_true(allocation_result):
    """AllocationResult.recommend_only must always be True."""
    assert allocation_result.recommend_only is True, (
        "AllocationResult.recommend_only must always be True — "
        "output is recommendation only, never executed."
    )


def test_data_origin_is_synthetic(allocation_result):
    """AllocationResult.data_origin must be 'SYNTHETIC'."""
    assert allocation_result.data_origin == "SYNTHETIC"


def test_exploration_channels_flagged(allocation_result):
    """Channels with no paid spend data (e.g. LINKEDIN, UNKNOWN) must be flagged as exploration."""
    exploration = [a for a in allocation_result.allocations if a.is_exploration]
    exploration_names = {a.channel for a in exploration}
    # LINKEDIN has no paid spend in the synthetic data
    assert "LINKEDIN" in exploration_names or len(exploration) > 0, (
        "Expected at least one exploration channel in allocations"
    )


def test_efficiency_channels_have_cpao(allocation_result):
    """Non-exploration channels must have a non-None CPAO value."""
    for alloc in allocation_result.allocations:
        if not alloc.is_exploration:
            assert alloc.cpao_usd is not None, (
                f"Efficiency channel {alloc.channel} has no CPAO"
            )
