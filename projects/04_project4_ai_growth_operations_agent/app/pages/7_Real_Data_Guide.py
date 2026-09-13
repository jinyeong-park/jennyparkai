"""Real Data Guide — What data you'd need to run this dashboard on real company data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st

from utils.theme import inject_theme, render_navigation, PRIMARY, BLUE, TEAL, GREEN, AMBER, RED, MUTED, MUTED_BAR, INK

st.set_page_config(
    page_title="Real Data Guide — Tablr Growth",
    page_icon=":material/database:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Real Data Guide</h1>",
    unsafe_allow_html=True,
)
st.caption("What data sources, schema, and pipeline this dashboard would need in a real company")

st.markdown("---")

# ── Intro ─────────────────────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
    padding:14px 18px;margin-bottom:24px;font-size:0.88rem;color:#14532d;line-height:1.7;'>
    This dashboard was built with 100% synthetic data to demonstrate analytical methodology.
    This page documents the <strong>real data sources, schema, and pipeline</strong> that would
    be required to run the same analysis on an actual B2B SaaS company.
    </div>""",
    unsafe_allow_html=True,
)

# ── Data Requirements by Page ─────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>01 — Data requirements by dashboard section</div>",
    unsafe_allow_html=True,
)

sections = [
    {
        "page": "Acquisition",
        "icon": "📣",
        "question": "Which channel acquires the most valuable customers?",
        "data_needed": [
            ("Ad performance", "Impressions, clicks, spend, CTR, CPM per campaign/ad set/creative/date", "META Ads API · TikTok Ads API · Google Ads API · LinkedIn Campaign Manager API"),
            ("Trial signups", "User ID, signup timestamp, UTM source/medium/campaign, landing page URL", "CRM (HubSpot/Salesforce) or product DB, populated via Segment"),
            ("Activation events", "User ID, event name (e.g. campaign_launched), event timestamp", "Product analytics — Mixpanel · Amplitude · PostHog · Heap · Pendo · Rudderstack · Snowplow · or custom backend event log directly to BigQuery / Snowflake"),
        ],
        "key_join": "ad_click → UTM params → trial signup → activation event",
        "refresh": "Daily",
        "hardest_part": "UTM parameters must survive the entire signup flow. Server-side attribution (not just cookies) is required to handle iOS privacy changes and cross-device gaps.",
    },
    {
        "page": "Creative Intelligence",
        "icon": "🎨",
        "question": "Which creative hook drives the lowest trial CAC?",
        "data_needed": [
            ("Creative-level ad performance", "Creative ID, impressions, clicks, spend, CTR per creative per week", "Ads APIs (creative breakdown available in META/TikTok)"),
            ("Creative metadata", "Hook type, format (video/image/carousel), target persona — internal tagging", "Internal creative management spreadsheet or naming convention"),
            ("Click-to-trial rate", "Ad clicks joined to trial signups via UTM click ID or creative ID", "Join between Ads API data and product DB"),
        ],
        "key_join": "creative_id → clicks → trial signups (via fbclid / gclid / UTM)",
        "refresh": "Daily (fatigue requires weekly trend — need ≥4 weeks of creative history)",
        "hardest_part": "Hook type is a human-defined label, not something ad platforms track. Requires a consistent internal taxonomy applied to every creative at upload time.",
    },
    {
        "page": "Retention",
        "icon": "📈",
        "question": "Are customers staying — and does it differ by acquisition channel?",
        "data_needed": [
            ("Subscription events", "Customer ID, subscription start date, status (active/churned), plan tier, churn date", "Billing system — Stripe or Chargebee"),
            ("Channel attribution", "Customer ID linked back to original acquisition channel", "Requires joining billing customer ID → trial signup → UTM channel"),
            ("Cohort assignment", "Signup week or conversion week per customer for cohort grouping", "Product DB or data warehouse"),
        ],
        "key_join": "billing customer_id → trial signup → channel attribution",
        "refresh": "Daily (subscription status changes daily; cohort curves mature over months)",
        "hardest_part": "Linking billing system customer IDs back to ad attribution. Requires a persistent user ID that survives from anonymous visitor → trial → paid subscriber.",
    },
    {
        "page": "LTV & Budget",
        "icon": "💰",
        "question": "Which channel produces the highest lifetime value per dollar spent?",
        "data_needed": [
            ("Revenue per customer", "Monthly recurring revenue (MRR), payment history, upgrade/downgrade events", "Stripe / Chargebee — MRR movements and invoice records"),
            ("Churn timing", "Exact churn date per customer to calculate observed LTV (sum of actual payments)", "Billing system churn events"),
            ("Channel spend", "Total media spend per channel per period for CPAO and LTV:CAC calculation", "Ads APIs aggregated in data warehouse"),
        ],
        "key_join": "customer MRR history → attributed channel → CPAO from ad spend",
        "refresh": "Daily for spend; monthly for LTV (cohorts need time to mature)",
        "hardest_part": "Observed LTV requires customers to have been active long enough. With a short history, you must fall back on projected LTV (avg price / churn rate) — which carries model risk.",
    },
    {
        "page": "Experiments",
        "icon": "🧪",
        "question": "Which variant wins — and is the difference real?",
        "data_needed": [
            ("Variant assignment log", "User ID, experiment ID, arm name (control/treatment), assignment timestamp", "Experimentation platform (LaunchDarkly, Optimizely, or custom flag service)"),
            ("Outcome events per variant", "Activation events, conversion events, and guardrail metrics (e.g. M1 retention) per user per arm", "Product analytics joined to variant assignment log"),
            ("Statistical inputs", "Event counts per arm to compute z-score and p-value", "Derived from variant assignment + outcome events"),
        ],
        "key_join": "user_id → variant assignment → downstream product events",
        "refresh": "Real-time variant assignment; daily outcome aggregation",
        "hardest_part": "Preventing contamination — users must not see both arms. And guardrail metrics (e.g. M1 retention) take 30 days to observe, so experiment runtime must extend well past the primary metric evaluation window.",
    },
]

for s in sections:
    with st.expander(f"**{s['icon']} {s['page']}** — {s['question']}", expanded=True):
        col_data, col_meta = st.columns([3, 1])

        with col_data:
            st.markdown("**Data needed:**")
            for label, fields, source in s["data_needed"]:
                st.markdown(
                    f"""<div style='border:1px solid #e2e8f0;border-radius:6px;padding:10px 14px;
                    margin-bottom:8px;background:#ffffff;'>
                    <div style='font-size:0.84rem;font-weight:700;color:#0f4c81;margin-bottom:4px;'>{label}</div>
                    <div style='font-size:0.82rem;color:#334155;margin-bottom:4px;'>{fields}</div>
                    <div style='font-size:0.78rem;color:#64748b;font-style:italic;'>Source: {source}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""<div style='background:#fef9ec;border:1px solid #fde68a;border-radius:6px;
                padding:8px 12px;font-size:0.82rem;color:#713f12;margin-top:4px;'>
                ⚠️ <b>Hardest part:</b> {s['hardest_part']}
                </div>""",
                unsafe_allow_html=True,
            )

        with col_meta:
            st.markdown(
                f"""<div style='background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;
                padding:14px 16px;font-size:0.83rem;'>
                <div style='color:#64748b;font-size:0.75rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.04em;margin-bottom:8px;'>Key join</div>
                <div style='color:#334155;font-family:monospace;font-size:0.78rem;line-height:1.6;
                margin-bottom:14px;'>{s['key_join']}</div>
                <div style='color:#64748b;font-size:0.75rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.04em;margin-bottom:4px;'>Refresh cadence</div>
                <div style='color:#0f4c81;font-weight:700;font-size:0.84rem;'>{s['refresh']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

st.markdown("---")

# ── Data Pipeline ─────────────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>02 — End-to-end data pipeline</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """<div style='font-size:0.84rem;color:#475569;margin-bottom:16px;'>
    In a real company, this dashboard would sit at the end of this pipeline:
    </div>""",
    unsafe_allow_html=True,
)

pipeline_steps = [
    ("Paid Media APIs", "META · TikTok · Google · LinkedIn", PRIMARY, "Campaign performance, spend, creative metrics — pulled daily via API"),
    ("Event Tracking", "Segment · Rudderstack → Mixpanel · Amplitude · PostHog · Heap · Snowplow · or direct to warehouse", BLUE, "User behavior events: trial signup, onboarding steps, campaign_launched, subscription events. Segment/Rudderstack route events to your chosen destination; PostHog and Snowplow can ingest directly without a CDP."),
    ("Billing System", "Stripe / Chargebee", TEAL, "MRR, churn, plan tier, invoice history per customer"),
    ("Data Warehouse", "BigQuery / Snowflake / Redshift", "#7c3aed", "Centralizes all sources. Attribution join happens here: ad click → user ID → billing customer ID"),
    ("Transformation", "dbt", GREEN, "Builds clean models: dim_channels, fct_activations, fct_subscriptions, cohort_retention, ltv_by_channel"),
    ("Dashboard", "This dashboard (DuckDB / Parquet)", AMBER, "Reads from transformed tables. In this portfolio version, DuckDB reads synthetic Parquet files directly"),
]

for i, (name, tools, color, desc) in enumerate(pipeline_steps):
    connector = (
        "<div style='width:2px;height:28px;background:#e2e8f0;margin:0 auto;'></div>"
        if i < len(pipeline_steps) - 1
        else ""
    )
    st.markdown(
        f"<div style='display:flex;align-items:flex-start;gap:16px;margin-bottom:4px;'>"
        f"<div style='display:flex;flex-direction:column;align-items:center;'>"
        f"<div style='width:36px;height:36px;border-radius:50%;background:{color};"
        f"display:flex;align-items:center;justify-content:center;"
        f"color:white;font-weight:800;font-size:0.85rem;flex-shrink:0;'>{i + 1}</div>"
        f"{connector}"
        f"</div>"
        f"<div style='background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;"
        f"padding:10px 16px;flex:1;margin-bottom:12px;border-left:3px solid {color};'>"
        f"<div style='font-weight:700;color:{color};font-size:0.9rem;'>{name}</div>"
        f"<div style='font-size:0.78rem;color:#64748b;font-style:italic;margin-bottom:4px;'>{tools}</div>"
        f"<div style='font-size:0.82rem;color:#334155;'>{desc}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Core Schema ───────────────────────────────────────────────────────────────
st.markdown(
    "<div class='section-header'>03 — Core tables this dashboard expects</div>",
    unsafe_allow_html=True,
)

tables = {
    "dim_trial_accounts": {
        "description": "One row per trial signup",
        "fields": [
            ("account_id", "string", "Unique trial account identifier"),
            ("trial_start_date", "date", "When the trial began"),
            ("channel", "string", "Acquisition channel (META / TIKTOK / GOOGLE_SEARCH / LINKEDIN)"),
            ("persona_segment", "string", "ICP segment label — tagged at signup or inferred from firmographics"),
            ("utm_source / utm_campaign", "string", "Raw UTM params — needed for sub-campaign attribution"),
        ],
    },
    "fact_ad_spend": {
        "description": "Daily ad performance by channel and creative",
        "fields": [
            ("date", "date", "Performance date"),
            ("channel", "string", "Ad platform"),
            ("creative_id", "string", "Creative asset identifier"),
            ("hook_type", "string", "Internal label — CONTRAST / OUTCOME / SOCIAL_PROOF etc."),
            ("impressions", "int", "Total impressions served"),
            ("clicks", "int", "Total link clicks"),
            ("spend_usd", "float", "Total media spend in USD"),
        ],
    },
    "fact_activations": {
        "description": "One row per account that completed activation (campaign_launched event)",
        "fields": [
            ("account_id", "string", "Links back to dim_trial_accounts"),
            ("activation_date", "date", "Date of first campaign launch"),
            ("days_to_activate", "int", "Days from trial start to activation"),
        ],
    },
    "fact_subscriptions": {
        "description": "One row per subscription, with status and billing info",
        "fields": [
            ("account_id", "string", "Links back to dim_trial_accounts"),
            ("subscription_tier", "string", "STARTER / GROWTH / PRO"),
            ("monthly_price_usd", "float", "MRR contributed by this subscription"),
            ("start_date", "date", "Subscription start date"),
            ("status", "string", "active / churned"),
            ("churn_date", "date", "Null if still active"),
        ],
    },
}

tab_names = list(tables.keys())
tabs = st.tabs(tab_names)

for tab, (tname, tinfo) in zip(tabs, tables.items()):
    with tab:
        st.caption(tinfo["description"])
        rows = []
        for fname, ftype, fdesc in tinfo["fields"]:
            rows.append({"Field": fname, "Type": ftype, "Description": fdesc})
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")

# ── What this simulation intentionally simplified ─────────────────────────────
st.markdown(
    "<div class='section-header'>04 — What this simulation intentionally simplified</div>",
    unsafe_allow_html=True,
)

simplifications = [
    ("Last-touch attribution only", "Real campaigns involve multiple touchpoints before conversion. Multi-touch attribution models (linear, time-decay, data-driven) would distribute credit across all touch points, not just the final click."),
    ("No view-through conversions", "Users who see but don't click an ad may still convert later. View-through windows (typically 1 day for TikTok, 7 days for META) are excluded here."),
    ("Single device / single session assumed", "Cross-device tracking requires a persistent user ID or identity graph. This simulation assumes one device per user."),
    ("Clean UTM coverage assumed", "In reality, ~10–20% of traffic arrives with missing or broken UTMs (direct, iOS Safari, email clients). The 7.6% UNKNOWN in this dashboard is conservative."),
    ("Constant churn rate for projected LTV", "Real churn rate varies by cohort age, plan tier, and acquisition channel. A survival curve model (Kaplan-Meier or BG/NBD) would be more accurate."),
    ("No seasonality or external events", "Real performance fluctuates with holidays, competitor activity, and platform algorithm changes. This simulation uses a flat weekly distribution."),
]

col1, col2 = st.columns(2)
for i, (title, detail) in enumerate(simplifications):
    col = col1 if i % 2 == 0 else col2
    with col:
        st.markdown(
            f"""<div style='border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;
            margin-bottom:10px;background:#ffffff;'>
            <div style='font-size:0.85rem;font-weight:700;color:#0f4c81;margin-bottom:6px;'>
            ☐ {title}</div>
            <div style='font-size:0.81rem;color:#475569;line-height:1.6;'>{detail}</div>
            </div>""",
            unsafe_allow_html=True,
        )
