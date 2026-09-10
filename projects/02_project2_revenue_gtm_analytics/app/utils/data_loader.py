"""
data_loader.py
==============
Cached data layer for the Revenue Intelligence Streamlit dashboard.
Wraps mart_simulator.py functions with @st.cache_data so each
mart table is built once per session.
"""

import os
import sys

import pandas as pd
import streamlit as st

# Allow importing mart_simulator from the python/ directory
_PYTHON_DIR = os.path.join(os.path.dirname(__file__), "../../python")
sys.path.insert(0, _PYTHON_DIR)

from mart_simulator import (  # noqa: E402
    build_dim_account,
    build_fct_bookings,
    build_fct_customer_lifecycle,
    build_fct_pipeline,
    build_fct_revenue,
    build_int_gtm_funnel,
    build_stg_customer_success,
    build_stg_leads,
    build_stg_opps,
)

# ── Consistent colour palette ──────────────────────────────────────────────────
SEGMENT_COLORS = {
    "Enterprise":  "#4C72B0",
    "Mid-Market":  "#55A868",
    "SMB":         "#C44E52",
    "Unknown":     "#C0C0C0",
}

RISK_COLORS = {
    "High Risk":   "#C44E52",
    "Medium Risk": "#CCB974",
    "On Track":    "#55A868",
}

STAGE_COLORS = {
    "Collected":     "#55A868",
    "Billed":        "#4C72B0",
    "Contracted":    "#CCB974",
    "Booking Only":  "#C44E52",
}

HEALTH_COLORS = {
    "Healthy":          "#55A868",
    "Needs Attention":  "#CCB974",
    "At Risk":          "#C44E52",
    "Unknown":          "#C0C0C0",
}


# ── Cached loaders ─────────────────────────────────────────────────────────────

@st.cache_data
def get_dim_account() -> pd.DataFrame:
    return build_dim_account()


@st.cache_data
def get_fct_pipeline() -> pd.DataFrame:
    return build_fct_pipeline()


@st.cache_data
def get_fct_bookings() -> pd.DataFrame:
    return build_fct_bookings()


@st.cache_data
def get_fct_revenue() -> pd.DataFrame:
    return build_fct_revenue()


@st.cache_data
def get_fct_lifecycle() -> pd.DataFrame:
    return build_fct_customer_lifecycle()


@st.cache_data
def get_gtm_funnel() -> pd.DataFrame:
    return build_int_gtm_funnel()


@st.cache_data
def get_stg_leads() -> pd.DataFrame:
    return build_stg_leads()


@st.cache_data
def get_stg_opps() -> pd.DataFrame:
    return build_stg_opps()


@st.cache_data
def get_stg_cs() -> pd.DataFrame:
    return build_stg_customer_success()


# ── Pre-computed overview metrics ──────────────────────────────────────────────

@st.cache_data
def get_overview_metrics() -> dict:
    bookings  = get_fct_bookings()
    pipeline  = get_fct_pipeline()
    lifecycle = get_fct_lifecycle()
    cs        = get_stg_cs()

    total_bookings        = bookings["crm_booking_amount"].sum()
    total_collected       = bookings["total_collected_usd"].sum()
    total_open_pipeline   = pipeline["pipeline_amount"].sum()
    weighted_pipeline     = pipeline["weighted_pipeline_amount"].sum()
    pct_churned           = cs["is_churned"].mean()
    pct_healthy           = (cs["health_tier"] == "Healthy").mean()
    at_risk_pipeline      = pipeline.loc[
        pipeline["pipeline_risk"] == "High Risk", "pipeline_amount"
    ].sum()
    high_risk_pct         = at_risk_pipeline / total_open_pipeline if total_open_pipeline else 0

    return {
        "total_bookings":       total_bookings,
        "total_collected":      total_collected,
        "collection_rate":      total_collected / total_bookings if total_bookings else 0,
        "total_open_pipeline":  total_open_pipeline,
        "weighted_pipeline":    weighted_pipeline,
        "high_risk_pipeline":   at_risk_pipeline,
        "high_risk_pct":        high_risk_pct,
        "pct_churned":          pct_churned,
        "pct_healthy":          pct_healthy,
        "open_deals":           len(pipeline),
        "won_deals":            len(bookings),
    }


@st.cache_data
def get_revenue_chain() -> dict:
    bookings = get_fct_bookings()
    return {
        "crm_bookings":    bookings["crm_booking_amount"].sum(),
        "contract_value":  bookings["contract_value"].sum(),
        "billed":          bookings["total_billed_usd"].sum(),
        "collected":       bookings["total_collected_usd"].sum(),
        "at_risk":         bookings["total_at_risk_usd"].fillna(0).sum(),
        "failed":          bookings["total_failed_usd"].fillna(0).sum(),
    }
