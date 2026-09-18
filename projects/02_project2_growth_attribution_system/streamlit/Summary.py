"""
Growth Attribution System — Executive Summary
=============================================
Story: Platform-reported ROAS is a fiction.
       Meta's true incremental ROAS is near zero.
       $100K reallocation → +3.2% projected revenue.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    PAID_CHANNELS,
    compute_attribution,
    get_geo_holdout_results,
    get_overview_metrics,
    get_roas_table,
)
from utils.theme import (
    C_MUTED, C_NAVY, C_RED, C_GREEN, C_AMBER, C_BORDER,
    action_box, alert, base_layout, hero, inject_css, insight, kpi,
)

st.set_page_config(
    page_title="Growth Attribution — Summary",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css(st)

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Multi-Touch Attribution & Geo-Incrementality")
    st.markdown("---")
    st.caption("Data: Jan – Jun 2026 · Channels: Meta, Google, TikTok")

# ── Load ───────────────────────────────────────────────────────────────────────
metrics = get_overview_metrics()
geo     = get_geo_holdout_results()
roas    = get_roas_table()
attr    = compute_attribution()

paid = roas[roas["channel"].isin(PAID_CHANNELS)].copy()
paid["true_roas"] = paid["channel"].map({
    "Meta Paid Social":   geo["incremental_roas"],
    "Google Paid Search": 2.65,
    "TikTok Ads":         2.10,
})

current = {ch: paid.loc[paid["channel"] == ch, "total_spend"].values[0] for ch in PAID_CHANNELS}
SHIFT = 100_000
recommended = {
    "Meta Paid Social":   current["Meta Paid Social"]   - SHIFT,
    "Google Paid Search": current["Google Paid Search"] + SHIFT * 0.5,
    "TikTok Ads":         current["TikTok Ads"]         + SHIFT * 0.5,
}
TRUE_ROAS = {"Meta Paid Social": geo["incremental_roas"], "Google Paid Search": 2.65, "TikTok Ads": 2.10}
curr_total = sum(current[ch] * TRUE_ROAS[ch] for ch in PAID_CHANNELS)
rec_total  = sum(recommended[ch] * TRUE_ROAS[ch] for ch in PAID_CHANNELS)
rec_delta  = (rec_total - curr_total) / curr_total * 100
rev_lift   = rec_total - curr_total

platform_roas = metrics["blended_platform_roas"]
actual_roas   = metrics["blended_actual_roas"]
overstatement = metrics["overstatement_pct"]

MONTHS = 6
spend_mo   = metrics["total_spend"]   / MONTHS
revenue_mo = metrics["total_revenue"] / MONTHS
convs_mo   = metrics["total_actual_convs"] / MONTHS

# ── Hero ───────────────────────────────────────────────────────────────────────
st.title("Executive Summary")

# Period badge
st.markdown(
    '<div style="display:inline-block;font-size:0.68rem;font-weight:700;letter-spacing:0.1em;'
    'text-transform:uppercase;color:#6B7788;background:#F2F4F7;border:1px solid #D9DEE7;'
    'border-radius:2px;padding:3px 10px;margin-bottom:14px;">6-Month Period · Jan – Jun 2026</div>',
    unsafe_allow_html=True,
)

_overstate_x = round(platform_roas / actual_roas) if actual_roas > 0 else "—"
st.markdown(hero(
    headline=(
        f"Meta, Google, and TikTok each claim full credit for the same sale — "
        f"inflating our blended ROAS from a real {actual_roas}x to a reported {platform_roas}x. "
        f"A 30-day controlled experiment proved Meta's ads drove almost no incremental revenue."
    ),
    metric=(
        f"${metrics['total_spend']/1e3:,.0f}K spent over 6 months  ·  "
        f"{metrics['total_actual_convs']:,} verified conversions  ·  "
        f"${metrics['total_revenue']/1e3:,.0f}K actual backend revenue"
    ),
    subtext=(
        f"Platform dashboards show {platform_roas}x return per dollar — "
        f"backend orders show {actual_roas}x, a {_overstate_x}× gap driven by cross-platform double-counting. "
        f"We paused Meta ads in 10 markets for 30 days: conversions barely moved, "
        f"confirming {geo['organic_share_pct']}% of Meta-attributed sales were organic."
    ),
), unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi(
        "Total Ad Spend",
        f"${metrics['total_spend']/1e3:,.0f}K",
        f"6-month total · ${spend_mo/1e3:,.0f}K/mo avg · Meta + Google + TikTok"
    ), unsafe_allow_html=True)
with k2:
    st.markdown(kpi(
        "Platform-Reported ROAS",
        f"{platform_roas}x",
        "Blended 6-month — includes cross-platform double-counting",
        "warn"
    ), unsafe_allow_html=True)
with k3:
    st.markdown(kpi(
        "True Revenue / Spend",
        f"{actual_roas}x",
        f"Backend orders ÷ spend · ${revenue_mo/1e3:,.0f}K/mo actual revenue",
        "bad"
    ), unsafe_allow_html=True)
with k4:
    st.markdown(kpi(
        "Meta Incremental ROAS",
        f"{geo['incremental_roas']}x",
        f"Geo-holdout result · {geo['organic_share_pct']}% of conversions were organic",
        "bad"
    ), unsafe_allow_html=True)

st.markdown("---")

# ── Bottom line ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:#EDF7F3;border:1px solid #087F5B;border-left:4px solid #087F5B;
                border-radius:4px;padding:20px 24px;margin-bottom:20px;">
      <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                  color:#087F5B;margin-bottom:8px;">Bottom Line Recommendation</div>
      <div style="font-size:1.05rem;font-weight:700;color:#18202B;margin-bottom:6px;">
        Shift $100K from Meta retargeting → Google Search + TikTok prospecting.
        Projected revenue lift: <span style="color:#087F5B;">+{rec_delta:.1f}% (+${rev_lift:,.0f})</span>.
      </div>
      <div style="font-size:0.82rem;color:#4E5B6B;line-height:1.6;">
        Meta's true incremental ROAS ({geo['incremental_roas']}x) is near break-even.
        Google (2.65x true) and TikTok (2.10x true) are undervalued by platform attribution.
        Total budget stays constant — this is a reallocation, not an increase.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Channel decision table ─────────────────────────────────────────────────────
st.markdown(
    """
    <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                color:#6B7788;margin-bottom:10px;">Channel-by-Channel Verdict</div>
    """,
    unsafe_allow_html=True,
)

ACTION_COLORS = {
    "Meta Paid Social":   ("#FDEAED", "#C53A4A", "↓ Cut $100K"),
    "Google Paid Search": ("#EDF7F3", "#087F5B", "↑ Add $50K"),
    "TikTok Ads":         ("#EDF7F3", "#087F5B", "↑ Add $50K"),
}

ch_cols = st.columns(3)
for col, ch in zip(ch_cols, PAID_CHANNELS):
    p_roas = paid.loc[paid["channel"] == ch, "Platform ROAS"].values[0]
    t_roas = TRUE_ROAS[ch]
    spend  = current[ch]
    bg, border, action = ACTION_COLORS[ch]

    with col:
        st.markdown(
            f"""
            <div style="background:{bg};border:1px solid {border};border-top:3px solid {border};
                        border-radius:4px;padding:16px 18px;">
              <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
                          color:{border};margin-bottom:8px;">{ch}</div>
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:0.75rem;color:#6B7788;">6-mo spend</span>
                <span style="font-size:0.75rem;font-weight:600;color:#18202B;">${spend/1e3:,.0f}K (${spend/MONTHS/1e3:,.0f}K/mo)</span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:0.75rem;color:#6B7788;">Platform ROAS</span>
                <span style="font-size:0.75rem;font-weight:600;color:#A15C00;">{p_roas:.2f}x</span>
              </div>
              <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                <span style="font-size:0.75rem;color:#6B7788;">True incremental ROAS</span>
                <span style="font-size:0.75rem;font-weight:700;color:{border};">{t_roas:.2f}x</span>
              </div>
              <div style="font-size:0.88rem;font-weight:700;color:{border};">{action}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Attribution gap chart (compact evidence) ───────────────────────────────────
st.markdown(
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;'
    'color:#6B7788;margin-bottom:10px;">Evidence — Platform-Reported vs SQL-Attributed Revenue</div>',
    unsafe_allow_html=True,
)

by_ch     = metrics["by_channel"].copy()
paid_ch   = by_ch[by_ch["channel"].isin(PAID_CHANNELS)].copy()
paid_attr = attr[attr["channel"].isin(PAID_CHANNELS)].copy()
merge_df  = paid_ch.merge(paid_attr[["channel", "time_decay_revenue"]], on="channel", how="left")

platform_colors = [C_RED if ch == "Meta Paid Social" else C_MUTED for ch in merge_df["channel"]]
actual_colors   = [C_NAVY if ch == "Meta Paid Social" else "#2E75B6" for ch in merge_df["channel"]]

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Platform-Reported Revenue",
    x=merge_df["channel"],
    y=merge_df["platform_revenue"],
    marker_color=platform_colors,
    opacity=0.5,
    text=[f"${v:,.0f}" for v in merge_df["platform_revenue"]],
    textposition="outside",
    textfont=dict(size=11),
))
fig.add_trace(go.Bar(
    name="SQL Time-Decay Revenue (ground truth)",
    x=merge_df["channel"],
    y=merge_df["time_decay_revenue"],
    marker_color=actual_colors,
    text=[f"${v:,.0f}" for v in merge_df["time_decay_revenue"]],
    textposition="outside",
    textfont=dict(size=11),
))
layout = base_layout(height=300, margin=dict(t=44, b=10, l=8, r=8))
layout.update(dict(
    title="Meta's platform revenue is most inflated — SQL attribution exposes the gap",
    barmode="group",
    yaxis=dict(title="Revenue (USD)", tickprefix="$", tickformat=",",
               gridcolor=C_BORDER, zeroline=False),
))
fig.update_layout(layout)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Go deeper ──────────────────────────────────────────────────────────────────
st.markdown(action_box([
    "Attribution Models → How First-Touch, Last-Touch, Linear, and Time-Decay each tell a different story.",
    f"Geo-Holdout → The controlled experiment that proved Meta's true ROAS is {geo['incremental_roas']}x.",
    f"Budget Decision → Interactive simulator for the $100K reallocation (+{rec_delta:.1f}% revenue).",
]), unsafe_allow_html=True)
