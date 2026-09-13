"""Retention Analysis — M1/M3/M6 by channel, cohort trends, subscription tiers.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from utils.data_loader import load_retention, load_cohort_by_week, load_subscription_tiers
from utils.metrics import fmt_pct, fmt_number
from utils.theme import inject_theme, render_navigation, GREEN, TEAL, BLUE, AMBER, RED, PRIMARY, MUTED, MUTED_BAR

st.set_page_config(
    page_title="Retention — Tablr Growth",
    page_icon=":material/trending_up:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Retention Analysis</h1>",
    unsafe_allow_html=True,
)
st.caption("M1/M3/M6 cohort retention · Cohort activation trends · Subscription tier breakdown")

st.markdown("---")

# ── Maturity warning ──────────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#fef3c7;border:1px solid #fde68a;border-radius:8px;
    padding:12px 16px;margin-bottom:16px;font-size:0.87rem;color:#92400e;'>
    <b>&#9888; Maturity Warning:</b> March 2026 cohorts are not yet 180 days old as of
    2026-09-13 (only ~170 days). M6 retention is shown only for cohorts where
    conversion_date + 180 days &le; 2026-09-13. Immature cohorts are excluded from M6 averages.
    </div>""",
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading retention data..."):
    retention = load_retention()
    cohorts = load_cohort_by_week()
    tiers = load_subscription_tiers()

# ── M1/M3/M6 by Channel ──────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>01 — TikTok retains subscribers best at every cohort milestone</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """<div style='background:#eff6ff;border-left:4px solid #1a6fbe;padding:10px 14px;
    border-radius:0 6px 6px 0;font-size:0.88rem;color:#1e3a5f;margin-bottom:12px;'>
    <b>Key finding:</b> TikTok M6 retention is 47.4% — corroborating the SCALE_CANDIDATE decision.
    High M6 retention means the LTV projection is not an outlier: TikTok customers actually stay.
    META M6 retention is the lowest of all measured channels, reinforcing the HOLD recommendation.
    </div>""",
    unsafe_allow_html=True,
)

channels = retention["channel"].tolist()

fig = go.Figure()
fig.add_trace(go.Bar(
    name="M1 (30d)", x=channels, y=retention["m1_rate"],
    marker_color=GREEN,
    text=[fmt_pct(v) for v in retention["m1_rate"]],
    textposition="outside",
))
fig.add_trace(go.Bar(
    name="M3 (90d)", x=channels, y=retention["m3_rate"],
    marker_color=TEAL,
    text=[fmt_pct(v) for v in retention["m3_rate"]],
    textposition="outside",
))
fig.add_trace(go.Bar(
    name="M6 (180d, mature only)", x=channels, y=retention["m6_rate"],
    marker_color=BLUE,
    text=[fmt_pct(v) if v and v == v else "N/A" for v in retention["m6_rate"]],
    textposition="outside",
))
fig.update_layout(
    barmode="group",
    height=360,
    margin=dict(l=0, r=10, t=10, b=40),
    yaxis=dict(tickformat=".0%", range=[0, 1.15], title="Retention Rate"),
    legend=dict(orientation="h", y=-0.2),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "M6 retention shown only for mature cohorts. "
    "TikTok leads at M6 47.4% — corroborating the SCALE_CANDIDATE policy decision."
)

# Retention table
st.markdown("<br>", unsafe_allow_html=True)
ret_display = []
for _, r in retention.iterrows():
    ret_display.append({
        "Channel": r["channel"],
        "Subscribers": fmt_number(int(r["subscribers"])),
        "M1 Retention": fmt_pct(r["m1_rate"]),
        "M3 Retention": fmt_pct(r["m3_rate"]),
        "M6 Retention": fmt_pct(r["m6_rate"]) if r["m6_eligible"] > 0 else "Immature",
        "M6 Eligible": fmt_number(int(r["m6_eligible"])),
        "M6 Immature": fmt_number(int(r["m6_immature"])),
    })
st.dataframe(pd.DataFrame(ret_display), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Cohort Activation by Week ─────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>02 — Cohort volume is stable week-over-week — no ramp-up or decay signal</div>",
    unsafe_allow_html=True,
)

if not cohorts.empty:
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=cohorts["cohort_week"], y=cohorts["trials"],
        mode="lines+markers", name="Trials",
        line=dict(color=PRIMARY, width=2),
        marker=dict(size=5),
    ))
    fig2.add_trace(go.Scatter(
        x=cohorts["cohort_week"], y=cohorts["onboarding_completed"],
        mode="lines+markers", name="Onboarding",
        line=dict(color=BLUE, width=2, dash="dot"),
        marker=dict(size=5),
    ))
    fig2.add_trace(go.Scatter(
        x=cohorts["cohort_week"], y=cohorts["activated_owners"],
        mode="lines+markers", name="Activated Owners",
        line=dict(color=TEAL, width=2),
        marker=dict(size=5),
    ))
    fig2.add_trace(go.Scatter(
        x=cohorts["cohort_week"], y=cohorts["subscriptions"],
        mode="lines+markers", name="Subscriptions",
        line=dict(color=GREEN, width=2),
        marker=dict(size=5),
    ))
    fig2.update_layout(
        height=320,
        margin=dict(l=0, r=10, t=10, b=40),
        xaxis=dict(title="Cohort Week", tickangle=-45),
        yaxis=dict(title="Count"),
        legend=dict(orientation="h", y=-0.3),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Weekly cohorts from Jan 5 – Mar 29, 2026. Each line = funnel stage.")
else:
    st.info("No cohort data available.")

# Activation rate by week
if not cohorts.empty:
    cohorts["activation_rate"] = cohorts["activated_owners"] / cohorts["trials"].replace(0, None)
    cohorts["conversion_rate"] = cohorts["subscriptions"] / cohorts["trials"].replace(0, None)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=cohorts["cohort_week"], y=cohorts["activation_rate"],
        name="Activation Rate",
        marker_color=TEAL,
        text=[fmt_pct(v) for v in cohorts["activation_rate"]],
        textposition="outside",
    ))
    fig3.add_trace(go.Bar(
        x=cohorts["cohort_week"], y=cohorts["conversion_rate"],
        name="Trial→Sub Rate",
        marker_color=GREEN,
        text=[fmt_pct(v) for v in cohorts["conversion_rate"]],
        textposition="outside",
    ))
    fig3.update_layout(
        barmode="group",
        height=260,
        margin=dict(l=0, r=10, t=10, b=60),
        xaxis=dict(tickangle=-45),
        yaxis=dict(tickformat=".0%", title="Rate"),
        legend=dict(orientation="h", y=-0.4),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Activation rate = campaign_launched within 14 days / trials.")

st.markdown("---")

# ── Subscription Tier Breakdown ───────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>03 — Subscription tier mix and churn rate by plan</div>",
    unsafe_allow_html=True,
)

col_tier, col_status = st.columns(2)

with col_tier:
    tier_totals = tiers.groupby("subscription_tier")["count"].sum().reset_index()

    TIER_COLORS = {
        "STARTER": TEAL,
        "GROWTH": BLUE,
        "PRO": PRIMARY,
    }

    fig_tier = go.Figure(go.Pie(
        labels=tier_totals["subscription_tier"],
        values=tier_totals["count"],
        hole=0.45,
        marker_colors=[TIER_COLORS.get(t, MUTED) for t in tier_totals["subscription_tier"]],
        textinfo="label+percent",
    ))
    fig_tier.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=20, b=10),
        title_text="By Tier (all)",
        showlegend=False,
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_tier, use_container_width=True)

with col_status:
    status_pivot = tiers.pivot_table(
        index="subscription_tier", columns="status", values="count", aggfunc="sum", fill_value=0
    ).reset_index()

    status_display = []
    for _, r in status_pivot.iterrows():
        active = int(r.get("active", 0))
        churned = int(r.get("churned", 0))
        total = active + churned
        churn_rate = churned / total if total else 0
        status_display.append({
            "Tier": r["subscription_tier"],
            "Active": fmt_number(active),
            "Churned": fmt_number(churned),
            "Total": fmt_number(total),
            "Churn Rate": fmt_pct(churn_rate),
        })

    st.dataframe(pd.DataFrame(status_display), use_container_width=True, hide_index=True)
    st.caption("Active = still subscribed as of simulation end.")

    avg_price_by_tier = tiers.groupby("subscription_tier")["avg_price"].mean().reset_index()
    st.markdown("<br>", unsafe_allow_html=True)
    for _, r in avg_price_by_tier.iterrows():
        st.metric(f"{r['subscription_tier']} avg price", f"${r['avg_price']:.0f}/mo")
