"""
Attribution Models page.

Key insight: the attribution model you choose changes which channel looks best.
First-Touch favors TikTok. Last-Touch favors Meta. Time-Decay gives the most
balanced view — and it shows Meta's weakness most clearly.
"""

import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from utils.data_loader import (
    CHANNEL_COLORS,
    MODEL_COLORS,
    PAID_CHANNELS,
    compute_attribution,
    get_attribution_long,
    get_roas_table,
)
from utils.theme import (
    C_MUTED, C_NAVY, C_GREEN, C_RED, C_AMBER, C_BORDER,
    action_box, alert, base_layout, hero, inject_css, insight, kpi, story_step,
)

st.set_page_config(page_title="Attribution Models", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Multi-Touch Attribution & Geo-Incrementality")

# ── Load ───────────────────────────────────────────────────────────────────────
agg      = compute_attribution()
long_df  = get_attribution_long()
roas_tbl = get_roas_table()

paid_agg  = agg[agg["channel"].isin(PAID_CHANNELS)].copy()
paid_long = long_df[long_df["channel"].isin(PAID_CHANNELS)].copy()

# ── Hero ───────────────────────────────────────────────────────────────────────
st.title("Attribution Models")

meta_ft  = paid_agg.loc[paid_agg["channel"] == "Meta Paid Social", "first_touch_revenue"].values[0]
meta_lt  = paid_agg.loc[paid_agg["channel"] == "Meta Paid Social", "last_touch_revenue"].values[0]
meta_td  = paid_agg.loc[paid_agg["channel"] == "Meta Paid Social", "time_decay_revenue"].values[0]
tiktok_ft = paid_agg.loc[paid_agg["channel"] == "TikTok Ads", "first_touch_revenue"].values[0]

st.markdown(hero(
    headline=(
        "The channel that looks best depends entirely on the attribution model. "
        "Meta leads under Last-Touch. TikTok leads under First-Touch. "
        "Time-Decay — the most balanced model — reveals Meta's weakest result."
    ),
    metric=(
        f"Meta: ${meta_lt:,.0f} Last-Touch  →  ${meta_td:,.0f} Time-Decay  "
        f"·  TikTok: ${tiktok_ft:,.0f} First-Touch"
    ),
    subtext=(
        "None of these models measures true causal impact — that requires a geo-holdout experiment. "
        "But comparing models side-by-side exposes where each platform captures vs creates demand."
    ),
), unsafe_allow_html=True)

st.markdown("---")

# ── 01 Model overview ─────────────────────────────────────────────────────────
st.markdown(story_step("01", "What does each attribution model reward — and what does it miss?"), unsafe_allow_html=True)

model_info = [
    ("First-Touch",  "Credits the first touchpoint 100%. Reveals awareness channels. Misses what closed the deal.", C_MUTED),
    ("Last-Touch",   "Credits the last touchpoint 100%. Favors retargeting (Meta). Ignores the full journey.",       C_MUTED),
    ("Linear",       "Equal credit across all touchpoints. Simple and unbiased. Treats all touches as equal.",        C_MUTED),
    ("Time-Decay",   "Exponential credit toward conversion (7-day half-life). Best for diagnosing closing channels.", C_NAVY),
]

cols = st.columns(4)
for col, (model, desc, color) in zip(cols, model_info):
    with col:
        border_style = f"border-left: 4px solid {color}; padding: 14px 16px; background: #F7F8FA; border-radius: 0 4px 4px 0; min-height: 130px;"
        label_color  = color if color == C_NAVY else "#6B7788"
        st.markdown(
            f'<div style="{border_style}">'
            f'<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{label_color};margin-bottom:6px;">{model}</div>'
            f'<div style="font-size:0.82rem;color:#4E5B6B;line-height:1.5;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── 02 All-models comparison ───────────────────────────────────────────────────
st.markdown(story_step("02", "How does attributed revenue shift across models for each channel?"), unsafe_allow_html=True)

st.markdown(insight(
    "<b>Time-Decay (navy) is the recommended reference model</b> — it penalizes early-funnel touches less than Last-Touch "
    "and gives more credit to channels that genuinely assist conversion. All other models are muted for comparison."
), unsafe_allow_html=True)

# "Highlight the exception": Time-Decay = C_NAVY, others = C_MUTED
MODEL_DISPLAY_COLORS = {
    "First-Touch": C_MUTED,
    "Last-Touch":  C_MUTED,
    "Linear":      "#B0BCCC",  # slightly visible
    "Time-Decay":  C_NAVY,
}

fig = go.Figure()
for model in ["First-Touch", "Last-Touch", "Linear", "Time-Decay"]:
    model_data = paid_long[paid_long["model"] == model].sort_values("channel")
    fig.add_trace(go.Bar(
        name=model,
        x=model_data["channel"],
        y=model_data["attributed_revenue"],
        marker_color=MODEL_DISPLAY_COLORS[model],
        opacity=1.0 if model == "Time-Decay" else 0.65,
        text=[f"${v:,.0f}" for v in model_data["attributed_revenue"]],
        textposition="outside",
        textfont=dict(size=10),
    ))
layout_all = base_layout(height=360, margin=dict(t=48, b=20, l=8, r=100))
layout_all.update(dict(
    title="Time-Decay cuts Meta's attributed revenue most sharply — exposing its late-funnel bias",
    barmode="group",
    yaxis=dict(title="Attributed Revenue (USD)", tickprefix="$", tickformat=",",
               gridcolor=C_BORDER, zeroline=False),
))
fig.update_layout(layout_all)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── 03 Single-model deep dive ──────────────────────────────────────────────────
st.markdown(story_step("03", "Which channel looks best under each individual model?"), unsafe_allow_html=True)

selected_model = st.radio(
    "Select a model:",
    options=["First-Touch", "Last-Touch", "Linear", "Time-Decay"],
    horizontal=True,
    index=3,  # default to Time-Decay
)

model_col_map = {
    "First-Touch": "first_touch_revenue",
    "Last-Touch":  "last_touch_revenue",
    "Linear":      "linear_revenue",
    "Time-Decay":  "time_decay_revenue",
}
rev_col = model_col_map[selected_model]

single = paid_agg[["channel", rev_col]].copy()
single = single.sort_values(rev_col, ascending=True)  # ascending for horizontal bar (best on top)
single["share_pct"] = (single[rev_col] / single[rev_col].sum() * 100).round(1)

# "Highlight the exception" — focal bar = highest revenue channel
top_ch = single.iloc[-1]["channel"]
bar_colors = [C_NAVY if ch == top_ch else C_MUTED for ch in single["channel"]]

fig2 = go.Figure(go.Bar(
    x=single[rev_col],
    y=single["channel"],
    orientation="h",
    marker_color=bar_colors,
    text=[f"${v:,.0f}  ({p:.0f}%)" for v, p in zip(single[rev_col], single["share_pct"])],
    textposition="outside",
))
layout2 = base_layout(height=240, margin=dict(t=48, b=20, l=8, r=160), show_legend=False)
layout2.update(dict(
    title=f"{selected_model}: '{top_ch}' receives the most credited revenue ({single.iloc[-1]['share_pct']:.0f}% share)",
    xaxis=dict(title="Attributed Revenue (USD)", tickprefix="$", tickformat=",",
               gridcolor=C_BORDER, zeroline=False),
    yaxis=dict(title=""),
))
fig2.update_layout(layout2)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── 04 ROAS table ─────────────────────────────────────────────────────────────
st.markdown(story_step("04", "How does ROAS change across models — and what does platform-reporting hide?"), unsafe_allow_html=True)

st.markdown(insight(
    "Platform ROAS is systematically higher than any SQL-computed model. "
    "<b>Meta's platform ROAS (3.25x) vs Time-Decay ROAS (lowest) illustrates the biggest gap</b> — "
    "platform reporting claims credit for conversions that attribution models can't justify. "
    "True incrementality is only measurable through a geo-holdout experiment (see next page)."
), unsafe_allow_html=True)

display_tbl = roas_tbl[roas_tbl["channel"].isin(PAID_CHANNELS)].copy()
display_tbl["Total Spend"] = display_tbl["total_spend"].apply(lambda v: f"${v:,.0f}")

roas_cols = ["Platform ROAS", "First-Touch ROAS", "Last-Touch ROAS", "Linear ROAS", "Time-Decay ROAS"]
show_cols = ["channel", "Total Spend"] + roas_cols

display_out = display_tbl[show_cols].rename(columns={"channel": "Channel"}).copy()
for c in roas_cols:
    display_out[c] = display_out[c].apply(lambda v: f"{v:.2f}x")

st.dataframe(display_out, use_container_width=True, hide_index=True)
st.caption("Platform ROAS = platform-reported conversions × $160 avg order value ÷ spend. SQL ROAS = backend conversions distributed by model ÷ spend.")

st.markdown("---")

st.markdown(action_box([
    "Use Time-Decay as the default reporting model — it best reflects the full conversion journey.",
    "Do not optimize budget toward Last-Touch ROAS — it systematically over-credits Meta retargeting.",
    "Platform ROAS numbers are inadmissible as budget evidence — they count the same conversion multiple times.",
    "Run a geo-holdout experiment (see next page) to measure true incremental ROAS before shifting budget.",
]), unsafe_allow_html=True)
