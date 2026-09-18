"""
Generate synthetic source data for the Revenue Intelligence & GTM Analytics project.

The generator creates reproducible, intentionally imperfect B2B revenue data that
can be loaded into dbt/BigQuery and used for GTM funnel, pipeline, revenue
reconciliation, customer lifecycle, and data-quality analysis.

Outputs:
    data/raw/raw_marketing_leads.csv
    data/raw/raw_salesforce_accounts.csv
    data/raw/raw_salesforce_opportunities.csv
    data/raw/raw_contracts.csv
    data/raw/raw_billing.csv
    data/raw/raw_product_events.csv
    data/raw/raw_customer_success.csv

Usage:
    python scripts/generate_synthetic_data.py
"""

from __future__ import annotations

import argparse
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = Path("data/raw")
START_DATE = pd.Timestamp("2024-01-01")
END_DATE = pd.Timestamp("2025-12-31")


@dataclass
class Config:
    seed: int = DEFAULT_SEED
    output_dir: Path = DEFAULT_OUTPUT_DIR
    n_accounts: int = 1200
    n_leads: int = 3200
    n_opportunities: int = 1800
    n_product_events: int = 25000


def random_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def make_rng(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    return np.random.default_rng(seed)


def random_dates(rng, n, start=START_DATE, end=END_DATE):
    days = (end - start).days
    offsets = rng.integers(0, days + 1, size=n)
    return pd.to_datetime(start) + pd.to_timedelta(offsets, unit="D")


def weighted_choice(rng, values, probabilities, size):
    return rng.choice(values, size=size, p=probabilities)


def generate_accounts(rng, cfg: Config) -> pd.DataFrame:
    account_ids = [f"ACC_{i:05d}" for i in range(1, cfg.n_accounts + 1)]

    segments = ["SMB", "Mid-Market", "Enterprise"]
    regions = ["North America", "EMEA", "APAC", "LATAM"]
    industries = ["Software", "Financial Services", "Retail", "Healthcare", "Media", "Professional Services"]
    revenue_models = ["Subscription", "Advertising", "Transactional", "Usage-Based", "Enterprise Services"]

    segment = weighted_choice(rng, segments, [0.48, 0.34, 0.18], cfg.n_accounts)
    company_size = np.select(
        [segment == "SMB", segment == "Mid-Market", segment == "Enterprise"],
        ["1-99", "100-999", "1000+"],
        default="Unknown",
    )

    created_at = random_dates(rng, cfg.n_accounts)
    account_status = weighted_choice(
        rng, ["Prospect", "Customer", "Churned"],
        [0.42, 0.49, 0.09], cfg.n_accounts
    )

    # Stable-ish synthetic account names make the data easier to inspect.
    account_names = [
        f"{rng.choice(['Northstar', 'Vertex', 'Summit', 'Pioneer', 'Atlas', 'BluePeak', 'Cobalt', 'Nova', 'Apex', 'Harbor'])} "
        f"{rng.choice(['Systems', 'Labs', 'Group', 'Technologies', 'Networks', 'Partners', 'Solutions'])} {i:04d}"
        for i in range(1, cfg.n_accounts + 1)
    ]

    df = pd.DataFrame({
        "account_id": account_ids,
        "account_name": account_names,
        "company_size": company_size,
        "segment": segment,
        "industry": rng.choice(industries, cfg.n_accounts),
        "sales_region": rng.choice(regions, cfg.n_accounts, p=[0.55, 0.20, 0.15, 0.10]),
        "revenue_model": rng.choice(revenue_models, cfg.n_accounts, p=[0.48, 0.16, 0.16, 0.12, 0.08]),
        "account_created_at": created_at.strftime("%Y-%m-%d"),
        "account_status": account_status,
    })

    # Intentional duplicate account records for data-quality testing.
    duplicate_count = max(8, cfg.n_accounts // 100)
    duplicates = df.sample(duplicate_count, random_state=cfg.seed).copy()
    duplicates["account_name"] = duplicates["account_name"] + " Duplicate"
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


def generate_leads(rng, cfg: Config, accounts: pd.DataFrame) -> pd.DataFrame:
    account_pool = accounts.loc[~accounts["account_id"].duplicated(), "account_id"].tolist()

    lead_ids = [f"LEAD_{i:06d}" for i in range(1, cfg.n_leads + 1)]
    created_at = random_dates(rng, cfg.n_leads)

    channel = weighted_choice(
        rng,
        ["Organic", "Paid Search", "Paid Social", "Partner", "Outbound", "Events", "Referral"],
        [0.22, 0.18, 0.14, 0.12, 0.13, 0.09, 0.12],
        cfg.n_leads,
    )

    lifecycle_stage = weighted_choice(
        rng,
        ["Lead", "MQL", "SQL", "Converted"],
        [0.45, 0.27, 0.17, 0.11],
        cfg.n_leads,
    )

    campaign_map = {
        "Organic": ["SEO", "Content Hub", "Product Blog"],
        "Paid Search": ["Search - Brand", "Search - Nonbrand", "Search - Competitor"],
        "Paid Social": ["LinkedIn ABM", "LinkedIn Demand Gen", "Paid Social Retargeting"],
        "Partner": ["Cloud Partner", "Reseller", "Technology Partner"],
        "Outbound": ["SDR Outbound", "Named Account Outreach"],
        "Events": ["Industry Conference", "Webinar", "Executive Roundtable"],
        "Referral": ["Customer Referral", "Employee Referral"],
    }

    campaigns = [random.choice(campaign_map[c]) for c in channel]

    account_ids = rng.choice(account_pool, cfg.n_leads)

    # Make Enterprise leads somewhat more likely to progress downstream.
    account_segment = accounts.drop_duplicates("account_id").set_index("account_id")["segment"]
    stage_rank = {"Lead": 0, "MQL": 1, "SQL": 2, "Converted": 3}
    base_rank = np.array([stage_rank[x] for x in lifecycle_stage])

    for i, aid in enumerate(account_ids):
        if account_segment.get(aid) == "Enterprise" and rng.random() < 0.35:
            base_rank[i] = min(3, base_rank[i] + 1)

    lifecycle_stage = np.array([list(stage_rank)[r] for r in base_rank])

    df = pd.DataFrame({
        "lead_id": lead_ids,
        "account_id": account_ids,
        "lead_source": channel,
        "campaign": campaigns,
        "channel": channel,
        "created_at": created_at.strftime("%Y-%m-%d"),
        "lifecycle_stage": lifecycle_stage,
        "company_size": [
            accounts.loc[accounts["account_id"] == aid, "company_size"].iloc[0]
            for aid in account_ids
        ],
        "segment": [
            accounts.loc[accounts["account_id"] == aid, "segment"].iloc[0]
            for aid in account_ids
        ],
    })

    # A small number of missing identifiers simulate imperfect source data.
    missing_idx = rng.choice(df.index, size=max(5, len(df) // 250), replace=False)
    df.loc[missing_idx, "account_id"] = None

    return df


def generate_opportunities(rng, cfg: Config, accounts: pd.DataFrame, leads: pd.DataFrame) -> pd.DataFrame:
    account_master = accounts.drop_duplicates("account_id").set_index("account_id")
    account_pool = account_master.index.tolist()

    n = cfg.n_opportunities
    opportunity_ids = [f"OPP_{i:06d}" for i in range(1, n + 1)]

    account_ids = rng.choice(account_pool, n)
    segment = account_master.loc[account_ids, "segment"].to_numpy()
    revenue_model = account_master.loc[account_ids, "revenue_model"].to_numpy()
    region = account_master.loc[account_ids, "sales_region"].to_numpy()

    owner_ids = rng.choice([f"REP_{i:03d}" for i in range(1, 31)], n)

    stage = weighted_choice(
        rng,
        ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed-Won", "Closed-Lost"],
        [0.14, 0.19, 0.20, 0.13, 0.20, 0.14],
        n,
    )

    base_amount = rng.lognormal(mean=9.7, sigma=1.0, size=n)
    multiplier = np.where(segment == "SMB", 0.55, np.where(segment == "Mid-Market", 1.0, 2.7))
    amount = np.round(np.maximum(2500, base_amount * multiplier), 2)

    created_at = random_dates(rng, n, START_DATE, pd.Timestamp("2025-10-31"))
    expected_close = created_at + pd.to_timedelta(rng.integers(20, 150, size=n), unit="D")

    is_closed = np.isin(stage, ["Closed-Won", "Closed-Lost"])
    actual_close = pd.Series(pd.NaT, index=np.arange(n), dtype="datetime64[ns]")
    close_offsets = rng.integers(15, 180, size=is_closed.sum())
    actual_close.loc[np.where(is_closed)[0]] = (
        created_at[is_closed] + pd.to_timedelta(close_offsets, unit="D")
    )

    # Close-date changes are intentionally represented as a separate count.
    close_date_changes = rng.choice([0, 1, 2, 3], n, p=[0.63, 0.24, 0.10, 0.03])

    # Historical conversion is weaker for some channels/segments to make analysis useful.
    source = rng.choice(
        ["Inbound", "Outbound", "Partner", "Marketing", "Referral"],
        n,
        p=[0.34, 0.22, 0.16, 0.20, 0.08],
    )

    df = pd.DataFrame({
        "opportunity_id": opportunity_ids,
        "account_id": account_ids,
        "owner_id": owner_ids,
        "opportunity_stage": stage,
        "amount": amount,
        "expected_close_date": pd.to_datetime(expected_close).strftime("%Y-%m-%d"),
        "actual_close_date": actual_close.dt.strftime("%Y-%m-%d"),
        "created_at": pd.to_datetime(created_at).strftime("%Y-%m-%d"),
        "sales_region": region,
        "segment": segment,
        "revenue_model": revenue_model,
        "lead_source": source,
        "close_date_changes": close_date_changes,
        "last_activity_at": (
            pd.to_datetime(created_at) + pd.to_timedelta(
                rng.integers(1, 120, size=n), unit="D"
            )
        ).strftime("%Y-%m-%d"),
    })

    # A few orphan opportunities intentionally have no valid account.
    orphan_idx = rng.choice(df.index, size=max(6, n // 200), replace=False)
    df.loc[orphan_idx, "account_id"] = [f"ACC_ORPHAN_{i}" for i in range(len(orphan_idx))]

    return df


def generate_contracts(rng, accounts: pd.DataFrame, opportunities: pd.DataFrame) -> pd.DataFrame:
    won = opportunities[opportunities["opportunity_stage"] == "Closed-Won"].copy()
    if won.empty:
        return pd.DataFrame()

    n = len(won)
    contract_ids = [f"CON_{i:06d}" for i in range(1, n + 1)]

    contract_date = pd.to_datetime(won["actual_close_date"]).fillna(
        pd.to_datetime(won["created_at"])
    )

    revenue_model = won["revenue_model"].to_numpy()
    term_months = np.where(
        revenue_model == "Subscription",
        rng.choice([6, 12, 24, 36], n, p=[0.10, 0.60, 0.20, 0.10]),
        rng.choice([1, 3, 6, 12], n, p=[0.35, 0.30, 0.20, 0.15]),
    )

    contract_value = np.round(won["amount"].to_numpy() * rng.uniform(0.90, 1.10, n), 2)
    start_date = contract_date + pd.to_timedelta(rng.integers(0, 15, n), unit="D")
    end_date = start_date + pd.to_timedelta(term_months * 30, unit="D")

    df = pd.DataFrame({
        "contract_id": contract_ids,
        "account_id": won["account_id"].to_numpy(),
        "opportunity_id": won["opportunity_id"].to_numpy(),
        "contract_date": contract_date.dt.strftime("%Y-%m-%d").to_numpy(),
        "contract_value": contract_value,
        "start_date": start_date.dt.strftime("%Y-%m-%d"),
        "end_date": end_date.dt.strftime("%Y-%m-%d"),
        "revenue_model": revenue_model,
        "contract_status": rng.choice(["Active", "Amended", "Cancelled"], n, p=[0.87, 0.08, 0.05]),
    })

    # Intentional duplicate contracts for reconciliation/data-quality analysis.
    duplicate_count = max(4, n // 150)
    if n >= duplicate_count:
        duplicates = df.sample(duplicate_count, random_state=123).copy()
        duplicates["contract_id"] = duplicates["contract_id"]  # same ID = detectable duplicate
        duplicates["contract_value"] = np.round(duplicates["contract_value"] * rng.uniform(0.98, 1.02, duplicate_count), 2)
        df = pd.concat([df, duplicates], ignore_index=True)

    return df


def generate_billing(rng, contracts: pd.DataFrame) -> pd.DataFrame:
    if contracts.empty:
        return pd.DataFrame()

    rows = []
    invoice_counter = 1

    for _, contract in contracts.drop_duplicates("contract_id").iterrows():
        start = pd.Timestamp(contract["start_date"])
        end = pd.Timestamp(contract["end_date"])
        contract_value = float(contract["contract_value"])
        model = contract["revenue_model"]

        if model == "Subscription":
            months = max(1, min(12, int(np.ceil((end - start).days / 30))))
            monthly = contract_value / months
            dates = [start + pd.DateOffset(months=i) for i in range(months)]
            amounts = [monthly] * months
        else:
            dates = [start]
            amounts = [contract_value]

        for billing_date, amount in zip(dates, amounts):
            if billing_date > END_DATE + pd.Timedelta(days=30):
                continue

            payment_status = rng.choice(
                ["Paid", "Pending", "Failed"],
                p=[0.88, 0.08, 0.04],
            )

            rows.append({
                "customer_id": contract["account_id"],
                "invoice_id": f"INV_{invoice_counter:07d}",
                "contract_id": contract["contract_id"],
                "billing_date": billing_date.strftime("%Y-%m-%d"),
                "billing_amount": round(float(amount), 2),
                "payment_status": payment_status,
                "currency": rng.choice(["USD", "USD", "USD", "EUR", "GBP"]),
            })
            invoice_counter += 1

    df = pd.DataFrame(rows)

    # Small timing/amount mismatch makes reconciliation meaningful.
    if len(df) > 20:
        idx = rng.choice(df.index, size=max(10, len(df) // 250), replace=False)
        df.loc[idx, "billing_amount"] = np.round(
            df.loc[idx, "billing_amount"] * rng.uniform(0.97, 1.03, len(idx)), 2
        )

    return df


def generate_product_events(rng, cfg: Config, accounts: pd.DataFrame) -> pd.DataFrame:
    account_master = accounts.drop_duplicates("account_id")
    account_ids = account_master["account_id"].tolist()
    n = cfg.n_product_events

    selected_accounts = rng.choice(account_ids, n)
    event_names = rng.choice(
        [
            "login",
            "workspace_created",
            "feature_used",
            "report_created",
            "integration_connected",
            "api_call",
            "invite_user",
            "activation_completed",
        ],
        n,
        p=[0.25, 0.08, 0.17, 0.10, 0.08, 0.12, 0.12, 0.08],
    )

    event_timestamp = random_dates(
        rng, n, START_DATE, END_DATE
    ) + pd.to_timedelta(rng.integers(0, 24 * 60, n), unit="m")

    user_ids = [
        f"USR_{abs(hash((aid, i))) % 1000000:06d}"
        for i, aid in enumerate(selected_accounts)
    ]

    feature_map = {
        "login": "Core Platform",
        "workspace_created": "Workspace",
        "feature_used": rng.choice(["Analytics", "Automation", "Collaboration"], n),
        "report_created": "Reporting",
        "integration_connected": rng.choice(["Salesforce", "Slack", "HubSpot", "API"], n),
        "api_call": "API",
        "invite_user": "Collaboration",
        "activation_completed": "Core Platform",
    }

    features = [
        feature_map[e] if not isinstance(feature_map[e], np.ndarray) else feature_map[e][i]
        for i, e in enumerate(event_names)
    ]

    active_users = rng.integers(1, 25, n)

    return pd.DataFrame({
        "user_id": user_ids,
        "account_id": selected_accounts,
        "event_name": event_names,
        "event_timestamp": event_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "feature_name": features,
        "active_users": active_users,
        "activation_event": event_names == "activation_completed",
    })


def generate_customer_success(rng, accounts: pd.DataFrame) -> pd.DataFrame:
    master = accounts.drop_duplicates("account_id").copy()
    customer_accounts = master[master["account_status"].isin(["Customer", "Churned"])].copy()

    n = len(customer_accounts)
    renewal_date = START_DATE + pd.to_timedelta(rng.integers(30, 730, n), unit="D")
    health = np.clip(
        rng.normal(
            np.where(customer_accounts["account_status"].eq("Churned"), 48, 72),
            17,
        ),
        5,
        100,
    ).round(1)

    renewal_status = np.where(
        customer_accounts["account_status"].eq("Churned"),
        "Churned",
        np.where(
            health < 35,
            "At Risk",
            np.where(health < 60, "Needs Attention", "Healthy"),
        ),
    )

    expansion_amount = np.where(
        (health >= 70) & customer_accounts["account_status"].eq("Customer"),
        np.round(rng.lognormal(7.2, 0.8, n), 2),
        0,
    )

    churn_reasons = rng.choice(
        ["Budget", "Low Adoption", "Competition", "Business Closure", "Poor Fit"],
        n,
    )
    churn_reasons = np.where(
        customer_accounts["account_status"].eq("Churned"),
        churn_reasons,
        None,
    )

    return pd.DataFrame({
        "account_id": customer_accounts["account_id"].to_numpy(),
        "customer_health_score": health,
        "renewal_date": pd.to_datetime(renewal_date).strftime("%Y-%m-%d"),
        "renewal_status": renewal_status,
        "expansion_amount": expansion_amount,
        "churn_reason": churn_reasons,
    })


def write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Revenue Intelligence source data.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--accounts", type=int, default=1200)
    parser.add_argument("--leads", type=int, default=3200)
    parser.add_argument("--opportunities", type=int, default=1800)
    parser.add_argument("--product-events", type=int, default=25000)
    args = parser.parse_args()

    cfg = Config(
        seed=args.seed,
        output_dir=args.output_dir,
        n_accounts=args.accounts,
        n_leads=args.leads,
        n_opportunities=args.opportunities,
        n_product_events=args.product_events,
    )

    rng = make_rng(cfg.seed)

    accounts = generate_accounts(rng, cfg)
    leads = generate_leads(rng, cfg, accounts)
    opportunities = generate_opportunities(rng, cfg, accounts, leads)
    contracts = generate_contracts(rng, accounts, opportunities)
    billing = generate_billing(rng, contracts)
    product_events = generate_product_events(rng, cfg, accounts)
    customer_success = generate_customer_success(rng, accounts)

    outputs = {
        "raw_salesforce_accounts.csv": accounts,
        "raw_marketing_leads.csv": leads,
        "raw_salesforce_opportunities.csv": opportunities,
        "raw_contracts.csv": contracts,
        "raw_billing.csv": billing,
        "raw_product_events.csv": product_events,
        "raw_customer_success.csv": customer_success,
    }

    for filename, df in outputs.items():
        write_csv(df, cfg.output_dir / filename)

    print("\nSynthetic Revenue Intelligence data generated successfully.")
    print(f"Output directory: {cfg.output_dir.resolve()}")
    print("\nRow counts:")
    for filename, df in outputs.items():
        print(f"  {filename:<38} {len(df):>7,} rows")

    print("\nIntentional data-quality scenarios included:")
    print("  - duplicate account records")
    print("  - missing account identifiers on some leads")
    print("  - orphan opportunities")
    print("  - duplicate contract IDs")
    print("  - billing amount/timing mismatches")
    print("  - failed and pending payments")
    print("  - multiple revenue models")
    print("  - close-date changes")
    print("  - incomplete lifecycle coverage")


if __name__ == "__main__":
    main()
