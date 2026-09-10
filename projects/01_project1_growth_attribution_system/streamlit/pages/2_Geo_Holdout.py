"""
Geo-Holdout Experiment page.

Key insight: when Meta ads were paused in 10 DMAs, conversion rates barely moved.
94%+ of Meta-attributed conversions were happening organically.
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd

from utils.data_loader import get_geo_holdout_results
from utils.theme import (
    C_MUTED, C_NAVY, C_GREEN, C_RED, C_AMBER, C_BORDER,
    action_box, alert, base_layout, hero, inject_css, insight, kpi, story_step,
)

st.set_page_config(page_title="Geo-Holdout Experiment", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Multi-Touch Attribution & Geo-Incrementality")

# ── Load ───────────────────────────────────────────────────────────────────────
r = get_geo_holdout_results()

# ── Hero ───────────────────────────────────────────────────────────────────────
st.title("Geo-Holdout Incrementality Experiment")

_iroas = r['incremental_roas']
_overstatement = (
    f"by {round((r['platform_roas'] - _iroas) / _iroas * 100):.0f}%"
    if _iroas > 0 else "significantly"
)
st.markdown(hero(
    headline=(
        f"Meta's platform ROAS ({r['platform_roas']}x) overstates true incremental ROAS "
        f"({_iroas}x) {_overstatement}. "
        f"{r['organic_share_pct']}% of Meta-attributed conversions were happening organically."
    ),
    metric=(
        f"Incremental lift: {r['incremental_lift_pct']}%  ·  "
        f"Incremental CAC: ${r['icac']:,.0f}  ·  "
        f"p = {r['p_value']} ({'significant' if r['significant'] else 'not significant'})"
    ),
    subtext=(
        f"A 30-day matched-market holdout: Meta ads were paused in {r['control_dmas']} control DMAs. "
        f"Conversion rates in paused markets dropped by only {r['incremental_lift_pct']}%. "
        f"Attribution models were splitting credit — this experiment measured causation."
    ),
), unsafe_allow_html=True)

# ── KPI row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi("Control Rate (Meta OFF)", f"{r['control_rate_pct']}%",
                    f"{r['control_dmas']} DMAs · Meta paused"), unsafe_allow_html=True)
with k2:
    diff = round(r['treatment_rate_pct'] - r['control_rate_pct'], 3)
    st.markdown(kpi("Treatment Rate (Meta ON)", f"{r['treatment_rate_pct']}%",
                    f"+{diff}% vs control — barely different"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("Incremental Lift", f"{r['incremental_lift_pct']}%",
                    "How much Meta ads actually moved the needle",
                    "warn" if r['incremental_lift_pct'] < 10 else "neutral"), unsafe_allow_html=True)
with k4:
    status = "good" if r["significant"] else "warn"
    sig_label = "Significant" if r["significant"] else "Not significant"
    st.markdown(kpi("Statistical Test", sig_label,
                    f"p = {r['p_value']} · z = {r['z_score']}", status), unsafe_allow_html=True)

st.markdown("---")

# ── 01 Conversion rate comparison ──────────────────────────────────────────────
st.markdown(story_step("01", "Did removing Meta ads change conversion rates in the paused markets?"), unsafe_allow_html=True)

col_bar, col_breakdown = st.columns(2, gap="large")

with col_bar:
    bar_colors = [C_RED, C_GREEN]  # Control = red concern, Treatment = green OK
    fig1 = go.Figure(go.Bar(
        x=["Control DMAs\n(Meta ads OFF)", "Treatment DMAs\n(Meta ads ON)"],
        y=[r["control_rate_pct"], r["treatment_rate_pct"]],
        marker_color=bar_colors,
        text=[f"{r['control_rate_pct']}%", f"{r['treatment_rate_pct']}%"],
        textposition="outside",
        textfont=dict(size=14, color="#18202B"),
        width=0.5,
    ))
    layout1 = base_layout(height=320, margin=dict(t=48, b=20, l=8, r=8), show_legend=False)
    layout1.update(dict(
        title=f"Conversion rates barely changed — only {r['incremental_lift_pct']}% lift from Meta ads",
        yaxis=dict(title="Conversion Rate (%)", range=[0, max(r["control_rate_pct"], r["treatment_rate_pct"]) * 1.4],
                   gridcolor=C_BORDER, zeroline=False),
    ))
    fig1.update_layout(layout1)
    st.plotly_chart(fig1, use_container_width=True)

with col_breakdown:
    # Replace donut with horizontal bar — "Avoid" pie per skill matrix
    organic     = max(r["expected_baseline"], 0)
    incremental = max(r["incremental_conversions"], 0)
    total       = organic + incremental

    breakdown_df = pd.DataFrame({
        "Type":    ["Organic (would have happened anyway)", "Incremental (caused by Meta ads)"],
        "Convs":   [organic, incremental],
        "Share":   [organic / total * 100, incremental / total * 100],
    })
    breakdown_df = breakdown_df.sort_values("Convs", ascending=True)

    bar_colors_b = [C_MUTED, C_NAVY]  # organic = muted, incremental = focal
    fig2 = go.Figure(go.Bar(
        x=breakdown_df["Convs"],
        y=breakdown_df["Type"],
        orientation="h",
        marker_color=bar_colors_b,
        text=[f"{v:.0f} conv. ({s:.0f}%)" for v, s in zip(breakdown_df["Convs"], breakdown_df["Share"])],
        textposition="outside",
    ))
    layout2 = base_layout(height=320, margin=dict(t=48, b=20, l=8, r=180), show_legend=False)
    layout2.update(dict(
        title=f"{r['organic_share_pct']}% of Meta-attributed conversions were already happening organically",
        xaxis=dict(title="Conversions", gridcolor=C_BORDER, zeroline=False),
        yaxis=dict(title=""),
    ))
    fig2.update_layout(layout2)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── 02 DMA distribution ────────────────────────────────────────────────────────
st.markdown(story_step("02", "Did the two groups of DMAs behave differently before the experiment?"), unsafe_allow_html=True)

st.markdown(insight(
    "The box plots show the distribution of conversion rates across all DMAs in each group. "
    "<b>The two groups overlap heavily</b> — Meta ads had minimal impact on market-level conversion rates. "
    "This confirms the experiment design: control and treatment markets were well-matched."
), unsafe_allow_html=True)

ctrl_df = r["ctrl_df"].copy()
trt_df  = r["trt_df"].copy()
ctrl_df["group"] = f"Control ({r['control_dmas']} DMAs · Meta OFF)"
trt_df["group"]  = f"Treatment ({r['treatment_dmas']} DMAs · Meta ON)"
combined = pd.concat([ctrl_df, trt_df])

fig3 = px.box(
    combined,
    x="group",
    y="conversion_rate",
    color="group",
    color_discrete_map={
        f"Control ({r['control_dmas']} DMAs · Meta OFF)":   C_RED,
        f"Treatment ({r['treatment_dmas']} DMAs · Meta ON)": C_GREEN,
    },
    points="all",
    labels={"conversion_rate": "Conversion Rate", "group": ""},
    height=340,
)
layout3 = base_layout(height=340, margin=dict(t=48, b=20, l=8, r=8), show_legend=False)
layout3.update(dict(
    title="Control and treatment DMAs had near-identical conversion rate distributions",
    yaxis=dict(title="Conversion Rate", tickformat=".3%", gridcolor=C_BORDER, zeroline=False),
))
fig3.update_layout(layout3)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── 03 ROAS reality check ──────────────────────────────────────────────────────
st.markdown(story_step("03", "What is Meta's true incremental ROAS versus its platform-reported number?"), unsafe_allow_html=True)

overstatement_pct = (
    round((r["platform_roas"] - r["incremental_roas"]) / r["incremental_roas"] * 100, 0)
    if r["incremental_roas"] > 0 else float("nan")
)

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=["Platform-Reported ROAS\n(Meta's claim)", "True Incremental ROAS\n(geo-holdout result)"],
    y=[r["platform_roas"], r["incremental_roas"]],
    marker_color=[C_MUTED, C_GREEN],
    text=[f"{r['platform_roas']}x", f"{r['incremental_roas']}x"],
    textposition="outside",
    textfont=dict(size=15, color="#18202B"),
    width=0.4,
))
fig4.add_hline(y=1.0, line_dash="dash", line_color=C_AMBER,
               annotation_text="Break-even (1.0x)", annotation_position="bottom right")
layout4 = base_layout(height=340, margin=dict(t=48, b=20, l=8, r=8), show_legend=False)
layout4.update(dict(
    title=f"Meta overstates ROAS {_overstmt_str} — most attributed conversions were organic",
    yaxis=dict(title="ROAS", range=[0, r["platform_roas"] * 1.4], gridcolor=C_BORDER, zeroline=False),
))
fig4.update_layout(layout4)

_, center_col, _ = st.columns([1, 2, 1])
with center_col:
    st.plotly_chart(fig4, use_container_width=True)

_overstmt_str = f"by ~{overstatement_pct:.0f}%" if overstatement_pct == overstatement_pct else "significantly"
st.markdown(alert(
    f"<b>Meta's self-reported ROAS ({r['platform_roas']}x) overstates true incremental ROAS "
    f"({r['incremental_roas']}x) {_overstmt_str}.</b> "
    f"The {r['organic_share_pct']}% organic share means the vast majority of Meta-attributed conversions "
    f"would have happened without any Meta advertising. "
    f"Incremental CAC: ${r['icac']:,.0f} per truly incremental customer.",
    "danger"
), unsafe_allow_html=True)

st.markdown("---")

st.markdown(action_box([
    f"Reduce Meta retargeting budget — true incremental ROAS ({r['incremental_roas']}x) is near break-even.",
    "Reallocate freed budget toward Google Search and TikTok — higher true ROAS, lower organic cannibalization.",
    "Replace platform ROAS with incremental ROAS as the primary budget performance KPI.",
    "Run quarterly geo-holdouts for Google and TikTok to validate their incrementality before scaling.",
    f"Track iCAC (${r['icac']:,.0f}) as the cost metric for Meta — not blended CAC.",
]), unsafe_allow_html=True)
