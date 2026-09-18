# Phase 4: Geo-Holdout Incrementality Experiment with Python

> **Core Question:** Of all the conversions we see when ads are running, how many of them would have happened anyway even without the ads?

---

## Why Attribution Models Are Not Enough

Multi-Touch Attribution (Phase 3) tells you how to fairly distribute credit across channels. What it cannot tell you is whether those conversions are **incremental** — meaning they would not have happened without the ad.

**The organic cannibalization problem:**

```
Scenario: Meta retargeting ads target users who already visited the product page.
          Many of these users were already planning to purchase.
          Even without seeing the retargeting ad, they would have returned and bought.

Result:   Meta gets attributed credit for a conversion that had nothing to do with Meta.
          The company pays $15 in retargeting spend for a conversion worth $0 in true incremental value.
```

The only way to measure true incrementality is to **run a controlled experiment**: pause ads in some markets and measure whether conversions decline.

---

## The Geo-Holdout Experiment Design

### Core Concept

Split U.S. geographic markets (DMAs) into two groups:

- **Treatment group:** Markets where Meta ads continue running as normal
- **Control group:** Markets where Meta ads are completely paused for 30 days

Measure the conversion rate difference between the two groups.
The difference represents the incremental lift attributable to Meta advertising.

```
Treatment DMAs (ads ON):     Conversion Rate = X%
Control DMAs (ads OFF):      Conversion Rate = Y%

Incremental Lift = X% - Y%
If Lift is near zero → the ads were not driving meaningful additional conversions
```

### Experiment Setup in This Project

| Parameter        | Value                                                                                                            |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| Total DMAs       | 50 U.S. markets                                                                                                  |
| Treatment DMAs   | 40 markets (ads continue running)                                                                                |
| Control DMAs     | 10 markets (Meta ads paused for 30 days)                                                                         |
| Test duration    | 30 days (June)                                                                                                   |
| Channel tested   | Meta Paid Social (retargeting campaigns)                                                                         |
| Control variable | Matched markets — control DMAs selected to mirror treatment DMAs in population size and baseline conversion rate |

### Why Geographic Markets (DMAs) Instead of Individual Users?

- Randomly assigning individual users to see or not see ads is not technically feasible across platforms
- Geographic markets are the smallest units where ad spend can be turned on or off reliably
- DMAs are large enough to have statistical stability and small enough to still be comparable

---

## The Python Incrementality Analysis

### Step 1: Load and Prepare the Data

```python
import pandas as pd
import numpy as np
from scipy import stats

# Load the conversion data with DMA labels
df = pd.read_csv('data/raw/raw_conversions.csv')
df['converted_at'] = pd.to_datetime(df['converted_at'])

# Filter to the experiment period (June)
experiment_start = pd.Timestamp('2026-06-01')
experiment_end   = pd.Timestamp('2026-06-30')
df_june = df[
    (df['converted_at'] >= experiment_start) &
    (df['converted_at'] <= experiment_end)
]

# Define which DMAs are control vs. treatment
# (In a real experiment, this is determined during planning, not after data collection)
control_dmas   = ['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix',
                  'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
treatment_dmas = [dma for dma in df_june['dma_code'].unique() if dma not in control_dmas]

# Split the data
df_control   = df_june[df_june['dma_code'].isin(control_dmas)]
df_treatment = df_june[df_june['dma_code'].isin(treatment_dmas)]
```

### Step 2: Load DMA Population Data

To compare conversion rates fairly, we normalize by the population of each DMA. A larger market will naturally have more conversions — what matters is the rate.

```python
# DMA population data (from U.S. Census or Nielsen)
dma_population = pd.read_csv('data/raw/dma_population.csv')  # dma_code, population

# Merge population into each group
df_control_agg = (
    df_control
    .groupby('dma_code')['conversion_id']
    .count()
    .reset_index()
    .rename(columns={'conversion_id': 'conversions'})
    .merge(dma_population, on='dma_code')
)

df_treatment_agg = (
    df_treatment
    .groupby('dma_code')['conversion_id']
    .count()
    .reset_index()
    .rename(columns={'conversion_id': 'conversions'})
    .merge(dma_population, on='dma_code')
)
```

### Step 3: Calculate Incremental Lift

```python
def calculate_geo_incrementality(df_treatment: pd.DataFrame,
                                  df_control: pd.DataFrame,
                                  ad_spend: float) -> dict:
    """
    Calculates incremental lift and true iCAC using Matched-Market Geo Testing.

    Parameters
    ----------
    df_treatment : pd.DataFrame
        One row per DMA in the treatment group. Must have 'conversions' and 'population' columns.
    df_control : pd.DataFrame
        One row per DMA in the control group. Must have 'conversions' and 'population' columns.
    ad_spend : float
        Total Meta ad spend in the treatment DMAs during the experiment period.

    Returns
    -------
    dict with keys: baseline_conversion_rate, expected_baseline_conversions,
                    actual_conversions, incremental_conversions, incremental_cac_usd
    """
    # Step A: Compute baseline conversion rate from control DMAs
    # This is the rate at which users convert WITHOUT any Meta ads
    baseline_rate = df_control['conversions'].sum() / df_control['population'].sum()

    # Step B: Project what treatment DMAs would have converted at baseline rate
    # This is the counterfactual: "how many conversions would treatment DMAs have had without ads?"
    expected_baseline = df_treatment['population'].sum() * baseline_rate

    # Step C: Measure actual conversions in treatment DMAs (ads were running)
    actual_conversions = df_treatment['conversions'].sum()

    # Step D: Incremental conversions = actual - expected baseline
    # This is the number of conversions that ads ACTUALLY caused
    incremental_conversions = actual_conversions - expected_baseline

    # Step E: Incremental CAC = spend / incremental conversions
    # This is the true cost to acquire one additional customer via the ads
    incremental_cac = ad_spend / incremental_conversions if incremental_conversions > 0 else float('inf')

    return {
        "baseline_conversion_rate":      round(baseline_rate * 100, 4),   # as a percentage
        "expected_baseline_conversions": round(expected_baseline, 0),
        "actual_conversions":            actual_conversions,
        "incremental_conversions":       round(incremental_conversions, 0),
        "incremental_cac_usd":           round(incremental_cac, 2),
        "incremental_lift_pct":          round((incremental_conversions / expected_baseline) * 100, 1)
    }


# Run the calculation
META_JUNE_SPEND_TREATMENT_DMAS = 60_000   # $60K of the $120K Meta budget was in treatment DMAs

results = calculate_geo_incrementality(
    df_treatment = df_treatment_agg,
    df_control   = df_control_agg,
    ad_spend     = META_JUNE_SPEND_TREATMENT_DMAS
)

for key, value in results.items():
    print(f"{key}: {value}")
```

**Expected output for this project:**

```
baseline_conversion_rate:       0.0341  (3.41% in control DMAs without Meta ads)
expected_baseline_conversions:  8,420   (projected conversions without ads in treatment DMAs)
actual_conversions:             8,891   (observed conversions with ads running)
incremental_conversions:        471     (true ad-driven conversions)
incremental_cac_usd:            127.39  ($127 to acquire one truly incremental customer)
incremental_lift_pct:           5.6     (only 5.6% lift — 94.4% of conversions were organic)
```

---

### Step 4: Statistical Significance Test

Before acting on the results, confirm the difference is statistically significant — not just random variation.

```python
def test_significance(df_treatment: pd.DataFrame,
                      df_control: pd.DataFrame,
                      alpha: float = 0.05) -> dict:
    """
    Two-proportion z-test: is the treatment conversion rate significantly different
    from the control conversion rate?
    """
    # Compute conversion rates per DMA
    treatment_rate = df_treatment['conversions'].sum() / df_treatment['population'].sum()
    control_rate   = df_control['conversions'].sum()   / df_control['population'].sum()

    # Pooled proportion for standard error calculation
    n_treatment = df_treatment['population'].sum()
    n_control   = df_control['population'].sum()
    pooled_p    = (df_treatment['conversions'].sum() + df_control['conversions'].sum()) / (n_treatment + n_control)

    # Standard error and z-score
    se      = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_treatment + 1/n_control))
    z_score = (treatment_rate - control_rate) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # two-tailed

    return {
        "treatment_conversion_rate": round(treatment_rate * 100, 4),
        "control_conversion_rate":   round(control_rate * 100, 4),
        "z_score":                   round(z_score, 3),
        "p_value":                   round(p_value, 4),
        "statistically_significant": p_value < alpha
    }

sig_results = test_significance(df_treatment_agg, df_control_agg)
print(sig_results)
```

**How to interpret the p-value:**

- `p_value < 0.05` — The difference between treatment and control is statistically significant; the lift is real
- `p_value >= 0.05` — Cannot confidently say the ads caused the difference; the result could be random noise

---

## Key Finding From This Experiment

```
Result: When Meta ads were paused in 10 control DMAs for 30 days:
  - Conversion rates in control DMAs dropped by only 5.6%
  - This means 94.4% of Meta-attributed conversions happened organically
  - Pausing Meta ads had almost no measurable impact on actual purchase behavior

Conclusion: Meta Retargeting has extremely low incremental lift.
            Most users who saw Meta retargeting ads and "converted" would have
            converted anyway through Organic Search or Direct navigation.

Implication: The $120,000 spent on Meta retargeting delivered only ~$23,760 in
             truly incremental revenue (at the platform-reported ROAS of 3.25x,
             the expected revenue was $390,000 — but the geo-holdout reveals the
             true incremental ROAS was only 1.26x).
```

---

## Incremental ROAS Calculation

After measuring true incremental conversions, calculate the real incremental ROAS:

```python
def calculate_incremental_roas(incremental_revenue: float, ad_spend: float) -> float:
    """
    Incremental ROAS = incremental revenue driven by ads / ad spend.
    Compare this against platform-reported ROAS to see the gap.
    """
    return round(incremental_revenue / ad_spend, 2)

# Example values for Meta (June experiment, treatment DMAs)
incremental_revenue = 75_600   # revenue from the 471 truly incremental conversions
meta_spend          = 60_000   # Meta spend in treatment DMAs during June

i_roas = calculate_incremental_roas(incremental_revenue, meta_spend)
print(f"True Incremental ROAS for Meta: {i_roas}x")
# Output: True Incremental ROAS for Meta: 1.26x
# Compare to Meta's self-reported ROAS of 3.25x — a 61% over-statement
```

---

## Limitations and Considerations

| Consideration                 | Detail                                                                                                                                                                |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Market matching quality**   | Control DMAs must closely resemble treatment DMAs in population size, baseline conversion rate, and seasonality. Poor matching introduces bias.                       |
| **Spillover effects**         | Users in control DMAs may see Meta ads on their mobile devices that are geo-targeted to a different location, contaminating the control group.                        |
| **Minimum detectable effect** | If the true incremental lift is small (e.g., 2%), a 30-day test with only 10 control DMAs may not have enough statistical power to detect it reliably.                |
| **Seasonality**               | Running the experiment during a high-traffic month (e.g., Q4 holiday) may distort results. Results should be compared to the same period in a prior year if possible. |
| **Generalizability**          | Results from a Meta retargeting holdout do not necessarily generalize to Meta prospecting campaigns, which target users who have not yet visited the site.            |

---

## Next Step

The Geo-Holdout experiment gives us the true incremental ROAS for each channel.
Combined with the SQL attribution models, we now have everything needed to make data-driven budget reallocation decisions.

→ [Phase 5: Marketing Insights and Budget Decisions](./05_marketing_insights.md)
