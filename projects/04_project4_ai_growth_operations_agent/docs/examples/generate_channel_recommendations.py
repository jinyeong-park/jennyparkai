"""Generate channel recommendations using synthetic data.

Runs PerformanceAnalyst with MockAnalystLLMProvider against
hard-coded synthetic metrics matching Phase 5/6 outputs.

[SYNTHETIC DATA]
"""

import json
import sys
from pathlib import Path

# Ensure src is on path when run directly
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from growth_agent.decisioning.policy import ChannelEvidence
from growth_agent.governance.audit import AuditLog
from growth_agent.agents.performance_analyst import (
    PerformanceAnalyst,
    MockAnalystLLMProvider,
    ChannelRecommendation,
)
from growth_agent.agents.growth_reviewer import GrowthReviewer, ReviewAction


def recommendation_to_dict(rec: ChannelRecommendation) -> dict:
    pd = rec.policy_decision
    return {
        "channel": rec.channel,
        "recommendation_state": pd.recommendation.value,
        "confidence": pd.confidence,
        "evidence_flags": pd.evidence_flags,
        "guardrail_violations": pd.guardrail_violations,
        "is_mature": pd.is_mature,
        "decided_at": str(pd.decided_at),
        "narrative_rationale": rec.narrative_rationale,
        "tradeoff": rec.tradeoff,
        "risk": rec.risk,
        "next_experiment_hypothesis": rec.next_experiment_hypothesis,
        "review_status": rec.review_status,
        "reviewer_notes": rec.reviewer_notes,
        "recommend_only": rec.recommend_only,
        "data_origin": rec.data_origin,
    }


def main() -> None:
    audit_log = AuditLog()
    provider = MockAnalystLLMProvider()
    analyst = PerformanceAnalyst(provider=provider, audit_log=audit_log)
    reviewer = GrowthReviewer(audit_log=audit_log)

    # --- TikTok: Best channel (Phase 5/6 synthetic data) ---
    tiktok_evidence = ChannelEvidence(
        channel="TIKTOK",
        evaluation_period_days=90,
        trials=412,
        activated_owners=228,
        spend_usd=207_024.0,
        cpao_usd=908.0,
        trial_cac_usd=335.0,
        m1_retention_rate=0.812,
        m3_retention_rate=0.634,
        m6_retention_rate=0.474,
        m6_is_mature=True,
        observed_ltv_usd=209.0,
        ltv_cac_ratio=0.23,
        min_trials_for_decision=100,
        cpao_efficiency_vs_baseline_pct=35.0,  # 35% better than baseline
        m1_retention_floor=0.70,
        data_origin="SYNTHETIC",
    )

    tiktok_rec = analyst.analyze_channel(tiktok_evidence)

    # --- META: Worst channel (Phase 5/6 synthetic data) ---
    meta_evidence = ChannelEvidence(
        channel="META",
        evaluation_period_days=90,
        trials=389,
        activated_owners=174,
        spend_usd=242_904.0,
        cpao_usd=1_396.0,
        trial_cac_usd=508.0,
        m1_retention_rate=0.778,
        m3_retention_rate=0.591,
        m6_retention_rate=0.432,
        m6_is_mature=True,
        observed_ltv_usd=181.0,
        ltv_cac_ratio=0.13,
        min_trials_for_decision=100,
        cpao_efficiency_vs_baseline_pct=-3.0,  # 3% worse than baseline
        m1_retention_floor=0.70,
        data_origin="SYNTHETIC",
    )

    meta_rec = analyst.analyze_channel(meta_evidence)

    # Leave both in PENDING_HUMAN_REVIEW (no auto-approval)
    # The reviewer could approve/reject — shown here as comments only:
    # reviewer.review(tiktok_rec, ReviewAction.APPROVE, "reviewer_001", "Approved for scale test Q4.")
    # reviewer.review(meta_rec, ReviewAction.REQUEST_REVISION, "reviewer_001", "Need creative experiment first.")

    # Assemble output
    output = {
        "data_origin": "SYNTHETIC",
        "generated_at": str(__import__("datetime").date.today()),
        "model": "deterministic_policy + mock_analyst_llm",
        "channels": [
            recommendation_to_dict(tiktok_rec),
            recommendation_to_dict(meta_rec),
        ],
        "audit_trail": [
            {
                "audit_id": r.audit_id,
                "timestamp": r.timestamp,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "previous_state": r.previous_state,
                "new_state": r.new_state,
                "actor": r.actor,
                "rationale": r.rationale,
                "data_origin": r.data_origin,
            }
            for r in audit_log.all_records()
        ],
    }

    out_path = Path(__file__).parent / "channel_recommendations.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Written to {out_path}")

    # Print summary
    print("\n=== SUMMARY ===")
    for ch in output["channels"]:
        print(
            f"{ch['channel']:15s} → {ch['recommendation_state']:20s} "
            f"(confidence={ch['confidence']}, review={ch['review_status']})"
        )
    print(f"\nAudit records: {len(output['audit_trail'])}")


if __name__ == "__main__":
    main()
