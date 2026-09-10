"""
Pipeline Page
=============
Story: Raw pipeline overstates closeable revenue.
       Zombie deals and high-risk signals tell you which deals need action now.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import RISK_COLORS, SEGMENT_COLORS, get_fct_pipeline
from utils.theme import (
    C_MUTED,
    action_box,
    alert,
    base_layout,
    hero,
    inject_css,
    insight,
    kpi,
    provenance,
    story_step,
)

st.set_page_config(page_title="Pipeline", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("Pipeline risk & forecast quality")

# ── Load & filter ──────────────────────────────────────────────────────────────
pipeline = get_fct_pipeline()

col_f1, col_f2 = st.columns(2)
with col_f1:
    segs = ["All"] + sorted(pipeline["segment"].dropna().unique().tolist())
    sel_seg = st.selectbox("Segment", segs)
with col_f2:
    risks = ["All"] + ["High Risk", "Medium Risk", "On Track"]
    sel_risk = st.selectbox("Risk Level", risks)

pipe_f = pipeline.copy()
if sel_seg  != "All": pipe_f = pipe_f[pipe_f["segment"]  == sel_seg]
if sel_risk != "All": pipe_f = pipe_f[pipe_f["pipeline_risk"] == sel_risk]

total_raw       = pipe_f["pipeline_amount"].sum()
total_weighted  = pipe_f["weighted_pipeline_amount"].sum()
high_risk_val   = pipe_f.loc[pipe_f["pipeline_risk"] == "High Risk", "pipeline_amount"].sum()
high_risk_pct   = high_risk_val / total_raw if total_raw else 0
weight_ratio    = total_weighted / total_raw if total_raw else 0
zombie_90       = pipe_f[pipe_f["days_since_last_activity"] > 90]
zombie_pct      = len(zombie_90) / len(pipe_f) if len(pipe_f) else 0
zombie_val      = zombie_90["pipeline_amount"].sum()
median_open     = pipe_f["days_open"].median()
median_activity = pipe_f["days_since_last_activity"].median()

# ── ① HERO ─────────────────────────────────────────────────────────────────────
st.title("Pipeline Analysis")

st.markdown(hero(
    headline=f"{high_risk_pct:.0%} of open pipeline is at high risk — "
             f"{len(zombie_90)} deals (${zombie_val/1e6:.1f}M) have had no activity in 90+ days.",
    metric=f"${total_weighted/1e6:.1f}M realistic forecast  ·  {weight_ratio:.0%} of ${total_raw/1e6:.1f}M raw",
    subtext=(
        f"{len(pipe_f):,} open deals · "
        f"${high_risk_val/1e6:.1f}M high-risk (past-due + repeated slip) · "
        f"Median deal age: {median_open:.0f} days · "
        f"Median since last activity: {median_activity:.0f} days."
    ),
), unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi("Open Deals", f"{len(pipe_f):,}", "Active opportunities"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Raw Pipeline", f"${total_raw/1e6:.1f}M", "Unweighted total"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("Weighted Forecast", f"${total_weighted/1e6:.1f}M",
                    f"{weight_ratio:.0%} of raw — probability-adjusted",
                    "good" if weight_ratio > 0.35 else "neutral"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("High-Risk Pipeline", f"${high_risk_val/1e6:.1f}M",
                    f"{high_risk_pct:.0%} of pipeline — review needed",
                    "bad" if high_risk_pct > 0.20 else "neutral"), unsafe_allow_html=True)

st.markdown("---")

# ── 01 Pipeline by Stage ──────────────────────────────────────────────────────
st.markdown(story_step("01", "Which stage carries the most closeable pipeline right now?"), unsafe_allow_html=True)

stage_agg = pipe_f.groupby(["opportunity_stage","stage_order"]).agg(
    deals=("opportunity_id","nunique"), raw=("pipeline_amount","sum"),
    weighted=("weighted_pipeline_amount","sum"), win_rate=("stage_win_rate","mean"),
).reset_index().sort_values("stage_order")

top_weighted_stage = stage_agg.nlargest(1,"weighted")["opportunity_stage"].iloc[0]
top_weighted_val   = stage_agg.nlargest(1,"weighted")["weighted"].iloc[0]

# Highlight the stage with most weighted pipeline; others muted
stage_highlight_colors_raw      = [
    C_MUTED if s != top_weighted_stage else "#1F3864"
    for s in stage_agg["opportunity_stage"]
]
stage_highlight_colors_weighted = [
    C_MUTED if s != top_weighted_stage else "#107C41"
    for s in stage_agg["opportunity_stage"]
]

fig_stage = go.Figure()
fig_stage.add_trace(go.Bar(
    name="Raw Pipeline", x=stage_agg["opportunity_stage"], y=stage_agg["raw"]/1e6,
    marker_color=stage_highlight_colors_raw, opacity=0.7,
))
fig_stage.add_trace(go.Bar(
    name="Weighted Forecast", x=stage_agg["opportunity_stage"], y=stage_agg["weighted"]/1e6,
    marker_color=stage_highlight_colors_weighted,
))
layout_stage = base_layout(height=290, margin=dict(t=44, b=20, l=8, r=8))
layout_stage.update(dict(
    title=f"'{top_weighted_stage}' drives the most weighted pipeline (${top_weighted_val/1e6:.1f}M) — focus closing effort there",
    barmode="group",
    yaxis=dict(title="Amount ($M)", gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
    legend=dict(orientation="h", x=0, y=-0.22, font=dict(size=10)),
))
fig_stage.update_layout(layout_stage)
st.plotly_chart(fig_stage, use_container_width=True)

stage_agg["coverage"] = stage_agg["weighted"] / total_weighted if total_weighted else 0
st.dataframe(
    stage_agg[["opportunity_stage","deals","raw","weighted","win_rate","coverage"]]
    .rename(columns={"opportunity_stage":"Stage","deals":"Deals","raw":"Raw ($)",
                     "weighted":"Weighted ($)","win_rate":"Win Rate","coverage":"% of Forecast"})
    .assign(**{
        "Raw ($)":       lambda d: d["Raw ($)"].map("${:,.0f}".format),
        "Weighted ($)":  lambda d: d["Weighted ($)"].map("${:,.0f}".format),
        "Win Rate":      lambda d: d["Win Rate"].map("{:.0%}".format),
        "% of Forecast": lambda d: d["% of Forecast"].map("{:.1%}".format),
    }),
    hide_index=True, use_container_width=True,
)
st.caption("Win rates: Prospecting 5% · Qualification 15% · Proposal 35% · Negotiation 65%. Replace with historical actuals.")
st.markdown("---")

# ── 02 Risk Signals ────────────────────────────────────────────────────────────
st.markdown(story_step("02", "Which risk signals are most prevalent in the current pipeline?"), unsafe_allow_html=True)

col_r1, col_r2, col_r3 = st.columns(3)
for col, signal, label, color, bg in [
    (col_r1, "is_past_due",       "Past Due",      "#C53A4A", "#FDEAED"),
    (col_r2, "is_stale",          "Stale (30d+)",  "#A15C00", "#FDF3E7"),
    (col_r3, "has_repeated_slip", "Repeated Slip", "#2E75B6", "#EAF1FB"),
]:
    n   = int(pipe_f[signal].sum())
    val = pipe_f.loc[pipe_f[signal], "pipeline_amount"].sum()
    pct = val / total_raw if total_raw else 0
    col.markdown(
        f'<div style="background:{bg};border-left:4px solid {color};'
        f'padding:14px 18px;border-radius:2px;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:{color};'
        f'text-transform:uppercase;letter-spacing:0.07em;">{label}</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:#1F3864;line-height:1.15;margin:4px 0 2px;">'
        f'{n} deals</div>'
        f'<div style="font-size:0.72rem;color:#555;">${val/1e6:.1f}M · {pct:.0%} of pipeline</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("")

risk_agg = pipe_f.groupby("pipeline_risk").agg(
    deals=("opportunity_id","nunique"), pipeline=("pipeline_amount","sum")
).reset_index()

# Identify top-risk segment for the title
top_risk_seg = (
    pipe_f[pipe_f["pipeline_risk"] == "High Risk"]
    .groupby("segment")["pipeline_amount"].sum()
    .idxmax() if (pipe_f["pipeline_risk"] == "High Risk").any() else "N/A"
)

risk_by_seg = pipe_f.groupby(["segment","pipeline_risk"])["pipeline_amount"].sum().reset_index()
fig_risk_seg = go.Figure()
for risk, color in RISK_COLORS.items():
    d = risk_by_seg[risk_by_seg["pipeline_risk"] == risk]
    if len(d):
        fig_risk_seg.add_trace(go.Bar(name=risk, x=d["segment"], y=d["pipeline_amount"]/1e6, marker_color=color))
layout_rseg = base_layout(height=280, margin=dict(t=44, b=10, l=8, r=8))
layout_rseg.update(dict(
    title=f"'{top_risk_seg}' carries the most high-risk pipeline — breakdown by segment",
    barmode="stack",
    yaxis=dict(title="Pipeline ($M)", gridcolor="#D9DEE7", linecolor="#D9DEE7", zeroline=False),
    legend=dict(orientation="h", x=0, y=-0.22, font=dict(size=10)),
))
fig_risk_seg.update_layout(layout_rseg)
st.plotly_chart(fig_risk_seg, use_container_width=True)

st.markdown("---")

# ── 03 Zombie Deals ────────────────────────────────────────────────────────────
st.markdown(story_step("03", "Which deals have gone silent and are inflating the pipeline number?"), unsafe_allow_html=True)

st.markdown(insight(
    f"<b>{len(zombie_90)} deals ({zombie_pct:.0%} of pipeline) have had no activity in 90+ days</b> "
    f"— ${zombie_val/1e6:.1f}M that almost certainly will not close this quarter. "
    f"Removing these from the active pipeline gives Finance a more accurate forecast."
), unsafe_allow_html=True)

col_da, col_db = st.columns(2)
with col_da:
    fig_age = go.Figure(go.Histogram(
        x=pipe_f["days_open"].dropna(), nbinsx=30,
        marker_color="#1F3864", opacity=0.8,
    ))
    fig_age.add_vline(x=median_open, line_dash="dash", line_color="#C55A11",
                      annotation_text=f"Median {median_open:.0f}d", annotation_position="top right")
    layout_age = base_layout(height=260, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
    layout_age.update(dict(title="How long have deals been in the pipeline?",
                           xaxis_title="Days Open", yaxis_title="Deals"))
    fig_age.update_layout(layout_age)
    st.plotly_chart(fig_age, use_container_width=True)

with col_db:
    fig_act = go.Figure(go.Histogram(
        x=pipe_f["days_since_last_activity"].dropna(), nbinsx=30,
        marker_color="#C55A11", opacity=0.8,
    ))
    fig_act.add_vline(x=30, line_dash="dash", line_color="#C55A11",
                      annotation_text="Stale (30d)", annotation_position="top right")
    fig_act.add_vline(x=90, line_dash="dash", line_color="#C00000",
                      annotation_text="Zombie (90d)", annotation_position="top right")
    layout_act = base_layout(height=260, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
    layout_act.update(dict(
        title=f"{zombie_pct:.0%} of deals have no activity in 90+ days — zombie territory",
        xaxis_title="Days Since Last Activity", yaxis_title="Deals",
    ))
    fig_act.update_layout(layout_act)
    st.plotly_chart(fig_act, use_container_width=True)

st.markdown(alert(
    f"<b>Action required: {len(zombie_90)} zombie deals, ${zombie_val/1e6:.1f}M at stake.</b> "
    f"RevOps should run a weekly hygiene sweep — mark as Lost or reassign to an active rep. "
    f"This also improves forecast accuracy: the {weight_ratio:.0%} weight ratio will improve "
    f"once zombie deals are removed from the denominator.",
    "danger"
), unsafe_allow_html=True)

st.markdown("---")

# ── Recommended Actions ────────────────────────────────────────────────────────
st.markdown(action_box([
    f"Zombie sweep (weekly): Mark or reassign {len(zombie_90)} deals with 90+ days no activity (${zombie_val/1e6:.1f}M).",
    f"Closing focus: Prioritise '{top_weighted_stage}' — highest weighted pipeline, best ROI on rep time.",
    f"Board forecast: Use ${total_weighted/1e6:.1f}M weighted (not ${total_raw/1e6:.1f}M raw) for exec reporting.",
    f"High-risk review: '{top_risk_seg}' segment needs a pipeline call — most high-risk concentration.",
    "Process: Set a 30-day activity SLA for all open deals; auto-flag violations for manager review.",
]), unsafe_allow_html=True)

