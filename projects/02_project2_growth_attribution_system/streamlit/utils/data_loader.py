"""
Data loader and attribution computation layer.

Replicates the dbt pipeline logic (stg → int → marts) directly from raw CSVs,
so the Streamlit app runs without a PostgreSQL connection.

All functions are decorated with @st.cache_data so computation runs only once
per session.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

CHANNEL_MAP = {
    "meta_paid_social":  "Meta Paid Social",
    "google_paid_search": "Google Paid Search",
    "tiktok_ads":        "TikTok Ads",
    "email_crm":         "Email / CRM",
    "google_organic":    "Google Organic",
}

PAID_CHANNELS = ["Meta Paid Social", "Google Paid Search", "TikTok Ads"]

CHANNEL_COLORS = {
    "Meta Paid Social":  "#1877F2",
    "Google Paid Search": "#34A853",
    "TikTok Ads":        "#EE1D52",
    "Email / CRM":       "#6C757D",
    "Google Organic":    "#FBBC04",
}

MODEL_COLORS = {
    "First-Touch":  "#E74C3C",
    "Last-Touch":   "#E67E22",
    "Linear":       "#3498DB",
    "Time-Decay":   "#9B59B6",
}

CONTROL_DMAS = {
    "DMA_100_SAN_FRANCISCO", "DMA_101_NEW_YORK",  "DMA_102_CHICAGO",
    "DMA_103_LOS_ANGELES",   "DMA_104_DALLAS",    "DMA_105_SEATTLE",
    "DMA_106_AUSTIN",        "DMA_107_ATLANTA",   "DMA_108_BOSTON",
    "DMA_109_DENVER",
}

# ─────────────────────────────────────────────────────────────────────────────
# Raw data loading
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tp  = pd.read_csv(DATA_DIR / "raw_user_touchpoints.csv")
    cv  = pd.read_csv(DATA_DIR / "raw_conversions.csv")
    sp  = pd.read_csv(DATA_DIR / "raw_ad_spend.csv")

    tp["timestamp"]    = pd.to_datetime(tp["timestamp"])
    cv["converted_at"] = pd.to_datetime(cv["converted_at"])
    sp["date"]         = pd.to_datetime(sp["date"])

    return tp, cv, sp


# ─────────────────────────────────────────────────────────────────────────────
# Staging: clean + normalize  (mirrors stg_user_touchpoints.sql)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def get_staged_touchpoints() -> pd.DataFrame:
    tp, _, _ = load_raw_data()
    df = tp.copy()
    df["channel"] = df["channel"].str.lower().str.strip().map(CHANNEL_MAP)
    df = df.dropna(subset=["channel"])
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Intermediate: dedup + attribution window  (mirrors int_* models)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def get_pre_conversion_touchpoints() -> pd.DataFrame:
    tp = get_staged_touchpoints()
    _, cv, _ = load_raw_data()

    # Dedup: keep earliest event_id per (user, timestamp, channel)
    tp = (
        tp.sort_values("event_id")
        .drop_duplicates(subset=["user_id", "timestamp", "channel"], keep="first")
    )

    # Attribution window: touchpoint ≤ conversion and ≥ 90 days before
    merged = tp.merge(
        cv[["user_id", "conversion_id", "converted_at", "order_value_usd"]],
        on="user_id",
        how="inner",
    )
    window = merged[
        (merged["timestamp"] <= merged["converted_at"]) &
        (merged["timestamp"] >= merged["converted_at"] - pd.Timedelta(days=90))
    ].copy()

    return window


# ─────────────────────────────────────────────────────────────────────────────
# Marts: attribution models  (mirrors mrt_* models)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def compute_attribution() -> pd.DataFrame:
    """
    Compute all four attribution models in one pass and return a long-format
    DataFrame with columns: channel, model, attributed_revenue.
    """
    df = get_pre_conversion_touchpoints().copy()
    df = df.sort_values(["conversion_id", "timestamp"])

    # Touch count and rank per conversion
    df["n_touches"]  = df.groupby("conversion_id")["event_id"].transform("count")
    df["touch_rank"] = df.groupby("conversion_id").cumcount() + 1  # 1 = first

    # Time-decay weight: half-life = 7 days
    df["days_before"]        = (df["converted_at"] - df["timestamp"]).dt.total_seconds() / 86400.0
    df["decay_weight"]       = np.power(2.0, -df["days_before"] / 7.0)
    df["total_decay_weight"] = df.groupby("conversion_id")["decay_weight"].transform("sum")

    # First-Touch: 100% to rank 1
    df["first_touch_credit"] = np.where(
        df["touch_rank"] == 1, df["order_value_usd"], 0.0
    )
    # Last-Touch: 100% to last rank
    df["last_touch_credit"] = np.where(
        df["touch_rank"] == df["n_touches"], df["order_value_usd"], 0.0
    )
    # Linear: equal split
    df["linear_credit"] = df["order_value_usd"] / df["n_touches"]
    # Time-Decay: proportional to recency weight
    df["time_decay_credit"] = (
        df["order_value_usd"] * df["decay_weight"] / df["total_decay_weight"]
    )

    # Aggregate by channel
    agg = (
        df.groupby("channel")
        .agg(
            first_touch_revenue  = ("first_touch_credit",  "sum"),
            last_touch_revenue   = ("last_touch_credit",   "sum"),
            linear_revenue       = ("linear_credit",        "sum"),
            time_decay_revenue   = ("time_decay_credit",    "sum"),
            total_conversions    = ("conversion_id",        "nunique"),
        )
        .reset_index()
    )
    return agg


@st.cache_data
def get_attribution_long() -> pd.DataFrame:
    """Return attribution results in long format for Plotly charts."""
    agg = compute_attribution()
    records = []
    for _, row in agg.iterrows():
        for model, col in [
            ("First-Touch",  "first_touch_revenue"),
            ("Last-Touch",   "last_touch_revenue"),
            ("Linear",       "linear_revenue"),
            ("Time-Decay",   "time_decay_revenue"),
        ]:
            records.append({
                "channel":            row["channel"],
                "model":              model,
                "attributed_revenue": row[col],
            })
    return pd.DataFrame(records)


@st.cache_data
def get_roas_table() -> pd.DataFrame:
    """ROAS by channel × model, plus platform-reported ROAS."""
    agg = compute_attribution()
    _, _, sp = load_raw_data()

    # Total spend per paid channel (all months)
    spend = (
        sp[sp["channel"].isin(["meta_paid_social", "google_paid_search", "tiktok_ads"])]
        .copy()
    )
    spend["channel"] = spend["channel"].map(CHANNEL_MAP)
    spend_by_channel = spend.groupby("channel")["daily_spend_usd"].sum().reset_index()
    spend_by_channel.columns = ["channel", "total_spend"]

    # Platform-reported conversions × avg order value proxy ($160)
    platform_rev = (
        spend.groupby("channel")["platform_reported_conversions"].sum() * 160
    ).reset_index()
    platform_rev.columns = ["channel", "platform_revenue"]

    df = (
        agg.merge(spend_by_channel, on="channel", how="left")
        .merge(platform_rev, on="channel", how="left")
    )

    for model, col in [
        ("First-Touch",  "first_touch_revenue"),
        ("Last-Touch",   "last_touch_revenue"),
        ("Linear",       "linear_revenue"),
        ("Time-Decay",   "time_decay_revenue"),
    ]:
        df[f"{model} ROAS"] = (df[col] / df["total_spend"]).round(2)

    df["Platform ROAS"] = (df["platform_revenue"] / df["total_spend"]).round(2)

    return df[["channel", "total_spend", "Platform ROAS",
               "First-Touch ROAS", "Last-Touch ROAS", "Linear ROAS", "Time-Decay ROAS"]]


# ─────────────────────────────────────────────────────────────────────────────
# Geo-Holdout
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def get_geo_holdout_results() -> dict:
    tp, cv, sp = load_raw_data()

    # Population proxy: unique users per DMA across all time
    dma_pop = (
        tp.groupby("dma_code")["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "population"})
    )

    # June conversions only
    june = cv[
        (cv["converted_at"] >= "2026-06-01") &
        (cv["converted_at"] <= "2026-06-30")
    ]

    all_dmas       = june["dma_code"].unique().tolist()
    treatment_dmas = [d for d in all_dmas if d not in CONTROL_DMAS]

    def agg_group(dma_list):
        grp = (
            june[june["dma_code"].isin(dma_list)]
            .groupby("dma_code")
            .agg(conversions=("conversion_id", "count"),
                 revenue=("order_value_usd", "sum"))
            .reset_index()
            .merge(dma_pop, on="dma_code", how="left")
        )
        grp["conversion_rate"] = grp["conversions"] / grp["population"]
        return grp

    ctrl = agg_group(list(CONTROL_DMAS))
    trt  = agg_group(treatment_dmas)

    baseline_rate     = ctrl["conversions"].sum() / ctrl["population"].sum()
    expected_baseline = trt["population"].sum() * baseline_rate
    actual_convs      = trt["conversions"].sum()
    incremental_convs = actual_convs - expected_baseline
    avg_order         = trt["revenue"].sum() / actual_convs
    incremental_rev   = incremental_convs * avg_order

    meta_spend = sp[
        (sp["date"] >= "2026-06-01") &
        (sp["date"] <= "2026-06-30") &
        (sp["channel"] == "meta_paid_social") &
        (~sp["dma_code"].isin(CONTROL_DMAS))
    ]["daily_spend_usd"].sum()

    icac   = meta_spend / incremental_convs if incremental_convs > 0 else float("inf")
    i_roas = incremental_rev / meta_spend if meta_spend > 0 else 0.0
    lift   = (incremental_convs / expected_baseline * 100) if expected_baseline > 0 else 0.0

    # Significance test
    from scipy import stats as scipy_stats
    n_t, n_c   = trt["population"].sum(), ctrl["population"].sum()
    cv_t, cv_c = trt["conversions"].sum(), ctrl["conversions"].sum()
    rate_t, rate_c = cv_t / n_t, cv_c / n_c
    pooled_p   = (cv_t + cv_c) / (n_t + n_c)
    se         = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_t + 1 / n_c))
    z_score    = (rate_t - rate_c) / se
    p_value    = 2 * (1 - scipy_stats.norm.cdf(abs(z_score)))

    return {
        "control_dmas":           len(ctrl),
        "treatment_dmas":         len(trt),
        "control_rate_pct":       round(rate_c * 100, 3),
        "treatment_rate_pct":     round(rate_t * 100, 3),
        "baseline_rate_pct":      round(baseline_rate * 100, 3),
        "expected_baseline":      round(expected_baseline, 0),
        "actual_conversions":     int(actual_convs),
        "incremental_conversions": round(incremental_convs, 0),
        "organic_share_pct":      round(100 - lift, 1),
        "incremental_lift_pct":   round(lift, 1),
        "meta_spend":             round(meta_spend, 0),
        "incremental_roas":       round(i_roas, 2),
        "platform_roas":          3.25,
        "icac":                   round(icac, 2),
        "z_score":                round(z_score, 3),
        "p_value":                round(p_value, 4),
        "significant":            p_value < 0.05,
        "ctrl_df":                ctrl,
        "trt_df":                 trt,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Overview metrics
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def get_overview_metrics() -> dict:
    _, cv, sp = load_raw_data()
    paid = sp[sp["channel"].isin(["meta_paid_social", "google_paid_search", "tiktok_ads"])]

    total_spend        = paid["daily_spend_usd"].sum()
    total_actual_convs = len(cv)
    total_platform_convs = paid["platform_reported_conversions"].sum()
    total_revenue      = cv["order_value_usd"].sum()

    platform_roas = (total_platform_convs * 160) / total_spend
    actual_roas   = total_revenue / total_spend
    overstatement = (platform_roas - actual_roas) / actual_roas * 100

    # By channel (paid only)
    paid_ch = paid.copy()
    paid_ch["channel"] = paid_ch["channel"].map(CHANNEL_MAP)
    by_channel = paid_ch.groupby("channel").agg(
        spend=("daily_spend_usd", "sum"),
        platform_conversions=("platform_reported_conversions", "sum"),
    ).reset_index()
    by_channel["platform_revenue"] = by_channel["platform_conversions"] * 160
    by_channel["platform_roas"]    = (by_channel["platform_revenue"] / by_channel["spend"]).round(2)

    return {
        "total_spend":          total_spend,
        "total_actual_convs":   total_actual_convs,
        "total_platform_convs": total_platform_convs,
        "total_revenue":        total_revenue,
        "blended_platform_roas": round(platform_roas, 2),
        "blended_actual_roas":  round(actual_roas, 2),
        "overstatement_pct":    round(overstatement, 1),
        "by_channel":           by_channel,
    }


@st.cache_data
def get_daily_spend() -> pd.DataFrame:
    _, _, sp = load_raw_data()
    paid = sp[sp["channel"].isin(["meta_paid_social", "google_paid_search", "tiktok_ads"])].copy()
    paid["channel"] = paid["channel"].map(CHANNEL_MAP)
    return (
        paid.groupby(["date", "channel"])["daily_spend_usd"]
        .sum()
        .reset_index()
    )
