"""
Real Data Guide
===============
What data sources, schema, and pipeline this dashboard would need
to run on real company data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pandas as pd
import streamlit as st

from utils.theme import (
    C_NAVY, C_BLUE, C_TEAL, C_GREEN, C_AMBER, C_RED, C_GRAY,
    inject_css, alert, insight, story_step,
)

st.set_page_config(page_title="Real Data Guide — Revenue Intelligence", layout="wide")
inject_css(st)

with st.sidebar:
    st.markdown("## Revenue Intelligence")
    st.markdown("Real data requirements")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1>Real Data Guide</h1>",
    unsafe_allow_html=True,
)
st.caption("What data sources, schema, and pipeline this dashboard would need in a real company")

st.markdown("---")

st.markdown(
    alert(
        "This dashboard was built with 100% synthetic data to demonstrate analytical methodology. "
        "This page documents the <strong>real data sources, schema, and pipeline</strong> "
        "that would be required to run the same analysis on an actual B2B SaaS company.",
        "info",
    ),
    unsafe_allow_html=True,
)

# ── Section 1: Data requirements by page ─────────────────────────────────────
st.markdown(story_step("01", "Data requirements by dashboard section"), unsafe_allow_html=True)

sections = [
    {
        "page": "GTM Funnel",
        "icon": "📣",
        "question": "Where does the funnel leak — and which sources convert best?",
        "data_needed": [
            (
                "Lead records",
                "Lead ID, created date, source (paid / organic / referral / outbound), MQL date, disqualification reason",
                "CRM — HubSpot · Salesforce",
            ),
            (
                "Opportunity records",
                "Opportunity ID, account ID, stage, amount, expected close date, owner, segment (Enterprise / Mid-Market / SMB)",
                "CRM — HubSpot · Salesforce",
            ),
            (
                "Closed-Won & Closed-Lost",
                "Win/loss outcome, close date, ARR, reason (won: competitive / inbound · lost: price / timing / fit)",
                "CRM — stage history table or custom field",
            ),
            (
                "Lifecycle stage transitions",
                "Account ID, transition timestamp, from_stage, to_stage — for funnel velocity and stuck-deal detection",
                "CRM stage history log or custom event tracking",
            ),
        ],
        "key_join": "account_id → lead → opportunity → close outcome",
        "refresh": "Daily",
        "hardest_part": (
            "Lead-to-account matching. Marketing leads and CRM accounts use different IDs "
            "and the same company may appear under multiple domains. "
            "A probabilistic matching step (email domain + company name normalization) is required "
            "before the funnel can be stitched together cleanly."
        ),
    },
    {
        "page": "Revenue Reconciliation",
        "icon": "💰",
        "question": "Why does CRM bookings overstate recognized revenue — and by how much?",
        "data_needed": [
            (
                "CRM bookings",
                "Opportunity ID, booking amount, booking date, contract term, ARR vs. one-time split",
                "CRM — Salesforce Opportunities or HubSpot Deals",
            ),
            (
                "Billing & invoices",
                "Invoice ID, customer ID, invoice date, billed amount, payment status (paid / pending / failed)",
                "Billing system — Stripe · Chargebee · Recurly",
            ),
            (
                "Revenue recognition records",
                "Contract ID, recognition schedule, recognized amount per period, deferred balance",
                "Revenue recognition tool — Maxio (formerly SaaSOptics) · Zuora · Netsuite Rev Rec",
            ),
            (
                "Contract amendments",
                "Upsell, downsell, cancellation, and ramp schedules per contract — required to reconcile ARR movements",
                "CRM + billing system — must be joined on a shared contract_id",
            ),
        ],
        "key_join": "opportunity_id → contract_id → invoice_id → recognition_schedule",
        "refresh": "Daily for billing; monthly close for revenue recognition",
        "hardest_part": (
            "The CRM-to-billing join. Sales often closes opportunities with slightly different amounts, "
            "terms, or start dates than what billing actually invoices. "
            "Reconciling requires a contract_id that exists in both systems — "
            "which is rarely set up correctly without a deliberate integration."
        ),
    },
    {
        "page": "Pipeline",
        "icon": "📊",
        "question": "Is the pipeline healthy — and what is the realistic forecast?",
        "data_needed": [
            (
                "Pipeline snapshots",
                "Daily snapshot of all open opportunities: stage, amount, close date, days in stage, last activity date",
                "CRM — daily extract or Change Data Capture (CDC) into data warehouse",
            ),
            (
                "Historical win rates by segment & stage",
                "Closed outcomes over trailing 12 months per segment and entry stage — used to weight pipeline",
                "CRM closed history — requires at least 6 months of data to be statistically meaningful",
            ),
            (
                "Deal velocity",
                "Median days from created to close by segment, source, and stage — for stuck-deal detection",
                "CRM stage history with timestamps",
            ),
            (
                "Activity log",
                "Calls, emails, meetings per opportunity and date — for engagement scoring and no-touch detection",
                "CRM activity log · Outreach · Salesloft · Gong",
            ),
        ],
        "key_join": "opportunity_id → daily_snapshot → stage_history → activity_log",
        "refresh": "Daily (pipeline changes intraday but daily snapshots are sufficient for weekly review)",
        "hardest_part": (
            "Pipeline inflation. Reps often keep stale deals open past expected close date. "
            "A 'days since last stage change' flag catches stuck deals, "
            "but it requires CRM stage history — which many teams do not enable by default. "
            "Without it, weighted pipeline will be systematically overstated."
        ),
    },
    {
        "page": "Customer Health",
        "icon": "💚",
        "question": "Which accounts are at risk — before they tell you they're leaving?",
        "data_needed": [
            (
                "Product usage events",
                "Account ID, user ID, event name, event timestamp — key events: login, feature_used, report_exported, integration_connected",
                "Product analytics — Mixpanel · Amplitude · PostHog · Heap · Segment → warehouse",
            ),
            (
                "Subscription & MRR",
                "Account ID, plan tier, MRR, contract start/end date, auto-renewal flag",
                "Billing system — Stripe · Chargebee",
            ),
            (
                "Support ticket history",
                "Account ID, ticket date, severity, resolution time, sentiment — high-severity open tickets are a leading churn signal",
                "Support platform — Zendesk · Intercom · Freshdesk",
            ),
            (
                "NPS / CSAT scores",
                "Account ID, survey date, score, verbatim feedback — low NPS with declining usage is the strongest churn predictor",
                "Survey tool — Delighted · Medallia · in-product survey via Pendo or Intercom",
            ),
        ],
        "key_join": "account_id → product_events → billing → support_tickets → nps_scores",
        "refresh": "Daily for usage events; real-time for support tickets",
        "hardest_part": (
            "The account_id join across systems. Product analytics uses an anonymous user_id, "
            "billing uses a customer_id, and CRM uses an account_id. "
            "An identity resolution step — mapping anonymous_id → user_id → account_id — "
            "is required, and it breaks every time a customer changes their SSO domain or email."
        ),
    },
]

for s in sections:
    with st.expander(f"**{s['icon']} {s['page']}** — {s['question']}", expanded=True):
        col_data, col_meta = st.columns([3, 1])

        with col_data:
            st.markdown("**Data needed:**")
            for label, fields, source in s["data_needed"]:
                st.markdown(
                    f"""<div style='border:1px solid #D9DEE7;border-radius:3px;padding:10px 14px;
                    margin-bottom:8px;background:#FFFFFF;'>
                    <div style='font-size:0.84rem;font-weight:700;color:{C_NAVY};margin-bottom:4px;'>{label}</div>
                    <div style='font-size:0.82rem;color:#18202B;margin-bottom:4px;'>{fields}</div>
                    <div style='font-size:0.78rem;color:{C_GRAY};font-style:italic;'>Source: {source}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""<div style='background:#FDF3E7;border:1px solid #F0D5B0;border-radius:3px;
                padding:8px 12px;font-size:0.82rem;color:#5C3400;margin-top:4px;'>
                ⚠️ <b>Hardest part:</b> {s['hardest_part']}
                </div>""",
                unsafe_allow_html=True,
            )

        with col_meta:
            st.markdown(
                f"""<div style='background:#F0F4FA;border:1px solid #D9DEE7;border-radius:3px;
                padding:14px 16px;font-size:0.83rem;'>
                <div style='color:{C_GRAY};font-size:0.72rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.06em;margin-bottom:8px;'>Key join</div>
                <div style='color:#18202B;font-family:monospace;font-size:0.77rem;line-height:1.7;
                margin-bottom:14px;'>{s['key_join']}</div>
                <div style='color:{C_GRAY};font-size:0.72rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.06em;margin-bottom:4px;'>Refresh cadence</div>
                <div style='color:{C_NAVY};font-weight:700;font-size:0.84rem;'>{s['refresh']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

st.markdown("---")

# ── Section 2: End-to-end pipeline ───────────────────────────────────────────
st.markdown(story_step("02", "End-to-end data pipeline"), unsafe_allow_html=True)

st.markdown(
    "<div style='font-size:0.84rem;color:#4E5B6B;margin-bottom:16px;'>"
    "In a real company, this dashboard would sit at the end of this pipeline:"
    "</div>",
    unsafe_allow_html=True,
)

pipeline_steps = [
    (
        "Source Systems",
        "CRM (HubSpot / Salesforce) · Billing (Stripe / Chargebee) · Product Analytics (Mixpanel / Amplitude / PostHog) · Support (Zendesk) · NPS (Delighted)",
        C_NAVY,
        "Raw transactional data: leads, opportunities, invoices, product events, support tickets, and survey responses. Each system has its own ID scheme and refresh cadence.",
    ),
    (
        "Ingestion / CDC",
        "Fivetran · Airbyte · Census · or native API connectors",
        C_BLUE,
        "Moves raw data into the warehouse. Change Data Capture (CDC) tracks row-level changes in CRM so pipeline snapshots can be reconstructed historically without full re-loads.",
    ),
    (
        "Data Warehouse",
        "BigQuery · Snowflake · Redshift",
        C_TEAL,
        "Central storage for all source tables. The account_id identity join happens here: anonymous_id → user_id → account_id → billing customer_id.",
    ),
    (
        "Transformation (dbt)",
        "dbt Core or Cloud",
        "#7c3aed",
        "Builds clean, tested models: dim_accounts, stg_leads, stg_opportunities, fct_pipeline, fct_revenue_chain, fct_lifecycle, fct_customer_health. Metric definitions live as code — no spreadsheet formulas.",
    ),
    (
        "Dashboard",
        "This dashboard (DuckDB / Parquet)",
        C_AMBER,
        "Reads from transformed tables. In this portfolio version, DuckDB reads synthetic Parquet files that mirror the schema of the dbt mart models.",
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
        f"<div style='width:34px;height:34px;border-radius:50%;background:{color};"
        f"display:flex;align-items:center;justify-content:center;"
        f"color:white;font-weight:800;font-size:0.82rem;flex-shrink:0;'>{i + 1}</div>"
        f"{connector}"
        f"</div>"
        f"<div style='background:#FFFFFF;border:1px solid #D9DEE7;border-radius:3px;"
        f"padding:10px 16px;flex:1;margin-bottom:4px;border-left:3px solid {color};'>"
        f"<div style='font-weight:700;color:{color};font-size:0.88rem;'>{name}</div>"
        f"<div style='font-size:0.77rem;color:{C_GRAY};font-style:italic;margin-bottom:4px;'>{tools}</div>"
        f"<div style='font-size:0.82rem;color:#18202B;'>{desc}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Section 3: Core schema ────────────────────────────────────────────────────
st.markdown(story_step("03", "Core tables this dashboard expects"), unsafe_allow_html=True)

tables = {
    "dim_accounts": {
        "description": "One row per account — master reference table",
        "fields": [
            ("account_id", "string", "Unique account identifier — must be consistent across CRM, billing, and product"),
            ("account_name", "string", "Company name"),
            ("segment", "string", "Enterprise / Mid-Market / SMB — firmographic classification"),
            ("industry", "string", "Industry vertical"),
            ("region", "string", "Geographic region"),
            ("created_date", "date", "When the account was first created in CRM"),
            ("csm_owner", "string", "Assigned Customer Success Manager"),
        ],
    },
    "stg_leads": {
        "description": "One row per marketing lead",
        "fields": [
            ("lead_id", "string", "CRM lead identifier"),
            ("account_id", "string", "Matched account — requires lead-to-account resolution"),
            ("created_date", "date", "Lead creation date"),
            ("source", "string", "Lead source: paid_search / organic / outbound / referral / event"),
            ("lifecycle_stage", "string", "Current stage: MQL / SQL / Opportunity / Closed-Won / Disqualified"),
            ("mql_date", "date", "Date lead reached MQL threshold"),
        ],
    },
    "fct_pipeline": {
        "description": "Daily snapshot of all open opportunities",
        "fields": [
            ("snapshot_date", "date", "Date of this pipeline snapshot"),
            ("opportunity_id", "string", "CRM opportunity identifier"),
            ("account_id", "string", "Links to dim_accounts"),
            ("stage", "string", "Sales stage: Discovery / Demo / Proposal / Negotiation / Closed-Won / Closed-Lost"),
            ("amount_usd", "float", "Opportunity ARR in USD"),
            ("expected_close_date", "date", "Rep-entered close date"),
            ("days_in_stage", "int", "Days the deal has been in its current stage"),
            ("last_activity_date", "date", "Date of most recent CRM activity log entry"),
        ],
    },
    "fct_revenue_chain": {
        "description": "Reconciliation bridge from bookings to cash",
        "fields": [
            ("account_id", "string", "Links to dim_accounts"),
            ("contract_id", "string", "Shared key between CRM opportunity and billing system"),
            ("booking_arr", "float", "ARR as recorded in CRM at close"),
            ("billed_amount", "float", "Amount invoiced by billing system"),
            ("recognized_amount", "float", "Revenue recognized per ASC 606 / IFRS 15 schedule"),
            ("cash_collected", "float", "Payments actually received"),
            ("period_date", "date", "Accounting period this row covers"),
        ],
    },
    "fct_customer_health": {
        "description": "One row per account per period — health scoring inputs",
        "fields": [
            ("account_id", "string", "Links to dim_accounts"),
            ("period_date", "date", "Health score snapshot date"),
            ("dau_7d", "int", "Daily active users over trailing 7 days"),
            ("feature_adoption_score", "float", "0–1 score based on key feature usage breadth"),
            ("open_high_severity_tickets", "int", "Count of unresolved P1/P2 support tickets"),
            ("last_nps_score", "int", "Most recent NPS response (0–10)"),
            ("mrr_usd", "float", "Current MRR for this account"),
            ("health_tier", "string", "Healthy / Needs Attention / At Risk — derived classification"),
        ],
    },
}

tab_names = list(tables.keys())
tabs = st.tabs(tab_names)

for tab, (tname, tinfo) in zip(tabs, tables.items()):
    with tab:
        st.caption(tinfo["description"])
        rows = [
            {"Field": fname, "Type": ftype, "Description": fdesc}
            for fname, ftype, fdesc in tinfo["fields"]
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Section 4: What this simulation simplified ────────────────────────────────
st.markdown(story_step("04", "What this simulation intentionally simplified"), unsafe_allow_html=True)

simplifications = [
    (
        "Single-touch attribution only",
        "Real B2B deals involve 6–12 touchpoints across marketing and sales over weeks or months. "
        "Multi-touch attribution (linear, U-shaped, W-shaped, time-decay) distributes credit across all touches. "
        "This simulation assigns source at lead creation only.",
    ),
    (
        "No deal influence or assisted revenue",
        "In real pipelines, marketing campaigns often influence deals that were sourced by outbound. "
        "'Influenced pipeline' and 'sourced pipeline' are tracked separately — "
        "conflating them overstates or understates marketing contribution depending on the model.",
    ),
    (
        "Static health scoring",
        "The health score uses a deterministic point-based formula. "
        "Real health models incorporate time-weighted usage trends, "
        "segment-specific usage baselines, and predictive models trained on historical churn outcomes.",
    ),
    (
        "No payment failure or dunning",
        "Revenue reconciliation omits involuntary churn from failed payments. "
        "In real billing data, 10–15% of churn is from card failures — "
        "a recoverable category that requires a dunning flow distinct from voluntary cancellations.",
    ),
    (
        "Clean account identity assumed",
        "Every lead, opportunity, invoice, and product event is assumed to share a consistent account_id. "
        "In reality, identity resolution (email domain matching, CRM de-duplication) "
        "is one of the most time-consuming data engineering tasks in B2B analytics.",
    ),
    (
        "No seasonality or deal-push behavior",
        "Real pipeline data clusters heavily at quarter-end due to rep deal-pushing. "
        "This creates artifacts in velocity and stage-duration metrics "
        "that require quarter-boundary awareness when computing medians.",
    ),
]

col1, col2 = st.columns(2)
for i, (title, detail) in enumerate(simplifications):
    col = col1 if i % 2 == 0 else col2
    with col:
        st.markdown(
            f"""<div style='border:1px solid #D9DEE7;border-radius:3px;padding:12px 14px;
            margin-bottom:10px;background:#FFFFFF;'>
            <div style='font-size:0.85rem;font-weight:700;color:{C_NAVY};margin-bottom:6px;'>
            ☐ {title}</div>
            <div style='font-size:0.81rem;color:#4E5B6B;line-height:1.6;'>{detail}</div>
            </div>""",
            unsafe_allow_html=True,
        )
