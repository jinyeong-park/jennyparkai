from pathlib import Path

import pandas as pd
import pytest

from app.utils.data_loader import load_tables
from app.utils.metrics import (
    activation_completion_days,
    activation_speed_by_segment,
    assign_engagement_tiers,
    auc_score,
    bonferroni_pairwise_results,
    build_account_metrics,
    channel_ltv,
    churn_by_feature,
    churn_risk_segments,
    engagement_retention_curve,
    experiment_decision,
    experiment_summary,
    first_key_action,
    funnel_by_channel,
    lifecycle_funnel,
    milestone_retention,
    mix_rate_decomposition,
    paid_survival_curve,
    prospective_engagement_dataset,
    prospective_usage_dataset,
    required_sample_size,
    retention_rate,
    retention_curve,
    revenue_trend,
    simulate_multivariate_variants,
    summarize_decomposition,
    targeted_rollout_impact,
    time_to_activate_trend,
    two_proportion_p_value,
    usage_engagement_features,
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


def test_funnel_by_channel_conditions_rates_on_prior_step():
    accounts = pd.DataFrame(
        {
            "org_id": [f"org_{i}" for i in range(6)],
            "acquisition_source": ["Content"] * 3 + ["Referral"] * 3,
            # Content: all 3 create a workspace, only 1 connects integration,
            # but that 1 activates and converts to paid.
            "workspace_created": [True, True, True, True, False, False],
            "integration_connected": [True, False, False, False, False, False],
            "activated_7d": [True, False, False, False, False, False],
            "paid_customer": [True, False, False, False, False, False],
        }
    )

    funnel = funnel_by_channel(accounts).set_index("acquisition_source")

    assert funnel.loc["Content", "workspace_rate"] == 1.0
    # 1 of 3 workspace-created accounts connected integration, not 1 of 3 signups.
    assert funnel.loc["Content", "workspace_to_integration_rate"] == pytest.approx(1 / 3)
    assert funnel.loc["Content", "activated_to_paid_rate"] == 1.0
    # Referral: only 1 of 3 created a workspace and none activated.
    assert funnel.loc["Referral", "workspace_rate"] == pytest.approx(1 / 3)
    assert funnel.loc["Referral", "activation_rate"] == 0.0
    assert pd.isna(funnel.loc["Referral", "activated_to_paid_rate"])


def test_first_key_action_breaks_ties_alphabetically():
    organizations = pd.DataFrame(
        {
            "org_id": ["org_tie", "org_sequential"],
            "created_at": pd.to_datetime(["2025-01-01", "2025-01-01"]),
        }
    )
    events = pd.DataFrame(
        {
            "org_id": ["org_tie", "org_tie", "org_sequential", "org_sequential"],
            "event_name": [
                "project_created",
                "integration_connected",
                "teammate_invited",
                "integration_connected",
            ],
            # org_tie: both events logged at the exact same timestamp (batch insert).
            # org_sequential: teammate_invited genuinely happens first.
            "event_timestamp": pd.to_datetime(
                ["2025-01-03", "2025-01-03", "2025-01-02", "2025-01-04"]
            ),
        }
    )

    first = first_key_action(events, organizations).set_index("org_id")

    assert len(first) == 2  # one row per org despite the timestamp tie
    assert first.loc["org_tie", "first_action"] == "integration_connected"  # alphabetically first
    assert first.loc["org_sequential", "first_action"] == "teammate_invited"
    assert first.loc["org_sequential", "days_from_signup"] == pytest.approx(1.0)


def test_milestone_retention_ranks_by_downstream_retention():
    account_metrics = pd.DataFrame(
        {
            "org_id": ["org_a", "org_b", "org_c", "org_d"],
            "paid_customer": [True, True, False, True],
            "eligible_60d": [True, True, True, True],
            "retained_60d": [True, False, True, True],
        }
    )
    first_actions = pd.DataFrame(
        {
            "org_id": ["org_a", "org_b", "org_c", "org_d"],
            "first_action": [
                "teammate_invited",
                "project_created",
                "teammate_invited",
                "integration_connected",
            ],
        }
    )

    result = milestone_retention(account_metrics, first_actions).set_index("first_action")

    assert result.loc["teammate_invited", "orgs"] == 2
    assert result.loc["teammate_invited", "retention_60d_rate"] == 1.0
    assert result.loc["project_created", "retention_60d_rate"] == 0.0
    # Ranked with the strongest retention signal first.
    assert result.index[0] in {"teammate_invited", "integration_connected"}


def test_time_to_activate_trend_uses_percentiles_not_mean():
    account_metrics = pd.DataFrame(
        {
            "org_id": [f"org_{i}" for i in range(5)],
            "created_at": pd.to_datetime(["2025-01-05"] * 5),
        }
    )
    # One extreme outlier (90 days) should not distort the P50 the way a mean would.
    first_actions = pd.DataFrame(
        {
            "org_id": [f"org_{i}" for i in range(5)],
            "days_from_signup": [2.0, 3.0, 4.0, 5.0, 90.0],
        }
    )

    trend = time_to_activate_trend(account_metrics, first_actions)

    assert len(trend) == 1
    assert trend.loc[0, "activated_orgs"] == 5
    assert trend.loc[0, "p50_days"] == 4.0
    assert trend.loc[0, "p50_days"] < first_actions["days_from_signup"].mean()


def test_activation_speed_by_segment_pairs_rate_with_speed():
    account_metrics = pd.DataFrame(
        {
            "org_id": ["org_smb_1", "org_smb_2", "org_ent_1", "org_ent_2"],
            "company_size": ["SMB", "SMB", "Enterprise", "Enterprise"],
            "activated_7d": [True, True, True, False],
        }
    )
    first_actions = pd.DataFrame(
        {
            "org_id": ["org_smb_1", "org_smb_2", "org_ent_1"],
            "days_from_signup": [2.0, 4.0, 20.0],
        }
    )

    result = activation_speed_by_segment(account_metrics, first_actions).set_index(
        "company_size"
    )

    assert result.loc["SMB", "activation_rate"] == 1.0
    assert result.loc["Enterprise", "activation_rate"] == 0.5
    assert result.loc["SMB", "p50_days_to_first_action"] == 3.0
    assert result.loc["Enterprise", "p50_days_to_first_action"] == 20.0


def test_engagement_retention_curve_excludes_day_zero_and_gates_maturity():
    organizations = pd.DataFrame(
        {
            "org_id": ["org_active", "org_signup_day_only", "org_immature"],
            "created_at": pd.to_datetime(["2025-01-01", "2025-01-01", "2025-03-01"]),
        }
    )
    events = pd.DataFrame(
        {
            "org_id": [
                "org_active",
                "org_active",
                "org_signup_day_only",
                "org_immature",
            ],
            "event_name": ["login"] * 4,
            "event_timestamp": pd.to_datetime(
                [
                    "2025-01-01",  # day 0 for org_active — should not count as D30 activity
                    "2025-01-15",  # day 14 — real D30-window activity
                    "2025-01-01",  # org_signup_day_only: only ever active on day 0
                    "2025-03-10",  # org_immature: within its own D30 window
                ]
            ),
        }
    )
    as_of_date = pd.Timestamp("2025-02-15")  # January cohort has reached D30; March hasn't

    curve = engagement_retention_curve(organizations, events, as_of_date).set_index(
        "cohort_month"
    )
    jan = curve.loc[pd.Timestamp("2025-01-01")]
    mar = curve.loc[pd.Timestamp("2025-03-01")]

    assert jan["cohort_size"] == 2
    # Only org_active had activity strictly after day 0 within the D30 window.
    assert jan["retention_d30"] == pytest.approx(0.5)
    # January cohort is mature enough for D30 but not D60/D90 as of as_of_date.
    assert pd.isna(jan["retention_d60"])
    # March cohort hasn't reached its own D30 horizon yet as of as_of_date.
    assert pd.isna(mar["retention_d30"])


def test_two_proportion_p_value_matches_identical_and_extreme_cases():
    # Identical rates: p-value should be exactly 1.0 (no evidence of a difference).
    assert two_proportion_p_value(50, 100, 50, 100) == 1.0
    # Huge, obvious effect with large samples should be far below alpha=0.05.
    assert two_proportion_p_value(100, 1000, 400, 1000) < 0.001


def test_required_sample_size_matches_mart_multivariate_formula():
    # baseline=35%, MDE=5pp, alpha=0.05, power=0.80 — same inputs used in
    # sql/marts/mart_multivariate.sql's sample-size calculator.
    n = required_sample_size(0.35, 0.05)
    assert n == 1468  # (1.96 + 0.842)^2 * (0.35*0.65 + 0.40*0.60) / 0.05^2, rounded up


def _experiment_accounts(
    control_n: int,
    treatment_n: int,
    control_activation: float,
    treatment_activation: float,
    control_paid: float = 0.30,
    treatment_paid: float = 0.30,
    company_size: str = "SMB",
) -> pd.DataFrame:
    def _variant_frame(n, activation_rate, paid_rate, variant):
        activated = int(round(n * activation_rate))
        paid = int(round(n * paid_rate))
        eligible = int(round(n * 0.5))
        retained = int(round(eligible * 0.9))
        return pd.DataFrame(
            {
                "org_id": [f"{variant}_{i}" for i in range(n)],
                "variant": variant,
                "company_size": company_size,
                "activated_7d": [True] * activated + [False] * (n - activated),
                "paid_customer": [True] * paid + [False] * (n - paid),
                "eligible_60d": [True] * eligible + [False] * (n - eligible),
                "retained_60d": [True] * retained + [False] * (n - eligible) + [False] * (eligible - retained),
            }
        )

    return pd.concat(
        [
            _variant_frame(control_n, control_activation, control_paid, "control"),
            _variant_frame(treatment_n, treatment_activation, treatment_paid, "treatment"),
        ],
        ignore_index=True,
    )


def test_experiment_decision_ships_when_significant_and_guardrails_hold():
    accounts = _experiment_accounts(
        control_n=1000, treatment_n=1000, control_activation=0.30, treatment_activation=0.45
    )
    decision = experiment_decision(accounts)
    assert decision["significant"]
    assert not decision["paid_guardrail_broken"]
    assert decision["verdict"] == "SHIP"


def test_experiment_decision_iterates_when_guardrail_significantly_degrades():
    accounts = _experiment_accounts(
        control_n=1000,
        treatment_n=1000,
        control_activation=0.30,
        treatment_activation=0.45,
        control_paid=0.50,
        treatment_paid=0.20,  # large, significant drop in paid conversion
    )
    decision = experiment_decision(accounts)
    assert decision["significant"]
    assert decision["paid_guardrail_broken"]
    assert decision["verdict"] == "ITERATE"


def test_experiment_decision_continues_when_underpowered():
    # Small sample, modest lift: not significant, and nowhere near the required N.
    accounts = _experiment_accounts(
        control_n=30, treatment_n=30, control_activation=0.30, treatment_activation=0.35
    )
    decision = experiment_decision(accounts)
    assert not decision["significant"]
    assert not decision["adequately_powered"]
    assert decision["verdict"] == "CONTINUE"


def test_experiment_decision_kills_when_adequately_powered_and_still_null():
    # Large sample, essentially no lift: not significant, but well-powered to detect
    # even a small effect — so the (absence of) effect is a real finding, not noise.
    accounts = _experiment_accounts(
        control_n=5000, treatment_n=5000, control_activation=0.30, treatment_activation=0.301
    )
    decision = experiment_decision(accounts)
    assert not decision["significant"]
    assert decision["adequately_powered"]
    assert decision["verdict"] == "KILL"


def test_simulate_multivariate_variants_is_deterministic_and_three_way():
    accounts = pd.DataFrame(
        {
            "org_id": [f"org_{i}" for i in range(60)],
            "variant": ["control"] * 20 + ["treatment"] * 40,
        }
    )

    first_run = simulate_multivariate_variants(accounts)
    second_run = simulate_multivariate_variants(accounts)

    assert (first_run["mv_variant"] == second_run["mv_variant"]).all()  # deterministic
    assert (first_run.loc[first_run["variant"].eq("control"), "mv_variant"] == "control").all()
    treatment_labels = set(first_run.loc[first_run["variant"].eq("treatment"), "mv_variant"])
    assert treatment_labels == {"v1_guided_checklist", "v2_video_walkthrough", "v3_interactive_demo"}


def _multivariate_accounts() -> pd.DataFrame:
    def _rows(n, successes, label):
        return pd.DataFrame(
            {
                "org_id": [f"{label}_{i}" for i in range(n)],
                "mv_variant": label,
                "activated_7d": [True] * successes + [False] * (n - successes),
            }
        )

    return pd.concat(
        [
            _rows(2000, 600, "control"),  # 30% baseline
            _rows(500, 225, "v1_ship"),  # 45% — huge effect, survives Bonferroni
            _rows(500, 175, "v2_iterate"),  # 35% — significant uncorrected, not after correction
            _rows(500, 100, "v3_kill"),  # 20% — underperforms control
        ],
        ignore_index=True,
    )


def test_bonferroni_pairwise_results_applies_multiple_comparison_correction():
    results = bonferroni_pairwise_results(_multivariate_accounts()).set_index("variant")

    # k=3 treatment variants -> adjusted alpha = 0.05/3, corrected z-threshold ~2.394
    assert results["adjusted_alpha"].iloc[0] == pytest.approx(0.05 / 3)
    assert results["z_threshold_bonferroni"].iloc[0] == pytest.approx(2.394, abs=0.01)

    assert results.loc["v1_ship", "significant_bonferroni"]
    assert results.loc["v1_ship", "decision"] == "SHIP"

    # Significant at the uncorrected 1.96 threshold, but not after Bonferroni —
    # this is exactly the case that motivates the correction in the first place.
    assert results.loc["v2_iterate", "significant_uncorrected"]
    assert not results.loc["v2_iterate", "significant_bonferroni"]
    assert results.loc["v2_iterate", "decision"] == "ITERATE"

    assert results.loc["v3_kill", "lift"] < 0
    assert results.loc["v3_kill", "decision"] == "KILL"


def _decomposition_accounts(rows: list[tuple[str, str, int, int]]) -> pd.DataFrame:
    """rows: (period 'YYYY-MM-DD', segment, signups, activated)."""
    frames = []
    for period, segment, signups, activated in rows:
        frames.append(
            pd.DataFrame(
                {
                    "org_id": [f"{period}_{segment}_{i}" for i in range(signups)],
                    "created_at": pd.Timestamp(period),
                    "acquisition_source": segment,
                    "activated_7d": [True] * activated + [False] * (signups - activated),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


PRIOR, CURRENT = pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")


def test_decomposition_pure_mix_shift_has_zero_rate_effect():
    # Study-doc example: same per-channel rates, but paid_search share goes 20% -> 50%.
    accounts = _decomposition_accounts(
        [
            ("2025-01-01", "organic", 800, 440),
            ("2025-01-01", "paid_search", 200, 40),
            ("2025-02-01", "organic", 500, 275),
            ("2025-02-01", "paid_search", 500, 100),
        ]
    )
    summary = summarize_decomposition(
        mix_rate_decomposition(accounts, "acquisition_source", PRIOR, CURRENT)
    )

    assert summary["rate_effect"] == pytest.approx(0.0)
    assert summary["mix_effect"] == pytest.approx(-0.105)
    assert summary["total_change"] == pytest.approx(0.375 - 0.48)
    assert summary["diagnosis"] == "Mix-driven (acquisition shift)"


def test_decomposition_pure_rate_drop_has_zero_mix_effect():
    accounts = _decomposition_accounts(
        [
            ("2025-01-01", "organic", 800, 440),  # 55%
            ("2025-01-01", "paid_search", 200, 40),  # 20%
            ("2025-02-01", "organic", 800, 360),  # 45%
            ("2025-02-01", "paid_search", 200, 30),  # 15%
        ]
    )
    summary = summarize_decomposition(
        mix_rate_decomposition(accounts, "acquisition_source", PRIOR, CURRENT)
    )

    assert summary["mix_effect"] == pytest.approx(0.0)
    assert summary["rate_effect"] == pytest.approx(-0.09)
    assert summary["diagnosis"] == "Rate-driven (product/UX issue)"


def test_decomposition_mix_effect_blames_the_below_average_segment():
    # Study-doc example: paid_search (20% rate, below the 48% average) grows from 20% to 50%
    # of signups. Uncentered, its mix effect reads +6pp (it "helped"); centered it is the
    # segment dragging the overall rate down, which is the actual story.
    accounts = _decomposition_accounts(
        [
            ("2025-01-01", "organic", 800, 440),
            ("2025-01-01", "paid_search", 200, 40),
            ("2025-02-01", "organic", 500, 275),
            ("2025-02-01", "paid_search", 500, 100),
        ]
    )
    by_segment = mix_rate_decomposition(
        accounts, "acquisition_source", PRIOR, CURRENT
    ).set_index("acquisition_source")

    assert by_segment.loc["paid_search", "mix_effect"] == pytest.approx(-0.084)
    assert by_segment.loc["organic", "mix_effect"] == pytest.approx(-0.021)
    assert by_segment["mix_effect"].sum() == pytest.approx(-0.105)  # total unchanged


def test_decomposition_reconciles_exactly_when_rate_and_mix_both_move():
    accounts = _decomposition_accounts(
        [
            ("2025-01-01", "organic", 600, 360),
            ("2025-01-01", "paid_search", 400, 120),
            ("2025-02-01", "organic", 400, 200),
            ("2025-02-01", "paid_search", 600, 150),
        ]
    )
    decomposition = mix_rate_decomposition(accounts, "acquisition_source", PRIOR, CURRENT)
    summary = summarize_decomposition(decomposition)

    actual_change = (200 + 150) / 1000 - (360 + 120) / 1000
    assert summary["interaction_effect"] != pytest.approx(0.0)  # both moved
    assert summary["total_change"] == pytest.approx(actual_change)  # still reconciles exactly


def test_decomposition_new_segment_is_a_pure_mix_effect_not_dropped():
    accounts = _decomposition_accounts(
        [
            ("2025-01-01", "organic", 1000, 500),
            ("2025-02-01", "organic", 500, 250),
            ("2025-02-01", "partner", 500, 100),  # channel that didn't exist last period
        ]
    )
    decomposition = mix_rate_decomposition(accounts, "acquisition_source", PRIOR, CURRENT)
    summary = summarize_decomposition(decomposition)

    assert summary["total_change"] == pytest.approx((250 + 100) / 1000 - 0.5)
    by_segment = decomposition.set_index("acquisition_source")
    assert by_segment.loc["partner", "rate_effect"] == 0.0
    # Prior overall rate is 50%. The new channel gained 50pp of share while activating
    # 30pp below that (20%), so it carries the whole mix drag; organic sits exactly at
    # the average, so its shrinking share costs nothing.
    assert by_segment.loc["partner", "mix_effect"] == pytest.approx(-0.15)
    assert by_segment.loc["organic", "mix_effect"] == pytest.approx(0.0)


def _ltv_inputs():
    organizations = pd.DataFrame(
        {
            "org_id": ["a1", "a2", "a3", "b1"],
            "acquisition_source": ["A", "A", "A", "B"],
        }
    )
    as_of = pd.Timestamp("2025-01-01") + pd.Timedelta(days=365)
    subscriptions = pd.DataFrame(
        {
            "org_id": ["a1", "a2", "a3", "b1", "a1"],
            "mrr_amount": [100.0, 100.0, 100.0, 50.0, 0.0],  # a1's 0-MRR row is a trial
            "start_date": pd.to_datetime(["2025-01-01"] * 5),
            # a1 churns after exactly 6 x 30.4375 days; a2 and a3 are still active; b1 never churns
            "end_date": pd.to_datetime(["2025-07-02", None, None, None, "2025-01-15"]),
            "status": ["churned", "active", "active", "active", "trial_ended"],
        }
    )
    return subscriptions, organizations, as_of


def test_channel_ltv_uses_exposure_months_not_cumulative_churned_share():
    subscriptions, organizations, as_of = _ltv_inputs()
    result = channel_ltv(subscriptions, organizations, as_of).set_index("acquisition_source")

    a = result.loc["A"]
    assert a["paid_accounts"] == 3  # the 0-MRR trial row is not a paid account
    assert a["churn_events"] == 1
    # Exposure: a1 ran ~182 days until it churned; a2 and a3 are censored at 365 days each.
    exposure_months = (182 + 365 + 365) / 30.4375
    assert a["exposure_months"] == pytest.approx(exposure_months, rel=1e-3)
    assert a["monthly_churn"] == pytest.approx(1 / exposure_months, rel=1e-3)
    # The cumulative shortcut (1 churned / 3 accounts = 33%) would be ~11x too high here.
    assert a["monthly_churn"] < 0.05
    assert a["ltv"] == pytest.approx(100.0 / a["monthly_churn"])
    assert a["ltv_low"] <= a["ltv_high"]  # bootstrap interval is ordered (3 accounts is too few to say more)


def test_channel_ltv_caps_lifetime_and_reports_a_budget_ceiling_not_a_cac():
    subscriptions, organizations, as_of = _ltv_inputs()
    result = channel_ltv(
        subscriptions, organizations, as_of, horizon_months=12, target_ltv_to_cac=3.0
    ).set_index("acquisition_source")

    a = result.loc["A"]
    churn = a["monthly_churn"]
    assert a["ltv_capped"] == pytest.approx(100.0 * (1 - (1 - churn) ** 12) / churn)
    assert a["ltv_capped"] < a["ltv"]  # truncating the horizon can only lower LTV
    assert a["max_cac"] == pytest.approx(a["ltv_capped"] / 3.0)
    assert a["ltv_capped_low"] <= a["ltv_capped_high"]


def test_channel_ltv_is_undefined_not_infinite_when_nothing_has_churned():
    subscriptions, organizations, as_of = _ltv_inputs()
    b = channel_ltv(subscriptions, organizations, as_of).set_index("acquisition_source").loc["B"]

    assert b["churn_events"] == 0
    assert b["monthly_churn"] == 0
    assert pd.isna(b["ltv"])  # cannot claim an LTV from zero observed churn


def test_paid_survival_curve_hazard_is_per_month_at_risk_and_ignores_partial_months():
    start = pd.Timestamp("2025-01-01")
    as_of = start + pd.Timedelta(days=365)
    day = lambda months: start + pd.Timedelta(days=round(months * 30.4375))
    subscriptions = pd.DataFrame(
        {
            "org_id": ["a", "b", "c", "d", "e"],
            "mrr_amount": [100.0] * 5,
            "start_date": [start] * 4 + [as_of - pd.Timedelta(days=15)],
            "end_date": [day(1.5), day(2.5), pd.NaT, pd.NaT, pd.NaT],
            "status": ["churned", "churned", "active", "active", "active"],
        }
    )

    curve = paid_survival_curve(subscriptions, as_of, max_months=4).set_index("month_since_paid")

    # e was observed for only half a month: never at risk in month 1, so it can't dilute it.
    assert curve.loc[1, "at_risk"] == 4 and curve.loc[1, "hazard"] == 0
    assert curve.loc[2, "hazard"] == pytest.approx(1 / 4)  # a churns in month 2
    assert curve.loc[3, "hazard"] == pytest.approx(1 / 3)  # b churns in month 3; a already gone
    assert curve.loc[3, "survival"] == pytest.approx(0.75 * (2 / 3))
    assert curve.loc[4, "hazard"] == 0  # after month 3 nobody churns: survival plateaus


def _engagement_inputs():
    organizations = pd.DataFrame(
        {"org_id": ["stay", "leave", "unpaid", "gone_already"], "created_at": pd.to_datetime(["2025-01-01"] * 4)}
    )
    subscriptions = pd.DataFrame(
        {
            "org_id": ["stay", "leave", "gone_already"],
            "mrr_amount": [100.0] * 3,
            "start_date": pd.to_datetime(["2025-01-10"] * 3),
            "end_date": pd.to_datetime([None, "2025-05-01", "2025-03-01"]),
            "status": ["active", "churned", "churned"],
        }
    )
    events = pd.DataFrame(
        {
            "org_id": ["stay", "stay", "leave", "leave"],
            "event_name": ["a", "b", "a", "b"],
            "event_timestamp": pd.to_datetime(
                ["2025-03-20", "2025-03-25", "2025-03-22", "2025-05-15"]  # leave's 2nd event is AFTER the cutoff
            ),
        }
    )
    return events, organizations, subscriptions


def test_prospective_dataset_uses_only_pre_cutoff_behavior_and_post_cutoff_outcome():
    events, organizations, subscriptions = _engagement_inputs()
    cutoff = pd.Timestamp("2025-04-01")
    data = prospective_engagement_dataset(
        events, organizations, subscriptions, as_of_date=pd.Timestamp("2025-12-31"), cutoffs=[cutoff], horizon_days=90
    ).set_index("org_id")

    # Only accounts paying at the cutoff: gone_already ended before it; unpaid never paid.
    assert set(data.index) == {"stay", "leave"}
    # leave's May event happened after the cutoff and must not leak into its features.
    assert data.loc["leave", "distinct_event_types"] == 1
    assert data.loc["leave", "days_since_last_event"] == 10
    # Outcome is churn within 90 days after the cutoff (leave ends 2025-05-01).
    assert data.loc["leave", "churned_within_horizon"]
    assert not data.loc["stay", "churned_within_horizon"]


def test_prospective_dataset_drops_cutoffs_whose_horizon_is_not_fully_observed():
    events, organizations, subscriptions = _engagement_inputs()
    data = prospective_engagement_dataset(
        events, organizations, subscriptions,
        as_of_date=pd.Timestamp("2025-05-01"),
        cutoffs=[pd.Timestamp("2025-04-01"), pd.Timestamp("2025-04-25")],
        horizon_days=90,
    )
    assert data.empty  # neither cutoff has 90 observable days left: nothing is censored into the sample


def test_churn_by_feature_within_strata_removes_tenure_confounding():
    def _rows(tenure, active, n, churned):
        return pd.DataFrame(
            {
                "tenure_bucket": tenure,
                "active_recent": active,
                "churned_within_horizon": [True] * churned + [False] * (n - churned),
            }
        )

    # Engagement has no effect inside either tenure stratum, but new accounts are mostly
    # "active" and mostly churn, so the pooled comparison makes activity look harmful.
    data = pd.concat(
        [
            _rows("new", True, 90, 18), _rows("new", False, 10, 2),
            _rows("old", True, 10, 0), _rows("old", False, 90, 0),
        ]
    )

    pooled = churn_by_feature(data, "active_recent").set_index("active_recent")["churn_rate"]
    assert pooled[True] == pytest.approx(0.18) and pooled[False] == pytest.approx(0.02)

    within = churn_by_feature(data, "active_recent", "tenure_bucket").set_index(["tenure_bucket", "active_recent"])["churn_rate"]
    assert within[("new", True)] == pytest.approx(within[("new", False)])
    assert within[("old", True)] == within[("old", False)] == 0


def _weeks(cutoff_monday: str, n: int):
    start = pd.Timestamp(cutoff_monday)
    return [start - pd.Timedelta(weeks=i) for i in range(n)]


def _usage_frame():
    # cutoff Wed 2025-03-12: the last FULL week is Mon 03-03; recent = 03-03..02-10, prior = 02-03..01-13
    weeks = _weeks("2025-03-03", 8)
    rows = []
    def add(org, recent, prior, features=3):
        for i, w in enumerate(weeks):
            rows.append({"org_id": org, "week_start": w, "sessions": (recent if i < 4 else prior), "features_used": features})
    add("A", 10, 20)          # halved: 40 vs 80 -> at risk
    add("B", 0, 12)           # used before, nothing recently -> dormant
    add("C", 0.25, 1)         # too little prior usage to count as a decline
    add("D", 25, 25, features=5)
    frame = pd.DataFrame(rows)
    frame.loc[(frame.org_id == "B") & (frame.week_start.isin(weeks[:4])), "sessions"] = 0
    partial = pd.DataFrame([{"org_id": "A", "week_start": pd.Timestamp("2025-03-10"), "sessions": 999, "features_used": 6}])
    return pd.concat([frame, partial], ignore_index=True)


def test_usage_features_use_only_weeks_that_ended_before_the_cutoff():
    features = usage_engagement_features(_usage_frame(), pd.Timestamp("2025-03-12"))

    # The partial week starting 03-10 (999 sessions) had not ended by the cutoff and must not leak in.
    assert features.loc["A", "recent_sessions"] == 40
    assert features.loc["A", "prior_sessions"] == 80
    assert features.loc["A", "trend_ratio"] == pytest.approx(0.5)
    assert features.loc["B", "recent_sessions"] == 0


def test_engagement_tiers_require_prior_usage_for_at_risk_and_never_see_churn():
    features = usage_engagement_features(_usage_frame(), pd.Timestamp("2025-03-12"))
    tiers = assign_engagement_tiers(features)

    assert tiers["A"] == "at_risk"     # had real usage, then halved
    assert tiers["B"] == "dormant"     # nothing in the recent window
    assert tiers["C"] == "active"      # tiny prior usage: not "used to be engaged"
    assert tiers["D"] == "power"       # top of the population, broad feature use


def test_auc_score_is_one_for_perfect_separation_and_half_for_no_signal():
    outcome = pd.Series([True, True, False, False])
    assert auc_score(outcome, pd.Series([0.9, 0.8, 0.2, 0.1])) == 1.0
    assert auc_score(outcome, pd.Series([0.5, 0.5, 0.5, 0.5])) == 0.5   # ties get average ranks
    assert pd.isna(auc_score(pd.Series([False, False]), pd.Series([1.0, 2.0])))  # undefined without both classes


def test_prospective_usage_dataset_drops_cutoffs_with_unobserved_horizon_and_uses_pre_cutoff_usage():
    organizations = pd.DataFrame(
        {
            "org_id": ["A", "B"],
            "created_at": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "acquisition_source": ["Content", "Content"],
            "company_size": ["SMB", "SMB"],
        }
    )
    subscriptions = pd.DataFrame(
        {
            "org_id": ["A", "B"],
            "mrr_amount": [100.0, 100.0],
            "start_date": pd.to_datetime(["2025-01-10", "2025-01-10"]),
            "end_date": pd.to_datetime(["2025-04-01", None]),
            "status": ["churned", "active"],
        }
    )
    usage = _usage_frame()
    usage = usage.loc[usage.org_id.isin(["A", "B"])]

    data = prospective_usage_dataset(
        usage, organizations, subscriptions,
        as_of_date=pd.Timestamp("2025-04-30"),
        cutoffs=[pd.Timestamp("2025-03-12"), pd.Timestamp("2025-04-25")],
        horizon_days=30,
    ).set_index("org_id")

    # 2025-04-25 + 30 days is past the data end, so only the 03-12 cutoff survives.
    assert set(data["cutoff"]) == {pd.Timestamp("2025-03-12")}
    assert data.loc["A", "churned_within_horizon"] and not data.loc["B", "churned_within_horizon"]
    assert data.loc["A", "recent_sessions"] == 40  # the 999-session partial week never leaks in


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
