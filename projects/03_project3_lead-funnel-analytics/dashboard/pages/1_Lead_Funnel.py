"""
1_Lead_Funnel.py  —  Lead Funnel Analysis
Story: Where does lead quality break down, and which channels are most efficient?
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.theme import (
    apply_theme, page_header, hero_block, section_header, insight_callout, provenance,
    chart_label, bar_legend_circles,
    C_NAVY, C_BLUE, C_TEAL, C_SKY, C_GREEN, C_AMBER, C_RED, C_GRAY, C_MUTED, C_BORDER,
    CHART_LAYOUT, LEGEND_V, CHANNEL_COLORS, FUNNEL_COLORS, fmt_compact, fmt_pct
)
from utils.data import load_raw, mart_lead_funnel

st.set_page_config(page_title="Lead Funnel", layout="wide")
apply_theme()

# ── Data ──────────────────────────────────────────────────────────────────────
leads, ad_perf, routing, revenue, partners, quote = load_raw()
funnel = mart_lead_funnel(leads, quote)

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("---")

channels  = sorted(funnel["channel"].unique())
verticals = sorted(funnel["insurance_vertical"].unique())
months    = sorted(funnel["month"].unique())

sel_channels  = st.sidebar.multiselect("Channel",            channels,  default=channels)
sel_verticals = st.sidebar.multiselect("Product Vertical", verticals, default=verticals)

month_labels = [m.strftime("%b %Y") for m in months]
month_map    = dict(zip(month_labels, months))
sel_ml       = st.sidebar.select_slider("Month range", options=month_labels,
                                         value=(month_labels[0], month_labels[-1]))
m_start, m_end = month_map[sel_ml[0]], month_map[sel_ml[1]]

# ── Apply filters ─────────────────────────────────────────────────────────────
df = funnel[
    funnel["channel"].isin(sel_channels) &
    funnel["insurance_vertical"].isin(sel_verticals) &
    funnel["month"].between(m_start, m_end)
].copy()

# ── Aggregate KPIs ────────────────────────────────────────────────────────────
total_sessions = df["sessions"].sum()
total_qs       = df["quote_starts"].sum()
total_qc       = df["quote_completions"].sum()
total_leads    = df["leads_submitted"].sum()
total_valid    = df["valid_leads"].sum()
total_dups     = df["duplicate_leads"].sum()
overall_cvr    = total_leads / total_sessions if total_sessions > 0 else 0
valid_rate     = total_valid / total_leads    if total_leads > 0 else 0
dup_rate       = total_dups  / total_leads    if total_leads > 0 else 0
q_pass_rate    = total_qc    / total_qs       if total_qs > 0 else 0

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<span style='font-size:0.68rem;font-weight:600;text-transform:uppercase;"
    "letter-spacing:0.1em;color:#6B7788'>LEAD FUNNEL ANALYSIS</span>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<h1 style='color:{C_NAVY};margin:4px 0 16px 0;font-size:1.9rem;"
    f"letter-spacing:-0.02em'>Lead Funnel</h1>",
    unsafe_allow_html=True,
)

# ── Hero block ─────────────────────────────────────────────────────────────────
sessions_lost = total_sessions - total_leads
loss_pct      = sessions_lost / total_sessions if total_sessions > 0 else 0
hero_block(
    label="FUNNEL EFFICIENCY",
    metric=fmt_pct(overall_cvr),
    insight=f"Only {overall_cvr:.0%} of sessions convert to a lead — {sessions_lost:,.0f} sessions ({loss_pct:.0%}) drop before submitting.",
    subtext=f"{total_sessions:,.0f} sessions &nbsp;·&nbsp; {total_leads:,.0f} leads &nbsp;·&nbsp; "
            f"{total_valid:,.0f} valid ({valid_rate:.0%}) &nbsp;·&nbsp; {total_dups:,.0f} duplicates ({dup_rate:.0%})",
    border_color=C_AMBER if overall_cvr < 0.25 else C_GREEN,
)

# ── 4 KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sessions",        f"{total_sessions:,.0f}")
c2.metric("Overall CVR",     fmt_pct(overall_cvr))
c3.metric("Valid Lead Rate", fmt_pct(valid_rate))
c4.metric("Duplicate Rate",  fmt_pct(dup_rate), delta_color="inverse")

st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

# ── Section 01: Full Funnel ────────────────────────────────────────────────────
section_header("01", "Where do most users drop off — quote start, completion, or submission?")

col_f, col_b = st.columns([1, 1])

with col_f:
    stages_v = [total_sessions, total_qs, total_qc, total_leads, total_valid]
    stages_l = ["Sessions", "Quote Starts", "Completions", "Leads Submitted", "Valid Leads"]
    funnel_colors = list(FUNNEL_COLORS.values())

    # Compute biggest drop step
    pass_throughs = []
    for i in range(1, len(stages_v)):
        pt = stages_v[i] / stages_v[i-1] if stages_v[i-1] > 0 else 1.0
        pass_throughs.append((stages_l[i-1] + " → " + stages_l[i], pt))
    biggest_drop_label, biggest_drop_pt = min(pass_throughs, key=lambda x: x[1])

    chart_label("Acquisition funnel — sequential pass-through rates")
    fig_funnel = go.Figure(go.Funnel(
        y=stages_l,
        x=stages_v,
        textinfo="value+percent previous",
        textfont=dict(size=12, color="white"),
        marker=dict(color=funnel_colors, line=dict(color="white", width=1.5)),
        connector=dict(line=dict(color=C_MUTED, width=1)),
        hovertemplate="<b>%{y}</b><br>Count: %{x:,.0f}<br>Pass-through: %{percentPrevious:.0%}<extra></extra>",
    ))
    layout_f = dict(CHART_LAYOUT)
    layout_f["height"]      = 360
    layout_f["margin"]      = dict(l=10, r=10, t=8, b=10)
    layout_f["showlegend"]  = False
    fig_funnel.update_layout(**layout_f)
    st.plotly_chart(fig_funnel, width="stretch")
    st.caption(f"Biggest drop: {biggest_drop_label} ({biggest_drop_pt:.0%} pass-through).")

with col_b:
    # Per-channel funnel (normalized to 100% sessions)
    ch_agg = df.groupby("channel").agg(
        sessions          = ("sessions",          "sum"),
        quote_starts      = ("quote_starts",      "sum"),
        quote_completions = ("quote_completions", "sum"),
        leads_submitted   = ("leads_submitted",   "sum"),
        valid_leads       = ("valid_leads",        "sum"),
    ).reset_index().sort_values("sessions", ascending=False)

    for col in ["quote_starts", "quote_completions", "leads_submitted", "valid_leads"]:
        ch_agg[col + "_pct"] = (ch_agg[col] / ch_agg["sessions"]).round(3)

    stages_norm = ["quote_starts_pct", "quote_completions_pct",
                   "leads_submitted_pct", "valid_leads_pct"]
    stage_labels_norm = ["Quote Start", "Completion", "Lead Submit", "Valid Lead"]
    norm_colors = [C_NAVY, C_MUTED, C_MUTED, C_MUTED]

    # Top CVR channel
    ch_agg["cvr"] = ch_agg["leads_submitted_pct"]
    top_cvr_ch = ch_agg.loc[ch_agg["cvr"].idxmax(), "channel"]
    top_cvr    = ch_agg["cvr"].max()

    chart_label("Funnel pass-through rates by channel (% of sessions)")
    fig_ch = go.Figure()
    for stage, label, color in zip(stages_norm, stage_labels_norm, norm_colors):
        fig_ch.add_trace(go.Bar(
            name=label,
            x=ch_agg["channel"],
            y=ch_agg[stage],
            marker_color=color,
            showlegend=False,
            hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.1%}}<extra></extra>",
        ))
    bar_legend_circles(fig_ch, list(zip(stage_labels_norm, norm_colors)))

    layout_ch = dict(CHART_LAYOUT)
    layout_ch["barmode"] = "group"
    layout_ch["height"]  = 320
    layout_ch["yaxis"]   = dict(tickformat=".0%", showgrid=True, gridcolor=C_BORDER,
                                zeroline=False, tickfont=dict(size=10))
    layout_ch["xaxis"]   = dict(showgrid=False, tickfont=dict(size=10))
    layout_ch["legend"]  = dict(LEGEND_V)
    layout_ch["margin"]  = dict(l=10, r=150, t=8, b=20)
    fig_ch.update_layout(**layout_ch)
    st.plotly_chart(fig_ch, width="stretch")
    st.caption(f"{top_cvr_ch.title()} has the highest session-to-lead CVR at {top_cvr:.1%}.")

# ── Section 02: CVR trend over time ───────────────────────────────────────────
section_header("02", "Is conversion rate improving month-over-month?")

trend = df.groupby(["month", "channel"]).agg(
    sessions        = ("sessions",        "sum"),
    leads_submitted = ("leads_submitted", "sum"),
    valid_leads     = ("valid_leads",     "sum"),
).reset_index()
trend["overall_cvr"] = (trend["leads_submitted"] / trend["sessions"]).round(3)

col_t1, col_t2 = st.columns(2)

ch_color_map = CHANNEL_COLORS

with col_t1:
    chart_label("Overall CVR trend by channel")
    fig_cvr = go.Figure()
    for ch in sorted(trend["channel"].unique()):
        sub = trend[trend["channel"] == ch].sort_values("month")
        fig_cvr.add_trace(go.Scatter(
            name=ch,
            x=sub["month"],
            y=sub["overall_cvr"],
            mode="lines+markers",
            line=dict(color=ch_color_map.get(ch, C_NAVY), width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{ch}</b><br>%{{x|%b %Y}}: %{{y:.1%}}<extra></extra>",
        ))
    layout_cvr = dict(CHART_LAYOUT)
    layout_cvr["height"] = 280
    layout_cvr["yaxis"]  = dict(tickformat=".0%", showgrid=True, gridcolor=C_BORDER,
                                zeroline=False, tickfont=dict(size=10), nticks=5)
    layout_cvr["xaxis"]  = dict(showgrid=False, tickfont=dict(size=10), nticks=5)
    layout_cvr["legend"] = dict(LEGEND_V)
    layout_cvr["margin"] = dict(l=10, r=150, t=8, b=20)
    fig_cvr.update_layout(**layout_cvr)
    st.plotly_chart(fig_cvr, width="stretch")
    st.caption("Month-over-month CVR trend highlights channels losing efficiency.")

with col_t2:
    vert_trend = df.groupby(["month", "insurance_vertical"]).agg(
        leads_submitted = ("leads_submitted", "sum"),
        valid_leads     = ("valid_leads",     "sum"),
    ).reset_index()
    vert_trend["valid_rate"] = (vert_trend["valid_leads"] / vert_trend["leads_submitted"]).round(3)

    vert_colors = [C_NAVY, C_BLUE, C_TEAL]
    chart_label("Valid lead rate trend by vertical")
    fig_vr = go.Figure()
    for i, v in enumerate(sorted(vert_trend["insurance_vertical"].unique())):
        sub = vert_trend[vert_trend["insurance_vertical"] == v].sort_values("month")
        fig_vr.add_trace(go.Scatter(
            name=v,
            x=sub["month"],
            y=sub["valid_rate"],
            mode="lines+markers",
            line=dict(color=vert_colors[i % len(vert_colors)], width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>{v}</b><br>%{{x|%b %Y}}: %{{y:.1%}}<extra></extra>",
        ))
    layout_vr = dict(CHART_LAYOUT)
    layout_vr["height"] = 280
    layout_vr["yaxis"]  = dict(tickformat=".0%", showgrid=True, gridcolor=C_BORDER,
                                zeroline=False, tickfont=dict(size=10), nticks=5)
    layout_vr["xaxis"]  = dict(showgrid=False, tickfont=dict(size=10), nticks=5)
    layout_vr["legend"] = dict(LEGEND_V)
    layout_vr["margin"] = dict(l=10, r=150, t=8, b=20)
    fig_vr.update_layout(**layout_vr)
    st.plotly_chart(fig_vr, width="stretch")
    st.caption("Valid lead rate is stable across verticals.")

# ── Section 03: Quality breakdown ─────────────────────────────────────────────
section_header("03", "Which channel × vertical combinations have the worst duplicate rate?")

dup_pivot = df.groupby(["channel", "insurance_vertical"]).agg(
    leads_submitted = ("leads_submitted", "sum"),
    duplicate_leads = ("duplicate_leads", "sum"),
).reset_index()
dup_pivot["dup_rate"] = (dup_pivot["duplicate_leads"] / dup_pivot["leads_submitted"]).round(3)

pivot = dup_pivot.pivot(
    index="channel", columns="insurance_vertical", values="dup_rate"
).fillna(0)

# Compute worst dup combination for caption
worst_dup_row = dup_pivot.sort_values("dup_rate", ascending=False).iloc[0]
worst_dup_ch   = worst_dup_row["channel"]
worst_dup_vert = worst_dup_row["insurance_vertical"]
worst_dup_rate = worst_dup_row["dup_rate"]

chart_label("Duplicate lead rate heatmap — channel × vertical")
fig_heat = go.Figure(go.Heatmap(
    z=pivot.values,
    x=pivot.columns.tolist(),
    y=pivot.index.tolist(),
    colorscale=[[0, "#E6F6EF"], [0.5, "#FDF3E7"], [1, "#FDEAED"]],
    text=[[f"{v:.1%}" for v in row] for row in pivot.values],
    texttemplate="%{text}",
    textfont=dict(size=12),
    showscale=True,
    colorbar=dict(tickformat=".0%", len=0.8),
    hovertemplate="<b>%{y} · %{x}</b><br>Dup Rate: %{z:.1%}<extra></extra>",
))
layout_h = dict(CHART_LAYOUT)
layout_h["height"]      = 250
layout_h["margin"]      = dict(l=80, r=20, t=8, b=50)
layout_h["xaxis"]       = dict(showgrid=False)
layout_h["yaxis"]       = dict(showgrid=False)
layout_h["showlegend"]  = False
fig_heat.update_layout(**layout_h)
st.plotly_chart(fig_heat, width="stretch")
st.caption(f"Highest duplicate concentration: {worst_dup_ch.title()} x {worst_dup_vert} at {worst_dup_rate:.1%}.")

# Worst dup rate callout
worst_dup = dup_pivot.sort_values("dup_rate", ascending=False).iloc[0]
if worst_dup["dup_rate"] > 0.10:
    insight_callout(
        f"<b>{worst_dup['channel'].title()} × {worst_dup['insurance_vertical']}</b> has the highest "
        f"duplicate rate at <b>{worst_dup['dup_rate']:.1%}</b> — investigate source list hygiene.",
        kind="warning",
    )

# ── Detail table ──────────────────────────────────────────────────────────────
with st.expander("Detail table - channel x vertical breakdown"):
    tbl = df.groupby(["channel", "insurance_vertical"]).agg(
        sessions          = ("sessions",          "sum"),
        leads_submitted   = ("leads_submitted",   "sum"),
        valid_leads       = ("valid_leads",        "sum"),
        duplicate_leads   = ("duplicate_leads",   "sum"),
    ).reset_index()
    tbl["overall_cvr"]   = (tbl["leads_submitted"] / tbl["sessions"]).round(3)
    tbl["valid_rate"]    = (tbl["valid_leads"]      / tbl["leads_submitted"]).round(3)
    tbl["duplicate_rate"] = (tbl["duplicate_leads"] / tbl["leads_submitted"]).round(3)
    fmt = {
        "sessions": "{:,.0f}", "leads_submitted": "{:,.0f}", "valid_leads": "{:,.0f}",
        "duplicate_leads": "{:,.0f}", "overall_cvr": "{:.1%}",
        "valid_rate": "{:.1%}", "duplicate_rate": "{:.1%}",
    }
    st.dataframe(
        tbl.sort_values("leads_submitted", ascending=False).style.format(fmt),
        width="stretch", hide_index=True,
    )

provenance()
