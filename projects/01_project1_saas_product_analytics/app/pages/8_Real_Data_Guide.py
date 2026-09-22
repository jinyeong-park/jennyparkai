"""Real Data Guide — what this dashboard needs to run on real company data."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st

from utils.theme import (
    AMBER, BLUE, GREEN, MUTED, PRIMARY, RED, TEAL,
    inject_theme, render_navigation,
)

st.set_page_config(page_title="Real Data Guide | Lifecycle Analytics", layout="wide")
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Real Data Guide")
st.caption(
    "This dashboard runs on synthetic lifecycle data. "
    "This guide documents the real data sources, schema, and pipeline needed for production."
)

st.markdown(
    f"<div style='background:#eef4ff;border-left:4px solid {PRIMARY};"
    f"border-radius:0 6px 6px 0;padding:14px 18px;margin-bottom:24px;"
    f"font-size:0.84rem;color:#0b1f3a;line-height:1.6;'>"
    f"Five CSV tables power all six pages — <code>organizations</code>, <code>users</code>, "
    f"<code>event_logs</code>, <code>subscriptions</code>, and <code>experiment_assignments</code>. "
    f"In production these map 1-to-1 to warehouse tables from your product database, CRM, and billing system."
    f"</div>",
    unsafe_allow_html=True,
)

# ── Section 1: Data requirements per page ────────────────────────────────────
st.subheader("Data requirements by page")

pages = [
    {
        "name": "Users",
        "icon": "👥",
        "color": PRIMARY,
        "sources": ["Product DB (users table)", "CRM / Salesforce", "IAM / Auth provider"],
        "key_fields": "user_id, org_id, signup_timestamp, plan_tier, role",
        "refresh": "Daily",
        "note": "Needs org-level hierarchy join to segment by account size and industry vertical.",
    },
    {
        "name": "Activation",
        "icon": "⚡",
        "color": BLUE,
        "sources": ["Product event stream (Segment / Amplitude)", "Feature flag log"],
        "key_fields": "user_id, event_name, event_timestamp, properties JSON",
        "refresh": "Daily",
        "note": "Key activation events (invite_sent, integration_connected, report_exported) must be pre-defined as a milestone list.",
    },
    {
        "name": "Retention",
        "icon": "📈",
        "color": TEAL,
        "sources": ["Product event stream", "Subscription table (Stripe / Chargebee)"],
        "key_fields": "user_id, cohort_week, active_flag, subscription_status",
        "refresh": "Weekly (cohort view) / Daily (actives)",
        "note": "Cohort retention requires a stable signup_date anchor and consistent definition of 'active' (e.g. ≥1 core event in the window).",
    },
    {
        "name": "Revenue",
        "icon": "💰",
        "color": GREEN,
        "sources": ["Billing system (Stripe / Zuora)", "CRM opportunity table"],
        "key_fields": "org_id, mrr, arr, plan_tier, start_date, end_date, churn_date",
        "refresh": "Daily",
        "note": "MRR movements (new, expansion, contraction, churn, reactivation) must be derived from subscription change events, not snapshots.",
    },
    {
        "name": "Experiments",
        "icon": "🔬",
        "color": AMBER,
        "sources": ["Feature flag system (LaunchDarkly / Statsig)", "Assignment log table"],
        "key_fields": "experiment_id, user_id, variant, assigned_at, converted, metric_value",
        "refresh": "Daily (during experiment)",
        "note": "Assignment must be logged at exposure time — not at analysis time — to avoid survivor bias in conversion metrics.",
    },
    {
        "name": "Churn Risk",
        "icon": "🛡️",
        "color": RED,
        "sources": ["Event logs (engagement signals)", "Subscription table", "Support tickets (Zendesk / Intercom)"],
        "key_fields": "org_id, days_since_last_login, feature_breadth, open_tickets, mrr, plan_age_days",
        "refresh": "Daily",
        "note": "Risk score is computed from behavioral features. Support ticket volume and NPS scores materially improve precision if available.",
    },
]

for page in pages:
    st.markdown(
        f"<div style='background:#fff;border:1px solid #dce6f4;border-radius:8px;"
        f"border-left:4px solid {page['color']};padding:18px 22px;margin-bottom:12px;'>"
        f"<div style='font-weight:700;font-size:0.95rem;color:{page['color']};margin-bottom:10px;'>"
        f"{page['icon']}  {page['name']}</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;font-size:0.82rem;'>"
        f"<div><div style='font-weight:700;color:#5b7194;font-size:0.67rem;text-transform:uppercase;"
        f"letter-spacing:0.09em;margin-bottom:5px;'>Source Systems</div>"
        + "".join(
            f"<div style='color:#0b1f3a;padding:2px 0;'>• {s}</div>"
            for s in page["sources"]
        ) +
        f"</div>"
        f"<div><div style='font-weight:700;color:#5b7194;font-size:0.67rem;text-transform:uppercase;"
        f"letter-spacing:0.09em;margin-bottom:5px;'>Key Fields</div>"
        f"<div style='color:#0b1f3a;font-family:monospace;font-size:0.77rem;line-height:1.65;'>{page['key_fields']}</div>"
        f"<div style='margin-top:9px;font-weight:700;color:#5b7194;font-size:0.67rem;text-transform:uppercase;"
        f"letter-spacing:0.09em;margin-bottom:4px;'>Refresh</div>"
        f"<div style='color:#0b1f3a;'>{page['refresh']}</div>"
        f"</div>"
        f"<div><div style='font-weight:700;color:#5b7194;font-size:0.67rem;text-transform:uppercase;"
        f"letter-spacing:0.09em;margin-bottom:5px;'>Note</div>"
        f"<div style='color:#0b1f3a;line-height:1.55;'>{page['note']}</div>"
        f"</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Section 2: End-to-end pipeline ───────────────────────────────────────────
st.subheader("End-to-end data pipeline")

pipeline_steps = [
    (
        "Product Database",
        "PostgreSQL · MySQL · Aurora",
        PRIMARY,
        "Source of truth for users, organizations, and subscriptions. "
        "Row-level changes captured via CDC (Debezium / Fivetran) into the warehouse.",
    ),
    (
        "Event Stream",
        "Segment · Amplitude · Rudderstack",
        BLUE,
        "User-level behavioral events with properties (event_name, user_id, timestamp, metadata). "
        "Activation milestones and engagement signals flow through here.",
    ),
    (
        "Billing System",
        "Stripe · Chargebee · Zuora",
        TEAL,
        "MRR movements, plan changes, churn events, invoice history. "
        "Critical for revenue page and churn risk feature engineering.",
    ),
    (
        "Data Warehouse",
        "BigQuery · Snowflake · Redshift",
        GREEN,
        "All sources land here. Partitioned by date, clustered by org_id. "
        "Raw → Staging → Mart pattern via dbt transformation layer.",
    ),
    (
        "dbt Transforms",
        "dbt Core · dbt Cloud",
        AMBER,
        "stg_users, stg_events → fct_activation, fct_retention_cohorts, fct_mrr_movements, "
        "fct_churn_risk. Experiment assignment joins happen here.",
    ),
    (
        "Dashboard",
        "Streamlit · Plotly",
        RED,
        "Reads Parquet snapshots of dbt mart outputs. "
        "No raw SQL in app code — all business logic lives in dbt models.",
    ),
]

for i, (name, tools, color, desc) in enumerate(pipeline_steps):
    connector = (
        "<div style='width:2px;height:26px;background:#dce6f4;margin:0 auto;'></div>"
        if i < len(pipeline_steps) - 1
        else ""
    )
    st.markdown(
        f"<div style='display:flex;align-items:flex-start;gap:16px;margin-bottom:4px;'>"
        f"<div style='display:flex;flex-direction:column;align-items:center;'>"
        f"<div style='width:36px;height:36px;border-radius:50%;background:{color};"
        f"color:#fff;display:flex;align-items:center;justify-content:center;"
        f"font-weight:800;font-size:0.85rem;flex-shrink:0;'>{i + 1}</div>"
        f"{connector}"
        f"</div>"
        f"<div style='background:#fff;border:1px solid #dce6f4;border-radius:8px;"
        f"padding:12px 16px;flex:1;margin-bottom:12px;border-left:3px solid {color};'>"
        f"<div style='font-weight:700;color:{color};font-size:0.9rem;'>{name}</div>"
        f"<div style='font-size:0.77rem;color:{MUTED};font-style:italic;margin-bottom:4px;'>{tools}</div>"
        f"<div style='font-size:0.82rem;color:#0b1f3a;'>{desc}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ── Section 3: Core schema tables ────────────────────────────────────────────
st.subheader("Core schema tables")

tables = [
    {
        "name": "organizations",
        "layer": "Staging",
        "color": PRIMARY,
        "desc": "One row per account. Source of account-level segmentation.",
        "columns": [
            ("org_id", "STRING", "Unique account identifier"),
            ("name", "STRING", "Company name"),
            ("created_at", "TIMESTAMP", "Account creation date (cohort anchor)"),
            ("plan_tier", "STRING", "free / starter / professional / enterprise"),
            ("industry", "STRING", "Vertical for segment analysis"),
            ("employee_count", "INT", "Proxy for account size"),
        ],
    },
    {
        "name": "users",
        "layer": "Staging",
        "color": BLUE,
        "desc": "One row per user. Linked to org via org_id.",
        "columns": [
            ("user_id", "STRING", "Unique user identifier"),
            ("org_id", "STRING", "FK → organizations"),
            ("signup_timestamp", "TIMESTAMP", "User signup date"),
            ("role", "STRING", "admin / member / viewer"),
            ("last_active_at", "TIMESTAMP", "Last product activity timestamp"),
        ],
    },
    {
        "name": "event_logs",
        "layer": "Staging",
        "color": TEAL,
        "desc": "One row per user event. Powers activation milestones and engagement scoring.",
        "columns": [
            ("event_id", "STRING", "Unique event identifier"),
            ("user_id", "STRING", "FK → users"),
            ("org_id", "STRING", "Denormalized for partition efficiency"),
            ("event_name", "STRING", "invite_sent / integration_connected / report_exported / …"),
            ("event_timestamp", "TIMESTAMP", "UTC timestamp of event"),
            ("properties", "JSON", "Event-specific metadata (feature, context, etc.)"),
        ],
    },
    {
        "name": "subscriptions",
        "layer": "Staging",
        "color": GREEN,
        "desc": "One row per subscription period. Change events derive MRR movements.",
        "columns": [
            ("subscription_id", "STRING", "Unique subscription identifier"),
            ("org_id", "STRING", "FK → organizations"),
            ("plan_tier", "STRING", "Plan at this subscription period"),
            ("mrr", "FLOAT", "Monthly recurring revenue in USD"),
            ("start_date", "DATE", "Subscription start"),
            ("end_date", "DATE", "Subscription end (NULL if active)"),
            ("churn_reason", "STRING", "voluntary / involuntary / downgrade (NULL if active)"),
        ],
    },
    {
        "name": "experiment_assignments",
        "layer": "Staging",
        "color": AMBER,
        "desc": "One row per user × experiment assignment. Logged at exposure time.",
        "columns": [
            ("assignment_id", "STRING", "Unique assignment record"),
            ("experiment_id", "STRING", "Experiment identifier"),
            ("user_id", "STRING", "FK → users"),
            ("variant", "STRING", "control / treatment (or treatment_a / treatment_b)"),
            ("assigned_at", "TIMESTAMP", "Assignment timestamp — must precede metric collection"),
            ("converted", "BOOLEAN", "Primary conversion outcome"),
            ("metric_value", "FLOAT", "Continuous metric (e.g. activation_days, revenue_30d)"),
        ],
    },
]

for table in tables:
    with st.expander(
        f"`{table['name']}` — {table['layer']}  ·  {table['desc']}", expanded=False
    ):
        col_rows = "".join(
            f"<tr>"
            f"<td style='font-family:monospace;font-size:0.8rem;color:{table['color']};"
            f"padding:6px 12px;border-bottom:1px solid #dce6f4;'>{c[0]}</td>"
            f"<td style='font-size:0.78rem;color:{MUTED};padding:6px 12px;"
            f"border-bottom:1px solid #dce6f4;white-space:nowrap;'>{c[1]}</td>"
            f"<td style='font-size:0.78rem;color:#0b1f3a;padding:6px 12px;"
            f"border-bottom:1px solid #dce6f4;'>{c[2]}</td>"
            f"</tr>"
            for c in table["columns"]
        )
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;'>"
            f"<thead><tr>"
            f"<th style='text-align:left;font-size:0.67rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.09em;color:{MUTED};padding:6px 12px;"
            f"border-bottom:2px solid #dce6f4;'>Column</th>"
            f"<th style='text-align:left;font-size:0.67rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.09em;color:{MUTED};padding:6px 12px;"
            f"border-bottom:2px solid #dce6f4;'>Type</th>"
            f"<th style='text-align:left;font-size:0.67rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.09em;color:{MUTED};padding:6px 12px;"
            f"border-bottom:2px solid #dce6f4;'>Description</th>"
            f"</tr></thead>"
            f"<tbody>{col_rows}</tbody>"
            f"</table>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Section 4: What's simplified ─────────────────────────────────────────────
st.subheader("What's simplified in the synthetic version")

simplifications = [
    (PRIMARY, "Scale", "Real product DBs have millions of users and billions of event rows. Synthetic uses ~2K orgs / 8K users / 180K events — enough to show all patterns without I/O overhead."),
    (BLUE, "Activation milestones", "Real activation events vary by product. Synthetic hard-codes five milestone types. Production would configure these per product area with a feature registry."),
    (TEAL, "Retention definition", "Real 'active' definitions are debated (DAU vs. WAU, core vs. any action). Synthetic uses a single binary flag. Production would parameterize the definition."),
    (GREEN, "MRR movements", "Real MRR waterfall requires change-data-capture on subscription events. Synthetic pre-computes movements as enum flags in a single CSV."),
    (AMBER, "Experiment stats", "Synthetic uses a simplified t-test. Production would use sequential testing (e.g. CUPED, mixture models) to control for peeking and novelty effects."),
    (RED, "Churn risk model", "Synthetic scores risk with a weighted rule engine. Production would use a trained ML model (gradient boosted trees) with SHAP explanations per account."),
]

cols = st.columns(2)
for i, (color, title, desc) in enumerate(simplifications):
    with cols[i % 2]:
        st.markdown(
            f"<div style='background:#f6f9ff;border:1px solid #dce6f4;border-radius:8px;"
            f"border-left:3px solid {color};padding:14px 16px;margin-bottom:12px;'>"
            f"<div style='font-weight:700;font-size:0.82rem;color:{color};margin-bottom:4px;'>{title}</div>"
            f"<div style='font-size:0.8rem;color:#0b1f3a;line-height:1.55;'>{desc}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()
st.markdown(
    f"<div style='background:#fff8ec;border-left:3px solid {AMBER};"
    f"border-radius:0 6px 6px 0;padding:12px 16px;font-size:0.82rem;"
    f"color:#0b1f3a;line-height:1.6;'>"
    f"In production this dashboard would connect to a live dbt project with BigQuery or Snowflake. "
    f"The Streamlit app reads from Parquet snapshots of dbt mart models — keeping the app layer "
    f"stateless, fast, and testable independently of the warehouse."
    f"</div>",
    unsafe_allow_html=True,
)
