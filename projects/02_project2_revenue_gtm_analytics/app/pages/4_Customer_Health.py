"""
Customer Health & Retention Page
==================================
Story: NRR tells you if the base is growing.
       Health scores tell you who is about to churn.
       The priority list tells you who to call.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    HEALTH_COLORS,
    SEGMENT_COLORS,
    get_dim_account,
    get_fct_lifecycle,
    get_fct_revenue,
    get_stg_cs,
)
from utils.theme import (
    C_MUTED,
    NRR_COLORS,
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

st.set_page_config(page_title="Customer Health", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("Retention, churn & NRR")

# ── Load ───────────────────────────────────────────────────────────────────────
cs        = get_stg_cs()
revenue   = get_fct_revenue()
lifecycle = get_fct_lifecycle()
dim       = get_dim_account()

# ── Pre-compute ────────────────────────────────────────────────────────────────
pct_healthy  = (cs["health_tier"] == "Healthy").mean()
pct_at_risk  = (cs["health_tier"] == "At Risk").mean()
pct_churned  = cs["is_churned"].mean()
n_at_risk    = (cs["health_tier"] == "At Risk").sum()
median_score = cs[cs["customer_health_score"] > 0]["customer_health_score"].median()
cs_with_seg  = cs.merge(dim[["account_id","segment"]], on="account_id", how="left")

# NRR
rev_nrr    = revenue.groupby(["segment","nrr_category"]).agg(total=("collected_amount_usd","sum")).reset_index()
seg_pivot  = rev_nrr.pivot_table(index="segment", columns="nrr_category", values="total", fill_value=0).reset_index()
for col in ["Churned","Expansion","Retained"]:
    if col not in seg_pivot.columns: seg_pivot[col] = 0
cs_exp_seg = cs_with_seg.groupby("segment")["expansion_amount"].sum().reset_index()
seg_pivot  = seg_pivot.merge(cs_exp_seg, on="segment", how="left")
seg_pivot["starting"] = seg_pivot["Retained"] + seg_pivot["Expansion"]
seg_pivot["nrr"] = np.where(
    seg_pivot["starting"] > 0,
    (seg_pivot["starting"] + seg_pivot["expansion_amount"]) / seg_pivot["starting"],
    np.nan
)
total_retained = revenue.loc[revenue["nrr_category"] == "Retained","collected_amount_usd"].sum()
total_exp_rev  = revenue.loc[revenue["nrr_category"] == "Expansion","collected_amount_usd"].sum()
total_exp_arr  = cs["expansion_amount"].sum()
starting_rev   = total_retained + total_exp_rev
overall_nrr    = (starting_rev + total_exp_arr) / starting_rev if starting_rev > 0 else 0
nrr_valid      = seg_pivot.dropna(subset=["nrr"]).sort_values("nrr", ascending=True)

# Segment health
seg_health = cs_with_seg.groupby("segment").agg(
    accounts=("account_id","nunique"),
    avg_health=("customer_health_score","mean"),
    pct_healthy=("health_tier", lambda x: (x=="Healthy").sum()/len(x)),
    pct_at_risk=("health_tier", lambda x: (x=="At Risk").sum()/len(x)),
    churned=("is_churned","sum"),
).reset_index().sort_values("avg_health", ascending=False)
highest_risk_seg  = seg_health.nlargest(1,"pct_at_risk")["segment"].iloc[0]
highest_risk_pct  = seg_health.nlargest(1,"pct_at_risk")["pct_at_risk"].iloc[0]

# Churn top reason
churned_cs = cs[cs["is_churned"]].copy()
top_churn_reason = "N/A"
if "churn_reason" in churned_cs.columns and churned_cs["churn_reason"].notna().any():
    top_churn_reason = churned_cs["churn_reason"].value_counts().index[0]

# ── ① HERO ─────────────────────────────────────────────────────────────────────
st.title("Customer Health & Retention")

nrr_story = "the customer base is growing" if overall_nrr >= 1 else "churn is outpacing expansion"
st.markdown(hero(
    headline=f"Overall NRR is {overall_nrr:.0%} — {nrr_story}. "
             f"{n_at_risk} accounts score below 35 and are at risk of churning at renewal.",
    metric=f"{pct_healthy:.0%} healthy  ·  {pct_at_risk:.0%} at risk  ·  {pct_churned:.0%} churned",
    subtext=(
        f"Median health score: {median_score:.0f}/100 · "
        f"Highest-risk segment: {highest_risk_seg} ({highest_risk_pct:.0%} at-risk accounts) · "
        f"Top churn reason: '{top_churn_reason}'. "
        f"Use the priority list at the bottom as your CS outreach queue."
    ),
), unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi("Overall NRR", f"{overall_nrr:.0%}",
                    "Above 100% = existing base growing",
                    "good" if overall_nrr >= 1 else "bad"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Healthy Customers", f"{pct_healthy:.0%}",
                    f"Score ≥ 70 · {(cs['health_tier']=='Healthy').sum()} accounts", "good"),
                unsafe_allow_html=True)
with k3:
    st.markdown(kpi("At Risk", f"{pct_at_risk:.0%}",
                    f"Score < 35 · {n_at_risk} accounts need outreach", "bad"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("Churned", f"{pct_churned:.0%}",
                    f"{cs['is_churned'].sum()} accounts lost · '{top_churn_reason}'", "bad"),
                unsafe_allow_html=True)

st.markdown("---")

# ── 01 Health Score Distribution ─────────────────────────────────────────────
st.markdown(story_step("01", "How is the health score distributed across the customer base?"), unsafe_allow_html=True)

cs_valid  = cs[cs["customer_health_score"] > 0]
pct_below = (cs_valid["customer_health_score"] < 35).mean()

col_hist, col_pie = st.columns([3, 2])
with col_hist:
    fig_hist = go.Figure(go.Histogram(
        x=cs_valid["customer_health_score"], nbinsx=25,
        marker_color="#2E75B6", opacity=0.85,
    ))
    fig_hist.add_vline(x=70, line_dash="dash", line_color="#107C41", line_width=2,
                       annotation_text="Healthy (70)", annotation_position="top right")
    fig_hist.add_vline(x=35, line_dash="dash", line_color="#C00000", line_width=2,
                       annotation_text="At Risk (35)", annotation_position="top left")
    fig_hist.add_vline(x=median_score, line_dash="dot", line_color="#1F3864",
                       annotation_text=f"Median {median_score:.0f}", annotation_position="bottom right")
    layout_hist = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
    layout_hist.update(dict(
        title=f"Median {median_score:.0f}/100 — {pct_below:.0%} of accounts score below the at-risk threshold of 35",
        xaxis_title="Health Score (0–100)", yaxis_title="Customers",
    ))
    fig_hist.update_layout(layout_hist)
    st.plotly_chart(fig_hist, use_container_width=True)

with col_pie:
    tier_order  = ["Healthy", "Needs Attention", "At Risk"]
    tier_counts = cs["health_tier"].value_counts()
    tier_pcts   = {t: tier_counts.get(t, 0) / len(cs) for t in tier_order}
    fig_tier = go.Figure()
    for tier in tier_order:
        fig_tier.add_trace(go.Bar(
            name=tier, x=[tier_pcts[tier]], y=["Customers"],
            orientation="h",
            marker_color=HEALTH_COLORS.get(tier, "#6B7788"),
            text=f"{tier_pcts[tier]:.0%}",
            textposition="inside",
            insidetextanchor="middle",
        ))
    layout_tier = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8))
    layout_tier.update(dict(
        title="Health tier breakdown — most accounts are healthy or need attention",
        barmode="stack",
        xaxis=dict(tickformat=".0%", gridcolor="#D9DEE7", linecolor="#D9DEE7", zeroline=False),
        yaxis=dict(showticklabels=False),
        legend=dict(orientation="h", x=0, y=-0.22, font=dict(size=10)),
    ))
    fig_tier.update_layout(layout_tier)
    st.plotly_chart(fig_tier, use_container_width=True)

st.markdown("---")

# ── 02 Segment Risk ───────────────────────────────────────────────────────────
st.markdown(story_step("02", "Which segment is most at risk of churn and needs CS prioritisation?"), unsafe_allow_html=True)

st.markdown(insight(
    f"<b>{highest_risk_seg}</b> has the highest at-risk proportion ({highest_risk_pct:.0%}) — "
    f"CS should treat this segment as the highest priority for proactive outreach. "
    f"Segments where 'At Risk %' approaches 'Healthy %' have an unstable health distribution."
), unsafe_allow_html=True)

col_h1, col_h2 = st.columns(2)
with col_h1:
    segs    = seg_health["segment"].tolist()
    healthy = seg_health["pct_healthy"].tolist()
    at_risk = seg_health["pct_at_risk"].tolist()

    # Highlight the highest-risk segment's At Risk bar; others muted
    at_risk_colors = [
        "#C00000" if s == highest_risk_seg else C_MUTED
        for s in segs
    ]
    fig_seg_h = go.Figure()
    fig_seg_h.add_trace(go.Bar(name="Healthy",  x=segs, y=healthy,  marker_color="#107C41"))
    fig_seg_h.add_trace(go.Bar(name="At Risk",  x=segs, y=at_risk,  marker_color=at_risk_colors))
    layout_segh = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8))
    layout_segh.update(dict(
        title=f"'{highest_risk_seg}' has the most at-risk accounts — CS priority",
        barmode="group",
        yaxis=dict(title="% of Segment", tickformat=".0%", gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
        legend=dict(orientation="h", x=0, y=-0.24, font=dict(size=10)),
    ))
    fig_seg_h.update_layout(layout_segh)
    st.plotly_chart(fig_seg_h, use_container_width=True)

with col_h2:
    # Highlight below-threshold segments; others neutral
    avg_bar_colors = [
        "#C00000" if v < 70 else "#107C41"
        for v in seg_health["avg_health"]
    ]
    fig_avg = go.Figure(go.Bar(
        x=seg_health["segment"], y=seg_health["avg_health"],
        marker_color=avg_bar_colors,
        text=[f"{v:.0f}" for v in seg_health["avg_health"]], textposition="outside",
    ))
    fig_avg.add_hline(y=70, line_dash="dash", line_color="#737373",
                      annotation_text="Healthy threshold (70)", annotation_position="right")
    layout_avg = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
    layout_avg.update(dict(
        title="Segments below 70 avg score are at collective churn risk",
        yaxis=dict(title="Avg Score", range=[0,108], gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
    ))
    fig_avg.update_layout(layout_avg)
    st.plotly_chart(fig_avg, use_container_width=True)

st.markdown("---")

# ── 03 NRR ────────────────────────────────────────────────────────────────────
st.markdown(story_step("03", "Is the existing customer base growing or contracting in revenue?"), unsafe_allow_html=True)

nrr_growth_segs      = (nrr_valid["nrr"] >= 1).sum()
nrr_contraction_segs = (nrr_valid["nrr"] < 1).sum()

st.markdown(insight(
    f"Overall NRR is <b>{overall_nrr:.0%}</b>. "
    f"<b>{nrr_growth_segs}</b> segment(s) above 100% (expansion > churn). "
    f"<b>{nrr_contraction_segs}</b> segment(s) contracting. "
    f"Any segment below 100% needs either churn reduction or focused upsell — pick one."
), unsafe_allow_html=True)

col_nrr_a, col_nrr_b = st.columns([1, 2])
with col_nrr_a:
    st.markdown(kpi("Overall NRR", f"{overall_nrr:.0%}",
                    "Above 100% = existing customers growing in value",
                    "good" if overall_nrr >= 1 else "bad"), unsafe_allow_html=True)
    st.markdown("")
    for _, row in nrr_valid.iterrows():
        color = "#107C41" if row["nrr"] >= 1 else "#C00000"
        st.markdown(
            f"**{row['segment']}** — "
            f'<span style="color:{color};font-size:1.05rem;font-weight:700">{row["nrr"]:.0%}</span>',
            unsafe_allow_html=True,
        )

with col_nrr_b:
    # Highlight contraction segments in red, growth in green
    nrr_bar_colors = ["#107C41" if n >= 1 else "#C00000" for n in nrr_valid["nrr"]]
    fig_nrr = go.Figure(go.Bar(
        x=nrr_valid["nrr"], y=nrr_valid["segment"],
        orientation="h", marker_color=nrr_bar_colors,
        text=[f"{n:.0%}" for n in nrr_valid["nrr"]], textposition="outside",
    ))
    fig_nrr.add_vline(x=1.0, line_dash="dash", line_color="#1F3864",
                      annotation_text="100% break-even", annotation_position="top right")
    layout_nrr = base_layout(height=260, margin=dict(t=44, b=20, l=8, r=60), show_legend=False)
    layout_nrr.update(dict(
        title=f"NRR {overall_nrr:.0%} overall — segments left of the line are contracting",
        xaxis=dict(title="NRR", tickformat=".0%", gridcolor="#EBEBEB", linecolor="#CCCCCC",
                   zeroline=False, range=[0, max(nrr_valid["nrr"])*1.2]),
    ))
    fig_nrr.update_layout(layout_nrr)
    st.plotly_chart(fig_nrr, use_container_width=True)

st.caption("NRR = (retained + expansion revenue + upsell ARR) / (retained + expansion). Simplified — replace with ARR waterfall for board reporting.")
st.markdown("---")

# ── 04 Churn Reasons ──────────────────────────────────────────────────────────
st.markdown(story_step("04", "Why are customers leaving — and what can be done about it?"), unsafe_allow_html=True)

if "churn_reason" in churned_cs.columns and churned_cs["churn_reason"].notna().any():
    reasons = churned_cs["churn_reason"].value_counts().reset_index()
    reasons.columns = ["reason","count"]
    reasons["pct"] = reasons["count"] / reasons["count"].sum()
    top_reason     = reasons.iloc[0]["reason"]
    top_reason_pct = reasons.iloc[0]["pct"]

    st.markdown(insight(
        f"<b>'{top_reason}'</b> is the #1 churn reason at <b>{top_reason_pct:.0%}</b> of churned accounts. "
        f"This single root cause deserves a dedicated response — pricing/packaging, feature investment, "
        f"or competitive positioning — before investing in more acquisition."
    ), unsafe_allow_html=True)

    # Highlight top reason; others muted
    churn_colors = [
        "#C00000" if r == top_reason else C_MUTED
        for r in reasons["reason"].head(8)
    ]
    fig_churn = go.Figure(go.Bar(
        x=reasons["count"].head(8), y=reasons["reason"].head(8),
        orientation="h", marker_color=churn_colors,
        text=[f"{c:,} ({p:.0%})" for c,p in zip(reasons["count"].head(8), reasons["pct"].head(8))],
        textposition="outside",
    ))
    layout_churn = base_layout(height=270, margin=dict(t=44, b=20, l=8, r=120), show_legend=False)
    layout_churn.update(dict(
        title=f"'{top_reason}' (red) drives {top_reason_pct:.0%} of churn — fix this first",
        yaxis=dict(autorange="reversed", gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
        xaxis=dict(gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
    ))
    fig_churn.update_layout(layout_churn)
    st.plotly_chart(fig_churn, use_container_width=True)
else:
    st.markdown(alert("Churn reason data not available in this dataset.", "info"), unsafe_allow_html=True)

st.markdown("---")

# ── 05 At-Risk Priority List ──────────────────────────────────────────────────
st.markdown(story_step("05", "Which paying customers should CS contact first?"), unsafe_allow_html=True)

min_score = st.slider("Max health score to include", min_value=0, max_value=70, value=50, step=5)

at_risk_df = (
    lifecycle[
        (lifecycle["customer_health_score"].notna())
        & (lifecycle["customer_health_score"] <= min_score)
        & (lifecycle["is_churned"].fillna(False) == False)
        & (lifecycle["total_collected_usd"] > 0)
    ]
    .merge(cs[["account_id","renewal_date","days_to_renewal","churn_reason"]], on="account_id", how="left")
    .sort_values(["customer_health_score","days_to_renewal"])
)[["account_name","segment","health_tier","customer_health_score",
   "days_to_renewal","total_collected_usd","renewal_status","churn_reason"]
].rename(columns={
    "account_name":"Account", "segment":"Segment", "health_tier":"Health Tier",
    "customer_health_score":"Score", "days_to_renewal":"Days to Renewal",
    "total_collected_usd":"Collected ($)", "renewal_status":"Renewal Status",
    "churn_reason":"Churn Reason",
})

n_accounts   = len(at_risk_df)
at_risk_rev  = lifecycle[
    (lifecycle["customer_health_score"].notna())
    & (lifecycle["customer_health_score"] <= min_score)
    & (lifecycle["is_churned"].fillna(False) == False)
    & (lifecycle["total_collected_usd"] > 0)
]["total_collected_usd"].sum()

st.markdown(insight(
    f"<b>{n_accounts} paying accounts</b> (score ≤ {min_score}, not yet churned) "
    f"represent <b>${at_risk_rev/1e3:.0f}K in collected revenue</b> at risk. "
    f"Sort by 'Days to Renewal' to prioritise accounts whose contract ends soonest — "
    f"they have the least time before a churn decision is made."
), unsafe_allow_html=True)

if n_accounts:
    display = at_risk_df.head(20).copy()
    display["Score"]           = display["Score"].map("{:.0f}".format)
    display["Collected ($)"]   = display["Collected ($)"].map("${:,.0f}".format)
    display["Days to Renewal"] = display["Days to Renewal"].map(lambda x: f"{x:.0f}d" if x==x else "—")
    st.dataframe(display, hide_index=True, use_container_width=True, height=380)
    st.caption(
        f"Top 20 of {n_accounts} accounts shown. "
        "Source: fct_customer_lifecycle + stg_customer_success. Adjust slider to change threshold."
    )
else:
    st.markdown(alert("No accounts match the current filter.", "info"), unsafe_allow_html=True)

st.markdown("---")

# ── Recommended Actions ────────────────────────────────────────────────────────
st.markdown(action_box([
    f"CS outreach: Work through the {n_accounts} at-risk accounts above — start with those renewing in < 90 days.",
    f"Segment focus: {highest_risk_seg} has the most at-risk accounts ({highest_risk_pct:.0%}) — assign dedicated CSM coverage.",
    f"Retention strategy: Address '{top_churn_reason}' head-on — it drives the most churn. Assign a product/commercial owner.",
    f"Expansion: Focus upsell effort on the Healthy tier ({pct_healthy:.0%} of base) — highest conversion probability.",
    "Automation: Trigger a CS alert when any account's health score drops below 50 mid-term, not just at renewal.",
]), unsafe_allow_html=True)

