"""
Real Data Guide
===============
What data sources, schema, and pipeline this dashboard would need
to run on real company data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st

from utils.theme import (
    C_NAVY, C_BLUE, C_GREEN, C_RED, C_AMBER, C_GRAY,
    inject_css, alert, insight, story_step,
)

st.set_page_config(page_title="Real Data Guide — Growth Attribution", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Growth Attribution System")
    st.markdown("Real data requirements")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1>Real Data Guide</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    insight(
        "This dashboard runs on <strong>synthetic data</strong> that mirrors real attribution patterns. "
        "This guide documents what real data sources, schema, and pipeline would look like in production."
    ),
    unsafe_allow_html=True,
)

st.divider()

# ── Section 1: Data requirements per page ────────────────────────────────────
st.markdown(story_step("1", "What data does each page need?"), unsafe_allow_html=True)

pages = [
    {
        "name": "Attribution Models",
        "color": C_NAVY,
        "sources": ["Ad platform APIs (Meta, Google, TikTok)", "CRM / MQL table", "Web analytics (GA4 / Segment)"],
        "key_fields": "touch_type, channel, timestamp, user_id, revenue",
        "refresh": "Daily",
        "note": "Requires user-level touch data across all channels to run first-touch, last-touch, and time-decay models.",
    },
    {
        "name": "Geo Holdout",
        "color": C_GREEN,
        "sources": ["Ad platform geo reports", "Revenue by DMA/region (CRM or ERP)", "Experiment assignment table"],
        "key_fields": "region_id, treatment_flag, spend, conversions, revenue, week",
        "refresh": "Weekly (during experiment)",
        "note": "Experiment must be pre-registered with clean treatment/control region split. Minimum 4-week run recommended.",
    },
    {
        "name": "Budget Decision",
        "color": C_AMBER,
        "sources": ["All attribution model outputs", "Geo holdout results", "Current budget allocation table"],
        "key_fields": "channel, incremental_roas, attributed_revenue, spend, lift_estimate",
        "refresh": "Weekly / on-demand",
        "note": "Simulator reads incremental ROAS from holdout results — Meta retargeting near-zero incrementality drives reallocation math.",
    },
]

for page in pages:
    st.markdown(
        f"<div style='background:#fff;border:1px solid #D9DEE7;border-radius:6px;"
        f"border-left:4px solid {page['color']};padding:18px 22px;margin-bottom:14px;'>"
        f"<div style='font-weight:700;font-size:0.95rem;color:{page['color']};margin-bottom:10px;'>"
        f"{page['name']}</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;font-size:0.82rem;'>"
        f"<div><div style='font-weight:600;color:#6B7788;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:4px;'>Source Systems</div>"
        f"{''.join(f'<div style=&quot;color:#18202B;padding:2px 0;&quot;>• {s}</div>' for s in page['sources'])}"
        f"</div>"
        f"<div><div style='font-weight:600;color:#6B7788;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:4px;'>Key Fields</div>"
        f"<div style='color:#18202B;font-family:monospace;font-size:0.78rem;line-height:1.6;'>{page['key_fields']}</div>"
        f"<div style='margin-top:8px;font-weight:600;color:#6B7788;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:4px;'>Refresh Cadence</div>"
        f"<div style='color:#18202B;'>{page['refresh']}</div>"
        f"</div>"
        f"<div><div style='font-weight:600;color:#6B7788;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;margin-bottom:4px;'>Note</div>"
        f"<div style='color:#18202B;line-height:1.5;'>{page['note']}</div>"
        f"</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Section 2: End-to-end pipeline ───────────────────────────────────────────
st.markdown(story_step("2", "What does the real data pipeline look like?"), unsafe_allow_html=True)

pipeline_steps = [
    (
        "Ad Platform APIs",
        "Meta Marketing API · Google Ads API · TikTok Ads API",
        C_NAVY,
        "Pull daily spend, impressions, clicks, conversions by campaign/ad set/geo. "
        "Store raw JSON → normalize to channel spend table.",
    ),
    (
        "Web & CRM Events",
        "Segment / Rudderstack · Salesforce / HubSpot",
        C_BLUE,
        "User-level touch events (page_view, ad_click, form_submit, purchase) with UTM params. "
        "MQL/SQL stages + revenue from CRM joined on user_id.",
    ),
    (
        "Data Warehouse",
        "BigQuery · Snowflake · Redshift",
        "#7C3AED",
        "Centralize all raw events + spend data. Partitioned by date, clustered by channel. "
        "Touch table: one row per user × channel × touchpoint.",
    ),
    (
        "dbt Transforms",
        "dbt Core · dbt Cloud",
        C_GREEN,
        "stg_touches → fct_attribution (all three models in one pass). "
        "fct_geo_holdout aggregates region × week. mart_budget_sim pre-computes ROAS inputs.",
    ),
    (
        "Dashboard",
        "Streamlit · Plotly",
        C_AMBER,
        "Reads Parquet snapshots (or live DuckDB) from dbt output. "
        "No raw SQL in app code — all logic lives in dbt models.",
    ),
]

for i, (name, tools, color, desc) in enumerate(pipeline_steps):
    connector = (
        "<div style='width:2px;height:28px;background:#D9DEE7;margin:0 auto;'></div>"
        if i < len(pipeline_steps) - 1
        else ""
    )
    st.markdown(
        f"<div style='display:flex;align-items:flex-start;gap:16px;margin-bottom:4px;'>"
        f"<div style='display:flex;flex-direction:column;align-items:center;'>"
        f"<div style='width:36px;height:36px;border-radius:50%;background:{color};"
        f"color:#fff;display:flex;align-items:center;justify-content:center;"
        f"font-weight:700;font-size:0.85rem;flex-shrink:0;'>{i+1}</div>"
        f"{connector}"
        f"</div>"
        f"<div style='background:#ffffff;border:1px solid #D9DEE7;border-radius:6px;"
        f"padding:12px 16px;flex:1;margin-bottom:12px;border-left:3px solid {color};'>"
        f"<div style='font-weight:700;color:{color};font-size:0.9rem;'>{name}</div>"
        f"<div style='font-size:0.78rem;color:#6B7788;font-style:italic;margin-bottom:4px;'>{tools}</div>"
        f"<div style='font-size:0.82rem;color:#18202B;'>{desc}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Section 3: Core schema tables ────────────────────────────────────────────
st.markdown(story_step("3", "What do the core schema tables look like?"), unsafe_allow_html=True)

tables = [
    {
        "name": "stg_touches",
        "layer": "Staging",
        "color": C_NAVY,
        "desc": "One row per user touchpoint. Normalized from raw ad platform + web events.",
        "columns": [
            ("user_id", "STRING", "Unified user identifier (email hash or device ID)"),
            ("touch_date", "DATE", "Date of the touchpoint"),
            ("channel", "STRING", "meta_paid / google_search / tiktok / organic / email"),
            ("touch_type", "STRING", "first_touch / last_touch / assist"),
            ("campaign_id", "STRING", "Source campaign reference"),
            ("converted", "BOOLEAN", "Did this user convert downstream?"),
            ("revenue", "FLOAT", "Attributed revenue (NULL until joined with CRM)"),
        ],
    },
    {
        "name": "fct_attribution",
        "layer": "Fact",
        "color": C_GREEN,
        "desc": "Channel-level attribution under all three models. One row per channel × model.",
        "columns": [
            ("channel", "STRING", "Paid channel name"),
            ("model", "STRING", "first_touch / last_touch / time_decay"),
            ("attributed_revenue", "FLOAT", "Revenue credited to this channel under this model"),
            ("attributed_conversions", "INT", "Conversions credited"),
            ("spend", "FLOAT", "Actual ad spend for this channel (period)"),
            ("roas", "FLOAT", "attributed_revenue / spend"),
        ],
    },
    {
        "name": "fct_geo_holdout",
        "layer": "Fact",
        "color": C_AMBER,
        "desc": "Region × week results from the geo holdout experiment. Treatment vs. control lift.",
        "columns": [
            ("region_id", "STRING", "DMA or geo region identifier"),
            ("week", "DATE", "Week start date"),
            ("treatment_flag", "BOOLEAN", "True = ads-on region"),
            ("channel", "STRING", "Channel being tested (e.g. meta_retargeting)"),
            ("conversions", "INT", "Conversions in region × week"),
            ("revenue", "FLOAT", "Revenue in region × week"),
            ("incremental_lift", "FLOAT", "Estimated lift vs. control (% or absolute)"),
        ],
    },
    {
        "name": "mart_budget_sim",
        "layer": "Mart",
        "color": "#7C3AED",
        "desc": "Pre-aggregated inputs for the budget reallocation simulator.",
        "columns": [
            ("channel", "STRING", "Paid channel name"),
            ("current_spend", "FLOAT", "Current weekly spend allocation"),
            ("incremental_roas", "FLOAT", "True incremental ROAS from holdout"),
            ("marginal_roas", "FLOAT", "Estimated marginal return on next $1K spend"),
            ("max_efficient_spend", "FLOAT", "Spend threshold above which ROAS degrades"),
        ],
    },
]

for table in tables:
    with st.expander(f"`{table['name']}` — {table['layer']}  ·  {table['desc']}", expanded=False):
        col_rows = "".join(
            f"<tr>"
            f"<td style='font-family:monospace;font-size:0.8rem;color:{table['color']};padding:6px 12px;border-bottom:1px solid #D9DEE7;'>{c[0]}</td>"
            f"<td style='font-size:0.78rem;color:#6B7788;padding:6px 12px;border-bottom:1px solid #D9DEE7;white-space:nowrap;'>{c[1]}</td>"
            f"<td style='font-size:0.78rem;color:#18202B;padding:6px 12px;border-bottom:1px solid #D9DEE7;'>{c[2]}</td>"
            f"</tr>"
            for c in table["columns"]
        )
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;'>"
            f"<thead><tr>"
            f"<th style='text-align:left;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.08em;color:#6B7788;padding:6px 12px;border-bottom:2px solid #D9DEE7;'>Column</th>"
            f"<th style='text-align:left;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.08em;color:#6B7788;padding:6px 12px;border-bottom:2px solid #D9DEE7;'>Type</th>"
            f"<th style='text-align:left;font-size:0.68rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.08em;color:#6B7788;padding:6px 12px;border-bottom:2px solid #D9DEE7;'>Description</th>"
            f"</tr></thead>"
            f"<tbody>{col_rows}</tbody>"
            f"</table>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Section 4: What's simplified ─────────────────────────────────────────────
st.markdown(story_step("4", "What's simplified in the synthetic version?"), unsafe_allow_html=True)

simplifications = [
    (C_RED, "Touch data", "Real touch tables have 10–50M rows/month. Synthetic version uses ~5K user journeys with statistically representative distributions."),
    (C_AMBER, "Geo holdout", "Real holdout requires 8–12 weeks of experiment run + pre-period for DiD baseline. Synthetic uses 12 weeks of pre-generated weekly data."),
    (C_NAVY, "Attribution logic", "Production attribution runs in dbt with Jinja macros that handle cross-device matching. Synthetic computes models in-memory with pandas."),
    (C_GREEN, "ROAS incrementality", "Real incremental ROAS from Meta retargeting is typically 0.1–0.3x vs. platform-reported 4–6x. Synthetic sets Meta near-zero to show the contrast."),
    ("#7C3AED", "Budget simulator", "Real simulator integrates diminishing-returns curves per channel. Synthetic uses linear ROAS × spend for demo clarity."),
    (C_GRAY, "Identity resolution", "Real pipelines join ad platform click IDs to CRM user_id via deterministic + probabilistic matching. Synthetic assumes perfect 1:1 join."),
]

cols = st.columns(2)
for i, (color, title, desc) in enumerate(simplifications):
    with cols[i % 2]:
        st.markdown(
            f"<div style='background:#F7F8FA;border:1px solid #D9DEE7;border-radius:6px;"
            f"border-left:3px solid {color};padding:14px 16px;margin-bottom:12px;'>"
            f"<div style='font-weight:700;font-size:0.82rem;color:{color};margin-bottom:4px;'>{title}</div>"
            f"<div style='font-size:0.8rem;color:#18202B;line-height:1.55;'>{desc}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()
st.markdown(
    alert(
        "In production this dashboard would connect to a live dbt project with BigQuery or Snowflake as the warehouse. "
        "The Streamlit app reads from Parquet snapshots of dbt mart models — keeping the app layer stateless and fast.",
        level="warning",
    ),
    unsafe_allow_html=True,
)
