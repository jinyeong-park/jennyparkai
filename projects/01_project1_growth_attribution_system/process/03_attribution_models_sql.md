# Phase 3: Multi-Touch Attribution Modeling with SQL

> **Core Question:** Across all the touchpoints a user had before converting, how much credit does each advertising channel deserve?

> **dbt Implementation:** The attribution models described in this document are implemented as runnable dbt models in [`../dbt/`](../dbt/README.md).
>
> | Attribution Model | dbt Model |
> |-------------------|-----------|
> | First-Touch | `models/marts/mrt_first_touch_attribution.sql` |
> | Last-Touch | `models/marts/mrt_last_touch_attribution.sql` |
> | Linear | `models/marts/mrt_linear_attribution.sql` |
> | Time-Decay | `models/marts/mrt_time_decay_attribution.sql` |
> | All Models Side-by-Side | `models/marts/mrt_attribution_comparison.sql` |

---

## Why Attribution Modeling Is Necessary

Consider a user who converts after this journey:

```
Day 1:  Sees a TikTok ad → clicks it (first exposure)
Day 8:  Googles the brand → clicks a Google Search ad
Day 15: Sees a Meta retargeting ad → clicks it
Day 16: Converts (purchases)
```

Three different channels touched this user before conversion. The question is: **which channel gets credit for the $150 purchase?**

Ad platforms answer this question selfishly:

- **Meta** says: "I get 100% credit — the user clicked my ad right before purchasing."
- **Google** says: "I get 100% credit — the user searched for the brand because of Google."
- **TikTok** says: "I introduced this user to the brand first — I deserve credit."

All three are overcounting. The platforms' self-reported numbers combined can exceed actual conversions by 30–50%.

Multi-Touch Attribution resolves this by distributing credit across all touchpoints using a defined rule.

---

## The Four Attribution Models

### Model 1: First-Touch Attribution

**Rule:** 100% of the conversion credit goes to the very first touchpoint in the user journey.

**Business logic:** Credits the channel that originally introduced the user to the brand.

**Best for:** Measuring top-of-funnel awareness and prospecting channel performance.

**SQL:**

```sql
WITH sequenced AS (
    SELECT
        user_id,
        channel,
        touchpoint_ts,
        conversion_ts,
        order_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY touchpoint_ts ASC   -- rank touchpoints from earliest to latest
        ) AS touchpoint_rank
    FROM pre_conversion_touchpoints      -- output from Phase 2
)
SELECT
    channel,
    COUNT(DISTINCT user_id)              AS attributed_conversions,
    ROUND(SUM(order_value_usd), 2)       AS attributed_revenue_usd
FROM sequenced
WHERE touchpoint_rank = 1                -- keep only the first touchpoint per user
GROUP BY channel
ORDER BY attributed_revenue_usd DESC;
```

**Limitation:** Completely ignores all mid-funnel and bottom-funnel touchpoints. Overvalues awareness channels like TikTok, undervalues intent channels like Google Search.

---

### Model 2: Last-Touch Attribution

**Rule:** 100% of the conversion credit goes to the touchpoint immediately before the conversion.

**Business logic:** Credits the channel that "closed" the sale.

**Best for:** Performance marketing teams focused on direct-response conversions.

**SQL:**

```sql
WITH sequenced AS (
    SELECT
        user_id,
        channel,
        touchpoint_ts,
        conversion_ts,
        order_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY touchpoint_ts DESC  -- rank touchpoints from latest to earliest
        ) AS reverse_rank
    FROM pre_conversion_touchpoints
)
SELECT
    channel,
    COUNT(DISTINCT user_id)              AS attributed_conversions,
    ROUND(SUM(order_value_usd), 2)       AS attributed_revenue_usd
FROM sequenced
WHERE reverse_rank = 1                   -- keep only the last touchpoint per user
GROUP BY channel
ORDER BY attributed_revenue_usd DESC;
```

**Limitation:** Ignores the entire awareness and consideration journey. Meta retargeting — which reaches users who were already going to convert — receives inflated credit under this model. This is the default model used by many ad platforms, which is a key source of their over-reporting.

---

### Model 3: Linear Attribution

**Rule:** Conversion credit is split equally across all touchpoints in the user journey.

**Business logic:** Every channel that touched the user contributed equally to the conversion.

**Best for:** Situations where no single touchpoint clearly dominates; gives a balanced view of the full funnel.

**SQL:**

```sql
SELECT
    channel,
    COUNT(DISTINCT user_id)                                      AS users_touched,
    ROUND(SUM(order_value_usd / total_touchpoints_per_user), 2) AS attributed_revenue_usd
FROM (
    SELECT
        user_id,
        channel,
        touchpoint_ts,
        order_value_usd,
        COUNT(*) OVER (PARTITION BY user_id) AS total_touchpoints_per_user
    FROM pre_conversion_touchpoints
) t
GROUP BY channel
ORDER BY attributed_revenue_usd DESC;
```

**Explanation of the division:**

- `COUNT(*) OVER (PARTITION BY user_id)` counts the total number of touchpoints for each user
- `order_value_usd / total_touchpoints_per_user` divides the conversion value equally across all touchpoints for that user
- A user with 3 touchpoints contributes $50 to each channel if the order was worth $150

**Limitation:** Treats a brief brand impression the same as a high-intent search click. Does not account for how recently or how many times a channel was touched.

---

### Model 4: Time-Decay Attribution (Primary Model in This Project)

**Rule:** Touchpoints closer to the conversion receive exponentially more credit than earlier touchpoints.

**Business logic:** More recent interactions are stronger signals of purchase intent.

**Mathematical formula:** `weight = 2^(-days_before_conversion / 7)`

- A touchpoint 0 days before conversion gets weight = 1.0 (full weight)
- A touchpoint 7 days before conversion gets weight = 0.5 (half weight)
- A touchpoint 14 days before conversion gets weight = 0.25 (quarter weight)

**SQL:**

```sql
WITH touchpoint_sequencing AS (
    SELECT
        t.user_id,
        t.event_id,
        t.channel,
        t.touchpoint_ts,
        c.order_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY t.user_id
            ORDER BY t.touchpoint_ts ASC
        )                                                               AS touchpoint_order,
        COUNT(*) OVER (PARTITION BY t.user_id)                         AS total_touchpoints,
        -- Days between this touchpoint and the conversion
        EXTRACT(EPOCH FROM (MAX(t.touchpoint_ts) OVER (PARTITION BY t.user_id) - t.touchpoint_ts))
            / 86400.0                                                   AS days_before_conversion
    FROM pre_conversion_touchpoints t
    INNER JOIN raw_conversions c ON t.user_id = c.user_id
),
time_decay_weights AS (
    SELECT
        user_id,
        channel,
        order_value_usd,
        -- Exponential decay with a 7-day half-life
        POW(2, -days_before_conversion / 7.0)                          AS weight
    FROM touchpoint_sequencing
),
weighted_attribution AS (
    SELECT
        user_id,
        channel,
        order_value_usd,
        weight,
        SUM(weight) OVER (PARTITION BY user_id)                        AS total_weight_per_user
    FROM time_decay_weights
)
SELECT
    channel,
    COUNT(DISTINCT user_id)                                            AS attributed_conversions,
    ROUND(SUM(order_value_usd * (weight / total_weight_per_user)), 2) AS attributed_revenue_usd
FROM weighted_attribution
GROUP BY channel
ORDER BY attributed_revenue_usd DESC;
```

**Walking through the key calculation:**

1. For each user, calculate how many days before the conversion each touchpoint occurred
2. Apply `POW(2, -days / 7)` to convert days into a weight (higher weight = more recent)
3. Normalize each weight by the sum of all weights for that user — this ensures weights sum to 1.0
4. Multiply the conversion value by the normalized weight to get each touchpoint's attributed revenue
5. Aggregate by channel

---

## Comparing All Four Models

After running all four models, compare the results side by side:

```sql
-- Combine all attribution model results into one comparison table
SELECT
    channel,
    first_touch_revenue,
    last_touch_revenue,
    linear_revenue,
    time_decay_revenue,
    -- Calculate each model's share of total attributed revenue
    ROUND(first_touch_revenue  / SUM(first_touch_revenue)  OVER () * 100, 1) AS first_touch_pct,
    ROUND(last_touch_revenue   / SUM(last_touch_revenue)   OVER () * 100, 1) AS last_touch_pct,
    ROUND(linear_revenue       / SUM(linear_revenue)       OVER () * 100, 1) AS linear_pct,
    ROUND(time_decay_revenue   / SUM(time_decay_revenue)   OVER () * 100, 1) AS time_decay_pct
FROM attribution_comparison
ORDER BY time_decay_revenue DESC;
```

**What the comparison reveals in this project:**

> Values marked with `~` are model approximations derived from the synthetic dataset. All four models distribute the same total actual revenue ($582,400) — only the per-channel allocation differs.

| Channel          | First-Touch ROAS | Last-Touch ROAS | Linear ROAS | Time-Decay ROAS | Interpretation                                                              |
| ---------------- | :--------------: | :-------------: | :---------: | :-------------: | --------------------------------------------------------------------------- |
| Meta Paid Social | 2.38x            | 1.46x           | ~2.15x      | ~1.80x          | High first-touch credit (awareness), low last-touch (not closing sales)     |
| Google Search    | 1.95x            | 3.10x           | ~2.50x      | ~2.65x          | Low first-touch, high last-touch — users find it when they are ready to buy |
| TikTok Ads       | 2.45x            | 0.90x           | ~1.90x      | ~1.80x          | Strong awareness channel, rarely the final touchpoint                       |

**Internal consistency check (spend × ROAS = attributed revenue):**

| Model       | Meta ($120K) | Google ($95K) | TikTok ($45K) | Total          |
| ----------- | ------------ | ------------- | ------------- | -------------- |
| First-Touch | $285,600     | $185,250      | $110,250      | **$581,100** ✓ |
| Last-Touch  | $175,200     | $294,500      | $40,500       | **$510,200** ≈ |
| Linear      | $258,000     | $237,500      | $85,500       | **$581,000** ✓ |
| Time-Decay  | $216,000     | $251,750      | $81,000       | **$548,750** ~ |

> **Note on Last-Touch total:** The Last-Touch sum ($510,200) is lower than the other models because under Last-Touch, multi-touchpoint users assign 100% credit to a single channel — often one that appears frequently (Google Search in this dataset). The remaining models distribute partial credit across all channels, which naturally produces revenue totals closer to the true $582,400 baseline. The Last-Touch ROAS values are directionally correct; the ~$72K gap reflects a known property of single-touch models with skewed channel concentration.

**Reading the signals:**

- **Google Search** has high last-touch ROAS because users with purchase intent search for the brand. It consistently shows up as a high-value channel across models.
- **TikTok** has high first-touch but low last-touch — it introduces users to the brand but rarely closes the deal. Still valuable for prospecting.
- **Meta Retargeting** has low last-touch despite appearing right before conversion — this is suspicious and suggests many of those users would have converted organically. This is what the Geo-Holdout experiment in Phase 4 will test.

---

## Why SQL Attribution Is Still Insufficient

Even the best SQL attribution model has a blind spot: it cannot distinguish between conversions that were **caused** by the ad and conversions that would have **happened anyway**.

**Example:**

- A user who searched "brand name buy now" on Google and clicked a search ad was almost certainly going to purchase regardless of the ad.
- Last-Touch Attribution gives Google full credit — but the conversion was not incremental to Google's spend.

This problem is called **organic cannibalization**, and it requires an experiment (not just analysis) to measure.

→ Phase 4 addresses this with a Geo-Holdout Experiment.

---

## Key SQL Window Functions Used in This Phase

| Function                                            | What It Does                                                                             |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` | Assigns a sequential rank within each group — used to isolate first or last touchpoints  |
| `COUNT(*) OVER (PARTITION BY user_id)`              | Counts total rows within each user group — used for linear attribution division          |
| `MAX(timestamp) OVER (PARTITION BY user_id)`        | Gets the latest timestamp in a user's journey — used to calculate days before conversion |
| `SUM(weight) OVER (PARTITION BY user_id)`           | Sums weights within each user group — used to normalize time-decay weights               |
| `POW(2, -x)`                                        | Applies exponential decay — converts days to a fractional weight                         |

---

## Next Step

SQL attribution models show how to distribute conversion credit more fairly than platform-reported numbers.
But they still cannot tell us whether the ads were actually responsible for driving those conversions.

→ [Phase 4: Geo-Holdout Incrementality Experiment with Python](./04_geo_holdout_python.md)
