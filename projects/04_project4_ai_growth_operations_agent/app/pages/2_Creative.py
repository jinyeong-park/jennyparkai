"""Creative Intelligence — Hook types, fatigue signals, top performers.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from utils.data_loader import load_hook_type_performance, load_fatigue_signals, load_creative_performance
from utils.metrics import fmt_currency, fmt_pct, fmt_number, channel_color
from utils.theme import inject_theme, render_navigation, GREEN, AMBER, RED, TEAL, BLUE, PRIMARY, MUTED, MUTED_BAR

st.set_page_config(
    page_title="Creative Intelligence — Tablr Growth",
    page_icon=":material/palette:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Creative Intelligence</h1>",
    unsafe_allow_html=True,
)
st.caption("Hook taxonomy · Fatigue detection · Top performers · High-CTR / low-activation flags")

st.markdown("---")

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading creative data..."):
    hooks = load_hook_type_performance()
    fatigue = load_fatigue_signals()
    creative_perf = load_creative_performance()

# ── Hook Type Performance ─────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>01 — CONTRAST hook cuts trial CAC below every other hook type</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """<div style='background:#eff6ff;border-left:4px solid #1a6fbe;padding:10px 14px;
    border-radius:0 6px 6px 0;font-size:0.88rem;color:#1e3a5f;margin-bottom:8px;'>
    <b>Key finding:</b> CONTRAST hook achieves the lowest trial CAC at $216 —
    significantly better than average. Hook type is a stronger lever than channel for
    improving mid-funnel efficiency.
    </div>""",
    unsafe_allow_html=True,
)
st.markdown(
    """<div style='font-size:0.82rem;color:#64748b;margin-bottom:14px;padding-left:2px;'>
    <b>Why trial CAC, not CTR?</b> CTR measures how many people click the ad —
    but a click that doesn't become a trial signup costs money without return.
    Trial CAC (spend ÷ signups) captures both click efficiency and landing page conversion together,
    making it a better proxy for what the creative is actually delivering.
    A hook with high CTR but low click-to-trial rate is wasting impression spend on the wrong audience.
    </div>""",
    unsafe_allow_html=True,
)

col_tbl, col_chart = st.columns([1, 2])

with col_tbl:
    hook_display = []
    for _, r in hooks.iterrows():
        hook_display.append({
            "Hook Type": r["hook_type"],
            "Impressions": fmt_number(int(r["impressions"])),
            "CTR": fmt_pct(r["ctr"], 2),
            "Trial Signups": fmt_number(int(r["trial_signups"])),
            "Trial CAC": fmt_currency(r["trial_cac_usd"]),
        })
    st.dataframe(pd.DataFrame(hook_display), use_container_width=True, hide_index=True)
    st.caption("Sorted by trial CAC ascending.")

with col_chart:
    hook_sorted = hooks.sort_values("trial_cac_usd", na_position="last")
    # Highlight exception: CONTRAST (winner) green, all others muted
    colors = [GREEN if h == "CONTRAST" else MUTED_BAR for h in hook_sorted["hook_type"]]

    fig = go.Figure(go.Bar(
        x=hook_sorted["hook_type"],
        y=hook_sorted["trial_cac_usd"],
        marker_color=colors,
        text=[fmt_currency(v) for v in hook_sorted["trial_cac_usd"]],
        textposition="outside",
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=10, t=10, b=40),
        yaxis=dict(title="Trial CAC (USD)", tickprefix="$"),
        xaxis=dict(title="Hook Type"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Green = best performer. Sorted ascending by trial CAC.")

st.markdown("---")

# ── Creative Fatigue ──────────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>02 — 17.8% of creatives show CTR fatigue — 16 assets need rotation</div>",
    unsafe_allow_html=True,
)

fatigued = fatigue[fatigue["is_fatigued"] == True]
total_creatives = len(fatigue)
n_fatigued = len(fatigued)

col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Total Creatives Tracked</div>
        <div class='metric-value'>{fmt_number(total_creatives)}</div>
        <div class='metric-delta'>across 4 channels · 5 personas</div>
        </div>""",
        unsafe_allow_html=True,
    )
with col_stat2:
    fatigue_pct = n_fatigued / total_creatives if total_creatives else 0
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Fatigued Creatives</div>
        <div class='metric-value' style='color:#dc2626;'>{fmt_number(n_fatigued)}</div>
        <div class='metric-delta-neg'>{fmt_pct(fatigue_pct)} of total · pause or refresh now</div>
        </div>""",
        unsafe_allow_html=True,
    )
with col_stat3:
    avg_drop = fatigued["ctr_drop_pct"].mean() if not fatigued.empty else 0
    st.markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>Avg CTR Drop (Fatigued)</div>
        <div class='metric-value' style='color:#dc2626;'>{fmt_pct(avg_drop)}</div>
        <div class='metric-delta-neg'>from peak · threshold: &gt;25% drop over 4+ weeks</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

if not fatigued.empty:
    fatigue_display = []
    for _, r in fatigued.iterrows():
        fatigue_display.append({
            "Creative ID": r["creative_id"],
            "Channel": r["channel"],
            "Hook Type": r["hook_type"],
            "Peak CTR": fmt_pct(r["peak_ctr"], 2),
            "Peak Week": int(r["peak_week"]),
            "Latest CTR": fmt_pct(r["latest_ctr"], 2),
            "Latest Week": int(r["latest_week"]),
            "CTR Drop": fmt_pct(r["ctr_drop_pct"]),
            "Fatigued": "YES",
        })
    st.dataframe(pd.DataFrame(fatigue_display), use_container_width=True, hide_index=True)
    st.caption(
        "Fatigue defined as >25% CTR drop from peak, with ≥4 weeks of data. "
        "Action: pause or refresh creative assets for flagged IDs."
    )
else:
    st.info("No fatigued creatives detected with the current threshold (25% CTR drop from peak).")

st.markdown("---")

# ── Top Performing Creatives ──────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>03 — Top 15 creatives by trial CAC — where to concentrate creative investment</div>",
    unsafe_allow_html=True,
)

top_creatives = (
    creative_perf[creative_perf["trial_cac_usd"].notna() & (creative_perf["trial_signups"] >= 5)]
    .sort_values("trial_cac_usd")
    .head(15)
)

top_display = []
for _, r in top_creatives.iterrows():
    top_display.append({
        "Creative ID": r["creative_id"],
        "Channel": r["channel"],
        "Hook Type": r["hook_type"],
        "Format": r["creative_format"],
        "Persona": r["persona_segment"],
        "Impressions": fmt_number(int(r["impressions"])),
        "CTR": fmt_pct(r["ctr"], 2),
        "Trial Signups": fmt_number(int(r["trial_signups"])),
        "Trial CAC": fmt_currency(r["trial_cac_usd"]),
    })

st.dataframe(pd.DataFrame(top_display), use_container_width=True, hide_index=True)
st.caption("Minimum 5 trial signups required for inclusion. Trial CAC is spend / trial signups.")

st.markdown("---")

# ── High CTR / Low Activation flag ───────────────────────────────────────────
st.markdown(
    "<div class='section-header'>04 — High CTR creatives that fail to convert — audience-message mismatch</div>",
    unsafe_allow_html=True,
)

# Find creatives with CTR in top quartile but low trial signups relative to clicks
creative_perf_filtered = creative_perf[creative_perf["impressions"] > 5000].copy()
if not creative_perf_filtered.empty:
    ctr_q75 = creative_perf_filtered["ctr"].quantile(0.75)
    # Use trial_signups / clicks as a proxy for post-click quality
    creative_perf_filtered["click_to_trial"] = (
        creative_perf_filtered["trial_signups"] / creative_perf_filtered["clicks"].replace(0, None)
    )
    ctt_q25 = creative_perf_filtered["click_to_trial"].quantile(0.25)

    flagged = creative_perf_filtered[
        (creative_perf_filtered["ctr"] >= ctr_q75) &
        (creative_perf_filtered["click_to_trial"] <= ctt_q25)
    ]

    if not flagged.empty:
        st.markdown(
            f"""<div style='background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;
            padding:12px 14px;margin-bottom:12px;font-size:0.87rem;color:#7c2d12;'>
            <b>&#9888; {len(flagged)} creative(s)</b> with CTR in top quartile but click-to-trial rate
            in bottom quartile. These creatives attract clicks but fail to convert to trial signups —
            possible audience-message mismatch or landing page disconnect.
            </div>""",
            unsafe_allow_html=True,
        )
        flag_display = []
        for _, r in flagged.iterrows():
            flag_display.append({
                "Creative ID": r["creative_id"],
                "Channel": r["channel"],
                "Hook Type": r["hook_type"],
                "CTR": fmt_pct(r["ctr"], 2),
                "Clicks": fmt_number(int(r["clicks"])),
                "Trial Signups": fmt_number(int(r["trial_signups"])),
                "Click→Trial Rate": fmt_pct(r["click_to_trial"]),
                "Flag": "High CTR / Low Trial Conversion",
            })
        st.dataframe(pd.DataFrame(flag_display), use_container_width=True, hide_index=True)
        st.caption("Top CTR quartile AND bottom click-to-trial quartile.")
    else:
        st.success("No high-CTR / low-activation creatives detected at current thresholds.")
else:
    st.info("Insufficient data for high-CTR / low-activation analysis (need >5,000 impressions per creative).")
