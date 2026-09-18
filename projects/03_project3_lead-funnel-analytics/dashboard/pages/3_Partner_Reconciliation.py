"""
3_Partner_Reconciliation.py  —  Partner and Reconciliation Analysis
Story: Where do leads break down after acquisition: partner routing or platform reporting?
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.theme import (
    apply_theme, hero_block, section_header, insight_callout, provenance,
    chart_label, bar_legend_circles,
    C_NAVY, C_BLUE, C_TEAL, C_GREEN, C_AMBER, C_RED, C_GRAY, C_MUTED, C_SUBTLE, C_BORDER,
    CHART_LAYOUT, LEGEND_V, fmt_compact, fmt_pct
)
from utils.data import load_raw, mart_partner_performance, mart_reconciliation

st.set_page_config(page_title="Partner & Reconciliation", layout="wide")
apply_theme()

# ── Data ──────────────────────────────────────────────────────────────────────
leads, ad_perf, routing, revenue, partners, quote = load_raw()
partner = mart_partner_performance(routing, revenue, partners)
recon = mart_reconciliation(leads, ad_perf)

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("---")

partner_names = sorted(partner["partner_name"].dropna().unique())
sel_partners  = st.sidebar.multiselect("Partner", partner_names, default=partner_names)

dates       = sorted(partner["route_date"].unique())
date_strs   = [str(d)[:10] for d in dates]
date_map    = dict(zip(date_strs, dates))
sel_dates   = st.sidebar.select_slider("Date range", options=date_strs,
                                        value=(date_strs[0], date_strs[-1]))
d_start, d_end = date_map[sel_dates[0]], date_map[sel_dates[1]]

# ── Apply filters ─────────────────────────────────────────────────────────────
df = partner[
    partner["partner_name"].isin(sel_partners) &
    (partner["route_date"] >= d_start) &
    (partner["route_date"] <= d_end)
].copy()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_delivered   = df["leads_delivered"].sum()
total_accepted    = df["leads_accepted"].sum()
total_rejected    = df["leads_rejected"].sum()
total_no_resp     = df["no_response"].sum()
total_revenue     = df["daily_revenue"].sum()
overall_acc_rate  = total_accepted / total_delivered if total_delivered > 0 else 0
rev_per_accepted  = total_revenue  / total_accepted  if total_accepted  > 0 else 0

# ── Partner-level aggregation ──────────────────────────────────────────────────
p_agg = df.groupby(["partner_id", "partner_name"]).agg(
    delivered  = ("leads_delivered",  "sum"),
    accepted   = ("leads_accepted",   "sum"),
    rejected   = ("leads_rejected",   "sum"),
    no_resp    = ("no_response",      "sum"),
    revenue    = ("daily_revenue",    "sum"),
    cap_exceed = ("capacity_exceeded","sum"),
).reset_index()
p_agg["acceptance_rate"] = (p_agg["accepted"] / p_agg["delivered"]).round(3)
p_agg["rejection_rate"]  = (p_agg["rejected"] / p_agg["delivered"]).round(3)
p_agg = p_agg.sort_values("acceptance_rate", ascending=True)

n_below_70 = (p_agg["acceptance_rate"] < 0.70).sum()
n_below_80 = (p_agg["acceptance_rate"] < 0.80).sum()
n_total    = len(p_agg)
worst      = p_agg.iloc[0]

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<span style='font-size:0.68rem;font-weight:600;text-transform:uppercase;"
    "letter-spacing:0.1em;color:#6B7788'>PARTNER & RECONCILIATION</span>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<h1 style='color:{C_NAVY};margin:4px 0 16px 0;font-size:1.9rem;"
    f"letter-spacing:-0.02em'>Partner & Reconciliation</h1>",
    unsafe_allow_html=True,
)

# ── Hero block ─────────────────────────────────────────────────────────────────
hero_block(
    label="PARTNER HEALTH",
    metric=f"{overall_acc_rate:.0%} acceptance rate",
    insight=(
        f"{n_below_70} partner{'s' if n_below_70 != 1 else ''} below the 70% minimum threshold."
        if n_below_70 > 0 else
        f"{n_below_80} partner{'s' if n_below_80 != 1 else ''} below the 80% target (none below minimum 70%)."
        if n_below_80 > 0 else
        "All partners are above the 80% acceptance rate target."
    ),
    subtext=f"{total_delivered:,.0f} delivered &nbsp;·&nbsp; {total_accepted:,.0f} accepted &nbsp;·&nbsp; "
            f"{total_rejected:,.0f} rejected &nbsp;·&nbsp; {fmt_compact(total_revenue)} revenue",
    border_color=C_RED if n_below_70 > 0 else C_AMBER if n_below_80 > 0 else C_GREEN,
)

# ── 4 KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Leads Delivered",  f"{total_delivered:,.0f}")
c2.metric("Acceptance Rate",  fmt_pct(overall_acc_rate))
c3.metric("Total Revenue",    fmt_compact(total_revenue))
c4.metric("Rev / Accepted",   f"${rev_per_accepted:.2f}")

st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

# ── Section 01: Acceptance rate snapshot ──────────────────────────────────────
section_header("01", "Which partners are below the 70% minimum or 80% target?")

chart_label("Partner acceptance rate against minimum and target thresholds")
fig_acc = go.Figure(go.Bar(
    x=p_agg["acceptance_rate"],
    y=p_agg["partner_name"],
    orientation="h",
    marker_color=[
        C_RED if r < 0.70 else C_AMBER if r < 0.80 else C_NAVY
        for r in p_agg["acceptance_rate"]
    ],
    text=[f"{r:.0%}" for r in p_agg["acceptance_rate"]],
    textposition="outside",
    textfont=dict(size=11),
    hovertemplate="<b>%{y}</b><br>Acceptance: %{x:.1%}<extra></extra>",
))
for thresh, label, color in [(0.70, "Min 70%", C_RED), (0.80, "Target 80%", C_AMBER)]:
    fig_acc.add_vline(x=thresh, line_dash="dot", line_color=color, line_width=1.5,
                      annotation_text=label, annotation_position="top right",
                      annotation_font_size=9, annotation_font_color=color)

layout_acc = dict(CHART_LAYOUT)
layout_acc["height"]      = max(280, len(p_agg) * 44)
layout_acc["xaxis"]       = dict(tickformat=".0%", range=[0, 1.18], showgrid=False)
layout_acc["yaxis"]       = dict(showgrid=False)
layout_acc["margin"]      = dict(l=160, r=80, t=8, b=20)
layout_acc["showlegend"]  = False
fig_acc.update_layout(**layout_acc)
st.plotly_chart(fig_acc, width="stretch")
st.caption(f"{n_below_70} of {n_total} partners are below the 70% minimum.")

if n_below_70 > 0:
    insight_callout(
        f"<b>{worst['partner_name']}</b> is the lowest at <b>{worst['acceptance_rate']:.0%}</b> — "
        f"consider restricting lead volume or renegotiating routing priority.",
        kind="alert",
    )

# ── Section 02: Rejection reasons ─────────────────────────────────────────────
section_header("02", "Why are leads rejected after routing?")

p_agg2 = p_agg.copy()
p_agg2["other_rejection"] = p_agg2["rejected"] - p_agg2["cap_exceed"]
p_agg2 = p_agg2.sort_values("delivered", ascending=False)

chart_label("Routing outcome breakdown by partner")
fig_rej = go.Figure()
fig_rej.add_trace(go.Bar(
    name="Accepted",
    x=p_agg2["partner_name"],
    y=p_agg2["accepted"],
    marker_color=C_NAVY,
    showlegend=False,
))
fig_rej.add_trace(go.Bar(
    name="Capacity Exceeded",
    x=p_agg2["partner_name"],
    y=p_agg2["cap_exceed"],
    marker_color=C_AMBER,
    showlegend=False,
))
fig_rej.add_trace(go.Bar(
    name="Other Rejection",
    x=p_agg2["partner_name"],
    y=p_agg2["other_rejection"],
    marker_color=C_RED,
    showlegend=False,
))
fig_rej.add_trace(go.Bar(
    name="No Response",
    x=p_agg2["partner_name"],
    y=p_agg2["no_resp"],
    marker_color=C_SUBTLE,
    showlegend=False,
))
bar_legend_circles(fig_rej, [
    ("Accepted",         C_NAVY),
    ("Capacity Exceeded",C_AMBER),
    ("Other Rejection",  C_RED),
    ("No Response",      C_SUBTLE),
])
layout_rej = dict(CHART_LAYOUT)
layout_rej["barmode"] = "stack"
layout_rej["height"]  = 280
layout_rej["yaxis"]   = dict(showgrid=True, gridcolor=C_BORDER, zeroline=False,
                             tickfont=dict(size=10))
layout_rej["xaxis"]   = dict(showgrid=False, tickangle=-20, tickfont=dict(size=10))
layout_rej["legend"]  = dict(LEGEND_V)
layout_rej["margin"]  = dict(l=10, r=150, t=8, b=20)
fig_rej.update_layout(**layout_rej)
st.plotly_chart(fig_rej, width="stretch")
st.caption("Capacity exceeded is the primary rejection driver.")

# ── Section 03: Platform reconciliation ──────────────────────────────────────
section_header("03", "Are platform-reported leads matching warehouse reality?")

recon_agg = recon.groupby("channel").agg(
    platform_leads   = ("platform_leads",   "sum"),
    warehouse_leads  = ("warehouse_leads",  "sum"),
    valid_leads      = ("valid_leads",      "sum"),
    lead_discrepancy = ("lead_discrepancy", "sum"),
).reset_index()
recon_agg["overclaim_rate"] = np.where(
    recon_agg["platform_leads"] > 0,
    (recon_agg["lead_discrepancy"] / recon_agg["platform_leads"]).round(3),
    np.nan,
)

total_platform = recon["platform_leads"].sum()
total_warehouse = recon["warehouse_leads"].sum()
total_gap = total_platform - total_warehouse
overclaim_rate = total_gap / total_platform if total_platform > 0 else 0
top_gap = recon_agg.sort_values("lead_discrepancy", ascending=False).iloc[0]

col_rec1, col_rec2 = st.columns(2)

with col_rec1:
    recon_sorted = recon_agg.sort_values("platform_leads", ascending=False)
    chart_label("Platform reported vs warehouse tracked leads")
    fig_rec = go.Figure()
    fig_rec.add_trace(go.Bar(
        name="Platform Reported",
        x=recon_sorted["channel"],
        y=recon_sorted["platform_leads"],
        marker_color=C_MUTED,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Platform: %{y:,.0f}<extra></extra>",
    ))
    fig_rec.add_trace(go.Bar(
        name="Warehouse Tracked",
        x=recon_sorted["channel"],
        y=recon_sorted["warehouse_leads"],
        marker_color=C_NAVY,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Warehouse: %{y:,.0f}<extra></extra>",
    ))
    bar_legend_circles(fig_rec, [("Platform Reported", C_MUTED), ("Warehouse Tracked", C_NAVY)])
    layout_rec = dict(CHART_LAYOUT)
    layout_rec["barmode"] = "group"
    layout_rec["height"] = 300
    layout_rec["yaxis"] = dict(showgrid=True, gridcolor=C_BORDER, zeroline=False,
                               tickfont=dict(size=10))
    layout_rec["legend"] = dict(LEGEND_V)
    layout_rec["margin"] = dict(l=10, r=150, t=8, b=20)
    fig_rec.update_layout(**layout_rec)
    st.plotly_chart(fig_rec, width="stretch")
    st.caption(f"{top_gap['channel'].title()} has the largest gap: {top_gap['lead_discrepancy']:,.0f} leads.")

with col_rec2:
    oc_sorted = recon_agg.dropna(subset=["overclaim_rate"]).sort_values("overclaim_rate", ascending=True)
    chart_label("Overclaim rate by channel")
    fig_oc = go.Figure(go.Bar(
        x=oc_sorted["overclaim_rate"],
        y=oc_sorted["channel"],
        orientation="h",
        marker_color=[
            C_RED if r > 0.10 else C_AMBER if r > 0.05 else C_GREEN
            for r in oc_sorted["overclaim_rate"]
        ],
        text=[f"{r:.0%}" for r in oc_sorted["overclaim_rate"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Overclaim: %{x:.1%}<extra></extra>",
    ))
    fig_oc.add_vline(x=0.10, line_dash="dot", line_color=C_RED, line_width=1.5,
                     annotation_text="10% audit threshold", annotation_position="top right",
                     annotation_font_size=9, annotation_font_color=C_RED)
    layout_oc = dict(CHART_LAYOUT)
    layout_oc["height"] = 300
    layout_oc["xaxis"] = dict(tickformat=".0%", showgrid=False,
                              range=[0, max(0.2, oc_sorted["overclaim_rate"].max() * 1.3)])
    layout_oc["yaxis"] = dict(showgrid=False)
    layout_oc["margin"] = dict(l=80, r=70, t=8, b=20)
    layout_oc["showlegend"] = False
    fig_oc.update_layout(**layout_oc)
    st.plotly_chart(fig_oc, width="stretch")
    st.caption(f"Overall platform overclaim is {overclaim_rate:.0%} versus warehouse submissions.")

if overclaim_rate > 0.10:
    insight_callout(
        f"Platforms report <b>{total_platform:,.0f}</b> leads versus "
        f"<b>{total_warehouse:,.0f}</b> in the warehouse, a gap of "
        f"<b>{total_gap:,.0f}</b> leads.",
        kind="alert",
    )

# ── Summary table ─────────────────────────────────────────────────────────────
with st.expander("Partner summary table"):
    fmt = {
        "delivered":       "{:,.0f}",
        "accepted":        "{:,.0f}",
        "rejected":        "{:,.0f}",
        "no_resp":         "{:,.0f}",
        "revenue":         "${:,.0f}",
        "acceptance_rate": "{:.1%}",
        "rejection_rate":  "{:.1%}",
    }
    st.dataframe(
        p_agg[["partner_name", "delivered", "accepted", "rejected", "no_resp",
               "acceptance_rate", "rejection_rate", "revenue"]]
        .sort_values("acceptance_rate", ascending=False).style.format(fmt),
        width="stretch", hide_index=True,
    )

provenance()
