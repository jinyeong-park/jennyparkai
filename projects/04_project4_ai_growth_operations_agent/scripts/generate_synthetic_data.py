"""Generate synthetic campaign and product-event data for the Tablr growth simulation.

All data is synthetic. No real companies, people, or ad accounts are represented.
Run: python scripts/generate_synthetic_data.py

Configuration is at the top of this file. The RANDOM_SEED guarantees reproducibility:
the same seed always produces the same row counts and the same first 10 account_ids.
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RANDOM_SEED: int = 20260913
DATA_ORIGIN: str = "SYNTHETIC"
START_DATE: date = date(2026, 1, 5)   # Week 1 start (Monday)
N_WEEKS: int = 12
N_TRIALS: int = 2_000
OUTPUT_DIR: Path = Path(__file__).parent.parent / "data" / "synthetic"

MONTHLY_BUDGET_USD: float = 150_000.0

# Channel budget shares (must sum to 1.0)
CHANNEL_BUDGET_SHARES: dict[str, float] = {
    "META": 0.40,
    "TIKTOK": 0.25,
    "GOOGLE_SEARCH": 0.20,
    "LINKEDIN": 0.15,
}

# ---------------------------------------------------------------------------
# Campaign / ad-group / creative taxonomy
# ---------------------------------------------------------------------------

CAMPAIGNS: list[dict] = [
    # META — 4 campaigns
    {"campaign_id": "camp_meta_001", "channel": "META", "name": "Meta - Broad Awareness",
     "ad_groups": ["ag_meta_001_001", "ag_meta_001_002", "ag_meta_001_003"]},
    {"campaign_id": "camp_meta_002", "channel": "META", "name": "Meta - Retargeting",
     "ad_groups": ["ag_meta_002_001", "ag_meta_002_002", "ag_meta_002_003"]},
    {"campaign_id": "camp_meta_003", "channel": "META", "name": "Meta - Lookalike",
     "ad_groups": ["ag_meta_003_001", "ag_meta_003_002", "ag_meta_003_003"]},
    {"campaign_id": "camp_meta_004", "channel": "META", "name": "Meta - UGC Testing",
     "ad_groups": ["ag_meta_004_001", "ag_meta_004_002", "ag_meta_004_003"]},
    # TIKTOK — 3 campaigns
    {"campaign_id": "camp_tiktok_001", "channel": "TIKTOK", "name": "TikTok - Native Discovery",
     "ad_groups": ["ag_tiktok_001_001", "ag_tiktok_001_002", "ag_tiktok_001_003"]},
    {"campaign_id": "camp_tiktok_002", "channel": "TIKTOK", "name": "TikTok - Owner UGC",
     "ad_groups": ["ag_tiktok_002_001", "ag_tiktok_002_002", "ag_tiktok_002_003"]},
    {"campaign_id": "camp_tiktok_003", "channel": "TIKTOK", "name": "TikTok - Before/After",
     "ad_groups": ["ag_tiktok_003_001", "ag_tiktok_003_002", "ag_tiktok_003_003"]},
    # GOOGLE_SEARCH — 2 campaigns
    {"campaign_id": "camp_google_001", "channel": "GOOGLE_SEARCH", "name": "Google - Branded",
     "ad_groups": ["ag_google_001_001", "ag_google_001_002", "ag_google_001_003"]},
    {"campaign_id": "camp_google_002", "channel": "GOOGLE_SEARCH", "name": "Google - Non-Branded",
     "ad_groups": ["ag_google_002_001", "ag_google_002_002", "ag_google_002_003"]},
    # LINKEDIN — 1 campaign
    {"campaign_id": "camp_linkedin_001", "channel": "LINKEDIN", "name": "LinkedIn - Decision Maker",
     "ad_groups": ["ag_linkedin_001_001", "ag_linkedin_001_002", "ag_linkedin_001_003"]},
]

# 3 creatives per ad group (average ~90 total)
CREATIVES_PER_AG: int = 3

# Persona segments and their default properties
PERSONA_SEGMENTS: list[str] = [
    "SCRAPPY_INDEPENDENT",
    "GROWTH_MINDED",
    "NEW_OWNER",
    "DELIVERY_HEAVY",
    "COMMUNITY_FOCUSED",
]

# Subscription tiers and monthly prices
TIER_PRICES: dict[str, int] = {"STARTER": 99, "GROWTH": 199, "PRO": 399}

# ---------------------------------------------------------------------------
# Intentional-pattern creative properties
# (These override baseline values for named creatives.)
# ---------------------------------------------------------------------------

CREATIVE_OVERRIDES: dict[str, dict] = {
    # Pattern 1: High CTR, low activation (FOMO hook attracts curiosity clickers)
    "cr_meta_001_001": {
        "ctr_mean": 0.050, "ctr_std": 0.005,
        "onboarding_rate_override": 0.18,
        "hook_type": "FEAR_OF_MISSING_OUT",
    },
    # Pattern 3: Creative fatigue — CTR decays after week 6
    "cr_meta_002_001": {
        "fatigue": True,
        "ctr_early": 0.032, "ctr_late": 0.011,
    },
    # Pattern 4: Platform-reported winner but weak blended CPAO
    "cr_meta_003_002": {
        "platform_roas_override": 4.2,
        "activation_rate_override": 0.22,
        # High signup volume achieved via low CVR floor boost: handled in allocation
    },
    # Pattern 5: Insufficient evidence (LinkedIn, weeks 11–12 only)
    "cr_linkedin_001_003": {
        "launch_week": 11,       # 0-indexed week (week 11 = last 2 weeks)
        "total_clicks_cap": 180,
        "state": "INSUFFICIENT_DATA",
    },
    # Pattern 6: Genuine winner
    "cr_tiktok_002_002": {
        "ctr_mean": 0.028, "ctr_std": 0.003,
        "activation_rate_override": 0.61,
        "m3_retention_override": 0.72,
        "cpao_override": 134.0,
    },
}

# Pattern 2: Community-focused persona overrides (applied at persona level)
COMMUNITY_FOCUSED_OVERRIDES: dict = {
    "m3_retention_override": 0.78,
    "ltv_override": 1450.0,
    "ctr_multiplier": 0.55,   # CTR ~1.2% vs ~2.2% baseline
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

END_DATE: date = START_DATE + timedelta(weeks=N_WEEKS) - timedelta(days=1)


def week_num(d: date) -> int:
    """Return 0-based week index relative to START_DATE."""
    return (d - START_DATE).days // 7


def date_range(start: date, end: date) -> list[date]:
    """Return list of dates from start to end inclusive."""
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


ALL_DATES: list[date] = date_range(START_DATE, END_DATE)


# ---------------------------------------------------------------------------
# Build creative dimension
# ---------------------------------------------------------------------------

def build_creative_dimension(rng: np.random.Generator) -> pd.DataFrame:
    """Return a DataFrame with one row per creative variant."""
    rows = []
    creative_num = 1

    hook_types = ["CONTRAST", "OUTCOME", "SOCIAL_PROOF", "DEMONSTRATION", "FEAR_OF_MISSING_OUT"]
    formats = ["STATIC_IMAGE", "SHORT_FORM_VIDEO", "UGC_VIDEO", "PRODUCT_DEMO", "CAROUSEL"]
    personas = PERSONA_SEGMENTS

    for camp in CAMPAIGNS:
        channel = camp["channel"]
        # abbreviation for creative IDs
        abbr = {"META": "meta", "TIKTOK": "tiktok", "GOOGLE_SEARCH": "google",
                "LINKEDIN": "linkedin"}[channel]

        for ag_id in camp["ad_groups"]:
            for cr_idx in range(CREATIVES_PER_AG):
                cid = f"cr_{abbr}_{creative_num:03d}_{cr_idx + 1:03d}"
                hook = rng.choice(hook_types)
                fmt = rng.choice(formats)
                persona = rng.choice(personas)

                overrides = CREATIVE_OVERRIDES.get(cid, {})
                if "hook_type" in overrides:
                    hook = overrides["hook_type"]

                rows.append({
                    "creative_id": cid,
                    "campaign_id": camp["campaign_id"],
                    "campaign_name": camp["name"],
                    "ad_group_id": ag_id,
                    "channel": channel,
                    "persona_segment": persona,
                    "hook_type": hook,
                    "creative_format": fmt,
                    "data_origin": DATA_ORIGIN,
                })
            creative_num += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate daily performance
# ---------------------------------------------------------------------------

def _ctr_for_creative(creative_id: str, d: date, rng: np.random.Generator,
                       channel: str) -> float:
    """Return a realistic CTR for a given creative and date."""
    # Baseline CTR by channel
    baseline = {"META": 0.022, "TIKTOK": 0.018, "GOOGLE_SEARCH": 0.035,
                "LINKEDIN": 0.008}[channel]

    overrides = CREATIVE_OVERRIDES.get(creative_id, {})

    if overrides.get("fatigue"):
        wk = week_num(d)
        if wk < 6:
            return float(rng.normal(overrides["ctr_early"], 0.003))
        else:
            # Linear decay from ctr_early at week 6 to ctr_late at week 11
            decay = (wk - 6) / 6.0
            target = overrides["ctr_early"] + decay * (overrides["ctr_late"] - overrides["ctr_early"])
            return float(rng.normal(target, 0.002))

    if "ctr_mean" in overrides:
        return float(rng.normal(overrides["ctr_mean"], overrides.get("ctr_std", 0.003)))

    # Pattern 2: COMMUNITY_FOCUSED persona gets lower CTR
    # (applied in generate_daily_performance per creative persona)
    return float(rng.normal(baseline, baseline * 0.2))


def generate_daily_performance(
    dim_creatives: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate one row per date × creative with realistic delivery metrics."""
    print("  Generating daily performance rows...")

    rows = []
    channel_monthly_budget = {
        ch: MONTHLY_BUDGET_USD * share for ch, share in CHANNEL_BUDGET_SHARES.items()
    }

    # Count creatives per channel to spread budget
    channel_creative_counts = dim_creatives.groupby("channel").size().to_dict()

    for _, cr in dim_creatives.iterrows():
        cid = cr["creative_id"]
        channel = cr["channel"]
        overrides = CREATIVE_OVERRIDES.get(cid, {})
        is_community = cr["persona_segment"] == "COMMUNITY_FOCUSED"

        # Budget share per creative per day
        n_creatives_ch = channel_creative_counts[channel]
        daily_budget = (channel_monthly_budget[channel] * N_WEEKS / 12.0) / (N_WEEKS * 7 * n_creatives_ch)

        launch_week = overrides.get("launch_week", 0)
        total_clicks_cap = overrides.get("total_clicks_cap", None)
        cumulative_clicks = 0

        for d in ALL_DATES:
            wk = week_num(d)
            if wk < launch_week:
                continue

            # Impressions from budget / CPM-equivalent
            cpm_base = {"META": 18, "TIKTOK": 5, "GOOGLE_SEARCH": 30, "LINKEDIN": 40}[channel]
            cpm = float(rng.normal(cpm_base, cpm_base * 0.15))
            impressions = int(daily_budget / (cpm / 1000))
            impressions = max(impressions, 10)

            # CTR
            ctr = _ctr_for_creative(cid, d, rng, channel)
            if is_community:
                ctr *= COMMUNITY_FOCUSED_OVERRIDES["ctr_multiplier"]
            ctr = max(0.001, min(ctr, 0.20))

            clicks = int(impressions * ctr)

            # Pattern 9: Data quality issue — ag_google_002_002 week 7
            if cr["ad_group_id"] == "ag_google_002_002" and wk == 6:  # week 7 is 0-indexed 6
                # 3 days with clicks > impressions (tracking pixel misconfiguration)
                day_in_week = (d - START_DATE).days % 7
                if day_in_week < 3:
                    clicks = impressions + int(rng.integers(10, 80))

            # Cap total clicks for insufficient-evidence creative
            if total_clicks_cap is not None:
                remaining = total_clicks_cap - cumulative_clicks
                if remaining <= 0:
                    clicks = 0
                else:
                    clicks = min(clicks, remaining)

            cumulative_clicks += clicks

            spend = round(impressions * cpm / 1000, 2)

            lp_view_rate = float(rng.uniform(0.85, 0.92))
            lp_views = int(clicks * lp_view_rate)

            # Trial signup CVR: 3–7% of LP views; varies by channel and persona
            base_cvr = {"META": 0.048, "TIKTOK": 0.040, "GOOGLE_SEARCH": 0.060,
                        "LINKEDIN": 0.035}[channel]
            if is_community:
                base_cvr *= 0.85  # slightly lower volume, higher quality
            cvr = float(rng.normal(base_cvr, base_cvr * 0.2))
            cvr = max(0.01, min(cvr, 0.15))
            trial_signups = int(lp_views * cvr)

            rows.append({
                "date": d.isoformat(),
                "channel": channel,
                "campaign_id": cr["campaign_id"],
                "campaign_name": cr["campaign_name"],
                "ad_group_id": cr["ad_group_id"],
                "ad_group_name": cr["ad_group_id"],  # simple label
                "creative_id": cid,
                "persona_segment": cr["persona_segment"],
                "impressions": impressions,
                "clicks": clicks,
                "spend_usd": round(spend, 2),
                "landing_page_views": lp_views,
                "trial_signups": trial_signups,
                "data_origin": DATA_ORIGIN,
            })

    df = pd.DataFrame(rows)
    print(f"    Daily performance rows: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Generate trial accounts
# ---------------------------------------------------------------------------

def generate_trial_accounts(
    daily_perf: pd.DataFrame,
    dim_creatives: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate N_TRIALS trial accounts distributed across creatives proportionally."""
    print(f"  Generating {N_TRIALS} trial accounts...")

    # Total signups per creative over the period
    signup_totals = daily_perf.groupby("creative_id")["trial_signups"].sum()
    total_signups = signup_totals.sum()
    if total_signups == 0:
        raise ValueError("No trial signups generated — check CTR/CVR settings.")

    # Proportional distribution of N_TRIALS
    weights = (signup_totals / total_signups).values
    creative_ids = signup_totals.index.tolist()
    creative_trial_counts = rng.multinomial(N_TRIALS, weights)

    cr_meta = dim_creatives.set_index("creative_id")

    tiers = list(TIER_PRICES.keys())
    tier_weights = [0.50, 0.35, 0.15]   # STARTER most common

    rows = []
    account_num = 1

    for cid, n_trials in zip(creative_ids, creative_trial_counts):
        if n_trials == 0:
            continue
        cr = cr_meta.loc[cid]
        channel = cr["channel"]
        campaign_id = cr["campaign_id"]
        ad_group_id = cr["ad_group_id"]
        persona = cr["persona_segment"]

        # Distribute signups across the campaign's date range
        # Use dates where this creative had signups > 0
        creative_dates = (
            daily_perf[daily_perf["creative_id"] == cid]["date"]
            .tolist()
        )
        # Filter to dates with non-zero signups for realism
        nonzero_mask = daily_perf["creative_id"] == cid
        nonzero_signups = daily_perf[nonzero_mask]["trial_signups"].values
        nonzero_dates = daily_perf[nonzero_mask]["date"].values
        if nonzero_signups.sum() > 0:
            date_weights = nonzero_signups / nonzero_signups.sum()
            chosen_dates = rng.choice(nonzero_dates, size=n_trials, p=date_weights)
        else:
            chosen_dates = rng.choice(nonzero_dates, size=n_trials)

        for i in range(n_trials):
            account_id = f"acct_{account_num:06d}"
            user_id = f"usr_{account_num:06d}"

            # Pattern 8: 8% missing attribution
            is_missing = rng.random() < 0.08
            row = {
                "account_id": account_id,
                "user_id": user_id,
                "signup_date": chosen_dates[i],
                "channel": None if is_missing else channel,
                "campaign_id": None if is_missing else campaign_id,
                "ad_group_id": None if is_missing else ad_group_id,
                "creative_id": None if is_missing else cid,
                "persona_segment": persona,
                "subscription_tier": None,   # filled after conversion
                "is_missing_attribution": is_missing,
                "data_origin": DATA_ORIGIN,
            }
            rows.append(row)
            account_num += 1

    df = pd.DataFrame(rows)
    df = df.sort_values("signup_date").reset_index(drop=True)
    print(f"    Trial accounts: {len(df):,}  (missing attribution: {df['is_missing_attribution'].sum():,})")
    return df


# ---------------------------------------------------------------------------
# Generate product events
# ---------------------------------------------------------------------------

def _onboarding_rate(account: pd.Series) -> float:
    """Return the fraction of trial signups who complete onboarding."""
    cid = account.get("creative_id")
    overrides = CREATIVE_OVERRIDES.get(cid or "", {})
    if "onboarding_rate_override" in overrides:
        return overrides["onboarding_rate_override"]
    return 0.42  # baseline


def _activation_rate(account: pd.Series) -> float:
    """Return the fraction of onboarded users who launch a campaign within 14 days."""
    cid = account.get("creative_id")
    persona = account.get("persona_segment", "")
    overrides = CREATIVE_OVERRIDES.get(cid or "", {})
    if "activation_rate_override" in overrides:
        return overrides["activation_rate_override"]
    # Pattern 4: platform winner but low activation
    if cid == "cr_meta_003_002":
        return overrides.get("activation_rate_override", 0.22)
    return 0.71  # baseline


def generate_product_events(
    trial_accounts: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate one row per product event per user."""
    print("  Generating product events...")

    event_rows = []

    for _, acct in trial_accounts.iterrows():
        signup_dt = pd.to_datetime(acct["signup_date"])
        acct_id = acct["account_id"]
        user_id = acct["user_id"]
        cid = acct.get("creative_id")
        persona = acct.get("persona_segment", "")

        # TRIAL_SIGNUP — always present
        event_rows.append({
            "event_id": f"evt_{acct_id}_trial_signup",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "TRIAL_SIGNUP",
            "event_timestamp": signup_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

        # ONBOARDING_COMPLETED (within 3 days)
        ob_rate = _onboarding_rate(acct)
        if rng.random() > ob_rate:
            continue
        onboard_delay = int(rng.integers(1, 4))  # 1–3 days after signup
        onboard_dt = signup_dt + timedelta(days=onboard_delay)
        event_rows.append({
            "event_id": f"evt_{acct_id}_onboarding",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "ONBOARDING_COMPLETED",
            "event_timestamp": onboard_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

        # PROFILE_CREATED (88% within 1 day of onboarding)
        if rng.random() > 0.88:
            continue
        profile_dt = onboard_dt + timedelta(days=1)
        event_rows.append({
            "event_id": f"evt_{acct_id}_profile",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "PROFILE_CREATED",
            "event_timestamp": profile_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

        # CAMPAIGN_LAUNCHED (activation: 71% baseline within 14 days of signup)
        # Must happen after PROFILE_CREATED (which is at profile_dt)
        act_rate = _activation_rate(acct)
        if rng.random() > act_rate:
            continue
        max_launch_delay = 14
        # Launch must be after profile_dt, but still within 14 days of signup
        min_launch_dt = profile_dt + timedelta(days=1)
        max_launch_dt = signup_dt + timedelta(days=max_launch_delay)
        if min_launch_dt > max_launch_dt:
            # Edge case: profile created too late; extend the window slightly
            max_launch_dt = min_launch_dt + timedelta(days=2)
        window_days = max((max_launch_dt - min_launch_dt).days, 1)
        launch_delay = int(rng.integers(0, window_days))
        launch_dt = min_launch_dt + timedelta(days=launch_delay)
        event_rows.append({
            "event_id": f"evt_{acct_id}_campaign_launched",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "CAMPAIGN_LAUNCHED",
            "event_timestamp": launch_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

        # FIRST_CUSTOMER_ACQUIRED (65% within 30 days of campaign launch)
        if rng.random() > 0.65:
            continue
        fca_delay = int(rng.integers(1, 30))
        fca_dt = launch_dt + timedelta(days=fca_delay)
        event_rows.append({
            "event_id": f"evt_{acct_id}_first_customer",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "FIRST_CUSTOMER_ACQUIRED",
            "event_timestamp": fca_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

        # SUBSCRIPTION_STARTED (78% of first-customer-acquired users)
        if rng.random() > 0.78:
            continue
        # Pattern 7: 15% have 7–14 day conversion delay after trial period (14 days)
        has_delay = rng.random() < 0.15
        trial_end = signup_dt + timedelta(days=14)
        if has_delay:
            conv_delay = int(rng.normal(10.5, 1.5))
            conv_delay = max(7, min(conv_delay, 14))
        else:
            conv_delay = 0
        sub_dt_candidate = trial_end + timedelta(days=conv_delay)
        # Ensure SUBSCRIPTION_STARTED is always after FIRST_CUSTOMER_ACQUIRED
        sub_dt = max(sub_dt_candidate, fca_dt + timedelta(days=1))
        event_rows.append({
            "event_id": f"evt_{acct_id}_subscription",
            "account_id": acct_id,
            "user_id": user_id,
            "event_type": "SUBSCRIPTION_STARTED",
            "event_timestamp": sub_dt.isoformat(),
            "creative_id": cid,
            "campaign_id": acct.get("campaign_id"),
            "data_origin": DATA_ORIGIN,
        })

    df = pd.DataFrame(event_rows)
    print(f"    Product events: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Generate subscriptions
# ---------------------------------------------------------------------------

def generate_subscriptions(
    trial_accounts: pd.DataFrame,
    product_events: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate one row per subscription lifecycle."""
    print("  Generating subscriptions...")

    sub_events = product_events[product_events["event_type"] == "SUBSCRIPTION_STARTED"].copy()
    trial_dt_map = (
        product_events[product_events["event_type"] == "TRIAL_SIGNUP"]
        .set_index("account_id")["event_timestamp"]
        .to_dict()
    )
    acct_meta = trial_accounts.set_index("account_id")

    tiers = list(TIER_PRICES.keys())
    tier_weights = [0.50, 0.35, 0.15]

    rows = []
    for _, sub in sub_events.iterrows():
        acct_id = sub["account_id"]
        sub_dt = pd.to_datetime(sub["event_timestamp"])
        trial_start = pd.to_datetime(trial_dt_map.get(acct_id, sub["event_timestamp"]))
        conv_delay = (sub_dt - trial_start - timedelta(days=14)).days
        conv_delay = max(0, conv_delay)

        acct = acct_meta.loc[acct_id] if acct_id in acct_meta.index else {}
        persona = acct.get("persona_segment", "") if hasattr(acct, "get") else ""
        cid = acct.get("creative_id", None) if hasattr(acct, "get") else None

        # Tier selection
        tier = rng.choice(tiers, p=tier_weights)
        monthly_price = TIER_PRICES[tier]

        # Retention: draw churn month
        m1_rate = 0.82
        m3_rate = 0.78 if persona == "COMMUNITY_FOCUSED" else 0.55
        m6_rate = 0.41

        # Override from genuine winner creative
        cr_overrides = CREATIVE_OVERRIDES.get(cid or "", {})
        if "m3_retention_override" in cr_overrides:
            m3_rate = cr_overrides["m3_retention_override"]

        # Simulate churn month (simplified: pick a churn date if subscriber churns)
        rand = rng.random()
        if rand > m1_rate:
            churn_months = 1
        elif rand > m3_rate:
            churn_months = int(rng.integers(2, 3))
        elif rand > m6_rate:
            churn_months = int(rng.integers(4, 6))
        else:
            churn_months = None  # active beyond 6 months

        status = "churned" if churn_months is not None else "active"
        churn_date = None
        if churn_months:
            churn_date = (sub_dt + timedelta(days=30 * churn_months)).date().isoformat()

        # Location count (expansion)
        loc_count = 1
        if persona == "GROWTH_MINDED" and rng.random() < 0.18:
            loc_count = int(rng.integers(2, 4))
        elif rng.random() < 0.06:
            loc_count = 2

        rows.append({
            "subscription_id": f"sub_{acct_id}",
            "account_id": acct_id,
            "trial_start_date": trial_start.date().isoformat(),
            "conversion_date": sub_dt.date().isoformat(),
            "conversion_delay_days": conv_delay,
            "subscription_tier": tier,
            "monthly_price_usd": monthly_price,
            "status": status,
            "churn_date": churn_date,
            "location_count": loc_count,
            "data_origin": DATA_ORIGIN,
        })

    df = pd.DataFrame(rows)
    print(f"    Subscriptions: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Generate revenue events
# ---------------------------------------------------------------------------

def generate_revenue_events(
    subscriptions: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate monthly MRR events per active subscription, plus expansion revenue."""
    print("  Generating revenue events...")

    rows = []
    rev_id = 1

    for _, sub in subscriptions.iterrows():
        conv_dt = pd.to_datetime(sub["conversion_date"])
        churn_dt = pd.to_datetime(sub["churn_date"]) if sub["churn_date"] else None
        monthly_price = sub["monthly_price_usd"]
        loc_count = sub["location_count"]

        # Monthly billing events up to END_DATE or churn
        billing_dt = conv_dt
        month_num = 0
        while billing_dt.date() <= END_DATE:
            if churn_dt and billing_dt >= churn_dt:
                break
            # Expansion: extra locations add MRR
            effective_price = monthly_price * loc_count
            rows.append({
                "revenue_event_id": f"rev_{rev_id:07d}",
                "account_id": sub["account_id"],
                "subscription_id": sub["subscription_id"],
                "event_date": billing_dt.date().isoformat(),
                "event_type": "MRR",
                "amount_usd": round(effective_price, 2),
                "month_num": month_num,
                "location_count": loc_count,
                "data_origin": DATA_ORIGIN,
            })
            rev_id += 1

            # Check for location_added event (expansion bump after month 2)
            if month_num == 2 and loc_count > 1:
                rows.append({
                    "revenue_event_id": f"rev_{rev_id:07d}",
                    "account_id": sub["account_id"],
                    "subscription_id": sub["subscription_id"],
                    "event_date": billing_dt.date().isoformat(),
                    "event_type": "EXPANSION",
                    "amount_usd": round(monthly_price * (loc_count - 1), 2),
                    "month_num": month_num,
                    "location_count": loc_count,
                    "data_origin": DATA_ORIGIN,
                })
                rev_id += 1

            billing_dt += timedelta(days=30)
            month_num += 1

    df = pd.DataFrame(rows)
    print(f"    Revenue events: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save_table(df: pd.DataFrame, name: str, output_dir: Path) -> None:
    """Save as Parquet and CSV."""
    parquet_path = output_dir / f"{name}.parquet"
    csv_path = output_dir / f"{name}.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    size_kb = parquet_path.stat().st_size / 1024
    print(f"    Saved {name}: {len(df):,} rows, {size_kb:.1f} KB (parquet)")


def save_manifest(record_counts: dict, output_dir: Path) -> None:
    """Save a generation manifest."""
    manifest = {
        "seed": RANDOM_SEED,
        "generation_timestamp": datetime.utcnow().isoformat() + "Z",
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "n_weeks": N_WEEKS,
        "n_trials_target": N_TRIALS,
        "record_counts": record_counts,
        "data_origin": DATA_ORIGIN,
        "version": "1.0.0",
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    print(f"    Saved manifest.json")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("Tablr Growth Simulation — Synthetic Data Generator")
    print(f"Seed: {RANDOM_SEED}  |  Start: {START_DATE}  |  Weeks: {N_WEEKS}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)

    print("\n[1/7] Building creative dimension...")
    dim_creatives = build_creative_dimension(rng)
    print(f"  Creatives: {len(dim_creatives):,}")

    print("\n[2/7] Generating daily performance...")
    daily_perf = generate_daily_performance(dim_creatives, rng)

    print("\n[3/7] Generating trial accounts...")
    trial_accounts = generate_trial_accounts(daily_perf, dim_creatives, rng)

    print("\n[4/7] Generating product events...")
    product_events = generate_product_events(trial_accounts, rng)

    print("\n[5/7] Generating subscriptions...")
    subscriptions = generate_subscriptions(trial_accounts, product_events, rng)

    print("\n[6/7] Generating revenue events...")
    revenue_events = generate_revenue_events(subscriptions, rng)

    print("\n[7/7] Saving all tables...")
    save_table(dim_creatives, "dim_creatives", OUTPUT_DIR)
    save_table(daily_perf, "fact_daily_performance", OUTPUT_DIR)
    save_table(trial_accounts, "dim_trial_accounts", OUTPUT_DIR)
    save_table(product_events, "fact_product_events", OUTPUT_DIR)
    save_table(subscriptions, "fact_subscriptions", OUTPUT_DIR)
    save_table(revenue_events, "fact_revenue_events", OUTPUT_DIR)

    record_counts = {
        "dim_creatives": len(dim_creatives),
        "fact_daily_performance": len(daily_perf),
        "dim_trial_accounts": len(trial_accounts),
        "fact_product_events": len(product_events),
        "fact_subscriptions": len(subscriptions),
        "fact_revenue_events": len(revenue_events),
    }
    save_manifest(record_counts, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("Generation complete.")
    for table, count in record_counts.items():
        print(f"  {table:<35} {count:>8,} rows")
    print("=" * 60)


if __name__ == "__main__":
    main()
