"""
GTM Funnel Page
===============
Story: The funnel converts a small fraction of accounts.
       Find where it leaks and which sources are worth investing in.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import SEGMENT_COLORS, get_fct_lifecycle, get_gtm_funnel, get_stg_leads, get_stg_opps
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

st.set_page_config(page_title="GTM Funnel", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("Lead-to-close funnel analysis")

# ── Load ───────────────────────────────────────────────────────────────────────
gtm   = get_gtm_funnel()
leads = get_stg_leads()
opps  = get_stg_opps()

# ── Filter ─────────────────────────────────────────────────────────────────────
segs    = ["All"] + sorted(gtm["segment"].dropna().unique().tolist())
sel_seg = st.selectbox("Segment", segs)
gtm_f   = gtm if sel_seg == "All" else gtm[gtm["segment"] == sel_seg]

# ── Pre-compute ────────────────────────────────────────────────────────────────
total     = len(gtm_f)
with_lead = int(gtm_f["has_lead"].sum())
mql_plus  = int((gtm_f["max_lifecycle_rank"] >= 2).sum())
sql_plus  = int((gtm_f["max_lifecycle_rank"] >= 3).sum())
with_opp  = int(gtm_f["has_opportunity"].sum())
with_won  = int(gtm_f["has_won_opportunity"].sum())

stages = ["All Accounts", "Has Lead", "MQL+", "SQL+", "Has Opportunity", "Closed-Won"]
counts = [total, with_lead, mql_plus, sql_plus, with_opp, with_won]

# Find the biggest absolute drop between consecutive stages
drops = [counts[i-1] - counts[i] for i in range(1, len(counts))]
biggest_drop_idx = drops.index(max(drops)) + 1   # index in stages/counts
biggest_drop_stage = stages[biggest_drop_idx]

lead_to_opp_rate = with_opp / max(with_lead, 1)
opp_to_won_rate  = with_won / max(with_opp, 1)
overall_win_rate = with_won / max(total, 1)

# ── ① HERO ─────────────────────────────────────────────────────────────────────
st.title("GTM Funnel Analysis")

st.markdown(hero(
    headline=f"Only {overall_win_rate:.0%} of accounts close as won revenue — "
             f"the funnel loses {total - with_won:,} accounts between first touch and close.",
    metric=f"{with_won:,} accounts won  ·  {lead_to_opp_rate:.0%} Lead → Opp  ·  {opp_to_won_rate:.0%} Opp → Won",
    subtext=(
        f"Biggest single drop: <b>{biggest_drop_stage}</b> "
        f"({counts[biggest_drop_idx-1]:,} → {counts[biggest_drop_idx]:,}, "
        f"−{drops[biggest_drop_idx-1]:,} accounts). "
        f"Fixing this stage has the highest leverage on overall revenue."
    ),
), unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(kpi("Lead Coverage", f"{with_lead/total:.0%}", f"{with_lead:,} accounts with ≥1 lead"), unsafe_allow_html=True)
with m2:
    st.markdown(kpi("Lead to Opp", f"{lead_to_opp_rate:.0%}",
                    "Biggest conversion lever", "bad" if lead_to_opp_rate < 0.30 else "neutral"),
                unsafe_allow_html=True)
with m3:
    st.markdown(kpi("Opp to Won", f"{opp_to_won_rate:.0%}",
                    "Sales close rate", "good" if opp_to_won_rate > 0.40 else "neutral"),
                unsafe_allow_html=True)
with m4:
    st.markdown(kpi("Accounts Won", f"{with_won:,}",
                    f"{overall_win_rate:.0%} end-to-end win rate"), unsafe_allow_html=True)

st.markdown("---")

# ── 01 Funnel Leak ─────────────────────────────────────────────────────────────
st.markdown(story_step("01", "Where does the funnel lose the most accounts?"), unsafe_allow_html=True)

# Highlight the exception: biggest drop stage = RED, Closed-Won = GREEN, others = MUTED
f_colors = []
for i in range(len(stages)):
    if i == len(stages) - 1:          # Closed-Won → outcome, highlight green
        f_colors.append("#107C41")
    elif i == biggest_drop_idx:        # Biggest drop destination → red alert
        f_colors.append("#C00000")
    elif i == 0:                       # All Accounts → anchor, navy
        f_colors.append("#1F3864")
    else:
        f_colors.append(C_MUTED)

fig_funnel = go.Figure(go.Funnel(
    y=stages,
    x=counts,
    marker_color=f_colors,
    textinfo="value+percent initial",
    textposition="inside",
    connector=dict(line=dict(color="#D9DEE7", width=1)),
))
layout_f = base_layout(height=340, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
layout_f.update(dict(
    title=f"'{biggest_drop_stage}' is the critical drop — "
          f"{counts[biggest_drop_idx-1]:,} accounts enter, only {counts[biggest_drop_idx]:,} advance",
    funnelmode="stack",
))
fig_funnel.update_layout(layout_f)
st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")

# ── 02 Lead Source Quality ────────────────────────────────────────────────────
st.markdown(story_step("02", "Which lead sources generate the most closeable pipeline?"), unsafe_allow_html=True)

leads_f = leads if sel_seg == "All" else leads[leads["segment"] == sel_seg]
vol = (
    leads_f.groupby("lead_source")
    .agg(lead_count=("lead_id", "nunique"), sql_count=("is_sales_qualified", "sum"))
    .reset_index()
)
vol["sql_rate"] = vol["sql_count"] / vol["lead_count"]

won_src = (
    gtm_f[gtm_f["primary_lead_source"].notna()]
    .groupby("primary_lead_source")
    .agg(
        accounts=("account_id", "nunique"),
        won_accounts=("has_won_opportunity", "sum"),
        total_won=("total_won_amount", "sum"),
    )
    .reset_index()
    .rename(columns={"primary_lead_source": "lead_source"})
)
won_src["win_rate"] = won_src["won_accounts"] / won_src["accounts"]
won_src["avg_deal"] = won_src["total_won"] / won_src["won_accounts"].replace(0, np.nan)

src = vol.merge(won_src, on="lead_source", how="left").sort_values("total_won", ascending=False)
src_sorted = src.dropna(subset=["win_rate"]).sort_values("win_rate", ascending=True)

top_by_winrate = src_sorted.iloc[-1]   # Highest win rate
top_by_revenue = src.dropna(subset=["total_won"]).nlargest(1, "total_won").iloc[0]

st.markdown(insight(
    f"<b>{top_by_winrate['lead_source']}</b> has the highest win rate "
    f"({top_by_winrate['win_rate']:.0%}). "
    f"<b>{top_by_revenue['lead_source']}</b> generates the most won revenue "
    f"(${top_by_revenue['total_won']/1e6:.1f}M). "
    f"If different, invest in the high-win-rate source — it converts more efficiently per lead."
), unsafe_allow_html=True)

col_chart, col_table = st.columns([3, 2])
with col_chart:
    # Highlight the exception: top win-rate source in navy, others muted
    bar_colors_src = [
        "#1F3864" if row["lead_source"] == top_by_winrate["lead_source"] else C_MUTED
        for _, row in src_sorted.iterrows()
    ]
    fig_src = go.Figure(go.Bar(
        y=src_sorted["lead_source"],
        x=src_sorted["win_rate"],
        orientation="h",
        marker_color=bar_colors_src,
        text=[f"{r:.0%}" for r in src_sorted["win_rate"]],
        textposition="outside",
    ))
    layout_src = base_layout(height=300, margin=dict(t=44, b=20, l=8, r=80), show_legend=False)
    layout_src.update(dict(
        title=f"'{top_by_winrate['lead_source']}' has the best win rate — see Won $ column for revenue",
        xaxis=dict(title="Win Rate", tickformat=".0%", gridcolor="#D9DEE7", linecolor="#D9DEE7", zeroline=False),
    ))
    fig_src.update_layout(layout_src)
    st.plotly_chart(fig_src, use_container_width=True)

with col_table:
    st.markdown("**Source Performance**")
    display_src = src[["lead_source", "lead_count", "sql_rate", "win_rate", "total_won"]].copy()
    display_src.columns = ["Source", "Leads", "SQL %", "Win %", "Won $"]
    display_src["SQL %"]  = display_src["SQL %"].map("{:.0%}".format)
    display_src["Win %"]  = display_src["Win %"].map(lambda x: f"{x:.0%}" if x == x else "—")
    display_src["Won $"]  = display_src["Won $"].map(lambda x: f"${x/1e6:.1f}M" if x == x else "—")
    display_src["Leads"]  = display_src["Leads"].map("{:,}".format)
    st.dataframe(display_src, hide_index=True, use_container_width=True, height=280)
    st.caption("Win % = won accounts ÷ total accounts with that source")

st.markdown("---")

# ── 03 Segment Conversion ─────────────────────────────────────────────────────
st.markdown(story_step("03", "Which segment converts most efficiently from lead to close?"), unsafe_allow_html=True)

seg_f = (
    gtm.groupby("segment")
    .agg(
        accounts=("account_id", "nunique"),
        has_lead=("has_lead", "sum"),
        has_opp=("has_opportunity", "sum"),
        has_won=("has_won_opportunity", "sum"),
        total_won=("total_won_amount", "sum"),
    )
    .reset_index()
)
seg_f["lead_rate"] = seg_f["has_lead"] / seg_f["accounts"]
seg_f["opp_rate"]  = seg_f["has_opp"]  / seg_f["accounts"]
seg_f["win_rate"]  = seg_f["has_won"]  / seg_f["accounts"]
seg_f["avg_deal"]  = seg_f["total_won"] / seg_f["has_won"].replace(0, np.nan)

top_win_seg  = seg_f.nlargest(1, "win_rate")["segment"].iloc[0]
top_deal_seg = seg_f.nlargest(1, "avg_deal")["segment"].iloc[0]

st.markdown(insight(
    f"<b>{top_win_seg}</b> has the highest win rate. "
    f"<b>{top_deal_seg}</b> has the largest average deal. "
    f"Optimal SDR allocation = win rate × avg deal size — prioritise the segment with the highest expected revenue per lead."
), unsafe_allow_html=True)

segs_order = seg_f.sort_values("win_rate", ascending=False)["segment"].tolist()

col_v, col_s = st.columns(2)
with col_v:
    fig_conv = go.Figure()
    for metric, color, name in [
        ("lead_rate", C_MUTED,   "Lead Coverage"),
        ("opp_rate",  "#C55A11", "Opp Rate"),
        ("win_rate",  "#107C41", "Win Rate"),
    ]:
        fig_conv.add_trace(go.Bar(
            name=name,
            x=segs_order,
            y=[seg_f.set_index("segment").loc[s, metric] for s in segs_order],
            marker_color=color,
        ))
    layout_conv = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8))
    layout_conv.update(dict(
        title=f"Win Rate (green) is the key outcome — {top_win_seg} leads",
        barmode="group",
        yaxis=dict(title="Rate", tickformat=".0%", gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
        legend=dict(orientation="h", x=0, y=-0.28, font=dict(size=10)),
    ))
    fig_conv.update_layout(layout_conv)
    st.plotly_chart(fig_conv, use_container_width=True)

with col_s:
    lc  = get_fct_lifecycle()[["segment", "lead_to_opp_days", "lead_to_close_days"]].dropna(subset=["lead_to_close_days"])
    vel = lc.groupby("segment").agg(l2o=("lead_to_opp_days","median"), l2c=("lead_to_close_days","median")).reset_index()

    fig_vel = go.Figure()
    fig_vel.add_trace(go.Bar(name="Lead → Opp (days)",   x=vel["segment"], y=vel["l2o"], marker_color=C_MUTED))
    fig_vel.add_trace(go.Bar(name="Lead → Close (days)", x=vel["segment"], y=vel["l2c"], marker_color="#1F3864", opacity=0.85))
    layout_vel = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8))
    layout_vel.update(dict(
        title="Longer cycles = larger deals — watch Enterprise velocity",
        barmode="overlay",
        yaxis_title="Median Days",
        legend=dict(orientation="h", x=0, y=-0.28, font=dict(size=10)),
    ))
    fig_vel.update_layout(layout_vel)
    st.plotly_chart(fig_vel, use_container_width=True)

st.markdown("---")

# ── 04 Data Quality ───────────────────────────────────────────────────────────
st.markdown(story_step("04", "What data quality issues are distorting these funnel metrics?"), unsafe_allow_html=True)

unmatched = leads[~leads["has_account"]]
orphan    = opps[opps["is_orphan"]]

dq1, dq2 = st.columns(2)
with dq1:
    st.markdown(alert(
        f"<b>{len(unmatched):,} unmatched leads ({len(unmatched)/len(leads):.1%})</b> have no account_id. "
        f"Marketing spend on these leads is invisible to pipeline reporting. "
        f"Fix: enforce account matching at the lead capture form.",
        "warning"
    ), unsafe_allow_html=True)
with dq2:
    st.markdown(alert(
        f"<b>{len(orphan):,} orphan opportunities</b> reference accounts that do not exist in Salesforce. "
        f"Combined pipeline: <b>${orphan['amount'].sum():,.0f}</b>. "
        f"Fix: RevOps to reassign before the next forecast cycle.",
        "warning"
    ), unsafe_allow_html=True)

st.markdown("---")

# ── Recommended Actions ────────────────────────────────────────────────────────
st.markdown(action_box([
    f"Priority fix: '{biggest_drop_stage}' is the biggest funnel leak — investigate qualification criteria or SDR capacity at that stage.",
    f"Lead source investment: Shift budget toward '{top_by_winrate['lead_source']}' (highest win rate at {top_by_winrate['win_rate']:.0%}).",
    f"Marketing Ops: Fix {len(unmatched):,} unmatched leads — enforce account_id capture at form submission.",
    f"RevOps: Reassign {len(orphan):,} orphan opportunities (${orphan['amount'].sum()/1e3:.0f}K) to valid accounts.",
    f"SDR focus: {top_win_seg} (best win rate) × {top_deal_seg} (largest deals) = highest-priority segments.",
]), unsafe_allow_html=True)

st.caption("Definitions: SQL = Sales Qualified Lead (lifecycle rank ≥ 3). Win rate = won accounts ÷ total accounts with that source.")
