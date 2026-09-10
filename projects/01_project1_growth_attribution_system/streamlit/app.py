"""
Growth Attribution System — Streamlit Dashboard
================================================
Home page: frames the business problem before the user dives into the analysis.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    CHANNEL_COLORS,
    get_daily_spend,
    get_overview_metrics,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Growth Attribution System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Multi-Touch Attribution & Geo-Incrementality")
    st.markdown("---")
    st.markdown(
        """
        **Navigate**
        1. 🏠 **Home** — The problem
        2. 📐 **Attribution Models** — Channel credit
        3. 🗺️ **Geo-Holdout** — True incrementality
        4. 💰 **Budget Decision** — Reallocation
        """
    )
    st.markdown("---")
    st.caption("Data: Jan – Jun 2026 | Channels: Meta, Google, TikTok")

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("📊 Growth Attribution System")
st.markdown(
    "#### Ad platforms reported **$1.2M+ in attributed revenue**. "
    "The true incremental number is significantly lower."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────

metrics = get_overview_metrics()

# ─────────────────────────────────────────────────────────────────────────────
# KPI Cards
# ─────────────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        label="Total Ad Spend",
        value=f"${metrics['total_spend']:,.0f}",
        help="Combined spend across Meta, Google, and TikTok (Jan–Jun 2026)",
    )
with c2:
    st.metric(
        label="Actual Conversions",
        value=f"{metrics['total_actual_convs']:,}",
        help="Unique completed orders in the backend database — ground truth",
    )
with c3:
    st.metric(
        label="Platform-Reported ROAS",
        value=f"{metrics['blended_platform_roas']}x",
        help="Blended ROAS as reported by Meta, Google, and TikTok dashboards",
    )
with c4:
    st.metric(
        label="Actual Revenue / Spend",
        value=f"{metrics['blended_actual_roas']}x",
        delta=f"-{metrics['overstatement_pct']}% vs platform",
        delta_color="inverse",
        help="Revenue from backend orders divided by actual ad spend",
    )

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
# Problem statement
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### The Self-Attribution Problem")

col_text, col_chart = st.columns([1, 1.6], gap="large")

with col_text:
    st.markdown(
        """
        Each ad platform measures conversions **independently** using its own
        attribution window. When a user converts after touching multiple channels,
        **every platform claims 100% of the credit**.

        The result: combined platform-reported conversions can exceed actual
        conversions by **30–50%**, leading to inflated ROAS figures and
        misallocated budget.

        > **Meta** reported 3.25x ROAS
        > **Google** reported 2.80x ROAS
        > **TikTok** reported 1.60x ROAS

        A geo-holdout experiment later revealed Meta's **true incremental ROAS
        was 1.26x** — the platform was claiming credit for conversions that
        would have happened organically.
        """
    )

with col_chart:
    by_ch = metrics["by_channel"].copy()
    by_ch = by_ch[by_ch["channel"].isin(["Meta Paid Social", "Google Paid Search", "TikTok Ads"])]

    # Actual revenue proxy: use time-decay attribution from loader
    from utils.data_loader import compute_attribution
    attr = compute_attribution()
    paid_attr = attr[attr["channel"].isin(["Meta Paid Social", "Google Paid Search", "TikTok Ads"])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Platform-Reported Revenue",
        x=by_ch["channel"],
        y=by_ch["platform_revenue"],
        marker_color=["#1877F2", "#34A853", "#EE1D52"],
        opacity=0.5,
    ))
    fig.add_trace(go.Bar(
        name="SQL-Attributed Revenue (Time-Decay)",
        x=paid_attr["channel"],
        y=paid_attr["time_decay_revenue"],
        marker_color=["#1877F2", "#34A853", "#EE1D52"],
    ))
    fig.update_layout(
        barmode="group",
        title="Platform-Reported vs SQL-Attributed Revenue",
        yaxis_title="Revenue (USD)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=340,
        margin=dict(t=60, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Daily spend trend
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Ad Spend by Channel — Jan to Jun 2026")
st.caption(
    "Meta ads were paused in 10 control DMAs during June (geo-holdout experiment). "
    "Total Meta spend drops slightly in June as a result."
)

daily = get_daily_spend()
daily_agg = daily.groupby(["date", "channel"])["daily_spend_usd"].sum().reset_index()

fig2 = px.line(
    daily_agg,
    x="date",
    y="daily_spend_usd",
    color="channel",
    color_discrete_map=CHANNEL_COLORS,
    labels={"daily_spend_usd": "Daily Spend (USD)", "date": "", "channel": "Channel"},
    height=320,
)
fig2.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(t=40, b=20),
)
fig2.update_traces(line_width=1.5)
st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Navigation prompt
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Explore the Analysis")
n1, n2, n3 = st.columns(3)
with n1:
    st.info("**📐 Attribution Models**\nHow much credit does each channel deserve? Compare 4 models.", icon="📐")
with n2:
    st.info("**🗺️ Geo-Holdout Experiment**\nWe paused Meta ads in 10 DMAs to measure true incrementality.", icon="🗺️")
with n3:
    st.info("**💰 Budget Decision**\nThe reallocation that reduced blended CAC by 14.2%.", icon="💰")
