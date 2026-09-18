import os
import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Fix random seed for reproducibility
np.random.seed(42)
random.seed(42)

# --- 1. Output directory and 50 DMA definitions ---
OUTPUT_DIR = "../data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_USERS  = 10000
START_DATE = datetime(2026, 1, 1)
END_DATE   = datetime(2026, 6, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

CITY_NAMES = [
    "SAN_FRANCISCO", "NEW_YORK",      "CHICAGO",       "LOS_ANGELES",   "DALLAS",
    "SEATTLE",       "AUSTIN",        "ATLANTA",        "BOSTON",        "DENVER",
    "MIAMI",         "PHOENIX",       "PHILADELPHIA",   "SAN_DIEGO",     "SAN_JOSE",
    "HOUSTON",       "DETROIT",       "MINNEAPOLIS",    "TAMPA",         "ORLANDO",
    "BALTIMORE",     "CLEVELAND",     "SACRAMENTO",     "PITTSBURGH",    "PORTLAND",
    "LAS_VEGAS",     "ST_LOUIS",      "CHARLOTTE",      "NASHVILLE",     "SALT_LAKE_CITY",
    "COLUMBUS",      "INDIANAPOLIS",  "SAN_ANTONIO",    "KANSAS_CITY",   "CINCINNATI",
    "MILWAUKEE",     "RALEIGH",       "OKLAHOMA_CITY",  "MEMPHIS",       "RICHMOND",
    "LOUISVILLE",    "NEW_ORLEANS",   "BUFFALO",        "HARTFORD",      "PROVIDENCE",
    "BIRMINGHAM",    "ROCHESTER",     "GREENVILLE",     "ALBUQUERQUE",   "TUCSON",
]

DMAS         = [f"DMA_{100 + i}_{name}" for i, name in enumerate(CITY_NAMES)]
HOLDOUT_DMAS = set(DMAS[:10])  # First 10 DMAs are the geo-holdout control group (Meta ads paused in June)

CHANNELS = ["meta_paid_social", "google_paid_search", "tiktok_ads", "email_crm", "google_organic"]

# Real-world UTM source noise: marketers type these manually, causing inconsistent capitalization
NOISY_UTM_SOURCES = {
    "meta_paid_social":  ["meta", "Meta", "META", "facebook_ads", None],
    "google_paid_search": ["google", "Google", "google_cpc", None],
    "tiktok_ads":        ["tiktok", "TikTok", "tiktok_cpc"],
    "email_crm":         ["klaviyo", "email", "newsletter"],
    "google_organic":    ["google", "organic", None],
}


def get_seasonal_campaign(dt):
    """Return a campaign name based on the month, with realistic capitalization noise."""
    month = dt.month
    if month in [1, 2, 3]:
        return random.choice(["q1_prospecting", "Q1_Prospecting", "q1_brand_awareness", None])
    elif month in [4, 5]:
        return random.choice(["q2_growth_promo", "Q2_Growth_Promo", "q2_prospecting", None])
    else:  # June
        return random.choice(["q2_retargeting", "Q2_Retargeting", "june_geo_experiment", None])


print("Generating synthetic Growth Analytics data (with campaign seasonality)...")

touchpoints   = []
conversions   = []
order_counter = 100000

for i in range(NUM_USERS):
    user_id  = f"USR_{10000 + i}"
    user_dma = random.choice(DMAS)

    first_touch_time = START_DATE + timedelta(
        days=random.randint(0, TOTAL_DAYS - 15),
        hours=random.randint(0, 23),
    )

    # Assign each user to one of three behavioral types
    user_type = np.random.choice(
        ["organic_direct", "multi_channel", "non_converter"],
        p=[0.20, 0.25, 0.55],
    )

    # ── organic_direct: single organic touchpoint, converts quickly ──────
    if user_type == "organic_direct":
        tp_time = first_touch_time
        touchpoints.append({
            "event_id":      str(uuid.uuid4()),
            "user_id":       user_id,
            "timestamp":     tp_time.strftime("%Y-%m-%d %H:%M:%S"),
            "channel":       "google_organic",
            "utm_source":    "google",
            "utm_medium":    "organic",
            "campaign_name": "brand_organic",
            "dma_code":      user_dma,
        })

        conv_time = tp_time + timedelta(minutes=random.randint(5, 60))
        order_counter += 1
        conversions.append({
            "conversion_id":  str(uuid.uuid4()),
            "user_id":        user_id,
            "order_id":       f"ORD_{order_counter}",
            "converted_at":   conv_time.strftime("%Y-%m-%d %H:%M:%S"),
            "order_value_usd": round(float(np.random.lognormal(mean=4.2, sigma=0.5)), 2),
            "dma_code":       user_dma,
        })

    # ── multi_channel: 2–5 paid/owned touchpoints before converting ──────
    elif user_type == "multi_channel":
        num_tps   = random.randint(2, 5)
        curr_time = first_touch_time

        for tp_idx in range(num_tps):
            available_channels = ["meta_paid_social", "google_paid_search", "tiktok_ads", "email_crm"]

            # Geo-holdout: Meta ads are paused in control DMAs during June
            if curr_time.month == 6 and user_dma in HOLDOUT_DMAS:
                available_channels.remove("meta_paid_social")

            ch      = random.choice(available_channels)
            utm_src = random.choice(NOISY_UTM_SOURCES[ch])

            tp_event = {
                "event_id":      str(uuid.uuid4()),
                "user_id":       user_id,
                "timestamp":     curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "channel":       ch,
                "utm_source":    utm_src,
                "utm_medium":    "cpc" if "paid" in ch or "ads" in ch else "email",
                "campaign_name": get_seasonal_campaign(curr_time),
                "dma_code":      user_dma,
            }
            touchpoints.append(tp_event)

            # ~3% of events are duplicates (double-click or network retry)
            if random.random() < 0.03:
                dup_event = tp_event.copy()
                dup_event["event_id"] = str(uuid.uuid4())
                touchpoints.append(dup_event)

            curr_time += timedelta(days=random.randint(1, 4), hours=random.randint(1, 12))

        conv_time = curr_time + timedelta(hours=random.randint(1, 24))
        order_counter += 1
        conversions.append({
            "conversion_id":  str(uuid.uuid4()),
            "user_id":        user_id,
            "order_id":       f"ORD_{order_counter}",
            "converted_at":   conv_time.strftime("%Y-%m-%d %H:%M:%S"),
            "order_value_usd": round(float(np.random.lognormal(mean=4.5, sigma=0.6)), 2),
            "dma_code":       user_dma,
        })

    # ── non_converter: browsed across paid channels but never purchased ──
    else:
        num_tps   = random.randint(1, 3)
        curr_time = first_touch_time

        for _ in range(num_tps):
            available_channels = ["meta_paid_social", "tiktok_ads", "google_paid_search"]

            # Geo-holdout: Meta ads are paused in control DMAs during June
            if curr_time.month == 6 and user_dma in HOLDOUT_DMAS:
                available_channels.remove("meta_paid_social")

            ch = random.choice(available_channels)
            touchpoints.append({
                "event_id":      str(uuid.uuid4()),
                "user_id":       user_id,
                "timestamp":     curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "channel":       ch,
                "utm_source":    random.choice(NOISY_UTM_SOURCES[ch]),
                "utm_medium":    "cpc",
                "campaign_name": get_seasonal_campaign(curr_time),
                "dma_code":      user_dma,
            })
            curr_time += timedelta(days=random.randint(1, 7))

df_touchpoints = pd.DataFrame(touchpoints)
df_conversions = pd.DataFrame(conversions)

# --- 2. Generate raw_ad_spend ---
# Platform-reported conversions are inflated by 25–45% above real conversions,
# simulating the self-attribution bias that each ad platform applies.
spend_records = []
date_range    = pd.date_range(START_DATE, END_DATE, freq="D")

for dt in date_range:
    date_str = dt.strftime("%Y-%m-%d")
    is_june  = dt.month == 6

    for dma in DMAS:
        for ch in ["meta_paid_social", "google_paid_search", "tiktok_ads"]:
            # No Meta spend in holdout DMAs during the June experiment
            if is_june and dma in HOLDOUT_DMAS and ch == "meta_paid_social":
                base_spend = 0.0
            else:
                base_spend = random.uniform(50.0, 300.0)

            real_convs            = int(base_spend / random.uniform(15.0, 25.0)) if base_spend > 0 else 0
            platform_claimed_convs = int(real_convs * random.uniform(1.25, 1.45))  # platform over-reports

            spend_records.append({
                "date":                         date_str,
                "channel":                      ch,
                "dma_code":                     dma,
                "daily_spend_usd":              round(base_spend, 2),
                "platform_reported_conversions": platform_claimed_convs,
            })

df_spend = pd.DataFrame(spend_records)

# --- 3. Save CSVs ---
df_touchpoints.to_csv(os.path.join(OUTPUT_DIR, "raw_user_touchpoints.csv"), index=False)
df_conversions.to_csv(os.path.join(OUTPUT_DIR, "raw_conversions.csv"), index=False)
df_spend.to_csv(os.path.join(OUTPUT_DIR, "raw_ad_spend.csv"), index=False)

print("\nData generation complete.")
print(f"  raw_user_touchpoints.csv : {len(df_touchpoints):,} rows")
print(f"  raw_conversions.csv      : {len(df_conversions):,} rows")
print(f"  raw_ad_spend.csv         : {len(df_spend):,} rows")

# --- 4. Holdout validation ---
# Verify that no Meta touchpoints exist in holdout DMAs during June (should be 0)
holdout_check = df_touchpoints[
    (df_touchpoints["dma_code"].isin(HOLDOUT_DMAS)) &
    (pd.to_datetime(df_touchpoints["timestamp"]).dt.month == 6) &
    (df_touchpoints["channel"] == "meta_paid_social")
]
print(f"\n[Holdout check] Meta touchpoints in control DMAs during June (expected 0): {len(holdout_check)}")
