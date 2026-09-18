"""
data.py  —  Load raw CSVs and compute all 5 mart DataFrames in-memory.
Mirrors the BigQuery mart SQL logic using pandas.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


# ── Raw data loader ────────────────────────────────────────────────────────────
@st.cache_data
def load_raw():
    leads = pd.read_csv(RAW_DIR / "raw_leads.csv")
    leads["submitted_at"] = pd.to_datetime(leads["submitted_at"], utc=True)
    leads["month"] = leads["submitted_at"].dt.to_period("M").dt.to_timestamp("s").dt.tz_localize(None)

    ad_perf = pd.read_csv(RAW_DIR / "raw_ad_performance.csv")
    ad_perf["performance_date"] = pd.to_datetime(ad_perf["performance_date"])
    ad_perf["month"] = ad_perf["performance_date"].dt.to_period("M").dt.to_timestamp("s")

    routing = pd.read_csv(RAW_DIR / "raw_routing_attempts.csv")
    routing["routed_at"] = pd.to_datetime(routing["routed_at"], utc=True)
    routing["route_date"] = routing["routed_at"].dt.date

    revenue = pd.read_csv(RAW_DIR / "raw_revenue_events.csv")
    revenue["revenue_timestamp"] = pd.to_datetime(revenue["revenue_timestamp"], utc=True)

    partners = pd.read_csv(RAW_DIR / "raw_partners.csv")

    quote = pd.read_csv(RAW_DIR / "raw_quote_events.csv")
    quote["event_timestamp"] = pd.to_datetime(quote["event_timestamp"], utc=True)
    quote["month"] = quote["event_timestamp"].dt.to_period("M").dt.to_timestamp("s").dt.tz_localize(None)

    return leads, ad_perf, routing, revenue, partners, quote


# ── Mart 1: Lead Funnel ────────────────────────────────────────────────────────
@st.cache_data
def mart_lead_funnel(leads, quote):
    # Sessions layer from quote events
    sess = quote.groupby(["month", "channel", "insurance_vertical"]).agg(
        sessions        = ("session_id", "nunique"),
        quote_starts    = ("event_name", lambda x: (x == "quote_started").sum()),
        quote_completions = ("event_name", lambda x: (x == "quote_completed").sum()),
    ).reset_index()

    # Leads layer
    ld = leads.groupby(["month", "channel", "insurance_vertical"]).agg(
        leads_submitted  = ("lead_id", "nunique"),
        valid_leads      = ("is_valid",     lambda x: (x == True).sum()),
        duplicate_leads  = ("is_duplicate", lambda x: (x == True).sum()),
    ).reset_index()

    df = sess.merge(ld, on=["month", "channel", "insurance_vertical"], how="left")

    df["session_to_quote_rate"]          = (df["quote_starts"]       / df["sessions"]).round(3)
    df["quote_start_to_completion_rate"] = (df["quote_completions"]  / df["quote_starts"]).round(3)
    df["completion_to_lead_rate"]        = (df["leads_submitted"]    / df["quote_completions"]).round(3)
    df["overall_cvr"]                    = (df["leads_submitted"]    / df["sessions"]).round(3)
    df["valid_lead_rate"]                = (df["valid_leads"]        / df["leads_submitted"]).round(3)
    df["duplicate_rate"]                 = (df["duplicate_leads"]    / df["leads_submitted"]).round(3)

    return df.sort_values(["month", "channel", "insurance_vertical"])


# ── Mart 2: Campaign Performance ──────────────────────────────────────────────
@st.cache_data
def mart_campaign_performance(leads, ad_perf, revenue):
    # Step 1: spend per campaign × month
    spend = ad_perf.groupby(["month", "campaign_id", "channel", "insurance_vertical"]).agg(
        total_spend      = ("spend", "sum"),
        impressions      = ("impressions", "sum"),
        clicks           = ("clicks", "sum"),
        platform_leads   = ("platform_reported_leads", "sum"),
        platform_revenue = ("platform_reported_revenue", "sum"),
    ).reset_index()

    # Step 2: leads per campaign × month
    ld = leads.groupby(["month", "campaign_id"]).agg(
        leads_submitted = ("lead_id", "nunique"),
        valid_leads     = ("is_valid",     lambda x: (x == True).sum()),
        duplicate_leads = ("is_duplicate", lambda x: (x == True).sum()),
    ).reset_index()

    # Step 3: revenue per campaign × month (bridged through leads)
    rev = leads[["lead_id", "month", "campaign_id"]].merge(
        revenue[["lead_id", "revenue_amount"]], on="lead_id", how="inner"
    ).groupby(["month", "campaign_id"]).agg(
        total_revenue = ("revenue_amount", "sum")
    ).reset_index()

    # Step 4: join
    df = spend.merge(ld,  on=["month", "campaign_id"], how="left")
    df = df.merge(rev, on=["month", "campaign_id"], how="left")

    df["total_revenue"]   = df["total_revenue"].fillna(0)
    df["leads_submitted"] = df["leads_submitted"].fillna(0)
    df["valid_leads"]     = df["valid_leads"].fillna(0)

    df["ctr"]                   = (df["clicks"] / df["impressions"]).round(4)
    df["cpc"]                   = (df["total_spend"] / df["clicks"]).round(2)
    df["platform_overclaim_rate"] = ((df["platform_leads"] - df["leads_submitted"]) / df["platform_leads"]).round(3)
    df["valid_lead_rate"]        = (df["valid_leads"] / df["leads_submitted"]).round(3)
    df["cpl"]                   = (df["total_spend"] / df["leads_submitted"]).round(2)
    df["cost_per_valid_lead"]    = (df["total_spend"] / df["valid_leads"]).round(2)
    df["revenue_per_lead"]       = (df["total_revenue"] / df["leads_submitted"]).round(2)
    df["roas"]                   = (df["total_revenue"] / df["total_spend"]).round(3)
    df["roi"]                    = ((df["total_revenue"] - df["total_spend"]) / df["total_spend"]).round(3)

    return df.sort_values(["month", "channel", "campaign_id"])


# ── Mart 3: Partner Performance ───────────────────────────────────────────────
@st.cache_data
def mart_partner_performance(routing, revenue, partners):
    routing["route_date"] = pd.to_datetime(routing["route_date"])

    # Daily routing stats per partner
    daily = routing.groupby(["partner_id", "route_date"]).agg(
        leads_delivered   = ("routing_attempt_id", "count"),
        leads_accepted    = ("response_status", lambda x: (x == "accepted").sum()),
        leads_rejected    = ("response_status", lambda x: (x == "rejected").sum()),
        no_response       = ("response_status", lambda x: (x == "no_response").sum()),
        capacity_exceeded = ("rejection_reason", lambda x: (x == "capacity_exceeded").sum()),
    ).reset_index()

    # Daily revenue per partner
    rev = revenue.copy()
    rev["route_date"] = rev["revenue_timestamp"].dt.date
    rev["route_date"] = pd.to_datetime(rev["route_date"])
    daily_rev = rev.groupby(["partner_id", "route_date"]).agg(
        daily_revenue = ("revenue_amount", "sum")
    ).reset_index()

    df = daily.merge(daily_rev, on=["partner_id", "route_date"], how="left")
    df["daily_revenue"] = df["daily_revenue"].fillna(0)

    # Partner metadata
    df = df.merge(partners[["partner_id", "partner_name", "insurance_verticals"]], on="partner_id", how="left")

    # Daily acceptance rate
    df["daily_acceptance_rate"] = (df["leads_accepted"] / df["leads_delivered"]).round(3)

    # Rolling 7-day acceptance rate (volume-weighted, calendar-day window)
    df = df.sort_values(["partner_id", "route_date"])
    df["unix_date"] = (df["route_date"] - pd.Timestamp("1970-01-01")).dt.days

    rows = []
    for pid, g in df.groupby("partner_id"):
        g = g.sort_values("route_date").reset_index(drop=True)
        for i, row in g.iterrows():
            window = g[g["unix_date"].between(row["unix_date"] - 6, row["unix_date"])]
            acc   = window["leads_accepted"].sum()
            deliv = window["leads_delivered"].sum()
            roll  = round(acc / deliv, 3) if deliv > 0 else None
            rows.append({**row.to_dict(), "rolling_7d_acceptance_rate": roll})

    df = pd.DataFrame(rows)

    # Cumulative revenue
    df = df.sort_values(["partner_id", "route_date"])
    df["cumulative_revenue"] = df.groupby("partner_id")["daily_revenue"].cumsum()

    return df


# ── Mart 4: Attribution ───────────────────────────────────────────────────────
@st.cache_data
def mart_attribution(leads, quote, revenue):
    # First-touch: earliest quote event for each lead at or before submitted_at
    q = quote[["quote_id", "channel", "event_timestamp"]].copy()
    q.columns = ["quote_id", "first_touch_channel", "event_timestamp"]

    l = leads[["lead_id", "quote_id", "channel", "submitted_at", "month",
                "insurance_vertical", "state", "is_valid"]].copy()
    l.columns = ["lead_id", "quote_id", "submitted_channel", "submitted_at", "month",
                 "insurance_vertical", "state", "is_valid"]

    merged = l.merge(q, on="quote_id", how="left")
    # Only events at or before submission
    merged = merged[merged["event_timestamp"] <= merged["submitted_at"]]
    # Keep earliest event per lead
    merged = merged.sort_values("event_timestamp").drop_duplicates(subset="lead_id", keep="first")

    # Revenue per lead
    rev = revenue.groupby("lead_id").agg(revenue_amount=("revenue_amount", "sum")).reset_index()
    merged = merged.merge(rev, on="lead_id", how="left")
    merged["revenue_amount"] = merged["revenue_amount"].fillna(0)
    merged["is_converted"] = merged["revenue_amount"] > 0

    # Hours to submit
    merged["hours_to_submit"] = (
        (merged["submitted_at"] - merged["event_timestamp"]).dt.total_seconds() / 3600
    ).round(1)

    # Multi-touch flag
    merged["is_multi_touch"] = merged["first_touch_channel"] != merged["submitted_channel"]

    return merged


# ── Mart 5: Reconciliation ────────────────────────────────────────────────────
@st.cache_data
def mart_reconciliation(leads, ad_perf):
    # Platform data per channel × month
    platform = ad_perf.groupby(["month", "channel"]).agg(
        platform_leads   = ("platform_reported_leads", "sum"),
        platform_revenue = ("platform_reported_revenue", "sum"),
        total_spend      = ("spend", "sum"),
    ).reset_index()

    # Warehouse data per channel × month
    warehouse = leads.groupby(["month", "channel"]).agg(
        warehouse_leads = ("lead_id", "nunique"),
        valid_leads     = ("is_valid", lambda x: (x == True).sum()),
    ).reset_index()

    # Left join: only channels with platform data (paid: google, meta, affiliate)
    # Organic/direct have no ad platform data and should not be reconciled here
    df = platform.merge(warehouse, on=["month", "channel"], how="left")

    df["platform_leads"]   = df["platform_leads"].fillna(0)
    df["warehouse_leads"]  = df["warehouse_leads"].fillna(0)
    df["valid_leads"]      = df["valid_leads"].fillna(0)
    df["lead_discrepancy"] = df["platform_leads"] - df["warehouse_leads"]

    # Overclaim rate: divide by platform (NULLIF logic: return NaN if platform=0)
    df["discrepancy_rate"] = np.where(
        df["platform_leads"] > 0,
        (df["lead_discrepancy"] / df["platform_leads"]).round(3),
        np.nan
    )

    # Status flag
    def status(row):
        if row["platform_leads"] > 0 and row["warehouse_leads"] > 0:
            return "matched"
        elif row["platform_leads"] == 0 and row["warehouse_leads"] > 0:
            return "warehouse_only"
        else:
            return "platform_only"

    df["reconciliation_status"] = df.apply(status, axis=1)

    return df.sort_values(["month", "channel"])
