# Phase 7 — Explainable Growth Decision Agent

[SYNTHETIC DATA] — all metrics in this document are simulated for portfolio purposes.

## Purpose

Transform validated analytics outputs (CPAO, M6 retention, LTV:CAC) into structured, auditable channel recommendations — without letting an LLM decide what those recommendations should be. The agent separates the concern of _what to recommend_ (deterministic policy) from _how to explain it_ (LLM narrative).

## Architecture

The decision pipeline has three sequential layers, each with a distinct role and strict constraints.

```
ChannelEvidence
      │
      ▼
┌─────────────────────────────────┐
│  Policy Layer (deterministic)   │  ← No LLM. Pure rule evaluation.
│  evaluate_channel()             │
│  Outputs: PolicyDecision        │
│  (recommendation, confidence,   │
│   evidence_flags, guardrail_    │
│   violations)                   │
└─────────────────────────────────┘
      │  recommendation locked here — never changes again
      ▼
┌─────────────────────────────────┐
│  LLM Narrative Layer            │  ← Reads metrics, writes prose only.
│  PerformanceAnalyst.analyze()   │  ← Cannot change recommendation state.
│  MockAnalystLLMProvider.        │  ← Cannot invent or adjust metric values.
│  complete()                     │
│  Outputs: RATIONALE, TRADEOFF,  │
│           RISK, NEXT_EXPERIMENT  │
└─────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────┐
│  Human Review Gate              │  ← APPROVE / REJECT / REVISION_REQUESTED
│  GrowthReviewer.review()        │  ← No recommendation becomes action without APPROVED.
│  Outputs: ReviewDecision        │
│           + Audit record        │
└─────────────────────────────────┘
```

Every state change at every layer is written to an append-only `AuditLog`. The log is the source of truth for what was decided, when, and why.

## Policy Rules

The policy engine applies these rules in priority order. The first matching rule wins.

| Priority | Condition | Recommendation | Confidence |
|---|---|---|---|
| 1 | `trials < min_trials_for_decision` | INSUFFICIENT_DATA | LOW |
| 2 | `cpao_usd is None` | INSUFFICIENT_DATA | LOW |
| 3 | `m1_retention_rate < m1_retention_floor (0.70)` | guardrail violation added; max state = HOLD | LOW |
| 4 | `ltv_cac_ratio >= 1.0` AND `m6_is_mature=True` | SCALE_CANDIDATE | HIGH |
| 5 | `ltv_cac_ratio >= 1.0` AND `m6_is_mature=False` | OBSERVE (M6 immature cap) | MEDIUM |
| 6 | `ltv_cac_ratio >= 0.50` | OBSERVE | MEDIUM |
| 7 | `ltv_cac_ratio < 0.20` | PAUSE_CANDIDATE | HIGH (mature) / MEDIUM (immature) |
| 8 | `0.20 <= ltv_cac_ratio < 0.50` | HOLD | MEDIUM |

The M1 retention guardrail (rule 3) acts as a cap: if it triggers, SCALE_CANDIDATE and OBSERVE are both downgraded to HOLD, and confidence drops to LOW. This prevents scaling channels that acquire low-quality cohorts even if their aggregate LTV:CAC looks acceptable.

The M6 maturity cap (rule 5) prevents SCALE_CANDIDATE without a mature 6-month retention signal. A channel can have a strong LTV:CAC estimate (≥ 1.0x) but still be blocked from scale until the retention data matures.

## Audit Trail

Every state transition is recorded as an `AuditRecord` with:

- `audit_id` — UUID, unique per record
- `timestamp` — UTC ISO 8601
- `entity_type` — e.g. `channel_recommendation`
- `entity_id` — e.g. `TIKTOK`, `META`
- `previous_state` — state before this change (empty string for initial entry)
- `new_state` — state after this change
- `actor` — `policy_engine` | `llm_agent` | `human_reviewer`
- `rationale` — short explanation of why the state changed
- `data_origin` — always `SYNTHETIC`

A typical `analyze_channel()` call produces exactly two audit records: one from `policy_engine` (recommendation locked), one from `llm_agent` (narrative added, state unchanged). A review call produces a third record from `human_reviewer`.

The log is append-only — records are never modified after creation. This means any downstream consumer can replay the audit trail and verify that the LLM never altered the recommendation state.

## TikTok vs META: Example Outcomes

Running the policy engine against the synthetic channel evidence produces the following decisions:

| Metric | TikTok | META |
|---|---|---|
| Trials | 1,005 | 379 |
| Activated Owners | 262 | 90 |
| Total Spend | $37,490 | $59,974 |
| CPAO | $143 | $666 |
| Trial CAC | $12 | $52 |
| M1 Retention | 79.9% | 82.5% |
| M3 Retention | 57.6% | 55.0% |
| M6 Retention | 37.5% | 45.0% |
| M6 Mature | Yes | Yes |
| Observed LTV | $291 | $318 |
| LTV:CAC Ratio | **2.03x** | **0.48x** |
| **Policy Decision** | **SCALE_CANDIDATE** | **HOLD** |
| Confidence | HIGH | HIGH |
| Guardrail Violations | None | None |

**TikTok — SCALE_CANDIDATE:** LTV:CAC of 2.03x far exceeds the 1.0x threshold. M6 retention is mature at 37.5%. M1 retention of 79.9% clears the 70% floor. All rules pass without block. Confidence is HIGH because trials (1,005) exceed 2× the minimum (100) and M6 is mature with no guardrail violations.

**META — HOLD:** LTV:CAC of 0.48x falls below the 0.50x OBSERVE threshold, mapping to HOLD. Despite receiving the highest absolute spend ($59,974), META produces only 90 activated owners — fewer than TikTok on 60% more budget. META's CPAO of $666 is 4.7x higher than TikTok's $143. The recommendation is to hold spend at minimum while running a creative experiment (DEMONSTRATION hook vs current CONTRAST hook) to determine whether the problem is structural (channel) or solvable (creative mix).

## Files

| File | Role |
|---|---|
| `src/growth_agent/decisioning/policy.py` | Deterministic policy — `evaluate_channel()`, `evaluate_creative()` |
| `src/growth_agent/governance/audit.py` | Append-only audit log — `AuditLog`, `AuditRecord` |
| `src/growth_agent/agents/performance_analyst.py` | Policy + LLM pipeline — `PerformanceAnalyst`, `MockAnalystLLMProvider` |
| `src/growth_agent/agents/growth_reviewer.py` | Human review gate — `GrowthReviewer`, `ReviewAction` |
| `prompts/performance_diagnosis.md` | LLM prompt template for narrative generation |
| `prompts/winner_iteration.md` | LLM prompt for next-experiment design on SCALE_CANDIDATE channels |
| `examples/channel_recommendations.json` | Output artifact: TikTok and META recommendations with full audit trail |
| `tests/unit/test_decisioning.py` | 28 unit tests covering policy rules, audit, review gate, and analyst pipeline |
