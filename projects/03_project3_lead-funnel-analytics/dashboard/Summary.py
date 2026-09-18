"""
Summary.py  —  Lead Funnel Analytics (Home)
Executive briefing: hero insight → 4 KPIs with MoM delta → funnel → campaign → partner
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.theme import (
    apply_theme, hero_block, section_header, insight_callout, provenance,
    chart_label, bar_legend_circles,
    C_NAVY, C_BLUE, C_TEAL, C_GREEN, C_AMBER, C_RED, C_GRAY, C_MUTED,
    C_GREEN_BG, C_AMBER_BG, C_RED_BG, CHART_LAYOUT, LEGEND_V, FUNNEL_COLORS,
    fmt_compact, fmt_pct
)
from utils.data import load_raw, mart_lead_funnel, mart_campaign_performance, mart_partner_performance

st.set_page_config(
    page_title="Lead Funnel Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# ── Load data ──────────────────────────────────────────────────────────────────
leads, ad_perf, routing, revenue, partners, quote = load_raw()
funnel   = mart_lead_funnel(leads, quote)
campaign = mart_campaign_performance(leads, ad_perf, revenue)
partner  = mart_partner_performance(routing, revenue, partners)

# ── Compute overall KPIs ───────────────────────────────────────────────────────
total_sessions  = funnel["sessions"].sum()
total_leads     = funnel["leads_submitted"].sum()
total_spend     = campaign["total_spend"].sum()
paid_revenue    = campaign["total_revenue"].sum()          # paid channels only (ad spend exists)
overall_cvr     = total_leads / total_sessions if total_sessions > 0 else 0
paid_roas       = paid_revenue / total_spend if total_spend > 0 else 0
valid_rate      = funnel["valid_leads"].sum() / total_leads if total_leads > 0 else 0
acceptance_rate = (partner["leads_accepted"].sum() / partner["leads_delivered"].sum()
                   if partner["leads_delivered"].sum() > 0 else 0)

# Organic & direct revenue: all revenue minus paid-campaign revenue
# Bridge: leads → revenue events (all channels)
paid_campaign_ids = set(campaign["campaign_id"].unique())
leads_df = leads.copy()
revenue_df = revenue.copy()
all_rev = leads_df[["lead_id", "campaign_id"]].merge(
    revenue_df[["lead_id", "revenue_amount"]], on="lead_id", how="inner"
)
organic_direct_rev = all_rev[~all_rev["campaign_id"].isin(paid_campaign_ids)]["revenue_amount"].sum()
total_revenue_all  = paid_revenue + organic_direct_rev   # full portfolio revenue

roas = paid_roas  # ROAS always shown on paid basis (meaningful denominator)

# ── MoM delta (last month vs prior month) ─────────────────────────────────────
months_sorted = sorted(funnel["month"].unique())
if len(months_sorted) >= 2:
    last_m  = months_sorted[-1]
    prior_m = months_sorted[-2]

    def _funnel_kpi(df, month):
        s = df[df["month"] == month]
        sess = s["sessions"].sum()
        ld   = s["leads_submitted"].sum()
        vl   = s["valid_leads"].sum()
        return sess, ld, (ld / sess if sess > 0 else 0), (vl / ld if ld > 0 else 0)

    sess_l, ld_l, cvr_l, vr_l  = _funnel_kpi(funnel, last_m)
    sess_p, ld_p, cvr_p, vr_p  = _funnel_kpi(funnel, prior_m)

    def _camp_kpi(df, month):
        s = df[df["month"] == month]
        sp = s["total_spend"].sum()
        rv = s["total_revenue"].sum()
        return sp, rv, (rv / sp if sp > 0 else 0)

    sp_l, rv_l, roas_l = _camp_kpi(campaign, last_m)
    sp_p, rv_p, roas_p = _camp_kpi(campaign, prior_m)

    delta_cvr   = cvr_l  - cvr_p   if cvr_p  > 0 else None
    delta_vr    = vr_l   - vr_p    if vr_p   > 0 else None
    delta_roas  = roas_l - roas_p  if roas_p > 0 else None
    delta_rev   = ((rv_l - rv_p)   / rv_p * 100) if rv_p > 0 else None
else:
    delta_cvr = delta_vr = delta_roas = delta_rev = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data:** 6-month synthetic dataset  \n"
    "**Grain:** Lead-level → 5 mart tables  \n"
    "**Period:** Jan 2025 – Jun 2025  \n"
    "**Source:** BigQuery / local CSV"
)

# ── Page title ─────────────────────────────────────────────────────────────────
st.markdown(
    f"<span style='font-size:0.68rem;font-weight:600;text-transform:uppercase;"
    f"letter-spacing:0.1em;color:#6B7788'>EXECUTIVE SUMMARY</span>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<h1 style='color:{C_NAVY};margin:4px 0 0 0;font-size:1.9rem;"
    f"letter-spacing:-0.02em'>Lead Funnel Analytics</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#6B7788;margin-top:4px;margin-bottom:20px;font-size:0.85rem'>"
    "Performance-based lead generation analytics — acquisition → validation → routing → revenue</p>",
    unsafe_allow_html=True,
)

# ── Hero block ─────────────────────────────────────────────────────────────────
if roas < 0.5:
    insight_txt = "Ad spend is running at a loss — revenue returns only {roas:.2f}x for every $1 spent. Lead quality is holding at {vr:.0%} validity, but spend efficiency needs immediate attention.".format(
        roas=roas, vr=valid_rate)
    hero_color = C_RED
elif roas < 1.0:
    insight_txt = "Campaigns are below break-even at {roas:.2f}x ROAS — valid lead rate ({vr:.0%}) is healthy, but revenue-per-lead needs to improve to cover acquisition costs.".format(
        roas=roas, vr=valid_rate)
    hero_color = C_AMBER
else:
    insight_txt = "Portfolio is profitable at {roas:.2f}x ROAS with {vr:.0%} valid lead rate.".format(
        roas=roas, vr=valid_rate)
    hero_color = C_GREEN

hero_block(
    label="Portfolio readout",
    metric=f"{roas:.2f}x Paid ROAS",
    insight=insight_txt,
    subtext=(
        f"{fmt_compact(total_spend)} paid spend &nbsp;·&nbsp; "
        f"{fmt_compact(paid_revenue)} paid revenue (ROAS {roas:.2f}x) &nbsp;·&nbsp; "
        f"+{fmt_compact(organic_direct_rev)} organic/direct (zero cost) &nbsp;·&nbsp; "
        f"{fmt_compact(total_revenue_all)} total portfolio revenue"
    ),
    border_color=hero_color,
)

# ── 4 KPIs with MoM delta ──────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

def _delta_str(delta, pct_pts=False, good="up"):
    if delta is None:
        return None
    if pct_pts:
        s = f"{delta*100:+.1f} pp MoM"
    else:
        s = f"{delta:+.1f}% MoM"
    return s

c1.metric(
    "Total Revenue",
    fmt_compact(total_revenue_all),
    delta=_delta_str(delta_rev),
    help=f"All channels: paid {fmt_compact(paid_revenue)} + organic/direct {fmt_compact(organic_direct_rev)} (zero acquisition cost)",
)
c2.metric(
    "Overall CVR",
    fmt_pct(overall_cvr),
    delta=_delta_str(delta_cvr, pct_pts=True),
    help="Leads submitted / Total sessions",
)
c3.metric(
    "Valid Lead Rate",
    fmt_pct(valid_rate),
    delta=_delta_str(delta_vr, pct_pts=True),
    help="Leads passing all validation rules / Total leads submitted",
)
c4.metric(
    "Paid ROAS",
    f"{roas:.2f}x",
    delta=_delta_str(delta_roas, pct_pts=True),
    delta_color="normal",
    help=f"Paid channel revenue {fmt_compact(paid_revenue)} / Paid spend {fmt_compact(total_spend)}. Organic/direct add {fmt_compact(organic_direct_rev)} at zero cost.",
)

st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

# Revenue breakdown callout
total_portfolio_roas = total_revenue_all / total_spend if total_spend > 0 else 0
insight_callout(
    f"<b>Revenue mix:</b> paid channels returned <b>{fmt_compact(paid_revenue)}</b> "
    f"on <b>{fmt_compact(total_spend)}</b> spend (<b>{roas:.2f}x</b>). "
    f"Organic and direct added <b>{fmt_compact(organic_direct_rev)}</b>, "
    f"lifting portfolio ROAS to <b>{total_portfolio_roas:.2f}x</b>.",
    kind="info",
)

# ── Section 01: Funnel ─────────────────────────────────────────────────────────
section_header("01", "Where do leads drop off in the acquisition funnel?")

# Compute overall funnel numbers
stages_vals = [
    funnel["sessions"].sum(),
    funnel["quote_starts"].sum(),
    funnel["quote_completions"].sum(),
    funnel["leads_submitted"].sum(),
    funnel["valid_leads"].sum(),
]
stages_labels = ["Sessions", "Quote Starts", "Completions", "Leads", "Valid Leads"]
funnel_colors = list(FUNNEL_COLORS.values())

# Compute biggest drop step for caption
pass_throughs = []
for i in range(1, len(stages_vals)):
    pt = stages_vals[i] / stages_vals[i-1] if stages_vals[i-1] > 0 else 1.0
    pass_throughs.append((stages_labels[i-1] + " → " + stages_labels[i], pt))
biggest_drop_label, biggest_drop_pt = min(pass_throughs, key=lambda x: x[1])

col_funnel, col_channel = st.columns([1, 1])

with col_funnel:
    chart_label("Acquisition funnel — sequential pass-through rates")
    fig_funnel = go.Figure(go.Funnel(
        y=stages_labels,
        x=stages_vals,
        textinfo="value+percent previous",
        textfont=dict(size=13, color="white"),
        marker=dict(
            color=funnel_colors,
            line=dict(color="white", width=1.5),
        ),
        connector=dict(line=dict(color=C_MUTED, width=1)),
        hovertemplate="<b>%{y}</b><br>Count: %{x:,.0f}<br>Pass-through: %{percentPrevious:.0%}<extra></extra>",
    ))
    layout_f = dict(CHART_LAYOUT)
    layout_f["height"]      = 340
    layout_f["margin"]      = dict(l=10, r=10, t=8, b=10)
    layout_f["showlegend"]  = False
    fig_funnel.update_layout(**layout_f)
    st.plotly_chart(fig_funnel, width="stretch")
    st.caption(f"Biggest drop: {biggest_drop_label} ({biggest_drop_pt:.0%} pass-through).")

with col_channel:
    ch_agg = funnel.groupby("channel").agg(
        leads_submitted = ("leads_submitted", "sum"),
        valid_leads     = ("valid_leads",     "sum"),
        sessions        = ("sessions",        "sum"),
    ).reset_index().sort_values("leads_submitted", ascending=True)

    ch_agg["valid_rate"] = (ch_agg["valid_leads"] / ch_agg["leads_submitted"]).round(3)

    max_ch = ch_agg["leads_submitted"].idxmax()
    bar_colors = [C_NAVY if i == max_ch else C_MUTED for i in ch_agg.index]

    top_ch_row = ch_agg.loc[max_ch]

    chart_label("Leads by channel — sorted by volume")
    fig_ch = go.Figure(go.Bar(
        x=ch_agg["leads_submitted"],
        y=ch_agg["channel"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:,.0f}" for v in ch_agg["leads_submitted"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Leads: %{x:,.0f}<extra></extra>",
    ))
    layout_ch = dict(CHART_LAYOUT)
    layout_ch["height"]      = 280
    layout_ch["margin"]      = dict(l=80, r=70, t=8, b=20)
    layout_ch["xaxis"]       = dict(showgrid=False, visible=False)
    layout_ch["yaxis"]       = dict(showgrid=False)
    layout_ch["showlegend"]  = False
    fig_ch.update_layout(**layout_ch)
    st.plotly_chart(fig_ch, width="stretch")
    st.caption(f"{top_ch_row['channel'].title()} leads volume at {top_ch_row['leads_submitted']:,.0f} leads; valid rate is {top_ch_row['valid_rate']:.0%}.")

    insight_callout(
        f"<b>{top_ch_row['channel'].title()}</b> leads in volume ({top_ch_row['leads_submitted']:,.0f} leads) "
        f"with a <b>{top_ch_row['valid_rate']:.0%}</b> valid lead rate.",
        kind="info",
    )

# ── Section 02: Spend vs Revenue ───────────────────────────────────────────────
section_header("02", "Which campaigns are returning spend, and which remain below break-even?")

camp_agg = campaign.groupby(["campaign_id", "channel"]).agg(
    total_spend   = ("total_spend",   "sum"),
    total_revenue = ("total_revenue", "sum"),
    leads_submitted = ("leads_submitted", "sum"),
).reset_index()
camp_agg["roas"] = (camp_agg["total_revenue"] / camp_agg["total_spend"]).round(3)
camp_agg = camp_agg.sort_values("total_spend", ascending=False)

n_below = (camp_agg["roas"] < 1.0).sum()
n_total  = len(camp_agg)

col_s1, col_s2 = st.columns(2)

with col_s1:
    chart_label("Spend vs Revenue — all campaigns (grouped bars)")
    fig_sp = go.Figure()
    fig_sp.add_trace(go.Bar(
        name="Spend",
        x=camp_agg["campaign_id"],
        y=camp_agg["total_spend"],
        marker_color=C_MUTED,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Spend: $%{y:,.0f}<extra></extra>",
    ))
    fig_sp.add_trace(go.Bar(
        name="Revenue",
        x=camp_agg["campaign_id"],
        y=camp_agg["total_revenue"],
        marker_color=C_NAVY,
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    bar_legend_circles(fig_sp, [("Spend", C_MUTED), ("Revenue", C_NAVY)])
    layout_sp = dict(CHART_LAYOUT)
    layout_sp["barmode"] = "group"
    layout_sp["height"]  = 280
    layout_sp["yaxis"]   = dict(tickprefix="$", tickformat=",.0f", showgrid=True,
                                gridcolor="#D9DEE7", zeroline=False, tickfont=dict(size=10))
    layout_sp["legend"]  = dict(LEGEND_V)
    layout_sp["margin"]  = dict(l=10, r=150, t=8, b=20)
    fig_sp.update_layout(**layout_sp)
    st.plotly_chart(fig_sp, width="stretch")
    st.caption(f"{n_below} of {n_total} campaigns are below break-even. Portfolio returns {fmt_compact(total_revenue_all)} on {fmt_compact(total_spend)} spend.")

with col_s2:
    camp_roas_sorted = camp_agg.sort_values("roas", ascending=True)
    best_camp_id = camp_roas_sorted.iloc[-1]["campaign_id"]
    best_roas    = camp_roas_sorted.iloc[-1]["roas"]

    chart_label("ROAS by campaign against break-even")
    fig_roas = go.Figure(go.Bar(
        x=camp_roas_sorted["roas"],
        y=camp_roas_sorted["campaign_id"],
        orientation="h",
        marker_color=[
            C_GREEN if r >= 1.0 else C_AMBER if r >= 0.5 else C_RED
            for r in camp_roas_sorted["roas"]
        ],
        text=[f"{r:.2f}x" for r in camp_roas_sorted["roas"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}x<extra></extra>",
    ))
    max_roas = camp_roas_sorted["roas"].max()
    fig_roas.add_vline(x=1.0, line_dash="dash", line_color=C_GRAY, line_width=1.5,
                       annotation_text="Break-even", annotation_position="top right",
                       annotation_font_size=9)
    layout_roas = dict(CHART_LAYOUT)
    layout_roas["height"]      = 280
    layout_roas["xaxis"]       = dict(showgrid=False, range=[0, max_roas * 1.3])
    layout_roas["yaxis"]       = dict(showgrid=False)
    layout_roas["margin"]      = dict(l=60, r=70, t=8, b=20)
    layout_roas["showlegend"]  = False
    fig_roas.update_layout(**layout_roas)
    st.plotly_chart(fig_roas, width="stretch")
    if best_roas >= 1.0:
        st.caption(f"Best performer: {best_camp_id} at {best_roas:.2f}x; {best_roas - 1:.2f}x above break-even.")
    else:
        st.caption(f"Best performer: {best_camp_id} at {best_roas:.2f}x; {1 - best_roas:.2f}x below break-even.")

insight_callout(
    f"<b>{n_below} of {n_total} campaigns</b> are operating below break-even (ROAS &lt; 1.0x). "
    f"Total spend of <b>{fmt_compact(total_spend)}</b> has returned only <b>{fmt_compact(total_revenue_all)}</b>.",
    kind="alert" if n_below == n_total else "warning",
)

# ── Section 03: Partner health ──────────────────────────────────────────────────
section_header("03", "Which partners are rejecting too many leads?")

p_agg = partner.groupby(["partner_id", "partner_name"]).agg(
    delivered = ("leads_delivered", "sum"),
    accepted  = ("leads_accepted",  "sum"),
).reset_index()
p_agg["acceptance_rate"] = (p_agg["accepted"] / p_agg["delivered"]).round(3)
p_agg = p_agg.sort_values("acceptance_rate", ascending=True)

n_below_70 = (p_agg["acceptance_rate"] < 0.70).sum()
n_below_80 = (p_agg["acceptance_rate"] < 0.80).sum()

worst = p_agg.iloc[0]

chart_label("Partner acceptance rate against minimum and target thresholds")
fig_partner = go.Figure(go.Bar(
    x=p_agg["acceptance_rate"],
    y=p_agg["partner_name"],
    orientation="h",
    marker_color=[
        C_RED if r < 0.70 else C_AMBER if r < 0.80 else C_GREEN
        for r in p_agg["acceptance_rate"]
    ],
    text=[f"{r:.0%}" for r in p_agg["acceptance_rate"]],
    textposition="outside",
    textfont=dict(size=11),
    hovertemplate="<b>%{y}</b><br>Acceptance: %{x:.1%}<extra></extra>",
))
for thresh, label, color in [(0.70, "Min 70%", C_RED), (0.80, "Target 80%", C_AMBER)]:
    fig_partner.add_vline(x=thresh, line_dash="dot", line_color=color, line_width=1.5,
                          annotation_text=label, annotation_position="top right",
                          annotation_font_size=9, annotation_font_color=color)

layout_p = dict(CHART_LAYOUT)
layout_p["height"]      = 300
layout_p["xaxis"]       = dict(tickformat=".0%", range=[0, 1.18], showgrid=False)
layout_p["yaxis"]       = dict(showgrid=False)
layout_p["margin"]      = dict(l=150, r=70, t=8, b=20)
layout_p["showlegend"]  = False
fig_partner.update_layout(**layout_p)
st.plotly_chart(fig_partner, width="stretch")
st.caption(f"{n_below_70} partners are below the 70% minimum. {worst['partner_name']} is lowest at {worst['acceptance_rate']:.0%}.")

if n_below_70 > 0:
    insight_callout(
        f"<b>{n_below_70} partner{'s' if n_below_70 > 1 else ''}</b> below the 70% minimum threshold. "
        f"<b>{worst['partner_name']}</b> is the lowest at <b>{worst['acceptance_rate']:.0%}</b> — "
        f"consider renegotiating routing priority.",
        kind="alert",
    )
elif n_below_80 > 0:
    insight_callout(
        f"<b>{n_below_80} partner{'s' if n_below_80 > 1 else ''}</b> below the 80% target. "
        f"No partners are below the minimum 70% threshold.",
        kind="warning",
    )
else:
    insight_callout("All partners are above the 80% acceptance rate target.", kind="positive")

# ── Data provenance ─────────────────────────────────────────────────────────────
provenance()
