"""Tablr Growth Intelligence Dashboard — Executive Summary.

— all numbers are simulated for portfolio purposes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_channel_scorecard, load_funnel, load_retention
from utils.metrics import (
    fmt_currency,
    fmt_number,
    fmt_pct,
    channel_color,
    state_badge_html,
)
from utils.theme import inject_theme, render_navigation, PRIMARY, BLUE, GREEN, AMBER, RED, TEAL, MUTED, MUTED_BAR, GRID

st.set_page_config(
    page_title="Tablr Growth Intelligence",
    page_icon=":material/dashboard:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Title row ─────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.8rem;font-weight:800;margin-bottom:0;'>"
    "Tablr Growth Intelligence Dashboard</h1>",
    unsafe_allow_html=True,
)
st.caption("AI-powered growth operations agent | 12-week simulation (Jan–Mar 2026)")

st.markdown("---")

# ── Hero block ────────────────────────────────────────────────────────────────
st.markdown(
    """<div class='hero-block'>
    <div class='hero-label'>12-Week Growth Verdict · Jan–Mar 2026</div>
    <div class='hero-statement'>
        TikTok is the only channel generating positive unit economics.<br>
        META is consuming 40% of budget at 4.7× the cost per activated owner.
    </div>
    <div class='hero-supporting'>
        TikTok CPAO $143 · LTV:CAC 2.03× → <strong style='color:#86efac;'>SCALE_CANDIDATE</strong>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        META CPAO $666 · LTV:CAC 0.48× → <strong style='color:#fca5a5;'>HOLD</strong>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        2,000 trials · 519 activated owners · $150K total spend
    </div>
    </div>""",
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    funnel_df = load_funnel()
    scorecard_df = load_channel_scorecard()
    retention_df = load_retention()

funnel = funnel_df.iloc[0]
trials = int(funnel["trials"])
onboarding = int(funnel["onboarding_completed"])
activated = int(funnel["activated_owners"])
subscriptions = int(funnel["subscriptions"])
total_spend = float(scorecard_df["spend_usd"].sum())

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Trial Signups</div>
        <div class='metric-value'>{fmt_number(trials)}</div>
        <div class='metric-delta'>~167/week · 12-week simulation</div>
        </div>""",
        unsafe_allow_html=True,
    )

with k2:
    act_rate = activated / trials if trials else 0
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Activated Owners</div>
        <div class='metric-value'>{fmt_number(activated)}</div>
        <div class='metric-delta'>{fmt_pct(act_rate)} of trials · TikTok best at 37%</div>
        </div>""",
        unsafe_allow_html=True,
    )

with k3:
    conv_rate = subscriptions / trials if trials else 0
    sub_of_act = subscriptions / activated if activated else 0
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Subscriptions</div>
        <div class='metric-value'>{fmt_number(subscriptions)}</div>
        <div class='metric-delta'>{fmt_pct(conv_rate)} of trials · {fmt_pct(sub_of_act)} of activated</div>
        </div>""",
        unsafe_allow_html=True,
    )

with k4:
    blended_cpao = total_spend / activated if activated else None
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Total Media Spend</div>
        <div class='metric-value'>{fmt_currency(total_spend)}</div>
        <div class='metric-delta'>Blended CPAO {fmt_currency(blended_cpao)} · TikTok $143 vs META $666</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Three-column main section ─────────────────────────────────────────────────
col_left, col_mid, col_right = st.columns([1, 1, 1])

# LEFT: Acquisition Funnel
with col_left:
    st.markdown(
        "<div class='section-header'>01 — Where does the funnel lose potential subscribers?</div>",
        unsafe_allow_html=True,
    )

    stages = ["Trial Signups", "Onboarding", "Activated Owners", "Subscriptions"]
    values = [trials, onboarding, activated, subscriptions]

    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        textfont=dict(size=12),
        marker=dict(color=[PRIMARY, BLUE, TEAL, GREEN]),
        connector=dict(line=dict(color=GRID, width=1)),
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Biggest drop: trial → onboarding (38% lost). Activation → subscription: 51% conversion.")

# MIDDLE: Channel CPAO Comparison
with col_mid:
    st.markdown(
        "<div class='section-header'>02 — TikTok's CPAO is 4.7× lower than META</div>",
        unsafe_allow_html=True,
    )

    ch_df = scorecard_df[scorecard_df["cpao_usd"].notna()].sort_values("cpao_usd")
    # Highlight exception: TikTok green (winner), META red (problem), rest muted
    bar_colors = []
    for c in ch_df["channel"]:
        if c == "TIKTOK":
            bar_colors.append(GREEN)
        elif c == "META":
            bar_colors.append(RED)
        else:
            bar_colors.append(MUTED_BAR)

    fig2 = go.Figure(go.Bar(
        x=ch_df["cpao_usd"],
        y=ch_df["channel"],
        orientation="h",
        marker_color=bar_colors,
        text=[fmt_currency(v) for v in ch_df["cpao_usd"]],
        textposition="outside",
    ))
    fig2.add_vline(
        x=ch_df["cpao_usd"].mean(),
        line_dash="dash",
        line_color=AMBER,
        annotation_text="Avg $375",
        annotation_position="top right",
    )
    fig2.update_layout(
        height=280,
        margin=dict(l=0, r=80, t=10, b=10),
        xaxis=dict(showgrid=False, showticklabels=False, title="CPAO (Cost per Activated Owner)"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Green = SCALE_CANDIDATE. Red = HOLD. Dashed = blended average.")

# RIGHT: Recommendation Queue
with col_right:
    st.markdown("<div class='section-header'>Recommendation Queue</div>", unsafe_allow_html=True)

    recs = [
        {"Channel": "TIKTOK", "State": "SCALE_CANDIDATE", "Confidence": "HIGH"},
        {"Channel": "GOOGLE_SEARCH", "State": "OBSERVE", "Confidence": "MEDIUM"},
        {"Channel": "META", "State": "HOLD", "Confidence": "HIGH"},
        {"Channel": "LINKEDIN", "State": "OBSERVE", "Confidence": "LOW"},
    ]

    for r in recs:
        badge = state_badge_html(r["State"])
        conf_color = {"HIGH": GREEN, "MEDIUM": AMBER, "LOW": MUTED}[r["Confidence"]]
        st.markdown(
            f"""<div style='display:flex;align-items:center;justify-content:space-between;
            padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:6px;
            background:#ffffff;'>
            <span style='font-weight:700;color:#0b1f3a;font-size:0.9rem;'>{r['Channel']}</span>
            <span>{badge}</span>
            <span style='font-size:0.78rem;font-weight:600;color:{conf_color};'>{r['Confidence']}</span>
            </div>""",
            unsafe_allow_html=True,
        )

    st.caption("RECOMMEND_ONLY=True. Human approval required for all actions.")

st.markdown("---")

# ── Bottom row ────────────────────────────────────────────────────────────────
bot_left, bot_right = st.columns([3, 2])

with bot_left:
    st.markdown(
        "<div class='section-header'>03 — TikTok retains subscribers best at every cohort milestone</div>",
        unsafe_allow_html=True,
    )

    channels = retention_df["channel"].tolist()
    m1 = retention_df["m1_rate"].tolist()
    m3 = retention_df["m3_rate"].tolist()
    m6 = retention_df["m6_rate"].tolist()

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="M1", x=channels, y=m1, marker_color=GREEN,
                          text=[fmt_pct(v) for v in m1], textposition="outside"))
    fig3.add_trace(go.Bar(name="M3", x=channels, y=m3, marker_color=TEAL,
                          text=[fmt_pct(v) for v in m3], textposition="outside"))
    fig3.add_trace(go.Bar(name="M6", x=channels, y=m6, marker_color=BLUE,
                          text=[fmt_pct(v) if v else "N/A" for v in m6], textposition="outside"))

    fig3.update_layout(
        barmode="group",
        height=300,
        margin=dict(l=0, r=10, t=10, b=10),
        yaxis=dict(tickformat=".0%", range=[0, 1.1]),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("M6 shown only for mature cohorts (conversion + 180 days <= 2026-09-13).")

with bot_right:
    st.markdown("<div class='section-header'>Data Quality & Simulation Notes</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='background:#fef9ec;border:1px solid #fde68a;border-radius:8px;padding:14px 16px;'>
        <ul style='margin:0;padding-left:16px;font-size:0.88rem;color:#92400e;line-height:1.7;'>
        <li><b>7.6% missing attribution</b> — 152 accounts labelled UNKNOWN</li>
        <li><b>16/90 creatives</b> (17.8%) showing CTR fatigue signals</li>
        <li><b>Simulation period:</b> Jan 5 – Mar 29, 2026 (12 weeks)</li>
        <li><b>M6 retention</b> capped at mature cohorts only</li>
        <li><b>Projected LTV</b> uses constant churn assumption (2–3 month observation window)</li>
        <li>All numbers are <b>synthetic</b> — no real Tablr data used</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(
        "Navigate to pages using the sidebar to explore Acquisition, "
        "Creative Intelligence, Retention, LTV & Budget, Experiments, and Recommendations.",
        icon=":material/arrow_forward:",
    )
