"""Unit tests for Phase 7: Explainable Growth Decision Agent.

[SYNTHETIC DATA]
"""

import pytest
from datetime import date

from growth_agent.decisioning.policy import (
    ChannelEvidence,
    PolicyDecision,
    evaluate_channel,
)
from growth_agent.domain.enums import RecommendationState
from growth_agent.governance.audit import AuditLog, AuditRecord
from growth_agent.agents.performance_analyst import (
    PerformanceAnalyst,
    MockAnalystLLMProvider,
    ChannelRecommendation,
)
from growth_agent.agents.growth_reviewer import GrowthReviewer, ReviewAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tiktok_evidence(**overrides) -> ChannelEvidence:
    """Baseline TikTok evidence — should produce SCALE_CANDIDATE (LTV:CAC 2.03x >= 1.0)."""
    defaults = dict(
        channel="TIKTOK",
        evaluation_period_days=90,
        trials=1_005,
        activated_owners=262,
        spend_usd=37_490.0,
        cpao_usd=143.0,
        trial_cac_usd=12.0,
        m1_retention_rate=0.799,
        m3_retention_rate=0.576,
        m6_retention_rate=0.375,
        m6_is_mature=True,
        observed_ltv_usd=291.0,
        ltv_cac_ratio=2.03,
        min_trials_for_decision=100,
        cpao_efficiency_vs_baseline_pct=35.0,
        m1_retention_floor=0.70,
        data_origin="SYNTHETIC",
    )
    defaults.update(overrides)
    return ChannelEvidence(**defaults)


def _meta_evidence(**overrides) -> ChannelEvidence:
    """Baseline META evidence — should produce HOLD (LTV:CAC 0.48x, between 0.20 and 0.50)."""
    defaults = dict(
        channel="META",
        evaluation_period_days=90,
        trials=379,
        activated_owners=90,
        spend_usd=59_974.0,
        cpao_usd=666.0,
        trial_cac_usd=52.0,
        m1_retention_rate=0.825,
        m3_retention_rate=0.550,
        m6_retention_rate=0.450,
        m6_is_mature=True,
        observed_ltv_usd=318.0,
        ltv_cac_ratio=0.48,
        min_trials_for_decision=100,
        cpao_efficiency_vs_baseline_pct=-3.0,
        m1_retention_floor=0.70,
        data_origin="SYNTHETIC",
    )
    defaults.update(overrides)
    return ChannelEvidence(**defaults)


def _make_audit() -> AuditLog:
    return AuditLog()


def _make_analyst(audit: AuditLog | None = None) -> PerformanceAnalyst:
    if audit is None:
        audit = _make_audit()
    return PerformanceAnalyst(
        provider=MockAnalystLLMProvider(),
        audit_log=audit,
    )


# ---------------------------------------------------------------------------
# Policy tests
# ---------------------------------------------------------------------------

class TestInsufficientData:
    def test_insufficient_data_when_trials_low(self):
        ev = _tiktok_evidence(trials=50, min_trials_for_decision=100)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.INSUFFICIENT_DATA
        assert decision.confidence == "LOW"
        assert any("trials=50" in f for f in decision.evidence_flags)

    def test_insufficient_data_when_cpao_none(self):
        ev = _tiktok_evidence(cpao_usd=None)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.INSUFFICIENT_DATA
        assert decision.confidence == "LOW"
        assert any("cpao_usd=None" in f for f in decision.evidence_flags)


class TestScaleCandidate:
    def test_scale_candidate_tiktok_profile(self):
        """TikTok: LTV:CAC 2.03x >= 1.0, cpao_efficiency >= 0, M6 mature → SCALE_CANDIDATE."""
        ev = _tiktok_evidence()
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.SCALE_CANDIDATE
        assert decision.confidence == "HIGH"
        assert decision.is_mature is True
        assert decision.guardrail_violations == []


class TestPauseCandidate:
    def test_pause_candidate_when_ltv_cac_below_0_20(self):
        """LTV:CAC < 0.20 → PAUSE_CANDIDATE regardless of other metrics."""
        ev = _meta_evidence(ltv_cac_ratio=0.15)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.PAUSE_CANDIDATE

    def test_hold_for_meta_profile(self):
        """META: LTV:CAC 0.48x (between 0.20 and 0.50) → HOLD."""
        ev = _meta_evidence()
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.HOLD

    def test_pause_candidate_meta_profile_with_bad_ratio(self):
        """META with LTV:CAC 0.10x (< 0.20) → PAUSE_CANDIDATE."""
        ev = _meta_evidence(ltv_cac_ratio=0.10)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.PAUSE_CANDIDATE


class TestGuardrails:
    def test_guardrail_blocks_scale_when_m1_below_floor(self):
        """M1 retention below floor must cap SCALE_CANDIDATE → HOLD."""
        ev = _tiktok_evidence(m1_retention_rate=0.65, m1_retention_floor=0.70)
        decision = evaluate_channel(ev)
        # SCALE_CANDIDATE would have been assigned without guardrail
        assert decision.recommendation == RecommendationState.HOLD
        assert len(decision.guardrail_violations) > 0
        assert any("M1 retention" in v for v in decision.guardrail_violations)
        # Confidence drops to LOW due to guardrail trigger
        assert decision.confidence == "LOW"

    def test_immature_m6_caps_at_observe(self):
        """Without mature M6, SCALE_CANDIDATE is blocked. LTV:CAC 2.03x → capped at OBSERVE."""
        ev = _tiktok_evidence(m6_is_mature=False)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.OBSERVE
        assert decision.is_mature is False
        assert any("m6_is_mature=False" in f for f in decision.evidence_flags)
        # Confidence should be LOW (M6 immature)
        assert decision.confidence == "LOW"


class TestObserve:
    def test_observe_when_ltv_cac_between_0_50_and_1_0(self):
        """LTV:CAC in [0.50, 1.0) → OBSERVE."""
        ev = _tiktok_evidence(ltv_cac_ratio=0.70, cpao_efficiency_vs_baseline_pct=5.0)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.OBSERVE

    def test_observe_when_ltv_cac_1_0_but_cpao_worse_than_baseline(self):
        """LTV:CAC >= 1.0 but cpao_efficiency < 0 → OBSERVE (not SCALE_CANDIDATE)."""
        ev = _tiktok_evidence(ltv_cac_ratio=1.10, cpao_efficiency_vs_baseline_pct=-5.0)
        decision = evaluate_channel(ev)
        assert decision.recommendation == RecommendationState.OBSERVE


# ---------------------------------------------------------------------------
# Audit tests
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_records_state_change(self):
        audit = _make_audit()
        audit.record(
            AuditRecord(
                entity_type="channel_recommendation",
                entity_id="TIKTOK",
                previous_state="",
                new_state="SCALE_CANDIDATE",
                actor="policy_engine",
                rationale="Test record",
            )
        )
        records = audit.all_records()
        assert len(records) == 1
        assert records[0].new_state == "SCALE_CANDIDATE"
        assert records[0].entity_id == "TIKTOK"

    def test_audit_is_append_only(self):
        """Existing records must be unchanged after adding a new record."""
        audit = _make_audit()
        audit.record(
            AuditRecord(
                entity_type="channel_recommendation",
                entity_id="TIKTOK",
                previous_state="",
                new_state="SCALE_CANDIDATE",
                actor="policy_engine",
                rationale="First record",
            )
        )
        first_id = audit.all_records()[0].audit_id
        first_state = audit.all_records()[0].new_state

        # Add second record
        audit.record(
            AuditRecord(
                entity_type="channel_recommendation",
                entity_id="TIKTOK",
                previous_state="SCALE_CANDIDATE",
                new_state="APPROVED",
                actor="human_reviewer",
                rationale="Second record",
            )
        )

        records = audit.all_records()
        assert len(records) == 2
        # First record unchanged
        assert records[0].audit_id == first_id
        assert records[0].new_state == first_state

    def test_audit_get_history_ordered(self):
        """get_history returns records in insertion order for a given entity_id."""
        audit = _make_audit()
        states = ["INSUFFICIENT_DATA", "OBSERVE", "SCALE_CANDIDATE"]
        for i, state in enumerate(states):
            audit.record(
                AuditRecord(
                    entity_type="channel_recommendation",
                    entity_id="TIKTOK",
                    previous_state=states[i - 1] if i > 0 else "",
                    new_state=state,
                    actor="policy_engine",
                    rationale=f"Step {i}",
                )
            )
        # Also add a record for a different entity to ensure filtering works
        audit.record(
            AuditRecord(
                entity_type="channel_recommendation",
                entity_id="META",
                previous_state="",
                new_state="HOLD",
                actor="policy_engine",
                rationale="META record",
            )
        )

        history = audit.get_history("TIKTOK")
        assert len(history) == 3
        assert [r.new_state for r in history] == states

    def test_audit_record_raises_on_missing_field(self):
        """record() must raise ValueError if a required field is empty."""
        audit = _make_audit()
        with pytest.raises(ValueError):
            audit.record(
                AuditRecord(
                    entity_type="channel_recommendation",
                    entity_id="",  # missing
                    previous_state="",
                    new_state="SCALE_CANDIDATE",
                    actor="policy_engine",
                    rationale="Missing entity_id",
                )
            )

    def test_audit_to_jsonl(self):
        """to_jsonl returns valid newline-delimited JSON."""
        import json

        audit = _make_audit()
        audit.record(
            AuditRecord(
                entity_type="channel_recommendation",
                entity_id="TIKTOK",
                previous_state="",
                new_state="SCALE_CANDIDATE",
                actor="policy_engine",
                rationale="JSONL test",
            )
        )
        jsonl = audit.to_jsonl()
        parsed = json.loads(jsonl)
        assert parsed["entity_id"] == "TIKTOK"
        assert parsed["new_state"] == "SCALE_CANDIDATE"


# ---------------------------------------------------------------------------
# Review gate tests
# ---------------------------------------------------------------------------

class TestGrowthReviewer:
    def _make_recommendation(self) -> ChannelRecommendation:
        audit = _make_audit()
        analyst = _make_analyst(audit)
        ev = _tiktok_evidence()
        return analyst.analyze_channel(ev)

    def test_review_approve_sets_status(self):
        rec = self._make_recommendation()
        audit = _make_audit()
        gr = GrowthReviewer(audit_log=audit)
        decision = gr.review(rec, ReviewAction.APPROVE, "reviewer_001", "Looks good.")
        assert rec.review_status == "APPROVED"
        assert decision.action == "APPROVED"
        assert decision.reviewer_id == "reviewer_001"

    def test_review_reject_sets_status(self):
        rec = self._make_recommendation()
        audit = _make_audit()
        gr = GrowthReviewer(audit_log=audit)
        gr.review(rec, ReviewAction.REJECT, "reviewer_002", "Disagree with scale decision.")
        assert rec.review_status == "REJECTED"

    def test_review_request_revision_sets_status(self):
        rec = self._make_recommendation()
        audit = _make_audit()
        gr = GrowthReviewer(audit_log=audit)
        gr.review(
            rec,
            ReviewAction.REQUEST_REVISION,
            "reviewer_003",
            "Need more creative data first.",
        )
        assert rec.review_status == "REVISION_REQUESTED"

    def test_review_invalid_action_raises(self):
        rec = self._make_recommendation()
        audit = _make_audit()
        gr = GrowthReviewer(audit_log=audit)
        with pytest.raises(ValueError, match="Invalid review action"):
            gr.review(rec, "AUTO_APPROVE", "bot_001", "No human needed.")

    def test_review_records_to_audit(self):
        rec = self._make_recommendation()
        audit = _make_audit()
        gr = GrowthReviewer(audit_log=audit)
        gr.review(rec, ReviewAction.APPROVE, "reviewer_001", "Approved.")
        records = audit.all_records()
        assert len(records) == 1
        assert records[0].actor == "human_reviewer"
        assert records[0].new_state == "APPROVED"


# ---------------------------------------------------------------------------
# PerformanceAnalyst integration tests
# ---------------------------------------------------------------------------

class TestPerformanceAnalyst:
    def test_recommendation_is_always_recommend_only(self):
        """Every ChannelRecommendation must have recommend_only=True."""
        audit = _make_audit()
        analyst = _make_analyst(audit)

        for ev in [_tiktok_evidence(), _meta_evidence()]:
            rec = analyst.analyze_channel(ev)
            assert rec.recommend_only is True, (
                f"{ev.channel} recommendation has recommend_only=False"
            )

    def test_policy_decision_recommendation_not_alterable_by_llm(self):
        """The policy_decision.recommendation must be unchanged after LLM narrative."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        ev = _tiktok_evidence()

        # Run the full pipeline
        rec = analyst.analyze_channel(ev)

        # Policy state before and after must match
        expected_state = RecommendationState.SCALE_CANDIDATE
        assert rec.policy_decision.recommendation == expected_state, (
            "LLM narrative generation must not alter policy_decision.recommendation"
        )
        # Narrative may be present but cannot change the state
        assert rec.narrative_rationale != ""
        # Confirm the state is still what policy computed
        assert rec.policy_decision.recommendation == expected_state

    def test_analyst_produces_narrative_fields(self):
        """All four narrative fields must be non-empty strings."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        ev = _tiktok_evidence()
        rec = analyst.analyze_channel(ev)

        assert isinstance(rec.narrative_rationale, str) and rec.narrative_rationale
        assert isinstance(rec.tradeoff, str) and rec.tradeoff
        assert isinstance(rec.risk, str) and rec.risk
        assert isinstance(rec.next_experiment_hypothesis, str) and rec.next_experiment_hypothesis

    def test_analyst_records_two_audit_entries(self):
        """Each analyze_channel call must produce exactly 2 audit entries."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        ev = _tiktok_evidence()
        analyst.analyze_channel(ev)

        records = audit.all_records()
        assert len(records) == 2
        actors = [r.actor for r in records]
        assert "policy_engine" in actors
        assert "llm_agent" in actors

    def test_review_status_pending_by_default(self):
        """Recommendations must start as PENDING_HUMAN_REVIEW."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        rec = analyst.analyze_channel(_meta_evidence())
        assert rec.review_status == "PENDING_HUMAN_REVIEW"

    def test_data_origin_is_synthetic(self):
        """All outputs must carry data_origin='SYNTHETIC'."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        rec = analyst.analyze_channel(_tiktok_evidence())
        assert rec.data_origin == "SYNTHETIC"
        assert rec.policy_decision.data_origin == "SYNTHETIC"
        for r in audit.all_records():
            assert r.data_origin == "SYNTHETIC"

    def test_tiktok_is_scale_candidate(self):
        """End-to-end: TikTok profile → SCALE_CANDIDATE."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        rec = analyst.analyze_channel(_tiktok_evidence())
        assert rec.policy_decision.recommendation == RecommendationState.SCALE_CANDIDATE

    def test_meta_is_hold(self):
        """End-to-end: META profile (LTV:CAC 0.48x) → HOLD."""
        audit = _make_audit()
        analyst = _make_analyst(audit)
        rec = analyst.analyze_channel(_meta_evidence())
        assert rec.policy_decision.recommendation == RecommendationState.HOLD
