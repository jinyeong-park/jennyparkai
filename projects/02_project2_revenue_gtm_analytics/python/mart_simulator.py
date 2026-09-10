"""
mart_simulator.py
=================
Replicates the dbt mart-layer transformations in pandas so that
analysis notebooks can run without a live database connection.

Each function mirrors the logic of the corresponding dbt model:
    build_stg_*()     → staging layer
    build_int_*()     → intermediate layer
    build_dim_*()     → dimension tables
    build_fct_*()     → fact tables

Imported by:
    02_gtm_funnel_analysis.ipynb
    03_revenue_reconciliation.ipynb
    04_pipeline_analysis.ipynb
    05_customer_health.ipynb
"""

import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "../data/raw")


# ---------------------------------------------------------------------------
# Raw loaders
# ---------------------------------------------------------------------------

def load_raw(table: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, f"{table}.csv")
    return pd.read_csv(path, low_memory=False)


# ---------------------------------------------------------------------------
# Staging layer
# ---------------------------------------------------------------------------

def build_stg_accounts() -> pd.DataFrame:
    df = load_raw("raw_salesforce_accounts")
    df = df.rename(columns={"sales_region": "region"})
    df["account_created_at"] = pd.to_datetime(df["account_created_at"])
    # Deduplicate (keep most recent per account_id)
    df = df.sort_values("account_created_at", ascending=False)
    df["_rn"] = df.groupby("account_id").cumcount() + 1
    df["had_duplicate_in_source"] = df.groupby("account_id")["account_id"].transform("count") > 1
    df = df[df["_rn"] == 1].drop(columns="_rn").reset_index(drop=True)
    df["segment"] = df["segment"].fillna("Unknown")
    return df


def build_stg_leads() -> pd.DataFrame:
    df = load_raw("raw_marketing_leads")
    df = df.rename(columns={"created_at": "lead_created_date"})
    df["lead_created_date"] = pd.to_datetime(df["lead_created_date"])
    df["has_account"] = df["account_id"].notna()
    stage_rank = {"Lead": 1, "MQL": 2, "SQL": 3, "Converted": 4}
    df["lifecycle_stage"] = df["lifecycle_stage"].fillna("Unknown")
    df["lifecycle_stage_rank"] = df["lifecycle_stage"].map(stage_rank).fillna(0).astype(int)
    df["is_sales_qualified"] = df["lifecycle_stage"].isin(["SQL", "Converted"])
    df = df.rename(columns={"campaign": "lead_source_detail"})
    return df


def build_stg_opps() -> pd.DataFrame:
    df = load_raw("raw_salesforce_opportunities")
    df = df.rename(columns={
        "created_at": "opportunity_created_at",
        "expected_close_date": "close_date",
        "sales_region": "region"
    })
    df["opportunity_created_at"] = pd.to_datetime(df["opportunity_created_at"])
    df["close_date"] = pd.to_datetime(df["close_date"])
    df["last_activity_at"] = pd.to_datetime(df["last_activity_at"])
    today = pd.Timestamp.today().normalize()

    df["is_won"] = df["opportunity_stage"] == "Closed-Won"
    df["is_lost"] = df["opportunity_stage"] == "Closed-Lost"
    df["is_open"] = ~df["opportunity_stage"].isin(["Closed-Won", "Closed-Lost"])
    df["is_orphan"] = df["account_id"].str.startswith("ACC_ORPHAN", na=False)
    df["days_open"] = (today - df["opportunity_created_at"]).dt.days
    df["days_past_due"] = (today - df["close_date"]).dt.days.clip(lower=0)
    df["days_since_last_activity"] = (today - df["last_activity_at"]).dt.days
    df["is_past_due"] = df["is_open"] & (df["close_date"] < today)
    df["is_stale"] = df["is_open"] & (df["days_since_last_activity"] > 30)
    df["has_repeated_slip"] = df["close_date_changes"] >= 2

    stage_order = {
        "Prospecting": 1, "Qualification": 2, "Proposal": 3,
        "Negotiation": 4, "Closed-Won": 5, "Closed-Lost": 5
    }
    df["stage_order"] = df["opportunity_stage"].map(stage_order).fillna(0).astype(int)
    return df


def build_stg_contracts() -> pd.DataFrame:
    df = load_raw("raw_contracts")
    df = df.rename(columns={
        "contract_date": "contract_signed_date",
        "start_date": "contract_start_date",
        "end_date": "contract_end_date"
    })
    for col in ["contract_signed_date", "contract_start_date", "contract_end_date"]:
        df[col] = pd.to_datetime(df[col])

    df["duplicate_count"] = df.groupby("contract_id")["contract_id"].transform("count")
    df["has_duplicate_contract_id"] = df["duplicate_count"] > 1
    df = df.sort_values("contract_value", ascending=False)
    df["dup_row_num"] = df.groupby("contract_id").cumcount() + 1
    df["is_canonical_record"] = df["dup_row_num"] == 1

    df["contract_end_date"] = pd.to_datetime(df["contract_end_date"])
    df["contract_start_date"] = pd.to_datetime(df["contract_start_date"])
    df["contract_term_months"] = (
        (df["contract_end_date"].dt.year - df["contract_start_date"].dt.year) * 12
        + (df["contract_end_date"].dt.month - df["contract_start_date"].dt.month)
    ).clip(lower=1)
    df["monthly_contract_value"] = df["contract_value"] / df["contract_term_months"]
    return df


def build_stg_billing() -> pd.DataFrame:
    df = load_raw("raw_billing")
    df["billing_date"] = pd.to_datetime(df["billing_date"])
    df["billing_year"] = df["billing_date"].dt.year
    df["billing_month"] = df["billing_date"].dt.month

    fx = {"USD": 1.00, "EUR": 1.08, "GBP": 1.27}
    df["fx_rate_to_usd"] = df["currency"].map(fx).fillna(1.0)
    df["billing_amount_usd"] = (df["billing_amount"] * df["fx_rate_to_usd"]).round(2)

    df["is_paid"] = df["payment_status"] == "Paid"
    df["is_pending"] = df["payment_status"] == "Pending"
    df["is_failed"] = df["payment_status"] == "Failed"
    df["collected_amount_usd"] = df["billing_amount_usd"].where(df["is_paid"], 0)
    df["at_risk_amount_usd"] = df["billing_amount_usd"].where(df["is_pending"], 0)
    df["failed_amount_usd"] = df["billing_amount_usd"].where(df["is_failed"], 0)
    return df


def build_stg_customer_success() -> pd.DataFrame:
    df = load_raw("raw_customer_success")
    df["renewal_date"] = pd.to_datetime(df["renewal_date"])
    today = pd.Timestamp.today().normalize()
    df["days_to_renewal"] = (df["renewal_date"] - today).dt.days

    def health_tier(score):
        if score >= 70:
            return "Healthy"
        elif score >= 35:
            return "Needs Attention"
        elif score > 0:
            return "At Risk"
        return "Unknown"

    df["health_tier"] = df["customer_health_score"].apply(health_tier)
    df["is_churned"] = df["renewal_status"] == "Churned"
    df["has_expansion"] = df["expansion_amount"] > 0
    return df


# ---------------------------------------------------------------------------
# Intermediate layer
# ---------------------------------------------------------------------------

def build_int_gtm_funnel() -> pd.DataFrame:
    accounts = build_stg_accounts()
    leads = build_stg_leads()
    opps = build_stg_opps()

    # Aggregate leads to account level
    leads_agg = (
        leads[leads["has_account"]]
        .groupby("account_id")
        .agg(
            lead_count=("lead_id", "nunique"),
            first_lead_date=("lead_created_date", "min"),
            last_lead_date=("lead_created_date", "max"),
            max_lifecycle_rank=("lifecycle_stage_rank", "max"),
            sql_lead_count=("is_sales_qualified", "sum"),
            primary_lead_source=("lead_source", lambda x: x.mode().iloc[0] if len(x) else None),
        )
        .reset_index()
    )

    # Aggregate opps to account level
    non_orphan = opps[~opps["is_orphan"]]
    opps_agg = (
        non_orphan.groupby("account_id")
        .agg(
            opp_count=("opportunity_id", "nunique"),
            won_opp_count=("is_won", "sum"),
            lost_opp_count=("is_lost", "sum"),
            open_opp_count=("is_open", "sum"),
            total_won_amount=("amount", lambda x: x[non_orphan.loc[x.index, "is_won"]].sum()),
            total_pipeline_amount=("amount", lambda x: x[non_orphan.loc[x.index, "is_open"]].sum()),
            first_opp_created_at=("opportunity_created_at", "min"),
        )
        .reset_index()
    )
    # Simpler won amount calculation
    won_agg = non_orphan[non_orphan["is_won"]].groupby("account_id")["amount"].sum().rename("total_won_amount")
    open_agg = non_orphan[non_orphan["is_open"]].groupby("account_id")["amount"].sum().rename("total_pipeline_amount")
    opps_agg = non_orphan.groupby("account_id").agg(
        opp_count=("opportunity_id", "nunique"),
        won_opp_count=("is_won", "sum"),
        lost_opp_count=("is_lost", "sum"),
        open_opp_count=("is_open", "sum"),
        first_opp_created_at=("opportunity_created_at", "min"),
        first_won_opp_at=("opportunity_created_at", lambda x: x[non_orphan.loc[x.index, "is_won"]].min()),
    ).reset_index()
    opps_agg = opps_agg.join(won_agg, on="account_id").join(open_agg, on="account_id")
    opps_agg["total_won_amount"] = opps_agg["total_won_amount"].fillna(0)
    opps_agg["total_pipeline_amount"] = opps_agg["total_pipeline_amount"].fillna(0)

    df = accounts.merge(leads_agg, on="account_id", how="left")
    df = df.merge(opps_agg, on="account_id", how="left")

    df["lead_count"] = df["lead_count"].fillna(0).astype(int)
    df["opp_count"] = df["opp_count"].fillna(0).astype(int)
    df["won_opp_count"] = df["won_opp_count"].fillna(0).astype(int)
    df["lost_opp_count"] = df["lost_opp_count"].fillna(0).astype(int)
    df["open_opp_count"] = df["open_opp_count"].fillna(0).astype(int)
    df["total_won_amount"] = df["total_won_amount"].fillna(0)
    df["total_pipeline_amount"] = df["total_pipeline_amount"].fillna(0)
    df["sql_lead_count"] = df["sql_lead_count"].fillna(0).astype(int)

    df["has_lead"] = df["lead_count"] > 0
    df["has_opportunity"] = df["opp_count"] > 0
    df["has_won_opportunity"] = df["won_opp_count"] > 0

    stage_map = {4: "Converted", 3: "SQL", 2: "MQL", 1: "Lead", 0: "No Lead"}
    df["max_lead_stage"] = df["max_lifecycle_rank"].fillna(0).astype(int).map(stage_map)

    def funnel_stage(row):
        if row["won_opp_count"] > 0:
            return "Closed-Won"
        elif row["open_opp_count"] > 0:
            return "Open Opportunity"
        elif row["lost_opp_count"] > 0:
            return "Closed-Lost"
        elif row.get("max_lifecycle_rank", 0) == 3:
            return "SQL"
        elif row.get("max_lifecycle_rank", 0) == 2:
            return "MQL"
        elif row.get("max_lifecycle_rank", 0) == 1:
            return "Lead"
        return "Account Only"

    df["funnel_stage"] = df.apply(funnel_stage, axis=1)

    df["lead_to_opp_days"] = (
        df["first_opp_created_at"] - df["first_lead_date"]
    ).dt.days

    return df


def build_int_revenue_lifecycle() -> pd.DataFrame:
    opps = build_stg_opps()
    contracts = build_stg_contracts()
    billing = build_stg_billing()

    won = opps[opps["is_won"] & ~opps["is_orphan"]].copy()
    canonical = contracts[contracts["is_canonical_record"]].copy()

    billing_agg = billing.groupby("contract_id").agg(
        invoice_count=("invoice_id", "nunique"),
        first_billing_date=("billing_date", "min"),
        last_billing_date=("billing_date", "max"),
        total_billed_usd=("billing_amount_usd", "sum"),
        total_collected_usd=("collected_amount_usd", "sum"),
        total_at_risk_usd=("at_risk_amount_usd", "sum"),
        total_failed_usd=("failed_amount_usd", "sum"),
        paid_invoice_count=("is_paid", "sum"),
        pending_invoice_count=("is_pending", "sum"),
        failed_invoice_count=("is_failed", "sum"),
        primary_currency=("currency", lambda x: x.mode().iloc[0] if len(x) else "USD"),
        currency_count=("currency", "nunique"),
    ).reset_index()

    df = won[["opportunity_id", "account_id", "opportunity_stage", "amount",
              "close_date", "opportunity_created_at", "days_open"]].copy()
    df = df.rename(columns={"amount": "crm_booking_amount", "days_open": "days_to_close"})

    df = df.merge(
        canonical[["opportunity_id", "contract_id", "contract_value", "contract_status",
                   "contract_start_date", "contract_end_date", "contract_term_months",
                   "monthly_contract_value", "has_duplicate_contract_id"]],
        on="opportunity_id", how="left"
    )
    df = df.merge(billing_agg, on="contract_id", how="left")

    df["contract_value"] = df["contract_value"].fillna(0)
    df["total_billed_usd"] = df["total_billed_usd"].fillna(0)
    df["total_collected_usd"] = df["total_collected_usd"].fillna(0)
    df["total_at_risk_usd"] = df["total_at_risk_usd"].fillna(0)
    df["total_failed_usd"] = df["total_failed_usd"].fillna(0)
    df["invoice_count"] = df["invoice_count"].fillna(0).astype(int)

    df["has_contract"] = df["contract_id"].notna()
    df["has_billing"] = df["invoice_count"] > 0
    df["has_collected_revenue"] = df["total_collected_usd"] > 0

    df["booking_to_contract_gap"] = df["crm_booking_amount"] - df["contract_value"]
    df["contract_to_billing_gap"] = df["contract_value"] - df["total_billed_usd"]
    df["billing_to_collected_gap"] = df["total_billed_usd"] - df["total_collected_usd"]

    df["cash_collection_rate"] = np.where(
        df["crm_booking_amount"] > 0,
        df["total_collected_usd"] / df["crm_booking_amount"],
        np.nan
    )

    def revenue_stage(row):
        if row["has_collected_revenue"]:
            return "Collected"
        elif row["has_billing"]:
            return "Billed"
        elif row["has_contract"]:
            return "Contracted"
        return "Booking Only"

    df["revenue_stage"] = df.apply(revenue_stage, axis=1)
    return df


# ---------------------------------------------------------------------------
# Mart layer
# ---------------------------------------------------------------------------

def build_dim_account() -> pd.DataFrame:
    accounts = build_stg_accounts()
    cs = build_stg_customer_success()
    gtm = build_int_gtm_funnel()

    base = accounts.merge(
        cs[["account_id", "customer_health_score", "health_tier",
            "renewal_status", "is_churned", "has_expansion", "expansion_amount"]],
        on="account_id", how="left"
    )

    gtm_cols = ["account_id", "lead_count", "opp_count", "won_opp_count",
                "open_opp_count", "total_won_amount", "total_pipeline_amount",
                "max_lead_stage", "max_lifecycle_rank", "funnel_stage",
                "has_lead", "has_opportunity", "has_won_opportunity"]
    base = base.merge(gtm[gtm_cols], on="account_id", how="left")

    billing = build_stg_billing()
    billing_agg = billing.groupby("customer_id").agg(
        total_billed_usd=("billing_amount_usd", "sum"),
        total_collected_usd=("collected_amount_usd", "sum"),
        is_in_billing=("invoice_id", lambda x: True)
    ).reset_index().rename(columns={"customer_id": "account_id"})

    base = base.merge(billing_agg, on="account_id", how="left")
    base["is_in_billing"] = base["is_in_billing"].fillna(False)
    base["is_in_marketing"] = base["has_lead"].fillna(False)
    base["is_in_customer_success"] = base["customer_health_score"].notna()
    base["is_in_crm"] = True
    base["systems_present"] = (
        1
        + base["is_in_marketing"].astype(int)
        + base["is_in_billing"].astype(int)
        + base["is_in_customer_success"].astype(int)
    )

    base["total_bookings_usd"] = base["total_won_amount"].fillna(0)
    base["total_billed_usd"] = base["total_billed_usd"].fillna(0)
    base["total_collected_usd"] = base["total_collected_usd"].fillna(0)

    def lifecycle_tier(row):
        if row.get("is_churned"):
            return "Churned"
        elif row["account_status"] == "Customer" and row["is_in_billing"]:
            return "Active Customer"
        elif row["account_status"] == "Customer":
            return "Customer - No Billing"
        elif row["total_bookings_usd"] > 0:
            return "Closed-Won Prospect"
        elif row.get("opp_count", 0) > 0:
            return "In Pipeline"
        elif row.get("max_lead_stage") in ("SQL", "MQL"):
            return "Marketing Qualified"
        elif row.get("lead_count", 0) > 0:
            return "Lead"
        return "Account Only"

    base["lifecycle_tier"] = base.apply(lifecycle_tier, axis=1)
    return base


def build_fct_pipeline() -> pd.DataFrame:
    opps = build_stg_opps()
    accounts = build_dim_account()[
        ["account_id", "account_name", "segment", "industry",
         "region", "revenue_model", "lifecycle_tier"]
    ]

    open_opps = opps[opps["is_open"] & ~opps["is_orphan"]].copy()
    # Drop columns from opps that also exist in accounts to avoid _x/_y conflicts
    overlap_cols = [c for c in ["segment", "revenue_model", "region"] if c in open_opps.columns]
    open_opps = open_opps.drop(columns=overlap_cols)
    df = open_opps.merge(accounts, on="account_id", how="left")
    df = df.rename(columns={"opportunity_id": "opportunity_id",
                             "amount": "pipeline_amount"})

    win_rates = {
        "Prospecting": 0.05, "Qualification": 0.15,
        "Proposal": 0.35, "Negotiation": 0.65
    }
    df["stage_win_rate"] = df["opportunity_stage"].map(win_rates).fillna(0.10)
    df["weighted_pipeline_amount"] = (df["pipeline_amount"] * df["stage_win_rate"]).round(2)

    def risk(row):
        if row["has_repeated_slip"] and row["is_past_due"]:
            return "High Risk"
        elif row["is_past_due"] or row["is_stale"]:
            return "Medium Risk"
        return "On Track"

    df["pipeline_risk"] = df.apply(risk, axis=1)
    df["snapshot_date"] = pd.Timestamp.today().normalize()
    return df


def build_fct_bookings() -> pd.DataFrame:
    lifecycle = build_int_revenue_lifecycle()
    accounts = build_dim_account()[
        ["account_id", "account_name", "segment", "industry",
         "region", "revenue_model", "lifecycle_tier"]
    ]
    df = lifecycle.merge(accounts, on="account_id", how="left")
    df["close_year"] = pd.to_datetime(df["close_date"]).dt.year
    df["close_month"] = pd.to_datetime(df["close_date"]).dt.month

    def discount_tier(row):
        if row["crm_booking_amount"] == 0:
            return None
        pct = row["booking_to_contract_gap"] / row["crm_booking_amount"]
        if pct > 0.15:
            return "Heavy Discount (>15%)"
        elif pct > 0.05:
            return "Moderate Discount (5-15%)"
        elif pct > 0:
            return "Minor Discount (<5%)"
        elif pct < 0:
            return "Contract Exceeds Booking"
        return "No Discount"

    def collection_status(row):
        if not row["has_contract"]:
            return "No Contract"
        elif row["total_failed_usd"] > 0 and (row["cash_collection_rate"] or 1) < 0.5:
            return "High Collection Risk"
        elif row["total_failed_usd"] > 0 or row["total_at_risk_usd"] > 0:
            return "Some Collection Risk"
        elif row["has_collected_revenue"] and (row["cash_collection_rate"] or 0) >= 0.95:
            return "Fully Collected"
        elif row["has_collected_revenue"]:
            return "Partially Collected"
        return "Not Yet Collected"

    df["discount_tier"] = df.apply(discount_tier, axis=1)
    df["collection_status"] = df.apply(collection_status, axis=1)
    return df


def build_fct_revenue() -> pd.DataFrame:
    billing = build_stg_billing()
    accounts = build_dim_account()[
        ["account_id", "account_name", "segment", "industry",
         "region", "revenue_model", "lifecycle_tier",
         "is_churned", "has_expansion", "health_tier", "renewal_status"]
    ]
    contracts = build_stg_contracts()
    canonical = contracts[contracts["is_canonical_record"]][
        ["contract_id", "contract_status", "contract_term_months", "monthly_contract_value"]
    ]

    df = billing.rename(columns={"customer_id": "account_id"})
    df = df.merge(accounts, on="account_id", how="left")
    df = df.merge(canonical, on="contract_id", how="left")

    def nrr_cat(row):
        if row.get("is_churned"):
            return "Churned"
        elif row.get("has_expansion") and not row.get("is_churned"):
            return "Expansion"
        return "Retained"

    df["nrr_category"] = df.apply(nrr_cat, axis=1)

    revenue_type_map = {
        "Subscription": "Recurring",
        "Usage-Based": "Variable",
        "One-Time": "Non-Recurring"
    }
    df["revenue_type"] = df["revenue_model"].map(revenue_type_map).fillna("Other")
    df["is_revenue_at_risk"] = df["is_pending"] | df["is_failed"]
    return df


def build_fct_customer_lifecycle() -> pd.DataFrame:
    # Use only account-attribute columns from dim — not the derived metrics
    # (dim already contains totals from billing/gtm merges; pulling metrics
    #  separately avoids _x/_y column conflicts on the join)
    dim = build_dim_account()[
        ["account_id", "account_name", "segment", "industry", "region",
         "revenue_model", "account_status", "account_created_at",
         "lifecycle_tier", "systems_present",
         "is_in_crm", "is_in_marketing", "is_in_billing", "is_in_customer_success",
         "customer_health_score", "health_tier", "renewal_status",
         "is_churned", "has_expansion", "expansion_amount"]
    ]
    gtm = build_int_gtm_funnel()
    revenue = build_int_revenue_lifecycle()
    cs = build_stg_customer_success()

    rev_agg = revenue.groupby("account_id").agg(
        first_close_date=("close_date", "min"),
        total_crm_bookings=("crm_booking_amount", "sum"),
        total_contract_value=("contract_value", "sum"),
        total_billed_usd=("total_billed_usd", "sum"),
        total_collected_usd=("total_collected_usd", "sum"),
        total_failed_usd=("total_failed_usd", "sum"),
        contract_count=("contract_id", "nunique"),
        has_any_contract=("has_contract", "any"),
        has_any_billing=("has_billing", "any"),
    ).reset_index()

    gtm_cols = [
        "account_id", "lead_count", "sql_lead_count", "first_lead_date",
        "last_lead_date", "primary_lead_source", "max_lead_stage",
        "opp_count", "won_opp_count", "lost_opp_count", "open_opp_count",
        "total_pipeline_amount", "first_opp_created_at", "first_won_opp_at",
        "has_lead", "has_opportunity", "has_won_opportunity", "funnel_stage",
        "lead_to_opp_days",
    ]

    df = dim.merge(gtm[gtm_cols], on="account_id", how="left")
    df = df.merge(rev_agg, on="account_id", how="left")

    df["total_crm_bookings"] = df["total_crm_bookings"].fillna(0)
    df["total_collected_usd"] = df["total_collected_usd"].fillna(0)
    df["total_billed_usd"] = df["total_billed_usd"].fillna(0)

    df["lead_to_close_days"] = (
        pd.to_datetime(df["first_close_date"]) - pd.to_datetime(df["first_lead_date"])
    ).dt.days

    # Ensure CS columns are present (dim already has them via build_dim_account)
    for col in ["is_churned", "has_expansion", "expansion_amount"]:
        if col not in df.columns:
            cs_col = cs.set_index("account_id")[col]
            df[col] = df["account_id"].map(cs_col)

    def nrr_cat(row):
        if row.get("is_churned"):
            return "Churned"
        elif row.get("has_expansion") and not row.get("is_churned"):
            return "Expansion"
        elif row.get("total_collected_usd", 0) > 0:
            return "Retained"
        return "No Revenue"

    df["nrr_category"] = df.apply(nrr_cat, axis=1)

    def lifecycle_completeness(row):
        if row.get("is_churned"):
            return "6 - Churned"
        elif row.get("has_expansion"):
            return "5 - Expansion"
        elif row.get("total_collected_usd", 0) > 0:
            return "4 - Paying Customer"
        elif row.get("has_any_contract"):
            return "3 - Contracted"
        elif row.get("has_won_opportunity"):
            return "2 - Closed-Won"
        elif row.get("has_opportunity"):
            return "1 - In Pipeline"
        return "0 - Pre-Pipeline"

    df["lifecycle_completeness"] = df.apply(lifecycle_completeness, axis=1)
    return df
