"""LTV & Budget Allocation — LTV:CAC analysis, interactive budget slider.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from utils.data_loader import load_ltv_cac, load_budget_allocation
from utils.metrics import fmt_currency, fmt_pct, fmt_number, fmt_ratio, channel_color
from utils.theme import inject_theme, render_navigation, GREEN, TEAL, BLUE, AMBER, RED, PRIMARY, MUTED, MUTED_BAR

st.set_page_config(
    page_title="LTV & Budget — Tablr Growth",
    page_icon=":material/attach_money:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>LTV & Budget Allocation</h1>",
    unsafe_allow_html=True,
)
st.caption("LTV:CAC analysis · Budget allocation simulator · Exploration reserve")

st.markdown("---")

# ── LTV assumption note ───────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#fef3c7;border:1px solid #fde68a;border-radius:8px;
    padding:12px 16px;margin-bottom:16px;font-size:0.87rem;color:#92400e;'>
    <b>&#9888; LTV Assumption:</b>
    Observed LTV covers only 2–3 months of revenue due to the short simulation window
    (2026-01-05 to 2026-03-29). Projected LTV uses a constant monthly churn rate assumption
    (LTV = avg monthly price / churn rate). Treat projected LTV as directional only.
    </div>""",
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading LTV data..."):
    ltv_df = load_ltv_cac()

# ── LTV:CAC Table ─────────────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>01 — Only TikTok clears the 1.0× LTV:CAC profitability threshold</div>",
    unsafe_allow_html=True,
)

ltv_display = []
for _, r in ltv_df.iterrows():
    ltv_display.append({
        "Channel": r["channel"],
        "Total Spend": fmt_currency(r["total_spend"]),
        "Activated Owners": fmt_number(int(r["activated_owners"])) if pd.notna(r["activated_owners"]) else "—",
        "CPAO": fmt_currency(r["cpao_usd"]),
        "Avg Monthly Price": fmt_currency(r["avg_monthly_price"]),
        "Observed LTV": fmt_currency(r["avg_observed_ltv"]),
        "Projected LTV": fmt_currency(r["projected_ltv"]),
        "LTV:CAC (Obs.)": fmt_ratio(r["ltv_cac_ratio_observed"]),
        "Payback (mo)": f"{r['payback_months']:.1f}" if r["payback_months"] and r["payback_months"] == r["payback_months"] else "—",
    })

st.dataframe(pd.DataFrame(ltv_display), use_container_width=True, hide_index=True)
st.caption(
    "LTV:CAC (Obs.) = avg observed LTV / CPAO. "
    "Projected LTV:CAC uses constant churn assumption — treat as directional only. "
    "Target: LTV:CAC ≥ 1.0x for SCALE_CANDIDATE. "
    "TikTok is the only channel above threshold on both observed and projected LTV."
)

# ── LTV:CAC Chart ─────────────────────────────────────────────────────────────
ltv_chart = ltv_df[ltv_df["ltv_cac_ratio_observed"].notna()].sort_values("ltv_cac_ratio_observed", ascending=False)
# Highlight exception: TikTok green (only profitable), META red (hold), rest muted
bar_colors = []
for c in ltv_chart["channel"]:
    if c == "TIKTOK":
        bar_colors.append(GREEN)
    elif c == "META":
        bar_colors.append(RED)
    else:
        bar_colors.append(MUTED_BAR)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=ltv_chart["channel"],
    y=ltv_chart["ltv_cac_ratio_observed"],
    marker_color=bar_colors,
    name="LTV:CAC (Observed)",
    text=[fmt_ratio(v) for v in ltv_chart["ltv_cac_ratio_observed"]],
    textposition="outside",
))
fig.add_hline(y=1.0, line_dash="dash", line_color=GREEN,
              annotation_text="SCALE threshold 1.0x", annotation_position="top right")
fig.add_hline(y=0.50, line_dash="dot", line_color=AMBER,
              annotation_text="OBSERVE threshold 0.50x", annotation_position="bottom right")
fig.add_hline(y=0.20, line_dash="dot", line_color=RED,
              annotation_text="PAUSE threshold 0.20x", annotation_position="bottom right")
fig.update_layout(
    height=340,
    margin=dict(l=0, r=10, t=10, b=40),
    yaxis=dict(title="LTV:CAC Ratio"),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Green = profitable (LTV > CPAO). Red = HOLD. Gray = OBSERVE. Dashed = policy thresholds.")

st.markdown("---")

# ── Budget Allocation Simulator ───────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>02 — Budget simulator: 1/CPAO algorithm recommends 56% to TikTok at $150K</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
    padding:12px 14px;margin-bottom:12px;font-size:0.87rem;color:#14532d;'>
    <b>RECOMMEND_ONLY=True.</b> This simulator shows data-informed budget recommendations only.
    No budget changes are executed automatically. All recommendations require human approval.
    <br>Allocation algorithm: 1/CPAO efficiency weighting, min 5% per channel, 10% exploration reserve.
    </div>""",
    unsafe_allow_html=True,
)

col_slider, col_notes = st.columns([2, 1])

with col_slider:
    total_budget = st.slider(
        "Total Monthly Budget (USD)",
        min_value=50_000,
        max_value=300_000,
        value=150_000,
        step=10_000,
        format="$%d",
    )

with col_notes:
    st.markdown("<br>", unsafe_allow_html=True)
    exploration_pct = 0.10
    st.metric("Exploration Reserve", f"${total_budget * exploration_pct:,.0f}", f"{exploration_pct:.0%} of total")
    st.caption("Minimum 5% per channel. Max 60% per channel. Always keeps 10% exploration.")

alloc_df = load_budget_allocation(total_budget)

# Display allocation
alloc_display = []
for _, r in alloc_df.iterrows():
    alloc_display.append({
        "Channel": r["channel"],
        "Type": "Exploration" if r["is_exploration"] else "Efficiency",
        "CPAO": fmt_currency(r["cpao_usd"]) if r["cpao_usd"] else "No data",
        "Recommended Spend": fmt_currency(r["recommended_spend"]),
        "% of Budget": fmt_pct(r["recommended_pct"]),
        "Expected Activations": fmt_number(int(r["recommended_spend"] / r["cpao_usd"])) if r["cpao_usd"] and r["cpao_usd"] > 0 else "—",
    })

st.dataframe(pd.DataFrame(alloc_display), use_container_width=True, hide_index=True)

# Pie chart of allocation
col_pie, col_bar = st.columns(2)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=alloc_df["channel"],
        values=alloc_df["recommended_spend"],
        hole=0.4,
        marker_colors=[channel_color(c) for c in alloc_df["channel"]],
        textinfo="label+percent",
        pull=[0.05 if not r["is_exploration"] else 0 for _, r in alloc_df.iterrows()],
    ))
    fig_pie.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=10),
        title_text=f"Budget Split (${total_budget:,.0f})",
        showlegend=False,
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    st.caption("Efficiency channels allocated by 1/CPAO score.")

with col_bar:
    fig_bar = go.Figure(go.Bar(
        x=alloc_df["channel"],
        y=alloc_df["recommended_spend"],
        marker_color=[channel_color(c) for c in alloc_df["channel"]],
        text=[fmt_currency(v) for v in alloc_df["recommended_spend"]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        height=300,
        margin=dict(l=0, r=10, t=20, b=40),
        yaxis=dict(tickprefix="$", title="Recommended Spend"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_text="Spend by Channel",
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption(f"At ${total_budget:,.0f} total budget.")

st.markdown(
    """<div style='background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;
    padding:12px 14px;margin-top:8px;font-size:0.85rem;color:#475569;'>
    <b>Exploration reserve note:</b> A minimum 10% budget reserve is maintained for
    exploration channels (LinkedIn, UNKNOWN attribution recovery experiments) regardless
    of efficiency score. This ensures continuous test-and-learn across potential new channels.
    Each efficiency channel also receives a minimum 5% floor to prevent complete budget withdrawal
    before incrementality evidence confirms zero value.
    </div>""",
    unsafe_allow_html=True,
)
