"""
Revenue Reconciliation Page
============================
Story: Three structural gaps explain why Finance sees less than Sales.
       The most urgent gap is failed payments — cash already billed but not collected.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import SEGMENT_COLORS, get_fct_bookings, get_fct_revenue, get_revenue_chain
from utils.theme import (
    C_MUTED,
    PAYMENT_COLORS,
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

st.set_page_config(page_title="Revenue Reconciliation", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("Bookings-to-cash gap analysis")

# ── Load ───────────────────────────────────────────────────────────────────────
bookings = get_fct_bookings()
revenue  = get_fct_revenue()
chain    = get_revenue_chain()

gap1        = chain["crm_bookings"] - chain["contract_value"]
gap2        = chain["contract_value"] - chain["billed"]
gap3        = chain["billed"] - chain["collected"]
at_risk_tot = chain["at_risk"] + chain["failed"]
gap1_pct    = gap1 / chain["crm_bookings"]
gap3_pct    = gap3 / max(chain["billed"], 1)
e2e_rate    = chain["collected"] / chain["crm_bookings"]

# Largest gap by value
gaps = {"Discount": gap1, "Billing Lag": gap2, "Payment Risk": gap3}
largest_gap_name = max(gaps, key=gaps.get)
largest_gap_val  = gaps[largest_gap_name]

# ── ① HERO ─────────────────────────────────────────────────────────────────────
st.title("Revenue Reconciliation")

st.markdown(hero(
    headline=f"${at_risk_tot/1e6:.1f}M in outstanding payments requires immediate collections action — "
             f"${chain['failed']/1e6:.1f}M has already failed.",
    metric=f"{e2e_rate:.0%} end-to-end cash rate  ·  ${(chain['crm_bookings']-chain['collected'])/1e6:.1f}M gap",
    subtext=(
        f"Gap breakdown: ${gap1/1e6:.1f}M in discounts at signing ({gap1_pct:.0%}) · "
        f"${gap2/1e6:.1f}M in unbilled contracts · "
        f"${gap3/1e6:.1f}M in payment risk ({gap3_pct:.0%} of billed). "
        f"The payment risk gap is the only one requiring active recovery."
    ),
), unsafe_allow_html=True)

g1, g2, g3, g4 = st.columns(4)
with g1:
    st.markdown(kpi("Booked (CRM)", f"${chain['crm_bookings']/1e6:.2f}M", "Starting point"), unsafe_allow_html=True)
with g2:
    st.markdown(kpi("Gap 1 — Discount", f"-${gap1/1e6:.2f}M",
                    f"{gap1_pct:.1%} given up at signing", "bad"), unsafe_allow_html=True)
with g3:
    st.markdown(kpi("Gap 2 — Billing Lag", f"-${gap2/1e6:.2f}M",
                    "Unbilled contract value · closes over time"), unsafe_allow_html=True)
with g4:
    st.markdown(kpi("Gap 3 — Payment Risk", f"-${gap3/1e6:.2f}M",
                    f"${chain['failed']/1e6:.1f}M failed · ${chain['at_risk']/1e6:.1f}M pending", "bad"),
                unsafe_allow_html=True)

st.markdown("---")

# ── 01 Revenue Waterfall ──────────────────────────────────────────────────────
st.markdown(story_step("01", "How much of each closed deal reaches the bank account?"), unsafe_allow_html=True)

labels  = ["CRM Bookings", "Contract Value", "Billed", "Collected Cash"]
amounts = [chain["crm_bookings"], chain["contract_value"], chain["billed"], chain["collected"]]
pcts    = [a / chain["crm_bookings"] for a in amounts]

# Highlight: Collected Cash (outcome) = green; others follow severity gradient
colors = ["#1F3864", C_MUTED, C_MUTED, "#107C41"]

fig_wf = go.Figure(go.Bar(
    x=labels, y=[a/1e6 for a in amounts],
    marker_color=colors,
    text=[f"${a/1e6:.2f}M ({p:.0%})" for a, p in zip(amounts, pcts)],
    textposition="outside", width=0.5,
))
layout_wf = base_layout(height=320, margin=dict(t=44, b=20, l=8, r=40), show_legend=False)
layout_wf.update(dict(
    title=f"${largest_gap_val/1e6:.1f}M lost to {largest_gap_name} — the largest single gap in this dataset",
    yaxis_title="Amount ($M)",
    yaxis=dict(gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False, range=[0, max(amounts)/1e6*1.25]),
))
fig_wf.update_layout(layout_wf)
st.plotly_chart(fig_wf, use_container_width=True)

st.markdown("---")

# ── 02 Discount Analysis ──────────────────────────────────────────────────────
st.markdown(story_step("02", "Are discounts at signing within acceptable policy limits?"), unsafe_allow_html=True)

has_contract = bookings[bookings["has_contract"]].copy()
seg_disc = (
    has_contract.groupby("segment")
    .agg(total_bookings=("crm_booking_amount","sum"), total_contracted=("contract_value","sum"), deals=("opportunity_id","nunique"))
    .reset_index()
)
seg_disc["avg_discount"] = (seg_disc["total_bookings"] - seg_disc["total_contracted"]) / seg_disc["total_bookings"]
seg_disc = seg_disc.sort_values("avg_discount", ascending=False)
top_disc_seg = seg_disc.iloc[0]["segment"]
top_disc_pct = seg_disc.iloc[0]["avg_discount"]

st.markdown(insight(
    f"<b>{top_disc_seg}</b> carries the highest average discount at <b>{top_disc_pct:.1%}</b>. "
    f"Heavy discounts (>15%) erode margin and may indicate end-of-quarter pressure or weak qualification. "
    f"Any deal in the 'Heavy Discount' tier should require VP approval."
), unsafe_allow_html=True)

col_disc_l, col_disc_r = st.columns(2)
with col_disc_l:
    tier_order = ["No Discount", "Minor Discount (<5%)", "Moderate Discount (5-15%)",
                  "Heavy Discount (>15%)", "Contract Exceeds Booking"]
    tier_counts = (
        has_contract["discount_tier"].value_counts()
        .reindex(tier_order).dropna().reset_index()
    )
    tier_counts.columns = ["tier", "count"]

    # Highlight the exception: Heavy Discount = red, No Discount = green, rest = muted
    tier_colors = []
    for t in tier_counts["tier"]:
        if t == "Heavy Discount (>15%)":       tier_colors.append("#C00000")
        elif t == "No Discount":               tier_colors.append("#107C41")
        elif t == "Contract Exceeds Booking":  tier_colors.append("#2E75B6")
        else:                                  tier_colors.append(C_MUTED)

    fig_disc = go.Figure(go.Bar(
        x=tier_counts["count"], y=tier_counts["tier"],
        orientation="h", marker_color=tier_colors,
        text=tier_counts["count"].map("{:,}".format), textposition="outside",
    ))
    layout_disc = base_layout(height=250, margin=dict(t=44, b=20, l=8, r=60), show_legend=False)
    layout_disc.update(dict(
        title="Heavy discounts (red) are the exception — flag for VP review",
        xaxis_title="Deals",
        yaxis=dict(autorange="reversed", gridcolor="#EBEBEB", linecolor="#CCCCCC", zeroline=False),
    ))
    fig_disc.update_layout(layout_disc)
    st.plotly_chart(fig_disc, use_container_width=True)

with col_disc_r:
    # Highlight the exception: top discount segment = red bar, others = muted
    seg_bar_colors = [
        "#C00000" if s == top_disc_seg else C_MUTED
        for s in seg_disc["segment"]
    ]
    fig_disc_seg = go.Figure(go.Bar(
        x=seg_disc["segment"], y=seg_disc["avg_discount"],
        marker_color=seg_bar_colors,
        text=[f"{v:.1%}" for v in seg_disc["avg_discount"]], textposition="outside",
    ))
    fig_disc_seg.add_hline(y=0.10, line_dash="dash", line_color="#C00000",
                           annotation_text="10% policy threshold", annotation_position="right")
    layout_disc_seg = base_layout(height=250, margin=dict(t=44, b=20, l=8, r=8), show_legend=False)
    layout_disc_seg.update(dict(
        title=f"{top_disc_seg} (red) averages {top_disc_pct:.0%} discount — check against policy",
        yaxis=dict(title="Avg Discount %", tickformat=".0%", gridcolor="#EBEBEB",
                   linecolor="#CCCCCC", zeroline=False),
    ))
    fig_disc_seg.update_layout(layout_disc_seg)
    st.plotly_chart(fig_disc_seg, use_container_width=True)

st.markdown("---")

# ── 03 Payment Risk ────────────────────────────────────────────────────────────
st.markdown(story_step("03", "Which invoices are at risk of not being collected?"), unsafe_allow_html=True)

seg_pay = revenue.groupby("segment").agg(
    billed=("billing_amount_usd","sum"), collected=("collected_amount_usd","sum"), failed=("failed_amount_usd","sum")
).reset_index()
seg_pay["collection_rate"] = seg_pay["collected"] / seg_pay["billed"]
avg_rate   = seg_pay["collected"].sum() / seg_pay["billed"].sum()
lowest_seg = seg_pay.nsmallest(1, "collection_rate")["segment"].iloc[0]
lowest_rate= seg_pay.nsmallest(1, "collection_rate")["collection_rate"].iloc[0]

st.markdown(insight(
    f"<b>${chain['failed']/1e6:.1f}M in failed payments</b> is the highest-priority recovery item — "
    f"this cash was billed but the payment was declined. "
    f"<b>{lowest_seg}</b> has the lowest collection rate at <b>{lowest_rate:.0%}</b> "
    f"(avg: {avg_rate:.0%})."
), unsafe_allow_html=True)

col_pay_l, col_pay_r = st.columns(2)
with col_pay_l:
    pay_agg = revenue.groupby("payment_status").agg(
        count=("invoice_id","nunique"), total=("billing_amount_usd","sum")
    ).reset_index()
    fig_pay = go.Figure(go.Pie(
        labels=pay_agg["payment_status"], values=pay_agg["total"],
        marker_colors=[PAYMENT_COLORS.get(s,"#737373") for s in pay_agg["payment_status"]],
        textinfo="label+percent", hole=0.45,
    ))
    fig_pay.update_layout(
        title="Invoice status by billed amount — Failed = immediate action",
        height=280, showlegend=False, margin=dict(t=44, b=10, l=8, r=8),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Segoe UI, Arial, sans-serif", size=11, color="#333333"),
    )
    st.plotly_chart(fig_pay, use_container_width=True)

with col_pay_r:
    seg_pay_sorted = seg_pay.sort_values("collection_rate", ascending=True)
    # Highlight lowest collection rate segment
    coll_colors = [
        "#C00000" if s == lowest_seg else C_MUTED
        for s in seg_pay_sorted["segment"]
    ]
    fig_coll = go.Figure()
    fig_coll.add_trace(go.Bar(
        x=seg_pay_sorted["collection_rate"], y=seg_pay_sorted["segment"],
        orientation="h", marker_color=coll_colors,
        text=[f"{r:.0%}" for r in seg_pay_sorted["collection_rate"]], textposition="outside",
    ))
    fig_coll.add_vline(x=avg_rate, line_dash="dash", line_color="#737373",
                       annotation_text=f"Avg {avg_rate:.0%}", annotation_position="top right")
    layout_coll = base_layout(height=280, margin=dict(t=44, b=20, l=8, r=60), show_legend=False)
    layout_coll.update(dict(
        title=f"{lowest_seg} (red) has the worst collection rate — prioritise for outreach",
        xaxis=dict(title="Collection Rate", tickformat=".0%", gridcolor="#EBEBEB",
                   linecolor="#CCCCCC", zeroline=False, range=[0, 1.15]),
    ))
    fig_coll.update_layout(layout_coll)
    st.plotly_chart(fig_coll, use_container_width=True)

st.markdown(alert(
    f"<b>${at_risk_tot/1e6:.2f}M total exposure:</b> "
    f"${chain['failed']/1e6:.2f}M failed (card declined / bank rejected — customer must update payment) + "
    f"${chain['at_risk']/1e6:.2f}M pending (invoiced, awaiting payment). "
    f"Resolve failed invoices first — they require direct customer action.",
    "danger"
), unsafe_allow_html=True)

st.markdown("---")

# ── 04 Monthly Trend ──────────────────────────────────────────────────────────
st.markdown(story_step("04", "Is the payment risk getting worse month over month?"), unsafe_allow_html=True)

monthly = (
    revenue.groupby(["billing_year","billing_month"])
    .agg(collected=("collected_amount_usd","sum"), at_risk=("at_risk_amount_usd","sum"), failed=("failed_amount_usd","sum"))
    .reset_index().sort_values(["billing_year","billing_month"])
)
monthly["period"] = pd.to_datetime(
    monthly["billing_year"].astype(str) + "-" + monthly["billing_month"].astype(str).str.zfill(2)
)
recent = monthly.tail(3)
recent_coll = recent["collected"].mean()
recent_risk = recent["at_risk"].mean()
recent_fail = recent["failed"].mean()

st.markdown(insight(
    f"Last 3 months: collected avg <b>${recent_coll/1e3:.0f}K/mo</b>, "
    f"pending avg <b>${recent_risk/1e3:.0f}K/mo</b>, "
    f"failed avg <b>${recent_fail/1e3:.0f}K/mo</b>. "
    f"Watch whether the orange/red bands are widening — that signals a collections process issue."
), unsafe_allow_html=True)

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=monthly["period"], y=monthly["collected"]/1e3,
    fill="tozeroy", mode="lines", name="Collected",
    line=dict(color="#107C41"), fillcolor="rgba(16,124,65,0.18)",
))
fig_trend.add_trace(go.Scatter(
    x=monthly["period"], y=(monthly["collected"]+monthly["at_risk"])/1e3,
    fill="tonexty", mode="lines", name="Pending",
    line=dict(color="#C55A11"), fillcolor="rgba(197,90,17,0.18)",
))
fig_trend.add_trace(go.Scatter(
    x=monthly["period"], y=(monthly["collected"]+monthly["at_risk"]+monthly["failed"])/1e3,
    fill="tonexty", mode="lines", name="Failed",
    line=dict(color="#C00000"), fillcolor="rgba(192,0,0,0.15)",
))
layout_trend = base_layout(height=290, margin=dict(t=44, b=20, l=8, r=8))
layout_trend.update(dict(
    title="A widening red/orange band means collections is falling behind",
    yaxis_title="Amount ($K)",
))
fig_trend.update_layout(layout_trend)
st.plotly_chart(fig_trend, use_container_width=True)

r1, r2, r3 = st.columns(3)
with r1:
    st.markdown(kpi("Avg Monthly Collected", f"${recent_coll/1e3:.0f}K", "Last 3 months", "good"), unsafe_allow_html=True)
with r2:
    st.markdown(kpi("Avg Monthly Pending", f"${recent_risk/1e3:.0f}K", "Last 3 months"), unsafe_allow_html=True)
with r3:
    st.markdown(kpi("Avg Monthly Failed", f"${recent_fail/1e3:.0f}K", "Last 3 months", "bad" if recent_fail > 10_000 else "neutral"), unsafe_allow_html=True)

st.markdown("---")

# ── Recommended Actions ────────────────────────────────────────────────────────
st.markdown(action_box([
    f"Collections (urgent): Contact accounts with failed payments (${chain['failed']/1e6:.1f}M) — ask them to update payment details.",
    f"Sales Ops: Review 'Heavy Discount' tier — add VP sign-off for deals above the 10% policy threshold.",
    f"Finance: Investigate {lowest_seg} collection rate ({lowest_rate:.0%}) — may indicate billing issue or product satisfaction.",
    "RevOps: Set an automated alert when monthly failed invoices exceed $50K for 2 consecutive months.",
    "Reconciliation: Close Gap 2 (unbilled contracts) within 90 days of contract signing — add to CS onboarding checklist.",
]), unsafe_allow_html=True)

