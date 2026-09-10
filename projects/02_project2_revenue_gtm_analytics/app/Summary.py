"""
Revenue Intelligence Dashboard — Home
======================================
Story: CRM bookings overstate cash. Three structural gaps explain the difference.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    get_dim_account,
    get_fct_pipeline,
    get_gtm_funnel,
    get_overview_metrics,
    get_revenue_chain,
    get_stg_cs,
)
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

st.set_page_config(page_title="Revenue Intelligence", layout="wide", initial_sidebar_state="expanded")
inject_css(st)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("B2B GTM & Revenue Analytics")

# ── Load ───────────────────────────────────────────────────────────────────────
metrics  = get_overview_metrics()
chain    = get_revenue_chain()
pipeline = get_fct_pipeline()

# GTM signal
gtm          = get_gtm_funnel()
_total       = len(gtm)
_with_lead   = int(gtm["has_lead"].sum())
_with_opp    = int(gtm["has_opportunity"].sum())
_with_won    = int(gtm["has_won_opportunity"].sum())
_stages      = ["All Accounts", "Has Lead", "MQL+", "SQL+", "Has Opportunity", "Closed-Won"]
_counts      = [_total, _with_lead,
                int((gtm["max_lifecycle_rank"] >= 2).sum()),
                int((gtm["max_lifecycle_rank"] >= 3).sum()),
                _with_opp, _with_won]
_drops       = [_counts[i-1] - _counts[i] for i in range(1, len(_counts))]
_biggest_drop_stage = _stages[_drops.index(max(_drops)) + 1]
gtm_win_rate = _with_won / _total if _total else 0
lead_to_opp  = _with_opp / max(_with_lead, 1)
opp_to_won   = _with_won / max(_with_opp, 1)

# Customer Health signal
cs           = get_stg_cs()
n_at_risk    = int((cs["health_tier"] == "At Risk").sum())
pct_at_risk  = (cs["health_tier"] == "At Risk").mean()
pct_healthy  = metrics["pct_healthy"]
pct_churned  = metrics["pct_churned"]

e2e_rate      = chain["collected"] / chain["crm_bookings"]
gap_pct       = 1 - e2e_rate
gap1          = chain["crm_bookings"] - chain["contract_value"]
gap2          = chain["contract_value"] - chain["billed"]
gap3          = chain["billed"] - chain["collected"]
gap1_pct      = gap1 / chain["crm_bookings"]
gap3_pct      = gap3 / max(chain["billed"], 1)
high_risk_pct = metrics["high_risk_pct"]

# ── ① HERO ─────────────────────────────────────────────────────────────────────
st.title("Revenue Overview")

st.markdown(hero(
    headline=f"Only {e2e_rate:.0%} of CRM bookings reach the bank account — "
             f"${(chain['crm_bookings'] - chain['collected']) / 1e6:.1f}M disappears across three structural gaps.",
    metric=f"${chain['crm_bookings']/1e6:.1f}M booked  ·  ${chain['collected']/1e6:.1f}M collected",
    subtext=(
        f"Gap 1 — Discounts at signing: ${gap1/1e6:.1f}M ({gap1_pct:.0%}).  "
        f"Gap 2 — Unbilled contracts: ${gap2/1e6:.1f}M.  "
        f"Gap 3 — Payment risk: ${gap3/1e6:.1f}M ({gap3_pct:.0%} of billed).  "
        f"Use the navigation to diagnose each gap."
    ),
), unsafe_allow_html=True)

# ── Top-line KPIs ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi("CRM Bookings", f"${metrics['total_bookings']/1e6:.1f}M", "Closed-won (CRM)"), unsafe_allow_html=True)
with c2:
    coll_rate = metrics["collection_rate"]
    st.markdown(kpi("Collected Cash", f"${metrics['total_collected']/1e6:.1f}M",
                    f"{coll_rate:.0%} of bookings reached the bank (target: 90%+)",
                    "good" if coll_rate >= 0.90 else "bad"), unsafe_allow_html=True)
with c3:
    w_ratio = metrics["weighted_pipeline"] / metrics["total_open_pipeline"]
    st.markdown(kpi("Weighted Pipeline", f"${metrics['weighted_pipeline']/1e6:.1f}M",
                    f"{w_ratio:.0%} of ${metrics['total_open_pipeline']/1e6:.1f}M raw (healthy: 35%+)",
                    "good" if w_ratio >= 0.35 else "bad"),
                unsafe_allow_html=True)
with c4:
    st.markdown(kpi("High-Risk Pipeline", f"${metrics['high_risk_pipeline']/1e6:.1f}M",
                    f"{high_risk_pct:.0%} of pipeline at risk (target: <10%)",
                    "bad" if high_risk_pct > 0.10 else "neutral"), unsafe_allow_html=True)

st.markdown("---")

# ── 01 The Revenue Chain ───────────────────────────────────────────────────────
st.markdown(story_step("01", "Where does revenue disappear between booking and cash?"), unsafe_allow_html=True)

labels  = ["CRM Bookings", "Contract Value", "Billed", "Collected Cash"]
amounts = [chain["crm_bookings"], chain["contract_value"], chain["billed"], chain["collected"]]
pcts    = [a / chain["crm_bookings"] for a in amounts]

# Highlight the exception: Collected Cash (the outcome) in green; others muted → navy gradient
bar_colors = [C_MUTED, C_MUTED, C_MUTED, "#107C41"]
bar_colors[0] = "#1F3864"  # Bookings = starting anchor, navy

fig_chain = go.Figure()
fig_chain.add_trace(go.Bar(
    x=labels,
    y=[a / 1e6 for a in amounts],
    marker_color=bar_colors,
    text=[f"${a/1e6:.1f}M ({p:.0%})" for a, p in zip(amounts, pcts)],
    textposition="outside",
    width=0.5,
))
for i, (label, a_from, a_to) in enumerate(zip(
    [f"−${gap1/1e6:.1f}M\ndiscount", f"−${gap2/1e6:.1f}M\nunbilled", f"−${gap3/1e6:.1f}M\npayment risk"],
    amounts[:3], amounts[1:]
)):
    fig_chain.add_annotation(
        x=i + 0.5, y=max(amounts) / 1e6 * 0.46,
        text=label, showarrow=False,
        font=dict(size=9, color="#888"), align="center",
    )
layout = base_layout(height=340, margin=dict(t=40, b=20, l=8, r=8))
layout.update(dict(
    title=f"The outcome (Collected Cash) is {e2e_rate:.0%} of what was closed — the gap is structural, not random",
    yaxis_title="Amount ($M)", showlegend=False,
))
fig_chain.update_layout(layout)
st.plotly_chart(fig_chain, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(alert(
        f"<b>Gap 1 — Discount at signing:</b> ${gap1/1e6:.1f}M ({gap1_pct:.1%}) "
        f"given up when legal signs the negotiated price. "
        f"Sales enters a round number in CRM; the contract reflects the actual agreed amount.",
        "info"
    ), unsafe_allow_html=True)
    st.markdown(alert(
        f"<b>Gap 2 — Contract vs. Billed:</b> ${gap2/1e6:.1f}M not yet invoiced. "
        f"Monthly contracts bill incrementally — this gap closes over the contract term.",
        "info"
    ), unsafe_allow_html=True)
with col_b:
    st.markdown(alert(
        f"<b>Gap 3 — Payment risk:</b> ${gap3/1e6:.1f}M outstanding. "
        f"${chain['failed']/1e6:.1f}M in <b>failed payments</b> (card declined / bank rejected) "
        f"and ${chain['at_risk']/1e6:.1f}M pending. Failed invoices need immediate action.",
        "danger"
    ), unsafe_allow_html=True)
    st.markdown(alert(
        f"<b>End-to-end rate: {e2e_rate:.0%}</b> — "
        f"For every $1.00 closed in the CRM, ${e2e_rate:.2f} is collected as cash. "
        f"B2B SaaS benchmark: 85–90%. Use Revenue Reconciliation to diagnose.",
        "success"
    ), unsafe_allow_html=True)

st.markdown("---")

# ── 02 Pipeline Risk ───────────────────────────────────────────────────────────
st.markdown(story_step("02", "How much of the open pipeline is actually closeable this quarter?"), unsafe_allow_html=True)

risk_agg = pipeline.groupby("pipeline_risk").agg(
    deals=("opportunity_id", "nunique"),
    pipeline=("pipeline_amount", "sum"),
).reset_index()
total_pipeline = pipeline["pipeline_amount"].sum()

r1, r2, r3 = st.columns(3)
for col, risk, color, bg in zip(
    [r1, r2, r3],
    ["On Track", "Medium Risk", "High Risk"],
    ["#107C41",  "#C55A11",     "#C00000"],
    ["#E8F4EE",  "#FDF3EC",     "#FDE9E9"],
):
    row = risk_agg[risk_agg["pipeline_risk"] == risk]
    if len(row):
        val = row["pipeline"].iloc[0]
        cnt = int(row["deals"].iloc[0])
        pct = val / total_pipeline
        col.markdown(
            f'<div style="background:{bg};border-left:4px solid {color};'
            f'padding:14px 18px;border-radius:2px;">'
            f'<div style="font-size:0.68rem;font-weight:700;color:{color};'
            f'text-transform:uppercase;letter-spacing:0.07em;">{risk}</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:#1F3864;line-height:1.15;margin:4px 0 2px;">'
            f'${val/1e6:.1f}M</div>'
            f'<div style="font-size:0.72rem;color:#555;">{pct:.0%} of pipeline &nbsp;·&nbsp; {cnt} deals</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown(insight(
    f"<b>{high_risk_pct:.0%} of pipeline is flagged high-risk</b> — past-due close date AND repeated slippage. "
    f"This portion is unlikely to close without direct intervention. "
    f"Open the <b>Pipeline page</b> for a deal-level breakdown and zombie deal list."
), unsafe_allow_html=True)

st.markdown("---")

# ── 03 Business Health Snapshot ────────────────────────────────────────────────
st.markdown(story_step("03", "Is the business healthy — funnel, pipeline, and customer base?"), unsafe_allow_html=True)

snap_gtm, snap_health = st.columns(2)

with snap_gtm:
    gtm_status = "good" if gtm_win_rate >= 0.25 else "bad"
    gtm_color  = "#087F5B" if gtm_status == "good" else "#C53A4A"
    st.markdown(
        f'<div style="background:#F7F8FA;border:1px solid #D9DEE7;border-left:4px solid {gtm_color};'
        f'padding:16px 20px;border-radius:2px;">'
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{gtm_color};margin-bottom:8px;">GTM Funnel</div>'
        f'<div style="font-size:1.6rem;font-weight:700;color:#1F3864;line-height:1.1;">'
        f'{gtm_win_rate:.0%} end-to-end win rate</div>'
        f'<div style="font-size:0.75rem;color:#4E5B6B;margin-top:6px;line-height:1.6;">'
        f'Biggest drop: <b>{_biggest_drop_stage}</b><br>'
        f'Lead → Opp: {lead_to_opp:.0%} &nbsp;·&nbsp; Opp → Won: {opp_to_won:.0%}<br>'
        f'<span style="color:{gtm_color};font-weight:600;">'
        f'{"On track — above 25% threshold" if gtm_status == "good" else "Below 25% — funnel needs attention"}'
        f'</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with snap_health:
    health_color = "#087F5B" if pct_churned < 0.20 and pct_at_risk < 0.10 else "#C53A4A"
    st.markdown(
        f'<div style="background:#F7F8FA;border:1px solid #D9DEE7;border-left:4px solid {health_color};'
        f'padding:16px 20px;border-radius:2px;">'
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{health_color};margin-bottom:8px;">Customer Health</div>'
        f'<div style="font-size:1.6rem;font-weight:700;color:#1F3864;line-height:1.1;">'
        f'{pct_healthy:.0%} healthy accounts</div>'
        f'<div style="font-size:0.75rem;color:#4E5B6B;margin-top:6px;line-height:1.6;">'
        f'At Risk: {pct_at_risk:.0%} ({n_at_risk} accounts need outreach)<br>'
        f'Churned: {pct_churned:.0%} of base<br>'
        f'<span style="color:{health_color};font-weight:600;">'
        f'{"Base stable — expand CS coverage on at-risk accounts" if pct_churned < 0.20 else "Churn rate elevated — CS intervention required"}'
        f'</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown("")
st.markdown("---")

# ── Recommended Actions ────────────────────────────────────────────────────────
st.markdown(action_box([
    f"Collections (urgent): Follow up on ${chain['failed']/1e6:.1f}M in failed payments — highest-ROI cash recovery action.",
    f"RevOps: Review ${metrics['high_risk_pipeline']/1e6:.1f}M High-Risk pipeline — mark stale deals Lost or reassign to active reps.",
    f"Finance: The {gap1_pct:.0%} average discount rate may warrant a deal-approval policy for large Enterprise discounts.",
    "Explore: Use GTM Funnel to find where pipeline starts, Revenue Reconciliation to track gaps, Customer Health for retention risk.",
]), unsafe_allow_html=True)

