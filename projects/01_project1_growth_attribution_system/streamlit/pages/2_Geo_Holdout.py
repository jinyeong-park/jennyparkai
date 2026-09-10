"""
Geo-Holdout Experiment page.

Key insight: When Meta ads were paused in 10 DMAs, conversion rates barely moved.
94%+ of Meta-attributed conversions were happening organically.
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import get_geo_holdout_results

st.set_page_config(page_title="Geo-Holdout Experiment", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("🗺️ Geo-Holdout Incrementality Experiment")
st.markdown(
    "#### Attribution models tell you how to split credit. "
    "This experiment tells you whether the credit was **real**."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────────

r = get_geo_holdout_results()

# ─────────────────────────────────────────────────────────────────────────────
# Experiment design cards
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Experiment Design")
e1, e2, e3, e4, e5 = st.columns(5)

design = [
    (e1, "📅 Period",        "June 2026",              "30-day holdout"),
    (e2, "📡 Channel Tested", "Meta Paid Social",       "Retargeting campaigns"),
    (e3, "🔴 Control DMAs",  f"{r['control_dmas']} markets", "Meta ads paused"),
    (e4, "🟢 Treatment DMAs", f"{r['treatment_dmas']} markets", "Meta ads running"),
    (e5, "📊 Test Type",     "Geo-Holdout",            "Matched-market"),
]

for col, label, value, sub in design:
    with col:
        st.markdown(
            f"""
            <div style="background:#f8f9fa; border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:13px; color:#6c757d; margin-bottom:4px;">{label}</div>
                <div style="font-size:18px; font-weight:700;">{value}</div>
                <div style="font-size:12px; color:#adb5bd; margin-top:4px;">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Key findings — KPI row
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Experiment Results")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Control Conversion Rate",
        f"{r['control_rate_pct']}%",
        help="Conversion rate in DMAs where Meta ads were paused",
    )
with k2:
    st.metric(
        "Treatment Conversion Rate",
        f"{r['treatment_rate_pct']}%",
        delta=f"{round(r['treatment_rate_pct'] - r['control_rate_pct'], 3)}%",
        help="Conversion rate in DMAs where Meta ads ran normally",
    )
with k3:
    st.metric(
        "Incremental Lift",
        f"{r['incremental_lift_pct']}%",
        help="How much Meta ads actually moved the needle",
    )
with k4:
    sig_label = "✅ Significant" if r["significant"] else "❌ Not significant"
    st.metric(
        "Statistical Significance",
        sig_label,
        delta=f"p = {r['p_value']}",
        delta_color="off",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Charts row
# ─────────────────────────────────────────────────────────────────────────────

left, right = st.columns(2, gap="large")

with left:
    st.markdown("**Conversion Rate: Control vs. Treatment**")
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=["Control DMAs\n(Meta ads OFF)", "Treatment DMAs\n(Meta ads ON)"],
        y=[r["control_rate_pct"], r["treatment_rate_pct"]],
        marker_color=["#E74C3C", "#2ECC71"],
        text=[f"{r['control_rate_pct']}%", f"{r['treatment_rate_pct']}%"],
        textposition="outside",
        width=0.5,
    ))
    fig1.update_layout(
        height=320,
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis_title="Conversion Rate (%)",
        yaxis_range=[0, max(r["control_rate_pct"], r["treatment_rate_pct"]) * 1.3],
        margin=dict(t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.markdown("**Where Did Treatment Conversions Come From?**")
    organic     = max(r["expected_baseline"], 0)
    incremental = max(r["incremental_conversions"], 0)

    fig2 = go.Figure(go.Pie(
        labels=["Organic\n(would have happened anyway)", "Incremental\n(caused by Meta ads)"],
        values=[organic, incremental],
        hole=0.55,
        marker_colors=["#95A5A6", "#3498DB"],
        textinfo="label+percent",
        textposition="outside",
    ))
    fig2.update_layout(
        height=320,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{r['actual_conversions']}</b><br>total",
            x=0.5, y=0.5, font_size=16, showarrow=False,
        )],
    )
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# DMA-level distribution
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### DMA-Level Conversion Rate Distribution")
st.caption("Each dot is one DMA. The two groups overlap heavily — Meta ads moved the needle very little.")

ctrl_df = r["ctrl_df"].copy()
trt_df  = r["trt_df"].copy()
ctrl_df["group"] = "Control (Meta OFF)"
trt_df["group"]  = "Treatment (Meta ON)"
combined = pd.concat([ctrl_df, trt_df])

fig3 = px.box(
    combined,
    x="group",
    y="conversion_rate",
    color="group",
    color_discrete_map={
        "Control (Meta OFF)": "#E74C3C",
        "Treatment (Meta ON)": "#2ECC71",
    },
    points="all",
    labels={"conversion_rate": "Conversion Rate", "group": ""},
    height=340,
)
fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    yaxis_tickformat=".3%",
    margin=dict(t=20, b=20),
)
st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROAS comparison
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### True Incremental ROAS vs. Platform-Reported ROAS")

r1, r2, r3 = st.columns([1, 2, 1])
with r2:
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=["Platform-Reported ROAS", "True Incremental ROAS"],
        y=[r["platform_roas"], r["incremental_roas"]],
        marker_color=["#E67E22", "#8E44AD"],
        text=[f"{r['platform_roas']}x", f"{r['incremental_roas']}x"],
        textposition="outside",
        textfont_size=16,
        width=0.45,
    ))
    fig4.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Break-even")
    fig4.update_layout(
        height=340,
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis_title="ROAS",
        yaxis_range=[0, r["platform_roas"] * 1.35],
        margin=dict(t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig4, use_container_width=True)

overstatement = round((r["platform_roas"] - r["incremental_roas"]) / r["incremental_roas"] * 100, 0)

st.error(
    f"**Meta's self-reported ROAS ({r['platform_roas']}x) overstates true incremental ROAS "
    f"({r['incremental_roas']}x) by ~{overstatement:.0f}%.** "
    f"The {r['organic_share_pct']}% organic share means the vast majority of "
    f"Meta-attributed conversions would have happened without any Meta advertising. "
    f"iCAC: ${r['icac']:,.0f} per truly incremental customer. "
    f"→ See **Budget Decision** for the reallocation."
)
