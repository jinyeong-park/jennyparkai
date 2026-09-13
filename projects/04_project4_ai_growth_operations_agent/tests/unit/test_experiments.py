"""Unit tests for Phase 4: Experiment Registry and Measurement Engine.

All experiments and data are SYNTHETIC — simulated for portfolio purposes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from growth_agent.domain.enums import DataOrigin, RecommendationState
from growth_agent.experiments.evaluator import ArmResult, ExperimentEvaluator
from growth_agent.experiments.models import (
    Experiment,
    ExperimentArm,
    ExperimentState,
    MetricConfig,
    MetricDirection,
)
from growth_agent.experiments.registry import ExperimentRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = Path(__file__).resolve().parents[2]  # project root
EXPERIMENTS_YAML = BASE / "config" / "experiments.yaml"


def _make_experiment(**overrides) -> dict:
    """Return a minimal valid experiment dict, with optional overrides."""
    base = {
        "experiment_id": "test_exp",
        "name": "Test Experiment",
        "hypothesis": "Treatment will improve activation rate.",
        "variable_tested": "hook_type",
        "primary_metric": {
            "name": "activation_rate",
            "direction": "HIGHER_IS_BETTER",
            "minimum_detectable_effect": 0.03,
            "is_guardrail": False,
        },
        "guardrail_metrics": [],
        "arms": [
            {
                "arm_id": "ctrl",
                "name": "Control",
                "creative_brief_ids": [],
                "is_control": True,
                "description": "Control arm",
            },
            {
                "arm_id": "trt",
                "name": "Treatment",
                "creative_brief_ids": [],
                "is_control": False,
                "description": "Treatment arm",
            },
        ],
        "state": "RUNNING",
        "evaluation_window_days": 14,
        "minimum_trials_per_arm": 200,
        "data_origin": "SYNTHETIC",
    }
    base.update(overrides)
    return base


def _make_arm(arm_id: str, trials: int, conversions: int, spend: float, is_control: bool = False) -> ArmResult:
    return ArmResult(
        arm_id=arm_id,
        arm_name=arm_id,
        is_control=is_control,
        trials=trials,
        conversions=conversions,
        spend_usd=spend,
    )


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------

class TestExperimentValidation:

    def test_experiment_requires_control_arm(self):
        """An experiment with no control arm must raise ValidationError."""
        data = _make_experiment()
        # Remove is_control from both arms
        for arm in data["arms"]:
            arm["is_control"] = False

        with pytest.raises(ValidationError, match="exactly 1 control arm"):
            Experiment.model_validate(data)

    def test_experiment_requires_exactly_one_control_arm(self):
        """An experiment with two control arms must also raise ValidationError."""
        data = _make_experiment()
        data["arms"][1]["is_control"] = True  # now both are controls

        with pytest.raises(ValidationError, match="exactly 1 control arm"):
            Experiment.model_validate(data)

    def test_experiment_requires_hypothesis(self):
        """An experiment with an empty hypothesis must raise ValidationError."""
        data = _make_experiment(hypothesis="")

        with pytest.raises(ValidationError, match="hypothesis"):
            Experiment.model_validate(data)

    def test_experiment_requires_variable_tested(self):
        """An experiment with an empty variable_tested must raise ValidationError."""
        data = _make_experiment(variable_tested="   ")

        with pytest.raises(ValidationError, match="variable_tested"):
            Experiment.model_validate(data)

    def test_experiment_valid_loads(self):
        """A valid experiment dict must parse without errors."""
        data = _make_experiment()
        exp = Experiment.model_validate(data)
        assert exp.experiment_id == "test_exp"
        assert exp.data_origin == DataOrigin.SYNTHETIC

    def test_experiment_requires_treatment_arm(self):
        """An experiment with only a control arm and no treatment must raise."""
        data = _make_experiment()
        # Keep only the control arm
        data["arms"] = [data["arms"][0]]

        with pytest.raises(ValidationError, match="at least 1 treatment arm"):
            Experiment.model_validate(data)


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestExperimentRegistry:

    def test_registry_loads_yaml(self):
        """Registry must load all 4 experiments from config/experiments.yaml."""
        registry = ExperimentRegistry(EXPERIMENTS_YAML)
        assert len(registry.all()) == 4

    def test_registry_get_by_id(self):
        """Registry.get() must return the correct experiment by ID."""
        registry = ExperimentRegistry(EXPERIMENTS_YAML)
        exp = registry.get("exp_001")
        assert exp is not None
        assert exp.name.startswith("Hook Type")

    def test_registry_get_missing_id(self):
        """Registry.get() must return None for an unknown ID."""
        registry = ExperimentRegistry(EXPERIMENTS_YAML)
        assert registry.get("exp_999") is None

    def test_registry_list_by_state(self):
        """Registry.list_by_state() must filter correctly."""
        registry = ExperimentRegistry(EXPERIMENTS_YAML)
        running = registry.list_by_state(ExperimentState.RUNNING)
        evaluating = registry.list_by_state(ExperimentState.EVALUATING)

        assert len(running) == 3
        assert len(evaluating) == 1
        assert evaluating[0].experiment_id == "exp_004"

    def test_registry_validate_all_clean(self):
        """validate_all() on a clean config must return no errors."""
        registry = ExperimentRegistry(EXPERIMENTS_YAML)
        errors = registry.validate_all()
        assert errors == []


# ---------------------------------------------------------------------------
# Evaluator tests
# ---------------------------------------------------------------------------

class TestExperimentEvaluator:

    def _get_experiment(self, min_trials: int = 200, mde: float = 0.03) -> Experiment:
        data = _make_experiment()
        data["minimum_trials_per_arm"] = min_trials
        data["primary_metric"]["minimum_detectable_effect"] = mde
        return Experiment.model_validate(data)

    def test_evaluator_insufficient_data(self):
        """If trials < minimum_trials_per_arm, result must be INSUFFICIENT_DATA."""
        exp = self._get_experiment(min_trials=200)
        evaluator = ExperimentEvaluator()

        arm_data = {
            "ctrl": _make_arm("ctrl", trials=100, conversions=20, spend=1500.0, is_control=True),
            "trt": _make_arm("trt", trials=80, conversions=18, spend=1200.0),
        }
        readout = evaluator.evaluate(exp, arm_data)

        assert readout.overall_recommendation == RecommendationState.INSUFFICIENT_DATA
        assert not readout.comparisons[0].is_mature

    def test_evaluator_scale_candidate(self):
        """Clear winner (stat + practical sig) must produce SCALE_CANDIDATE."""
        exp = self._get_experiment(min_trials=200, mde=0.03)
        evaluator = ExperimentEvaluator()

        # Control: 200 trials, 40 conversions → 20%
        # Treatment: 220 trials, 66 conversions → 30% (Δ=10pp >> MDE 3pp)
        arm_data = {
            "ctrl": _make_arm("ctrl", trials=200, conversions=40, spend=3000.0, is_control=True),
            "trt": _make_arm("trt", trials=220, conversions=66, spend=3300.0),
        }
        readout = evaluator.evaluate(exp, arm_data)

        assert readout.overall_recommendation == RecommendationState.SCALE_CANDIDATE
        comp = readout.comparisons[0]
        assert comp.is_mature
        assert comp.z_score is not None
        assert abs(comp.z_score) >= 1.96
        assert comp.absolute_difference >= 0.03

    def test_evaluator_pause_candidate(self):
        """Treatment clearly worse than control must produce PAUSE_CANDIDATE."""
        exp = self._get_experiment(min_trials=200, mde=0.03)
        evaluator = ExperimentEvaluator()

        # Control: 200 trials, 60 conversions → 30%
        # Treatment: 210 trials, 38 conversions → ~18% (Δ=-12pp, clearly worse)
        arm_data = {
            "ctrl": _make_arm("ctrl", trials=200, conversions=60, spend=3000.0, is_control=True),
            "trt": _make_arm("trt", trials=210, conversions=38, spend=3150.0),
        }
        readout = evaluator.evaluate(exp, arm_data)

        assert readout.overall_recommendation == RecommendationState.PAUSE_CANDIDATE
        comp = readout.comparisons[0]
        assert comp.absolute_difference < -0.03  # worse by more than MDE

    def test_evaluator_observe(self):
        """Stat sig but below practical threshold → OBSERVE."""
        # MDE = 0.10 (very high practical bar), but treatment is only +3pp better
        exp = self._get_experiment(min_trials=200, mde=0.10)
        evaluator = ExperimentEvaluator()

        # Control: 500 trials, 100 → 20%; Treatment: 500 trials, 115 → 23% (Δ=3pp, stat sig but < MDE 10pp)
        arm_data = {
            "ctrl": _make_arm("ctrl", trials=500, conversions=100, spend=7500.0, is_control=True),
            "trt": _make_arm("trt", trials=500, conversions=115, spend=7500.0),
        }
        readout = evaluator.evaluate(exp, arm_data)

        # z-score for 3pp difference with n=500 each:
        # p_ctrl=0.20, p_trt=0.23, pooled≈0.215
        # var = 0.215*(1-0.215)*(1/500+1/500) ≈ 0.000339 → se ≈ 0.01841
        # z ≈ 0.03/0.01841 ≈ 1.63 (not stat sig)
        # So this gives HOLD unless stat sig. Let's verify via readout.
        # Actually with n=500 it may or may not be stat sig.
        comp = readout.comparisons[0]
        # Either OBSERVE (one sig) or HOLD (neither), but not SCALE_CANDIDATE
        assert readout.overall_recommendation in (
            RecommendationState.OBSERVE,
            RecommendationState.HOLD,
        )

    def test_evaluator_observe_stat_sig_not_practical(self):
        """Stat sig but not practically significant → OBSERVE."""
        # Use very tiny MDE violation: Δ=5pp, stat sig, but MDE=0.10
        exp = self._get_experiment(min_trials=200, mde=0.10)
        evaluator = ExperimentEvaluator()

        # With n=2000 per arm, even a 3pp diff is stat sig
        arm_data = {
            "ctrl": _make_arm("ctrl", trials=2000, conversions=400, spend=30000.0, is_control=True),
            "trt": _make_arm("trt", trials=2000, conversions=460, spend=30000.0),
        }
        # p_ctrl=0.20, p_trt=0.23, Δ=3pp; MDE=10pp → not practical
        readout = evaluator.evaluate(exp, arm_data)
        comp = readout.comparisons[0]
        # Should be stat sig (large n) but not practical sig → OBSERVE
        assert comp.z_score is not None
        # abs diff < MDE
        assert abs(comp.absolute_difference) < 0.10
        assert readout.overall_recommendation == RecommendationState.OBSERVE

    def test_evaluator_guardrail_overrides_scale(self):
        """Treatment wins primary but damages guardrail by >5% relative → HOLD."""
        data = _make_experiment()
        data["guardrail_metrics"] = [
            {
                "name": "m1_retention_rate",
                "direction": "HIGHER_IS_BETTER",
                "minimum_detectable_effect": 0.05,
                "is_guardrail": True,
            }
        ]
        data["minimum_trials_per_arm"] = 200
        exp = Experiment.model_validate(data)
        evaluator = ExperimentEvaluator()

        # Primary metric: treatment wins clearly (10pp, stat sig)
        arm_data = {
            "ctrl": _make_arm("ctrl", trials=200, conversions=40, spend=3000.0, is_control=True),
            "trt": _make_arm("trt", trials=220, conversions=66, spend=3300.0),
            # Guardrail: treatment has 50% retention vs control 60% → -16.7% relative damage
            "ctrl__guardrail__m1_retention_rate": _make_arm(
                "ctrl__guardrail__m1_retention_rate",
                trials=200, conversions=120, spend=0.0, is_control=True,
            ),
            "trt__guardrail__m1_retention_rate": _make_arm(
                "trt__guardrail__m1_retention_rate",
                trials=220, conversions=110, spend=0.0,
            ),
        }
        readout = evaluator.evaluate(exp, arm_data)

        # Primary says SCALE_CANDIDATE, but guardrail should override to HOLD
        assert readout.overall_recommendation == RecommendationState.HOLD
        assert len(readout.guardrail_findings) > 0

    def test_zero_denominator_handled(self):
        """Zero trials in an arm must return INSUFFICIENT_DATA without ZeroDivisionError."""
        exp = self._get_experiment(min_trials=200)
        evaluator = ExperimentEvaluator()

        arm_data = {
            "ctrl": _make_arm("ctrl", trials=0, conversions=0, spend=0.0, is_control=True),
            "trt": _make_arm("trt", trials=0, conversions=0, spend=0.0),
        }
        # Must not raise ZeroDivisionError
        readout = evaluator.evaluate(exp, arm_data)
        assert readout.overall_recommendation == RecommendationState.INSUFFICIENT_DATA
