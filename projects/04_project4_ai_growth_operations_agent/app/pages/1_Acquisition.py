"""Acquisition Analysis — Channel scorecard, funnel, persona breakdown.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from utils.data_loader import load_channel_scorecard, load_trials_by_persona, load_funnel
from utils.metrics import fmt_currency, fmt_pct, fmt_number, channel_color
from utils.theme import inject_theme, render_navigation, PRIMARY, BLUE, TEAL, GREEN, AMBER, RED, MUTED, MUTED_BAR

st.set_page_config(
    page_title="Acquisition — Tablr Growth",
    page_icon=":material/ads_click:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Acquisition Analysis</h1>",
    unsafe_allow_html=True,
)
st.caption("Channel scorecard · Funnel breakdown · Missing attribution analysis")

st.markdown("---")

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading acquisition data..."):
    scorecard = load_channel_scorecard()
    personas = load_trials_by_persona()
    funnel = load_funnel()

# ── Channel Scorecard Table ────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>01 — Full channel scorecard: trial volume vs. activation efficiency</div>",
    unsafe_allow_html=True,
)

display_cols = {
    "channel": "Channel",
    "impressions": "Impressions",
    "clicks": "Clicks",
    "ctr": "CTR",
    "cpm_usd": "CPM",
    "spend_usd": "Spend",
    "trial_signups": "Trial Signups",
    "trial_cac_usd": "Trial CAC",
    "activated_owners": "Activated Owners",
    "cpao_usd": "CPAO",
}

table_data = []
for _, r in scorecard.iterrows():
    table_data.append({
        "Channel": r["channel"],
        "Impressions": fmt_number(int(r["impressions"])),
        "Clicks": fmt_number(int(r["clicks"])),
        "CTR": fmt_pct(r["ctr"], 2),
        "CPM": fmt_currency(r["cpm_usd"]),
        "Spend": fmt_currency(r["spend_usd"]),
        "Trial Signups": fmt_number(int(r["trial_signups"])),
        "Trial CAC": fmt_currency(r["trial_cac_usd"]),
        "Activated Owners": fmt_number(int(r["activated_owners"])),
        "CPAO": fmt_currency(r["cpao_usd"]) if r["cpao_usd"] else "—",
    })

st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
st.caption(
    "CPAO = Cost per Activated Owner (spend / campaign_launched within 14 days of trial). "
    "Key signal: lower CPAO = more efficient activation, regardless of trial volume."
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Trial CAC vs CPAO: The Reversal ──────────────────────────────────────────
st.markdown(
    "<div class='section-header'>02 — META looks cheaper on trial CAC ($52) but costs 4.7× more per activated owner</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """<div style='background:#eff6ff;border-left:4px solid #1a6fbe;padding:10px 14px;
    border-radius:0 6px 6px 0;font-size:0.88rem;color:#1e3a5f;margin-bottom:12px;'>
    <b>Key insight:</b> META's trial CAC ($52) is higher than TikTok's ($12), but the CPAO gap
    is even larger: META is 4.7x more expensive per activated owner ($666 vs $143). Trial CAC
    alone understates META's inefficiency — CPAO is the metric that reveals the true cost.
    </div>""",
    unsafe_allow_html=True,
)

ch_df = scorecard[scorecard["cpao_usd"].notna()].copy()
channels = ch_df["channel"].tolist()
colors = [channel_color(c) for c in channels]

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Trial CAC",
    x=channels,
    y=ch_df["trial_cac_usd"],
    marker_color=TEAL,
    text=[fmt_currency(v) for v in ch_df["trial_cac_usd"]],
    textposition="outside",
))
fig.add_trace(go.Bar(
    name="CPAO",
    x=channels,
    y=ch_df["cpao_usd"],
    marker_color=RED,
    text=[fmt_currency(v) for v in ch_df["cpao_usd"]],
    textposition="outside",
))
fig.update_layout(
    barmode="group",
    height=340,
    margin=dict(l=0, r=10, t=10, b=40),
    yaxis=dict(title="USD", tickprefix="$"),
    legend=dict(orientation="h", y=-0.2),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig, use_container_width=True)
st.caption("CPAO is the primary efficiency metric — not trial CAC.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Persona Funnel Breakdown ──────────────────────────────────────────────────
col_a, col_b = st.columns([2, 3])

with col_a:
    st.markdown(
        "<div class='section-header'>03 — Persona mix: who is trying Tablr?</div>",
        unsafe_allow_html=True,
    )

    persona_totals = personas.groupby("persona_segment")["trials"].sum().reset_index()
    persona_totals = persona_totals.sort_values("trials", ascending=False)

    PERSONA_COLORS = {
        "scrappy_independent": "#0f4c81",
        "growth_minded": "#1a6fbe",
        "delivery_heavy": "#0d9488",
        "multi_location": "#16a34a",
        "new_owner": "#d97706",
        "UNKNOWN": "#64748b",
    }

    fig_p = go.Figure(go.Pie(
        labels=persona_totals["persona_segment"],
        values=persona_totals["trials"],
        hole=0.45,
        marker_colors=[PERSONA_COLORS.get(p, MUTED) for p in persona_totals["persona_segment"]],
        textinfo="label+percent",
        textfont_size=11,
    ))
    fig_p.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_p, use_container_width=True)
    st.caption("5 ICP personas + unattributed accounts.")

with col_b:
    st.markdown(
        "<div class='section-header'>04 — Channel × persona breakdown: where each segment comes from</div>",
        unsafe_allow_html=True,
    )

    pivot = personas.pivot_table(
        index="persona_segment", columns="channel", values="trials", aggfunc="sum", fill_value=0
    ).reset_index()
    st.dataframe(pivot, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # Missing attribution note
    unknown_trials = int(personas[personas["channel"] == "UNKNOWN"]["trials"].sum())
    total_trials = int(personas["trials"].sum())
    missing_pct = unknown_trials / total_trials if total_trials else 0

    st.markdown(
        f"""<div style='background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;
        padding:12px 14px;font-size:0.87rem;color:#7c2d12;'>
        <b>Missing Attribution:</b> {fmt_number(unknown_trials)} accounts ({fmt_pct(missing_pct)})
        have no channel attribution. These are labelled UNKNOWN and excluded from CPAO calculations.
        Possible causes: UTM parameter stripping, direct navigation, or post-install deep-link failure.
        <br><br>
        <b>Impact:</b> Blended CPAO may be understated if UNKNOWN accounts are more expensive to acquire.
        Recommendation: Implement server-side attribution tracking before Q2 2026.
        </div>""",
        unsafe_allow_html=True,
    )
