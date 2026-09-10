# Phase 5: Marketing Insights and Budget Decisions

> **Primary Role:** Marketing Analyst / Growth Lead (owns this phase), all other roles inform it
> **Core Question:** Given everything the data tells us, where should we reallocate budget and why?

---

## The Decision Framework: From Data to Action

This phase is where analysis becomes strategy. The outputs of Phases 2–4 feed into a structured decision process:

```
SQL Attribution ROAS  ─────┐
  (Phase 3)                 ├──→ Channel Scorecard ──→ Budget Decision
Geo-Holdout iROAS    ─────┘
  (Phase 4)
```

A channel's performance must be assessed across multiple lenses simultaneously:
- **Platform-reported ROAS** — what the platform claims (directionally useful, but biased)
- **SQL Attribution ROAS** — a fairer view after deduplication and multi-touch weighting
- **Geo-Holdout iROAS** — the true causal impact; the most reliable signal

---

## Channel Scorecard: Reading the Final Numbers

| Metric | Meta Paid Social | Google Paid Search | TikTok Ads |
|--------|------------------|--------------------|------------|
| Total Spend (Q1–Q2) | $120,000 | $95,000 | $45,000 |
| Platform-Reported ROAS | 3.25x | 2.80x | 1.60x |
| First-Touch ROAS (SQL) | 2.38x | 1.95x | 2.45x |
| Last-Touch ROAS (SQL) | 1.46x | 3.10x | 0.90x |
| **Geo-Holdout iROAS (True)** | **1.26x** | **2.65x** | **2.10x** |
| Organic Cannibalization Rate | ~60% | ~5% | ~20% |

**How to read this table:**
- The further a channel's platform ROAS drifts from its geo-holdout iROAS, the higher its organic cannibalization — it is taking credit for conversions that would have happened anyway
- Meta's platform ROAS of 3.25x vs. iROAS of 1.26x means **61% of its claimed conversions were organic** — the ad spend is largely cannibalizing purchases that would have occurred through Organic Search or Direct navigation
- Google's platform ROAS and iROAS are close to each other — a sign that Google Search is genuinely driving incremental conversions, not just capturing existing intent

---

## Interpreting Each Channel

### Meta Paid Social — Scale Back Retargeting

**What the data shows:**
- Platform claims 3.25x ROAS. Actual incremental ROAS is 1.26x.
- Geo-Holdout finding: pausing Meta ads in 10 markets for 30 days caused only a 5.6% drop in conversions. Over 60% of Meta-attributed conversions happened organically.
- Last-Touch ROAS (1.46x) is already low, suggesting users click the Meta retargeting ad as a final step, but they were already committed to purchasing.

**What this means in plain language:**
> Meta retargeting ads are mostly showing up in front of people who were already going to buy.
> We are paying ~$15 per retargeting click to get credit for a conversion that did not need our nudge.

**Recommended action:**
- Reduce overall Meta retargeting budget by 40–50%
- Shift remaining Meta budget from retargeting (low incrementality) toward prospecting audiences (higher potential for genuine new-user acquisition)
- Establish a monthly geo-holdout monitoring rotation to track incremental lift over time

**Metrics to watch after change:**
- Blended CAC (should decrease as retargeting waste is cut)
- Organic and Direct conversion rates (should stay flat or increase if those users were always going to convert)
- New customer acquisition rate (should not decline significantly if prospecting is maintained)

---

### Google Paid Search — Increase Budget

**What the data shows:**
- Platform claims 2.80x ROAS. Actual incremental ROAS is 2.65x — very close.
- High Last-Touch ROAS (3.10x) reflects that Google Search captures users with explicit purchase intent (they searched for the brand or category).
- Low organic cannibalization (~5%) means that most users who clicked Google Search ads would not have converted without the ad.

**What this means in plain language:**
> When someone searches "brand name buy now," they are already deep in the purchase funnel.
> Google captures that intent at the right moment. The ad is actually driving the conversion, not just appearing before an organic one.

**Recommended action:**
- Increase Google Search budget — prioritize high-intent keywords (brand + competitor + category terms)
- Test expanding to generic non-brand keywords, which have lower cannibalization risk than retargeting
- Implement conversion value bidding to optimize toward revenue, not just conversion count

**Metrics to watch after change:**
- Cost per Click (CPC) — may rise as budget increases, watch for efficiency plateau
- Search Impression Share — how much of available search traffic is being captured
- Revenue from Google-attributed users at 30-day customer lifetime value

---

### TikTok Ads — Scale Up Top-of-Funnel

**What the data shows:**
- Platform claims 1.60x ROAS (looks weak). Actual incremental ROAS is 2.10x (genuinely strong).
- Highest First-Touch ROAS (2.45x) — TikTok is the most effective channel at introducing new users to the brand.
- Low Last-Touch ROAS (0.90x) — TikTok is not the channel that closes sales, but that is expected for a top-of-funnel prospecting channel.
- Organic cannibalization is low (~20%) — TikTok is reaching genuinely new audiences.

**What this means in plain language:**
> TikTok's platform-reported ROAS (1.60x) looks bad compared to Meta (3.25x) and Google (2.80x).
> But this is misleading. TikTok's job is not to close sales — it is to create awareness among people who have never heard of the brand.
> The geo-holdout shows TikTok is actually driving real new-user acquisition at a 2.10x iROAS.
> The company was underinvesting here because it was comparing TikTok's top-of-funnel ROAS unfairly to Google's bottom-of-funnel ROAS.

**Recommended action:**
- Increase TikTok budget toward prospecting campaigns (new audience expansion, Lookalike audiences)
- Do not evaluate TikTok on Last-Touch or ROAS alone — use First-Touch contribution and new-visitor acquisition rate as primary metrics
- Test TikTok creative formats: short-form product demos, testimonials, and entertainment-led content that drives awareness and search intent

**Metrics to watch after change:**
- New-to-brand users (users with no prior site visits)
- Assisted conversions — how often TikTok appears earlier in the conversion path of users who eventually convert via another channel
- Branded search volume on Google — a downstream proxy for TikTok awareness lift

---

## The Budget Reallocation Decision

**Before (original allocation):**
| Channel | Q1–Q2 Budget |
|---------|-------------|
| Meta Paid Social | $120,000 |
| Google Paid Search | $95,000 |
| TikTok Ads | $45,000 |
| **Total** | **$260,000** |

**After (recommended reallocation — $100K shifted):**
| Channel | New Budget | Change | Rationale |
|---------|-----------|--------|-----------|
| Meta Paid Social | $70,000 | -$50,000 | Cut low-incrementality retargeting |
| Google Paid Search | $130,000 | +$35,000 | Increase high-intent, high-iROAS channel |
| TikTok Ads | $60,000 | +$15,000 | Expand proven top-of-funnel acquisition |
| **Total** | **$260,000** | **$0** | Same total spend, better allocation |

**Projected impact of reallocation:**
- Blended CAC: $61.90 → $53.10 (**-14.2% improvement**)
- Total acquisition volume: maintained at same level
- Platform-reported ROAS will likely drop (because less retargeting = less inflated credit), but actual incremental value increases

---

## Why Platform ROAS Will Drop After This Decision (And Why That Is Fine)

This is the most important thing to communicate to stakeholders and leadership:

> When you cut Meta retargeting, Meta's reported ROAS will appear to get worse.
> This is expected and is not a sign that the strategy is wrong.

**Why this happens:**
- Meta retargeting had inflated ROAS because it was taking credit for organic conversions
- After cutting retargeting, those users still convert — but now through Organic Search or Direct, which are tracked differently
- The blended/total ROAS seen in the executive dashboard may stay flat or even appear to decline short-term

**How to explain this to stakeholders:**
```
"We reduced Meta retargeting spend because our geo-holdout experiment showed that
60% of those 'conversions' would have happened without the ad. We are not losing sales;
we are stopping paying for sales that were already going to happen.

The real metric to watch is Blended CAC and New Customer Acquisition Rate.
Both should improve over the next 60–90 days as the reallocation takes effect."
```

---

## Ongoing Measurement Cadence

Do not treat this as a one-time analysis. Marketing mix efficiency erodes over time as audiences saturate, competitors adjust, and platform algorithms change.

| Frequency | Action |
|-----------|--------|
| Weekly | Review Blended CAC and channel-level spend vs. conversion trends |
| Monthly | Run lightweight geo-holdout checks on the highest-spend channel |
| Quarterly | Full attribution analysis refresh across all channels |
| Bi-annually | Re-run 30-day geo-holdout experiment; update iROAS benchmarks |

---

## Summary: The Three-Line Takeaway

1. **Meta Retargeting** had the highest platform-reported ROAS but the lowest true incremental ROAS — $50K of spend was primarily cannibalizing organic conversions, not driving new ones.

2. **Google Search** is the most reliable high-intent channel with near-zero cannibalization — it deserves more budget.

3. **TikTok** was undervalued because its platform ROAS looked weak — but geo-holdout revealed it is the strongest top-of-funnel new-user acquisition channel at 2.10x iROAS.

> The core lesson: **never make budget decisions from platform-reported numbers alone.**
> Always triangulate with independent attribution (SQL) and experimental validation (Geo-Holdout).
