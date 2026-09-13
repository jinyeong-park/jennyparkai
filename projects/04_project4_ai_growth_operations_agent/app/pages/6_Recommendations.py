"""Recommendations Dashboard — Channel recommendations, audit trail, human review.

RECOMMEND_ONLY=True — All actions require human approval before execution.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pandas as pd
import streamlit as st

from utils.metrics import state_badge_html, fmt_currency, fmt_ratio, recommendation_color
from utils.theme import inject_theme, render_navigation, GREEN, AMBER, RED, TEAL, BLUE, PRIMARY, MUTED

st.set_page_config(
    page_title="Recommendations — Tablr Growth",
    page_icon=":material/recommend:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Channel Recommendations</h1>",
    unsafe_allow_html=True,
)
st.caption("Deterministic policy output · Evidence flags · Human review queue · Audit trail")

st.markdown("---")

# ── RECOMMEND_ONLY banner ──────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#fef3c7;border:1px solid #fde68a;border-radius:8px;
    padding:12px 18px;margin-bottom:20px;display:flex;align-items:flex-start;gap:12px;'>
    <span style='font-size:1.2rem;line-height:1.4;'>&#x1F6A7;</span>
    <div>
    <span style='font-size:0.82rem;font-weight:800;color:#92400e;text-transform:uppercase;
    letter-spacing:0.05em;'>Decision Support Only — RECOMMEND_ONLY = True</span><br>
    <span style='font-size:0.84rem;color:#78350f;line-height:1.6;'>
    This system outputs data-informed suggestions only.
    No budget changes, campaign pauses, or bid adjustments are executed automatically.
    Every action requires explicit human approval.
    </span>
    </div>
    </div>""",
    unsafe_allow_html=True,
)

# ── Load channel_recommendations.json ────────────────────────────────────────
REC_PATH = Path(__file__).parents[2] / "docs" / "examples" / "channel_recommendations.json"

try:
    with open(REC_PATH) as f:
        recs_data = json.load(f)
except Exception as e:
    st.error(f"Could not load channel_recommendations.json: {e}")
    st.stop()

channels = recs_data.get("channels", [])
audit_trail = recs_data.get("audit_trail", [])

# ── Recommendation cards ──────────────────────────────────────────────────────
st.markdown(
    """<div class='hero-block' style='margin-bottom:20px;'>
    <div class='hero-label'>Policy Engine Output · 3-Layer Decision System</div>
    <div class='hero-statement'>
        One clear action: scale TikTok, hold META, observe the rest.
    </div>
    <div class='hero-supporting'>
        Deterministic policy set recommendation state · LLM wrote narrative only · Human approval required before any action
    </div>
    </div>""",
    unsafe_allow_html=True,
)
st.markdown("<div class='section-header'>Recommendation Queue</div>", unsafe_allow_html=True)

for ch in channels:
    state = ch.get("recommendation_state", "")
    confidence = ch.get("confidence", "")
    channel = ch.get("channel", "")
    evidence = ch.get("evidence", {})
    review_status = ch.get("review_status", "")

    color = recommendation_color(state)
    conf_bg = {"HIGH": "#dcfce7", "MEDIUM": "#fef3c7", "LOW": "#fee2e2"}.get(confidence, "#f1f5f9")
    conf_color = {"HIGH": GREEN, "MEDIUM": AMBER, "LOW": RED}.get(confidence, MUTED)

    with st.expander(
        f"**{channel}** — {state} | Confidence: {confidence} | {review_status}",
        expanded=True,
    ):
        col_top, col_badge = st.columns([5, 1])
        with col_top:
            st.markdown(state_badge_html(state), unsafe_allow_html=True)
        with col_badge:
            st.markdown(
                f"<span style='background:{conf_bg};color:{conf_color};font-size:0.78rem;"
                f"font-weight:700;padding:3px 10px;border-radius:4px;'>{confidence}</span>",
                unsafe_allow_html=True,
            )

        col_ev, col_narr = st.columns([1, 2])

        with col_ev:
            st.markdown("**Evidence Summary**")
            ev_rows = {
                "Trials": f"{evidence.get('trials', '—'):,}",
                "Activated Owners": f"{evidence.get('activated_owners', '—'):,}",
                "Spend": fmt_currency(evidence.get("spend_usd")),
                "CPAO": fmt_currency(evidence.get("cpao_usd")),
                "Trial CAC": fmt_currency(evidence.get("trial_cac_usd")),
                "M1 Retention": fmt_ratio(evidence.get("m1_retention_rate"), 1) if evidence.get("m1_retention_rate") else "—",
                "M3 Retention": fmt_ratio(evidence.get("m3_retention_rate"), 1) if evidence.get("m3_retention_rate") else "—",
                "M6 Retention": fmt_ratio(evidence.get("m6_retention_rate"), 1) if evidence.get("m6_retention_rate") else "—",
                "Observed LTV": fmt_currency(evidence.get("observed_ltv_usd")),
                "LTV:CAC": fmt_ratio(evidence.get("ltv_cac_ratio")),
            }
            for k, v in ev_rows.items():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;font-size:0.84rem;"
                    f"padding:3px 0;border-bottom:1px solid #f1f5f9;'>"
                    f"<span style='color:#475569;'>{k}</span>"
                    f"<span style='font-weight:700;color:#0b1f3a;'>{v}</span></div>",
                    unsafe_allow_html=True,
                )

            # Evidence flags
            st.markdown("<br>**Evidence Flags:**", unsafe_allow_html=True)
            for flag in ch.get("evidence_flags", []):
                st.markdown(
                    f"<div style='font-size:0.78rem;color:#475569;font-family:monospace;"
                    f"background:#f8faff;padding:2px 6px;border-radius:3px;margin:2px 0;'>"
                    f"{flag}</div>",
                    unsafe_allow_html=True,
                )

            if ch.get("guardrail_violations"):
                st.markdown("<br>**Guardrail Violations:**", unsafe_allow_html=True)
                for v in ch["guardrail_violations"]:
                    st.markdown(
                        f"<div style='font-size:0.78rem;color:#dc2626;background:#fee2e2;"
                        f"padding:4px 8px;border-radius:4px;margin:2px 0;'>&#9888; {v}</div>",
                        unsafe_allow_html=True,
                    )

        with col_narr:
            st.markdown("**Rationale**")
            st.markdown(
                f"<div style='background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;"
                f"padding:12px 14px;font-size:0.86rem;color:#334155;line-height:1.6;'>"
                f"{ch.get('narrative_rationale', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("<br>**Tradeoff**", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#fefce8;border:1px solid #fde68a;border-radius:6px;"
                f"padding:10px 12px;font-size:0.84rem;color:#713f12;'>"
                f"{ch.get('tradeoff', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("<br>**Risk**", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#fff7f7;border:1px solid #fecaca;border-radius:6px;"
                f"padding:10px 12px;font-size:0.84rem;color:#7f1d1d;'>"
                f"{ch.get('risk', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("<br>**Next Experiment Hypothesis**", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;"
                f"padding:10px 12px;font-size:0.82rem;color:#14532d;'>"
                f"{ch.get('next_experiment_hypothesis', '').replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True,
            )

        # Human review buttons (display only)
        st.markdown("<br>**Review Actions** *(display only — no real action taken)*", unsafe_allow_html=True)
        rb1, rb2, rb3, _ = st.columns([1, 1, 1.5, 3])
        with rb1:
            st.button(
                "APPROVE", key=f"approve_{channel}",
                help="Display only. No action taken. Human approval required externally.",
                disabled=True,
            )
        with rb2:
            st.button(
                "REJECT", key=f"reject_{channel}",
                help="Display only. No action taken.",
                disabled=True,
            )
        with rb3:
            st.button(
                "REQUEST REVISION", key=f"revise_{channel}",
                help="Display only. No action taken.",
                disabled=True,
            )

        st.markdown(
            f"<div style='font-size:0.78rem;color:#64748b;margin-top:4px;'>"
            f"Review status: <b>{review_status}</b></div>",
            unsafe_allow_html=True,
        )

        if ch.get("reviewer_notes"):
            st.markdown(f"*Reviewer notes: {ch['reviewer_notes']}*")

st.markdown("---")

# ── Audit Trail ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Audit Trail</div>", unsafe_allow_html=True)

st.markdown(
    """<div style='background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;
    padding:10px 14px;margin-bottom:12px;font-size:0.84rem;color:#475569;'>
    Every state transition is logged with actor, timestamp, and rationale.
    The policy engine always writes before the LLM layer — LLM cannot change the recommendation state.
    </div>""",
    unsafe_allow_html=True,
)

if audit_trail:
    audit_display = []
    for entry in audit_trail:
        audit_display.append({
            "Audit ID": entry.get("audit_id", "")[:12] + "...",
            "Timestamp": entry.get("timestamp", "")[:19],
            "Entity": entry.get("entity_id", ""),
            "Actor": entry.get("actor", ""),
            "Previous State": entry.get("previous_state", "—"),
            "New State": entry.get("new_state", ""),
            "Rationale": entry.get("rationale", "")[:80] + "..." if len(entry.get("rationale", "")) > 80 else entry.get("rationale", ""),
        })
    st.dataframe(pd.DataFrame(audit_display), use_container_width=True, hide_index=True)
    st.caption(
        "Immutable audit log. All recommendations logged at generation time. "
        f"Data origin: {recs_data.get('data_origin', 'SYNTHETIC')} | "
        f"Generated: {recs_data.get('generated_at', '—')}"
    )
else:
    st.info("No audit trail entries found.")

st.markdown("---")
st.markdown(
    """<div style='background:#fef9ec;border:1px solid #fde68a;border-radius:8px;
    padding:12px 14px;font-size:0.84rem;color:#92400e;'>
    <b>&#9888; Architecture note:</b> The 3-layer decision system ensures:
    (1) Deterministic policy engine sets recommendation state — no ML hallucinations;
    (2) LLM agent writes narrative rationale only — cannot change the state;
    (3) Human review required before any budget or campaign action.
    RECOMMEND_ONLY=True is enforced at all layers.
    </div>""",
    unsafe_allow_html=True,
)
