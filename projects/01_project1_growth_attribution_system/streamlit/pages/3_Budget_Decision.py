"""
Budget Decision page.

Key insight: reallocating $100K from low-incrementality Meta retargeting
toward Google Search and TikTok prospecting increases true incremental revenue.
This page includes an interactive simulator.
"""

import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from utils.data_loader import (
    PAID_CHANNELS,
    get_geo_holdout_results,
    get_roas_table,
)
from utils.theme import (
    C_MUTED, C_NAVY, C_GREEN, C_RED, C_AMBER, C_BORDER,
    action_box, alert, base_layout, hero, inject_css, insight, kpi, story_step,
)

st.set_page_config(page_title="Budget Decision", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Multi-Touch Attribution & Geo-Incrementality")

# ── Load ───────────────────────────────────────────────────────────────────────
geo  = get_geo_holdout_results()
roas = get_roas_table()
paid = roas[roas["channel"].isin(PAID_CHANNELS)].copy()

TRUE_ROAS = {
    "Meta Paid Social":   geo["incremental_roas"],
    "Google Paid Search": 2.65,
    "TikTok Ads":         2.10,
}

paid["true_roas"]     = paid["channel"].map(TRUE_ROAS)
total_budget          = paid["total_spend"].sum()

current = {
    ch: paid.loc[paid["channel"] == ch, "total_spend"].values[0]
    for ch in PAID_CHANNELS
}

SHIFT = 100_000
recommended = {
    "Meta Paid Social":   current["Meta Paid Social"]   - SHIFT,
    "Google Paid Search": current["Google Paid Search"] + SHIFT * 0.5,
    "TikTok Ads":         current["TikTok Ads"]         + SHIFT * 0.5,
}

def projected_revenue(allocation, roas_map):
    return {ch: allocation[ch] * roas for ch, roas in roas_map.items()}

curr_rev  = projected_revenue(current, TRUE_ROAS)
rec_rev   = projected_revenue(recommended, TRUE_ROAS)
curr_total = sum(curr_rev.values())
rec_total  = sum(rec_rev.values())
rec_delta  = (rec_total - curr_total) / curr_total * 100

# ── Hero ───────────────────────────────────────────────────────────────────────
st.title("Budget Decision & Reallocation")

st.markdown(hero(
    headline=(
        f"Shifting $100K from Meta retargeting (true ROAS: {geo['incremental_roas']}x) "
        f"to Google Search (2.65x) and TikTok prospecting (2.10x) "
        f"increases projected incremental revenue by {rec_delta:.1f}%."
    ),
    metric=(
        f"Current projected revenue: ${curr_total:,.0f}  →  "
        f"After reallocation: ${rec_total:,.0f}  "
        f"(+${rec_total - curr_total:,.0f})"
    ),
    subtext=(
        "True ROAS for Meta comes from the geo-holdout experiment. "
        "Google and TikTok figures are from SQL time-decay attribution. "
        "All projections assume stable conversion rates — validate with a post-move holdout."
    ),
), unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
d1, d2, d3, d4 = st.columns(4)
with d1:
    st.markdown(kpi("Budget Shifted", f"${SHIFT:,.0f}",
                    "Out of Meta, into Google + TikTok"), unsafe_allow_html=True)
with d2:
    st.markdown(kpi("Meta Spend After", f"${recommended['Meta Paid Social']:,.0f}",
                    f"−${SHIFT:,.0f} from ${current['Meta Paid Social']:,.0f}",
                    "warn"), unsafe_allow_html=True)
with d3:
    g_t = recommended["Google Paid Search"] + recommended["TikTok Ads"]
    st.markdown(kpi("Google + TikTok After", f"${g_t:,.0f}",
                    f"+${SHIFT:,.0f} combined",
                    "good"), unsafe_allow_html=True)
with d4:
    st.markdown(kpi("Revenue Lift", f"+{rec_delta:.1f}%",
                    f"+${rec_total - curr_total:,.0f} projected incremental",
                    "good"), unsafe_allow_html=True)

st.markdown("---")

# ── 01 Platform vs True ROAS ───────────────────────────────────────────────────
st.markdown(story_step("01", "How does platform-reported ROAS compare to true incremental ROAS per channel?"), unsafe_allow_html=True)

# "Highlight the exception": Meta is the gap story (focal = C_RED for its high platform claim vs low truth)
platform_roas_vals = paid.set_index("channel")["Platform ROAS"].to_dict()

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    name="Platform-Reported ROAS",
    x=PAID_CHANNELS,
    y=[platform_roas_vals[c] for c in PAID_CHANNELS],
    marker_color=[C_MUTED, C_MUTED, C_MUTED],
    opacity=0.6,
    text=[f"{platform_roas_vals[c]:.2f}x" for c in PAID_CHANNELS],
    textposition="outside",
))
fig1.add_trace(go.Bar(
    name="True Incremental ROAS",
    x=PAID_CHANNELS,
    y=[TRUE_ROAS[c] for c in PAID_CHANNELS],
    marker_color=[C_RED, C_GREEN, C_GREEN],  # Meta red (problem), others green (opportunity)
    text=[f"{TRUE_ROAS[c]:.2f}x" for c in PAID_CHANNELS],
    textposition="outside",
))
fig1.add_hline(y=1.0, line_dash="dash", line_color=C_AMBER,
               annotation_text="Break-even", annotation_position="bottom right")
layout1 = base_layout(height=360, margin=dict(t=48, b=20, l=8, r=8))
layout1.update(dict(
    title="Meta has the biggest ROAS gap — platform overstates, Google and TikTok understate",
    barmode="group",
    yaxis=dict(title="ROAS", range=[0, max(platform_roas_vals.values()) * 1.4],
               gridcolor=C_BORDER, zeroline=False),
))
fig1.update_layout(layout1)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ── 02 Budget reallocation — horizontal bars ───────────────────────────────────
st.markdown(story_step("02", "What does the recommended budget look like before and after the shift?"), unsafe_allow_html=True)

st.markdown(insight(
    "The bars show absolute spend per channel — before (muted) and after (accent). "
    "<b>Meta shrinks. Google and TikTok grow.</b> "
    "Total budget stays constant at ${:,.0f}.".format(total_budget)
), unsafe_allow_html=True)

channels_sorted = sorted(PAID_CHANNELS, key=lambda c: current[c], reverse=True)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="Current Spend",
    y=channels_sorted,
    x=[current[c] for c in channels_sorted],
    orientation="h",
    marker_color=C_MUTED,
    opacity=0.65,
    text=[f"${current[c]:,.0f}" for c in channels_sorted],
    textposition="outside",
))
fig2.add_trace(go.Bar(
    name="Recommended Spend",
    y=channels_sorted,
    x=[recommended[c] for c in channels_sorted],
    orientation="h",
    marker_color=[C_RED, C_GREEN, C_GREEN],  # Meta down, others up
    text=[f"${recommended[c]:,.0f}" for c in channels_sorted],
    textposition="outside",
))
layout2 = base_layout(height=280, margin=dict(t=48, b=20, l=8, r=160))
layout2.update(dict(
    title="$100K shifts from Meta (low incrementality) to Google + TikTok (high incrementality)",
    barmode="group",
    xaxis=dict(title="Spend (USD)", tickprefix="$", tickformat=",", gridcolor=C_BORDER, zeroline=False),
    yaxis=dict(title=""),
))
fig2.update_layout(layout2)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── 03 Budget simulator ────────────────────────────────────────────────────────
st.markdown(story_step("03", "What happens to projected revenue at different reallocation amounts?"), unsafe_allow_html=True)

st.markdown(insight(
    "Drag the slider to model different shift amounts. "
    "Projected revenue uses true incremental ROAS from the geo-holdout (Meta) and SQL time-decay (Google, TikTok). "
    "<b>The $100K shift is the recommended starting point</b> — validate results with a post-move holdout."
), unsafe_allow_html=True)

shift_amount = st.slider(
    "Amount to shift away from Meta (USD)",
    min_value=0,
    max_value=int(current["Meta Paid Social"] * 0.6),
    value=100_000,
    step=10_000,
    format="$%d",
)

split = st.radio(
    "Redistribute to:",
    ["50% Google / 50% TikTok", "100% Google Search", "100% TikTok Ads"],
    horizontal=True,
)

g_share = {"50% Google / 50% TikTok": 0.5, "100% Google Search": 1.0, "100% TikTok Ads": 0.0}[split]
t_share = 1.0 - g_share

sim_alloc = {
    "Meta Paid Social":   current["Meta Paid Social"]   - shift_amount,
    "Google Paid Search": current["Google Paid Search"] + shift_amount * g_share,
    "TikTok Ads":         current["TikTok Ads"]         + shift_amount * t_share,
}
sim_rev   = projected_revenue(sim_alloc, TRUE_ROAS)
sim_total = sum(sim_rev.values())
sim_delta = (sim_total - curr_total) / curr_total * 100

# Results
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(kpi("Current Revenue", f"${curr_total:,.0f}", "Baseline (true ROAS)"), unsafe_allow_html=True)
with s2:
    st.markdown(kpi("Simulated Revenue", f"${sim_total:,.0f}",
                    f"{sim_delta:+.1f}% vs current",
                    "good" if sim_delta > 0 else "bad"), unsafe_allow_html=True)
with s3:
    st.markdown(kpi("Budget Shifted", f"${shift_amount:,.0f}",
                    f"${current['Meta Paid Social'] - sim_alloc['Meta Paid Social']:,.0f} out of Meta"),
                unsafe_allow_html=True)

st.markdown("")

sim_rows = [{
    "Channel":      ch,
    "Current Spend":  f"${current[ch]:,.0f}",
    "Sim Spend":      f"${sim_alloc[ch]:,.0f}",
    "True ROAS":      f"{TRUE_ROAS[ch]:.2f}x",
    "Current Rev":    f"${curr_rev[ch]:,.0f}",
    "Sim Rev":        f"${sim_rev[ch]:,.0f}",
    "Rev Δ":          f"${sim_rev[ch] - curr_rev[ch]:+,.0f}",
} for ch in PAID_CHANNELS]

st.dataframe(pd.DataFrame(sim_rows), use_container_width=True, hide_index=True)

st.markdown("---")

st.markdown(action_box([
    "Reduce Meta retargeting by $100K immediately — incremental ROAS of 1.26x barely clears break-even.",
    "Increase Google Paid Search — highest true ROAS (2.65x), minimal organic cannibalization.",
    "Increase TikTok Ads prospecting — true ROAS (2.10x) exceeds platform-reported (1.60x); undervalued channel.",
    "After the shift, run a 60-day measurement period and compare blended CAC before and after.",
    "Establish quarterly geo-holdouts for Google and TikTok to validate their true incrementality at scale.",
]), unsafe_allow_html=True)
