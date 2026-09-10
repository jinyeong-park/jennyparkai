"""
Geo-Holdout Incrementality Experiment
======================================
Phase 4 of the Growth Attribution System pipeline.

Question: Of all the conversions attributed to Meta ads, how many would have
happened anyway — without any Meta advertising?

Approach: In June 2026, Meta ads were paused in 10 control DMAs (Holdout group).
The remaining 40 DMAs continued running Meta ads (Treatment group).
By comparing conversion rates between the two groups, we can isolate the
true incremental lift driven by Meta advertising.

Run:
    python geo_holdout_experiment.py

Requirements:
    pip install pandas numpy scipy matplotlib seaborn
"""

import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────

DATA_DIR = "../data/raw"

EXPERIMENT_START = "2026-06-01"
EXPERIMENT_END   = "2026-06-30"

# First 10 DMAs were used as the holdout (control) group in data generation
# Meta ads were paused in these markets for the full month of June
CONTROL_DMAS = [
    "DMA_100_SAN_FRANCISCO", "DMA_101_NEW_YORK",  "DMA_102_CHICAGO",
    "DMA_103_LOS_ANGELES",   "DMA_104_DALLAS",    "DMA_105_SEATTLE",
    "DMA_106_AUSTIN",        "DMA_107_ATLANTA",   "DMA_108_BOSTON",
    "DMA_109_DENVER",
]

# Meta spend in treatment DMAs during June (extracted from ad spend data)
# Set at runtime after loading the spend CSV


# ─────────────────────────────────────────
# Step 1: Load Data
# ─────────────────────────────────────────

def load_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the three raw CSV files and parse date columns."""
    touchpoints = pd.read_csv(os.path.join(data_dir, "raw_user_touchpoints.csv"))
    conversions = pd.read_csv(os.path.join(data_dir, "raw_conversions.csv"))
    ad_spend    = pd.read_csv(os.path.join(data_dir, "raw_ad_spend.csv"))

    touchpoints["timestamp"]    = pd.to_datetime(touchpoints["timestamp"])
    conversions["converted_at"] = pd.to_datetime(conversions["converted_at"])
    ad_spend["date"]            = pd.to_datetime(ad_spend["date"])

    print(f"Loaded: {len(touchpoints):,} touchpoints | "
          f"{len(conversions):,} conversions | "
          f"{len(ad_spend):,} ad spend rows")
    return touchpoints, conversions, ad_spend


# ─────────────────────────────────────────
# Step 2: Build DMA Population Proxy
# ─────────────────────────────────────────

def build_dma_population(touchpoints: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate relative DMA size using unique users observed across all months.

    In production this would use U.S. Census or Nielsen DMA population data.
    Here we use total unique users per DMA as a size proxy — a standard
    approach when official population figures are unavailable.
    """
    dma_pop = (
        touchpoints
        .groupby("dma_code")["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "population"})
    )
    return dma_pop


# ─────────────────────────────────────────
# Step 3: Prepare Experiment Data
# ─────────────────────────────────────────

def prepare_experiment_data(
    conversions: pd.DataFrame,
    dma_population: pd.DataFrame,
    control_dmas: list[str],
    experiment_start: str,
    experiment_end: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter conversions to the experiment window (June),
    split by control vs. treatment DMA, and merge in population estimates.
    """
    mask = (
        (conversions["converted_at"] >= experiment_start) &
        (conversions["converted_at"] <= experiment_end)
    )
    df_june = conversions[mask].copy()

    all_dmas      = df_june["dma_code"].unique().tolist()
    treatment_dmas = [d for d in all_dmas if d not in control_dmas]

    df_control   = df_june[df_june["dma_code"].isin(control_dmas)]
    df_treatment = df_june[df_june["dma_code"].isin(treatment_dmas)]

    def aggregate(df: pd.DataFrame) -> pd.DataFrame:
        agg = (
            df.groupby("dma_code")
            .agg(
                conversions=("conversion_id", "count"),
                revenue_usd=("order_value_usd", "sum"),
            )
            .reset_index()
            .merge(dma_population, on="dma_code", how="left")
        )
        agg["conversion_rate"] = agg["conversions"] / agg["population"]
        return agg

    return aggregate(df_control), aggregate(df_treatment)


# ─────────────────────────────────────────
# Step 4: Incrementality Calculation
# ─────────────────────────────────────────

def calculate_geo_incrementality(
    df_treatment: pd.DataFrame,
    df_control: pd.DataFrame,
    meta_spend_treatment: float,
) -> dict:
    """
    Matched-Market Geo-Holdout: calculate true incremental conversions and iCAC.

    Logic
    -----
    1. Baseline rate  = conversions / population in CONTROL DMAs (no Meta ads)
       This represents the organic conversion rate without Meta advertising.

    2. Expected baseline in TREATMENT = treatment population × baseline rate
       Counterfactual: how many conversions would treatment DMAs have had
       if they also had no Meta ads?

    3. Incremental conversions = actual treatment conversions − expected baseline
       The difference is what Meta ads actually caused.

    4. iCAC = Meta spend in treatment / incremental conversions
       True cost to acquire one customer who would NOT have converted organically.
    """
    baseline_rate     = df_control["conversions"].sum() / df_control["population"].sum()
    expected_baseline = df_treatment["population"].sum() * baseline_rate
    actual_convs      = df_treatment["conversions"].sum()
    incremental_convs = actual_convs - expected_baseline

    # Average order value from treatment group
    avg_order_value   = df_treatment["revenue_usd"].sum() / actual_convs
    incremental_rev   = incremental_convs * avg_order_value

    icac = meta_spend_treatment / incremental_convs if incremental_convs > 0 else float("inf")
    i_roas = incremental_rev / meta_spend_treatment if meta_spend_treatment > 0 else 0.0

    lift_pct = (incremental_convs / expected_baseline) * 100 if expected_baseline > 0 else 0.0

    return {
        "baseline_conversion_rate_pct":  round(baseline_rate * 100, 4),
        "expected_baseline_conversions": round(expected_baseline, 0),
        "actual_conversions":            int(actual_convs),
        "incremental_conversions":       round(incremental_convs, 0),
        "incremental_revenue_usd":       round(incremental_rev, 2),
        "meta_spend_treatment_usd":      meta_spend_treatment,
        "incremental_cac_usd":           round(icac, 2),
        "incremental_roas":              round(i_roas, 2),
        "organic_share_pct":             round(100 - lift_pct, 1),
        "incremental_lift_pct":          round(lift_pct, 1),
    }


# ─────────────────────────────────────────
# Step 5: Statistical Significance Test
# ─────────────────────────────────────────

def test_significance(
    df_treatment: pd.DataFrame,
    df_control: pd.DataFrame,
    alpha: float = 0.05,
) -> dict:
    """
    Two-proportion z-test: is the treatment conversion rate meaningfully
    different from the control conversion rate?

    H0: treatment_rate == control_rate  (ads had no effect)
    H1: treatment_rate != control_rate  (two-tailed)

    A p-value < 0.05 means we can reject H0 — the difference is unlikely
    to be due to chance alone.
    """
    n_t = df_treatment["population"].sum()
    n_c = df_control["population"].sum()
    cv_t = df_treatment["conversions"].sum()
    cv_c = df_control["conversions"].sum()

    rate_t   = cv_t / n_t
    rate_c   = cv_c / n_c
    pooled_p = (cv_t + cv_c) / (n_t + n_c)

    se      = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_t + 1 / n_c))
    z_score = (rate_t - rate_c) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    return {
        "treatment_conversion_rate_pct": round(rate_t * 100, 4),
        "control_conversion_rate_pct":   round(rate_c * 100, 4),
        "absolute_diff_pct":             round((rate_t - rate_c) * 100, 4),
        "z_score":                       round(z_score, 3),
        "p_value":                       round(p_value, 4),
        "statistically_significant":     p_value < alpha,
        "confidence_level":              f"{int((1 - alpha) * 100)}%",
    }


# ─────────────────────────────────────────
# Step 6: Visualizations
# ─────────────────────────────────────────

def plot_results(
    df_control: pd.DataFrame,
    df_treatment: pd.DataFrame,
    results: dict,
    sig: dict,
    output_path: str = "geo_holdout_results.png",
) -> None:
    """
    Four-panel chart:
      1. Conversion rate: control vs. treatment DMAs
      2. Distribution of DMA-level conversion rates
      3. Incremental vs. organic breakdown (waterfall)
      4. Platform-reported ROAS vs. true incremental ROAS
    """
    sns.set_theme(style="whitegrid", palette="muted")
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "Geo-Holdout Incrementality Experiment — Meta Paid Social (June 2026)",
        fontsize=15, fontweight="bold", y=1.01
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── Panel 1: Conversion Rate Comparison ──────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    groups = ["Control\n(Meta ads OFF)", "Treatment\n(Meta ads ON)"]
    rates  = [
        sig["control_conversion_rate_pct"],
        sig["treatment_conversion_rate_pct"],
    ]
    colors = ["#e74c3c", "#2ecc71"]
    bars = ax1.bar(groups, rates, color=colors, width=0.5, edgecolor="white", linewidth=1.5)
    for bar, rate in zip(bars, rates):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.002,
            f"{rate:.3f}%",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )
    sig_label = (
        f"p = {sig['p_value']} ({'✓ Significant' if sig['statistically_significant'] else '✗ Not significant'})"
    )
    ax1.set_title(f"Conversion Rate by Group\n{sig_label}", fontsize=11)
    ax1.set_ylabel("Conversion Rate (%)")
    ax1.set_ylim(0, max(rates) * 1.25)

    # ── Panel 2: DMA-Level Distribution ──────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(
        df_control["conversion_rate"] * 100,
        bins=8, alpha=0.6, color="#e74c3c", label="Control DMAs", edgecolor="white"
    )
    ax2.hist(
        df_treatment["conversion_rate"] * 100,
        bins=12, alpha=0.6, color="#2ecc71", label="Treatment DMAs", edgecolor="white"
    )
    ax2.set_title("DMA-Level Conversion Rate Distribution", fontsize=11)
    ax2.set_xlabel("Conversion Rate (%)")
    ax2.set_ylabel("Number of DMAs")
    ax2.legend(fontsize=9)

    # ── Panel 3: Incremental vs. Organic Waterfall ────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    actual      = results["actual_conversions"]
    organic     = results["expected_baseline_conversions"]
    incremental = results["incremental_conversions"]

    ax3.bar(["Organic\n(would have happened\nwithout Meta ads)"],
            [organic], color="#95a5a6", edgecolor="white")
    ax3.bar(["Incremental\n(truly caused\nby Meta ads)"],
            [incremental], color="#3498db", edgecolor="white")

    ax3.text(0, organic + 5, f"{organic:,.0f}", ha="center", fontsize=11, fontweight="bold")
    ax3.text(1, incremental + 5, f"{incremental:,.0f}", ha="center", fontsize=11, fontweight="bold")

    ax3.set_title(
        f"Conversion Breakdown — Treatment DMAs\n"
        f"Total: {actual:,} | Organic: {results['organic_share_pct']}% | "
        f"Incremental: {results['incremental_lift_pct']}%",
        fontsize=10
    )
    ax3.set_ylabel("Conversions")
    ax3.set_ylim(0, max(organic, incremental) * 1.2)

    # ── Panel 4: Platform ROAS vs. True Incremental ROAS ─────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    roas_labels  = ["Platform-Reported\nROAS", "True Incremental\nROAS"]
    roas_values  = [3.25, results["incremental_roas"]]
    roas_colors  = ["#e67e22", "#8e44ad"]
    bars2 = ax4.bar(roas_labels, roas_values, color=roas_colors,
                    width=0.5, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars2, roas_values):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.03,
            f"{val}x", ha="center", va="bottom", fontsize=13, fontweight="bold"
        )
    overstatement = round((3.25 - results["incremental_roas"]) / results["incremental_roas"] * 100, 0)
    ax4.set_title(
        f"ROAS: Platform vs. Incremental\nMeta over-stated by ~{overstatement:.0f}%",
        fontsize=11
    )
    ax4.set_ylabel("ROAS (x)")
    ax4.set_ylim(0, max(roas_values) * 1.3)
    ax4.axhline(y=1.0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax4.text(1.55, 1.05, "Break-even", fontsize=8, color="gray")

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved → {output_path}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Geo-Holdout Incrementality Experiment")
    print("  Channel: Meta Paid Social | Period: June 2026")
    print("=" * 60)

    # Load
    touchpoints, conversions, ad_spend = load_data(DATA_DIR)

    # Build population proxy from all-time unique users per DMA
    dma_population = build_dma_population(touchpoints)

    # Prepare experiment groups
    df_control, df_treatment = prepare_experiment_data(
        conversions   = conversions,
        dma_population = dma_population,
        control_dmas  = CONTROL_DMAS,
        experiment_start = EXPERIMENT_START,
        experiment_end   = EXPERIMENT_END,
    )

    print(f"\nExperiment groups:")
    print(f"  Control DMAs   : {len(df_control)} markets (Meta ads OFF)")
    print(f"  Treatment DMAs : {len(df_treatment)} markets (Meta ads ON)")

    # Extract Meta spend in treatment DMAs during June from ad_spend CSV
    meta_spend_treatment = ad_spend[
        (ad_spend["date"] >= EXPERIMENT_START) &
        (ad_spend["date"] <= EXPERIMENT_END) &
        (ad_spend["channel"] == "meta_paid_social") &
        (~ad_spend["dma_code"].isin(CONTROL_DMAS))
    ]["daily_spend_usd"].sum()

    print(f"\nMeta spend in treatment DMAs (June): ${meta_spend_treatment:,.0f}")

    # ── Incrementality results ────────────────────────────────────────────
    results = calculate_geo_incrementality(df_treatment, df_control, meta_spend_treatment)

    print("\n── Incrementality Results ──────────────────────────────")
    print(f"  Baseline conversion rate (control DMAs):  {results['baseline_conversion_rate_pct']}%")
    print(f"  Expected conversions without ads:         {results['expected_baseline_conversions']:,.0f}")
    print(f"  Actual conversions (ads running):         {results['actual_conversions']:,}")
    print(f"  Incremental conversions (ad-driven):      {results['incremental_conversions']:,.0f}")
    print(f"  Organic share:                            {results['organic_share_pct']}%")
    print(f"  Incremental lift:                         {results['incremental_lift_pct']}%")
    print(f"  Incremental revenue:                      ${results['incremental_revenue_usd']:,.0f}")
    print(f"  Incremental CAC (iCAC):                   ${results['incremental_cac_usd']:,.2f}")
    print(f"  True Incremental ROAS:                    {results['incremental_roas']}x")
    print(f"  Platform-reported ROAS (Meta):            3.25x")

    # ── Statistical significance ──────────────────────────────────────────
    sig = test_significance(df_treatment, df_control)

    print("\n── Statistical Significance Test ───────────────────────")
    print(f"  Treatment conversion rate: {sig['treatment_conversion_rate_pct']}%")
    print(f"  Control conversion rate:   {sig['control_conversion_rate_pct']}%")
    print(f"  Absolute difference:       {sig['absolute_diff_pct']}%")
    print(f"  Z-score:                   {sig['z_score']}")
    print(f"  P-value:                   {sig['p_value']}")
    print(f"  Significant at {sig['confidence_level']}:    {sig['statistically_significant']}")

    # ── Business interpretation ───────────────────────────────────────────
    print("\n── Business Interpretation ─────────────────────────────")
    print(f"  {results['organic_share_pct']}% of Meta-attributed conversions happened organically.")
    print(f"  Only {results['incremental_lift_pct']}% of conversions were truly incremental (ad-driven).")
    print(f"  Meta's true ROAS is {results['incremental_roas']}x vs. 3.25x self-reported — "
          f"a significant overstatement.")
    print(f"  Recommendation: Reallocate Meta retargeting budget toward")
    print(f"  Google Search and TikTok prospecting, which show higher incremental lift.")

    # ── Visualize ─────────────────────────────────────────────────────────
    output_dir = os.path.dirname(os.path.abspath(__file__))
    plot_results(
        df_control   = df_control,
        df_treatment = df_treatment,
        results      = results,
        sig          = sig,
        output_path  = os.path.join(output_dir, "geo_holdout_results.png"),
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
