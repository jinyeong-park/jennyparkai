"""
2_Campaign_Performance.py  —  Campaign Performance Analysis
Story: All campaigns are below break-even — which ones are closest to recovery?
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.theme import (
    apply_theme, hero_block, section_header, insight_callout, provenance,
    chart_label, bar_legend_circles,
    C_NAVY, C_BLUE, C_TEAL, C_GREEN, C_AMBER, C_RED, C_GRAY, C_MUTED, C_BORDER,
    CHART_LAYOUT, LEGEND_V, CHANNEL_COLORS, fmt_compact, fmt_pct
)
from utils.data import load_raw, mart_campaign_performance, mart_attribution

st.set_page_config(page_title="Campaign Performance", layout="wide")
apply_theme()

# ── Data ──────────────────────────────────────────────────────────────────────
leads, ad_perf, routing, revenue, partners, quote = load_raw()
campaign = mart_campaign_performance(leads, ad_perf, revenue)
attr = mart_attribution(leads, quote, revenue)

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("---")

channels  = sorted(campaign["channel"].unique())
verticals = sorted(campaign["insurance_vertical"].unique())
months    = sorted(campaign["month"].unique())

sel_channels  = st.sidebar.multiselect("Channel",            channels,  default=channels)
sel_verticals = st.sidebar.multiselect("Product Vertical", verticals, default=verticals)
month_labels  = [m.strftime("%b %Y") for m in months]
month_map     = dict(zip(month_labels, months))
sel_ml        = st.sidebar.select_slider("Month range", options=month_labels,
                                          value=(month_labels[0], month_labels[-1]))
m_start, m_end = month_map[sel_ml[0]], month_map[sel_ml[1]]

# ── Apply filters ─────────────────────────────────────────────────────────────
df = campaign[
    campaign["channel"].isin(sel_channels) &
    campaign["insurance_vertical"].isin(sel_verticals) &
    campaign["month"].between(m_start, m_end)
].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_spend  = df["total_spend"].sum()
total_rev    = df["total_revenue"].sum()
total_leads  = df["leads_submitted"].sum()
total_valid  = df["valid_leads"].sum()
roas  = total_rev   / total_spend  if total_spend > 0 else 0
cpl   = total_spend / total_leads  if total_leads > 0 else 0
cpvl  = total_spend / total_valid  if total_valid > 0 else 0
rpl   = total_rev   / total_leads  if total_leads > 0 else 0

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<span style='font-size:0.68rem;font-weight:600;text-transform:uppercase;"
    "letter-spacing:0.1em;color:#6B7788'>CAMPAIGN PERFORMANCE</span>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<h1 style='color:{C_NAVY};margin:4px 0 16px 0;font-size:1.9rem;"
    f"letter-spacing:-0.02em'>Campaign Performance</h1>",
    unsafe_allow_html=True,
)

# ── Hero block ─────────────────────────────────────────────────────────────────
camp_agg = df.groupby(["campaign_id", "channel"]).agg(
    total_spend   = ("total_spend",   "sum"),
    total_revenue = ("total_revenue", "sum"),
    leads_submitted = ("leads_submitted", "sum"),
).reset_index()
camp_agg["roas"] = (camp_agg["total_revenue"] / camp_agg["total_spend"]).round(3)

n_profitable = (camp_agg["roas"] >= 1.0).sum()
best_camp    = camp_agg.loc[camp_agg["roas"].idxmax()]
worst_camp   = camp_agg.loc[camp_agg["roas"].idxmin()]

hero_block(
    label="SPEND EFFICIENCY",
    metric=f"{fmt_compact(total_spend)} spent",
    insight=f"Portfolio ROAS is {roas:.2f}x — returning {fmt_compact(total_rev)} on {fmt_compact(total_spend)} ad spend. "
            f"{'No' if n_profitable == 0 else str(n_profitable)} campaign{'s are' if n_profitable != 1 else ' is'} above break-even.",
    subtext=f"Best ROAS: <b>{best_camp['campaign_id']}</b> at {best_camp['roas']:.2f}x &nbsp;·&nbsp; "
            f"CPL: {fmt_compact(cpl)} &nbsp;·&nbsp; Cost/Valid Lead: {fmt_compact(cpvl)}",
    border_color=C_RED if roas < 0.5 else C_AMBER if roas < 1.0 else C_GREEN,
)

# ── 4 KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Spend",      fmt_compact(total_spend))
c2.metric("ROAS",             f"{roas:.2f}x",
          help="Revenue / Spend. Break-even = 1.0x")
c3.metric("CPL",              fmt_compact(cpl),
          help="Total spend / Leads submitted")
c4.metric("Cost/Valid Lead",  fmt_compact(cpvl),
          help="Total spend / Valid leads only")

st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

# ── Section 01: Spend efficiency ───────────────────────────────────────────────
section_header("01", "Which campaigns are above break-even, and which remain below target?")

camp_sorted = camp_agg.sort_values("roas", ascending=True)

col_r1, col_r2 = st.columns([1, 1])

with col_r1:
    best_camp_id = camp_sorted.iloc[-1]["campaign_id"]
    best_roas    = camp_sorted.iloc[-1]["roas"]

    chart_label("ROAS by campaign against break-even")
    fig_roas = go.Figure(go.Bar(
        x=camp_sorted["roas"],
        y=camp_sorted["campaign_id"],
        orientation="h",
        marker_color=[
            C_NAVY if r >= 1.0 else C_AMBER if r >= 0.5 else C_RED
            for r in camp_sorted["roas"]
        ],
        text=[f"{r:.2f}x" for r in camp_sorted["roas"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}x<extra></extra>",
    ))
    fig_roas.add_vline(x=1.0, line_dash="dash", line_color=C_GRAY, line_width=1.5,
                       annotation_text="Break-even (1.0x)",
                       annotation_position="top right",
                       annotation_font_size=9)
    layout_roas = dict(CHART_LAYOUT)
    layout_roas["height"]      = 300
    layout_roas["xaxis"]       = dict(showgrid=False, range=[0, camp_sorted["roas"].max() * 1.35])
    layout_roas["yaxis"]       = dict(showgrid=False)
    layout_roas["margin"]      = dict(l=60, r=70, t=8, b=20)
    layout_roas["showlegend"]  = False
    fig_roas.update_layout(**layout_roas)
    st.plotly_chart(fig_roas, width="stretch")
    if best_roas >= 1.0:
        st.caption(f"{best_camp_id} leads at {best_roas:.2f}x ROAS; {best_roas - 1:.2f}x above break-even.")
    else:
        st.caption(f"{best_camp_id} is closest to break-even at {best_roas:.2f}x; {1 - best_roas:.2f}x short.")

with col_r2:
    camp_sp = camp_agg.sort_values("total_spend", ascending=False)
    top_spend_camp = camp_sp.iloc[0]["campaign_id"]
    top_spend_pct  = camp_sp.iloc[0]["total_spend"] / camp_sp["total_spend"].sum()
    top_rev_pct    = camp_sp.iloc[0]["total_revenue"] / camp_sp["total_revenue"].sum() if camp_sp["total_revenue"].sum() > 0 else 0

    chart_label("Spend vs revenue by campaign")
    fig_sp = go.Figure()
    fig_sp.add_trace(go.Bar(
        name="Spend",
        x=camp_sp["campaign_id"],
        y=camp_sp["total_spend"],
        marker_color=C_MUTED,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Spend: $%{y:,.0f}<extra></extra>",
    ))
    fig_sp.add_trace(go.Bar(
        name="Revenue",
        x=camp_sp["campaign_id"],
        y=camp_sp["total_revenue"],
        marker_color=C_NAVY,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    bar_legend_circles(fig_sp, [("Spend", C_MUTED), ("Revenue", C_NAVY)])
    layout_sp = dict(CHART_LAYOUT)
    layout_sp["barmode"] = "group"
    layout_sp["height"]  = 300
    layout_sp["yaxis"]   = dict(tickprefix="$", tickformat=",.0f", showgrid=True,
                                gridcolor=C_BORDER, zeroline=False, tickfont=dict(size=10))
    layout_sp["legend"]  = dict(LEGEND_V)
    layout_sp["margin"]  = dict(l=10, r=150, t=8, b=20)
    fig_sp.update_layout(**layout_sp)
    st.plotly_chart(fig_sp, width="stretch")
    st.caption(f"{top_spend_camp} accounts for {top_spend_pct:.0%} of spend and {top_rev_pct:.0%} of revenue.")

# ── Section 02: CPL trend ──────────────────────────────────────────────────────
section_header("02", "Is cost-per-lead improving as campaigns mature?")

cpl_trend = df.groupby(["month", "channel"]).agg(
    total_spend     = ("total_spend",     "sum"),
    leads_submitted = ("leads_submitted", "sum"),
    valid_leads     = ("valid_leads",     "sum"),
).reset_index()
cpl_trend["cpl"]  = (cpl_trend["total_spend"] / cpl_trend["leads_submitted"]).round(2)
cpl_trend["cpvl"] = (cpl_trend["total_spend"] / cpl_trend["valid_leads"]).round(2)

ch_color_map = CHANNEL_COLORS

col_c1, col_c2 = st.columns(2)

with col_c1:
    chart_label("CPL trend by channel — cost per lead over time")
    fig_cpl = go.Figure()
    for ch in sorted(cpl_trend["channel"].unique()):
        sub = cpl_trend[cpl_trend["channel"] == ch].sort_values("month")
        fig_cpl.add_trace(go.Scatter(
            name=ch,
            x=sub["month"],
            y=sub["cpl"],
            mode="lines+markers",
            line=dict(color=ch_color_map.get(ch, C_NAVY), width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{ch}</b><br>%{{x|%b %Y}}: $%{{y:.2f}}<extra></extra>",
        ))
    layout_cpl = dict(CHART_LAYOUT)
    layout_cpl["height"] = 280
    layout_cpl["yaxis"]  = dict(tickprefix="$", showgrid=True, gridcolor=C_BORDER,
                                zeroline=False, tickfont=dict(size=10), nticks=5)
    layout_cpl["xaxis"]  = dict(showgrid=False, tickfont=dict(size=10), nticks=5)
    layout_cpl["legend"] = dict(LEGEND_V)
    layout_cpl["margin"] = dict(l=10, r=150, t=8, b=20)
    fig_cpl.update_layout(**layout_cpl)
    st.plotly_chart(fig_cpl, width="stretch")
    st.caption("CPL trend shows whether acquisition efficiency is improving over time.")

with col_c2:
    chart_label("CPVL trend by channel — cost per valid lead over time")
    fig_cpvl = go.Figure()
    for ch in sorted(cpl_trend["channel"].unique()):
        sub = cpl_trend[cpl_trend["channel"] == ch].sort_values("month")
        fig_cpvl.add_trace(go.Scatter(
            name=ch,
            x=sub["month"],
            y=sub["cpvl"],
            mode="lines+markers",
            line=dict(color=ch_color_map.get(ch, C_NAVY), width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{ch}</b><br>%{{x|%b %Y}}: $%{{y:.2f}}<extra></extra>",
        ))
    layout_cpvl = dict(CHART_LAYOUT)
    layout_cpvl["height"] = 280
    layout_cpvl["yaxis"]  = dict(tickprefix="$", showgrid=True, gridcolor=C_BORDER,
                                 zeroline=False, tickfont=dict(size=10), nticks=5)
    layout_cpvl["xaxis"]  = dict(showgrid=False, tickfont=dict(size=10), nticks=5)
    layout_cpvl["legend"] = dict(LEGEND_V)
    layout_cpvl["margin"] = dict(l=10, r=150, t=8, b=20)
    fig_cpvl.update_layout(**layout_cpvl)
    st.plotly_chart(fig_cpvl, width="stretch")
    st.caption("CPVL shows acquisition cost after invalid traffic is removed.")

# ── Section 03: Attribution summary ───────────────────────────────────────────
section_header("03", "Which first-touch channels create the most revenue?")

attr_df = attr[
    attr["insurance_vertical"].isin(sel_verticals) &
    attr["month"].between(m_start, m_end)
].copy()

ft = attr_df.groupby("first_touch_channel").agg(
    leads     = ("lead_id",        "count"),
    converted = ("is_converted",   "sum"),
    revenue   = ("revenue_amount", "sum"),
).reset_index()
ft["conv_rate"] = (ft["converted"] / ft["leads"]).round(3)
ft["rpl"]       = (ft["revenue"] / ft["leads"]).round(2)

col_a1, col_a2 = st.columns(2)

with col_a1:
    ft_rev = ft.sort_values("revenue", ascending=True)
    top_rev_idx = ft_rev["revenue"].idxmax()
    top_rev_ch = ft_rev.loc[top_rev_idx, "first_touch_channel"]
    top_rev_share = (
        ft_rev.loc[top_rev_idx, "revenue"] / ft_rev["revenue"].sum()
        if ft_rev["revenue"].sum() > 0 else 0
    )
    bar_colors = [C_NAVY if i == top_rev_idx else C_MUTED for i in ft_rev.index]

    chart_label("Attributed revenue by first-touch channel")
    fig_attr_rev = go.Figure(go.Bar(
        x=ft_rev["revenue"],
        y=ft_rev["first_touch_channel"],
        orientation="h",
        marker_color=bar_colors,
        text=[fmt_compact(v) for v in ft_rev["revenue"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>",
    ))
    layout_attr_rev = dict(CHART_LAYOUT)
    layout_attr_rev["height"] = 280
    layout_attr_rev["xaxis"] = dict(showgrid=False, visible=False)
    layout_attr_rev["yaxis"] = dict(showgrid=False)
    layout_attr_rev["margin"] = dict(l=80, r=80, t=8, b=20)
    layout_attr_rev["showlegend"] = False
    fig_attr_rev.update_layout(**layout_attr_rev)
    st.plotly_chart(fig_attr_rev, width="stretch")
    st.caption(f"{top_rev_ch.title()} drives {top_rev_share:.0%} of first-touch attributed revenue.")

with col_a2:
    ft_cvr = ft.sort_values("conv_rate", ascending=True)
    top_cvr_idx = ft_cvr["conv_rate"].idxmax()
    top_cvr_ch = ft_cvr.loc[top_cvr_idx, "first_touch_channel"]
    top_cvr = ft_cvr.loc[top_cvr_idx, "conv_rate"]
    cvr_colors = [C_NAVY if i == top_cvr_idx else C_MUTED for i in ft_cvr.index]

    chart_label("Conversion rate by first-touch channel")
    fig_attr_cvr = go.Figure(go.Bar(
        x=ft_cvr["conv_rate"],
        y=ft_cvr["first_touch_channel"],
        orientation="h",
        marker_color=cvr_colors,
        text=[f"{r:.0%}" for r in ft_cvr["conv_rate"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>CVR: %{x:.1%}<extra></extra>",
    ))
    layout_attr_cvr = dict(CHART_LAYOUT)
    layout_attr_cvr["height"] = 280
    layout_attr_cvr["xaxis"] = dict(tickformat=".0%", showgrid=False,
                                    range=[0, ft_cvr["conv_rate"].max() * 1.3])
    layout_attr_cvr["yaxis"] = dict(showgrid=False)
    layout_attr_cvr["margin"] = dict(l=80, r=60, t=8, b=20)
    layout_attr_cvr["showlegend"] = False
    fig_attr_cvr.update_layout(**layout_attr_cvr)
    st.plotly_chart(fig_attr_cvr, width="stretch")
    st.caption(f"{top_cvr_ch.title()} has the highest first-touch CVR at {top_cvr:.0%}.")

# ── Summary table ─────────────────────────────────────────────────────────────
with st.expander("Full campaign table"):
    tbl = df.groupby(["campaign_id", "channel", "insurance_vertical"]).agg(
        total_spend     = ("total_spend",     "sum"),
        total_revenue   = ("total_revenue",   "sum"),
        leads_submitted = ("leads_submitted", "sum"),
        valid_leads     = ("valid_leads",     "sum"),
        platform_leads  = ("platform_leads",  "sum"),
    ).reset_index()
    tbl["roas"]         = (tbl["total_revenue"]    / tbl["total_spend"]).round(3)
    tbl["cpl"]          = (tbl["total_spend"]      / tbl["leads_submitted"]).round(2)
    tbl["valid_rate"]   = (tbl["valid_leads"]      / tbl["leads_submitted"]).round(3)
    tbl["overclaim"]    = ((tbl["platform_leads"] - tbl["leads_submitted"]) / tbl["platform_leads"]).round(3)
    fmt = {
        "total_spend": "${:,.0f}", "total_revenue": "${:,.0f}",
        "roas": "{:.2f}x", "cpl": "${:.2f}",
        "leads_submitted": "{:,.0f}", "valid_rate": "{:.1%}", "overclaim": "{:.1%}",
    }
    st.dataframe(
        tbl[["campaign_id", "channel", "insurance_vertical",
             "total_spend", "total_revenue", "roas", "leads_submitted",
             "valid_rate", "cpl", "overclaim"]]
        .sort_values("total_spend", ascending=False).style.format(fmt),
        width="stretch", hide_index=True,
    )

provenance()
