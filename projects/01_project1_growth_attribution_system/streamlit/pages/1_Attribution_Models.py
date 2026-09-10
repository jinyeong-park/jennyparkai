"""
Attribution Models page.

Key insight: the attribution model you choose changes which channel looks best.
First-Touch favors TikTok. Last-Touch favors Meta. Time-Decay gives a more
balanced view. Showing all four side by side prevents model bias.
"""

import plotly.express as px
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

st.set_page_config(page_title="Attribution Models", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("📐 Attribution Models")
st.markdown(
    "#### The channel that looks best depends entirely on which attribution "
    "model you use. Here's why that matters."
)
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────────

agg      = compute_attribution()
long_df  = get_attribution_long()
roas_tbl = get_roas_table()

paid_agg = agg[agg["channel"].isin(PAID_CHANNELS)].copy()
paid_long = long_df[long_df["channel"].isin(PAID_CHANNELS)].copy()

# ─────────────────────────────────────────────────────────────────────────────
# Model explainer cards
# ─────────────────────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)

model_info = {
    "First-Touch": {
        "icon": "🥇",
        "color": MODEL_COLORS["First-Touch"],
        "desc": "100% credit to the **first** touchpoint. Favors awareness channels (TikTok, top-of-funnel).",
        "bias": "Ignores what closed the deal.",
    },
    "Last-Touch": {
        "icon": "🏁",
        "color": MODEL_COLORS["Last-Touch"],
        "desc": "100% credit to the **last** touchpoint before conversion. Favors retargeting (Meta).",
        "bias": "Ignores what introduced the user.",
    },
    "Linear": {
        "icon": "⚖️",
        "color": MODEL_COLORS["Linear"],
        "desc": "Equal credit split across **all** touchpoints. Simple and unbiased.",
        "bias": "Treats all touches as equally important.",
    },
    "Time-Decay": {
        "icon": "⏱️",
        "color": MODEL_COLORS["Time-Decay"],
        "desc": "Exponential credit, heavier near conversion. 7-day half-life.",
        "bias": "Penalizes long-cycle discovery channels.",
    },
}

for col, (model, info) in zip([c1, c2, c3, c4], model_info.items()):
    with col:
        st.markdown(
            f"""
            <div style="border-left: 4px solid {info['color']}; padding: 12px 16px;
                        background: #fafafa; border-radius: 4px; height: 160px;">
                <div style="font-size:22px;">{info['icon']}</div>
                <div style="font-weight:700; font-size:15px; margin:6px 0;">{model}</div>
                <div style="font-size:13px; color:#444;">{info['desc']}</div>
                <div style="font-size:12px; color:#888; margin-top:6px;">⚠ {info['bias']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Revenue comparison — all models side by side
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Attributed Revenue by Channel — All Models")
st.caption(
    "Same conversions, same data — different revenue allocations depending on the model. "
    "Notice how Meta dominates Last-Touch but shrinks under Time-Decay."
)

fig = px.bar(
    paid_long,
    x="channel",
    y="attributed_revenue",
    color="model",
    barmode="group",
    color_discrete_map=MODEL_COLORS,
    labels={
        "attributed_revenue": "Attributed Revenue (USD)",
        "channel": "",
        "model": "Attribution Model",
    },
    height=380,
)
fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    yaxis_tickprefix="$",
    yaxis_tickformat=",",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(t=40, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Single-model deep dive
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### Single-Model View")
selected_model = st.radio(
    "Select a model to inspect:",
    options=["First-Touch", "Last-Touch", "Linear", "Time-Decay"],
    horizontal=True,
)

model_col_map = {
    "First-Touch": "first_touch_revenue",
    "Last-Touch":  "last_touch_revenue",
    "Linear":      "linear_revenue",
    "Time-Decay":  "time_decay_revenue",
}
rev_col = model_col_map[selected_model]

single = paid_agg[["channel", rev_col, "total_conversions"]].copy()
single = single.sort_values(rev_col, ascending=False)
single["share_pct"] = (single[rev_col] / single[rev_col].sum() * 100).round(1)

left, right = st.columns([1.2, 1], gap="large")

with left:
    fig2 = px.bar(
        single,
        x=rev_col,
        y="channel",
        orientation="h",
        color="channel",
        color_discrete_map=CHANNEL_COLORS,
        text=single[rev_col].apply(lambda v: f"${v:,.0f}"),
        labels={rev_col: "Attributed Revenue (USD)", "channel": ""},
        height=280,
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        xaxis_tickprefix="$",
        xaxis_tickformat=",",
        margin=dict(t=20, b=10, l=10, r=80),
    )
    st.plotly_chart(fig2, use_container_width=True)

with right:
    fig3 = px.pie(
        single,
        names="channel",
        values=rev_col,
        color="channel",
        color_discrete_map=CHANNEL_COLORS,
        hole=0.5,
        height=280,
    )
    fig3.update_traces(textposition="outside", textinfo="label+percent")
    fig3.update_layout(
        showlegend=False,
        margin=dict(t=20, b=10, l=10, r=10),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROAS table
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("### ROAS by Channel × Model")
st.caption(
    "Platform ROAS uses each platform's own reported conversions × $160 avg order value. "
    "SQL-model ROAS uses actual backend conversions distributed by attribution logic."
)

display_tbl = roas_tbl[roas_tbl["channel"].isin(PAID_CHANNELS)].copy()
display_tbl["total_spend"] = display_tbl["total_spend"].apply(lambda v: f"${v:,.0f}")

roas_cols = ["Platform ROAS", "First-Touch ROAS", "Last-Touch ROAS", "Linear ROAS", "Time-Decay ROAS"]


def color_roas(val):
    try:
        v = float(val)
        if v >= 2.5:
            return "background-color: #d4edda; color: #155724"
        elif v >= 1.5:
            return "background-color: #fff3cd; color: #856404"
        else:
            return "background-color: #f8d7da; color: #721c24"
    except (ValueError, TypeError):
        return ""


st.dataframe(
    display_tbl.rename(columns={"total_spend": "Total Spend"})
    .style.applymap(color_roas, subset=roas_cols)
    .format({c: "{:.2f}x" for c in roas_cols}),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.info(
    "**Key takeaway:** Meta looks like the top channel under Last-Touch (highest ROAS) "
    "but drops to the bottom under Time-Decay. Platform-reported ROAS consistently "
    "overstates all channels. → See **Geo-Holdout** to find out Meta's true incremental ROAS.",
    icon="💡",
)
