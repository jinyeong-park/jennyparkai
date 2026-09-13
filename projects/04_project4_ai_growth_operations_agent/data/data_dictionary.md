# Data Dictionary — Tablr Growth Simulation

**Data origin:** SYNTHETIC  
**Version:** 1.0.0  
**Random seed:** 20260913  
**Currency:** USD  
**Timezone:** UTC (all timestamps are UTC ISO 8601)  
**Attribution window:** 7-day click, 1-day view (simulated; matches Meta default)

All data is synthetic. Formulas and metric definitions below are the authoritative
source of truth. Dashboards, notebooks, and the analytics layer must not redefine
these independently.

---

## 1. dim_creatives

One row per creative variant. Stable reference dimension.

| Column | Type | Description |
|--------|------|-------------|
| `creative_id` | string | Stable unique identifier. Pattern: `cr_{channel_abbr}_{campaign_num}_{creative_num}` |
| `campaign_id` | string | Foreign key to the campaign this creative belongs to |
| `campaign_name` | string | Human-readable campaign name |
| `ad_group_id` | string | Ad group (targeting slice) this creative runs under |
| `channel` | string (enum) | `META`, `TIKTOK`, `GOOGLE_SEARCH`, `LINKEDIN` |
| `persona_segment` | string (enum) | Target persona: `SCRAPPY_INDEPENDENT`, `GROWTH_MINDED`, `NEW_OWNER`, `DELIVERY_HEAVY`, `COMMUNITY_FOCUSED` |
| `hook_type` | string (enum) | Creative hook pattern: `CONTRAST`, `OUTCOME`, `SOCIAL_PROOF`, `DEMONSTRATION`, `FEAR_OF_MISSING_OUT` |
| `creative_format` | string (enum) | `STATIC_IMAGE`, `SHORT_FORM_VIDEO`, `UGC_VIDEO`, `PRODUCT_DEMO`, `CAROUSEL` |
| `data_origin` | string | Always `SYNTHETIC` in this dataset |

---

## 2. fact_daily_performance

One row per date × creative. Grain: calendar day × creative_id.

| Column | Type | Description |
|--------|------|-------------|
| `date` | string (ISO 8601) | Calendar date (UTC) |
| `channel` | string (enum) | Same as dim_creatives |
| `campaign_id` | string | Foreign key |
| `campaign_name` | string | Denormalized for convenience |
| `ad_group_id` | string | Foreign key |
| `ad_group_name` | string | Ad group label (same as ad_group_id in v1) |
| `creative_id` | string | Foreign key to dim_creatives |
| `persona_segment` | string (enum) | Target persona for this row |
| `impressions` | integer | Number of times the ad was shown |
| `clicks` | integer | Number of clicks (NOTE: intentionally > impressions for ag_google_002_002 week 7) |
| `spend_usd` | float | Media spend in USD, rounded to 2 decimal places |
| `landing_page_views` | integer | Landing page loads after ad click (85–92% of clicks) |
| `trial_signups` | integer | Trial accounts created from this creative on this date |
| `data_origin` | string | Always `SYNTHETIC` |

### Derived metrics (not stored; calculated at query time)

```
CTR (Click-Through Rate) = clicks / impressions
CPC (Cost per Click) = spend_usd / clicks
CPM (Cost per Mille) = (spend_usd / impressions) * 1000
Landing page CVR = landing_page_views / clicks
Trial signup CVR = trial_signups / landing_page_views
Trial CAC = spend_usd / trial_signups  [sum over period, then divide]
```

---

## 3. dim_trial_accounts

One row per simulated trial signup. Grain: account_id.

| Column | Type | Description |
|--------|------|-------------|
| `account_id` | string | Stable unique identifier. Pattern: `acct_XXXXXX` |
| `user_id` | string | User who created the account. Pattern: `usr_XXXXXX` |
| `signup_date` | string (ISO 8601 date) | Date the trial was created |
| `channel` | string (enum) or NULL | Acquisition channel. NULL if missing attribution |
| `campaign_id` | string or NULL | NULL if missing attribution |
| `ad_group_id` | string or NULL | NULL if missing attribution |
| `creative_id` | string or NULL | NULL if missing attribution |
| `persona_segment` | string (enum) | Assigned persona (even for missing-attribution accounts) |
| `subscription_tier` | string (enum) or NULL | `STARTER`, `GROWTH`, or `PRO`. NULL until converted |
| `is_missing_attribution` | boolean | True for ~8% of accounts (direct/organic untracked traffic) |
| `data_origin` | string | Always `SYNTHETIC` |

---

## 4. fact_product_events

One row per event per user. Append-only event log.

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | string | Unique event identifier |
| `account_id` | string | Foreign key to dim_trial_accounts |
| `user_id` | string | User who performed the action |
| `event_type` | string (enum) | See event definitions below |
| `event_timestamp` | string (ISO 8601 datetime) | UTC timestamp |
| `creative_id` | string or NULL | Attribution: creative that drove the trial |
| `campaign_id` | string or NULL | Attribution: campaign that drove the trial |
| `data_origin` | string | Always `SYNTHETIC` |

### Event type definitions

| Event | Definition |
|-------|------------|
| `TRIAL_SIGNUP` | Restaurant owner creates a free 14-day trial account |
| `ONBOARDING_COMPLETED` | Owner completes the setup wizard (profile + first integration). Baseline rate: 42% within 3 days of signup |
| `PROFILE_CREATED` | Restaurant profile published on the Tablr platform. Baseline rate: 88% of onboarded users within 1 day |
| `CAMPAIGN_LAUNCHED` | Owner publishes their first customer-facing campaign. Baseline rate: 71% of profile-created users within 14 days of signup |
| `FIRST_CUSTOMER_ACQUIRED` | First tracked customer attributed to a Tablr campaign. Rate: 65% of campaign-launched users within 30 days |
| `SUBSCRIPTION_STARTED` | Owner converts from trial to paid subscription. Rate: 78% of first-customer-acquired users |
| `LOCATION_ADDED` | Owner adds a second or subsequent restaurant location |
| `REVENUE_GENERATED` | Recognized MRR associated with the account |

### Activation definition (MVP)

> **An Activated Owner** is a trial-acquired restaurant owner who launches their
> first customer-facing campaign (`CAMPAIGN_LAUNCHED` event) within **14 calendar
> days** of their `TRIAL_SIGNUP` timestamp.

This is the primary activation gate used to calculate CPAO.

### CPAO formula

```
CPAO = Total Paid Media Spend (for a creative/channel/period)
       ÷ Number of Paid-Acquired Activated Restaurant Owners

Where "Paid-Acquired" means is_missing_attribution = FALSE
and "Activated" means CAMPAIGN_LAUNCHED within 14 days of TRIAL_SIGNUP.
```

---

## 5. fact_subscriptions

One row per subscription. Grain: subscription_id (= account_id in v1).

| Column | Type | Description |
|--------|------|-------------|
| `subscription_id` | string | Unique subscription identifier |
| `account_id` | string | Foreign key to dim_trial_accounts |
| `trial_start_date` | string (ISO 8601 date) | Date of TRIAL_SIGNUP |
| `conversion_date` | string (ISO 8601 date) | Date SUBSCRIPTION_STARTED occurred |
| `conversion_delay_days` | integer | Days after trial end (day 14) until conversion. 0 for same-day. Pattern 7: 15% have 7–14 day delay |
| `subscription_tier` | string (enum) | `STARTER` ($99), `GROWTH` ($199), `PRO` ($399) per month per location |
| `monthly_price_usd` | integer | Base monthly price in USD for the selected tier |
| `status` | string | `active` or `churned` |
| `churn_date` | string (ISO 8601 date) or NULL | Date of churn. NULL if still active |
| `location_count` | integer | Number of restaurant locations on the account (expansion metric) |
| `data_origin` | string | Always `SYNTHETIC` |

### Retention window definitions

Retention windows are calculated from `conversion_date`, not `trial_start_date`.

| Window | Definition |
|--------|------------|
| **M1 retained** | Account is on a paid subscription 30 days after `conversion_date`. Baseline: 82% |
| **M3 retained** | Account is on a paid subscription 90 days after `conversion_date`. Baseline: 55% (78% for COMMUNITY_FOCUSED) |
| **M6 retained** | Account is on a paid subscription 180 days after `conversion_date`. Baseline: 41% |

A cohort is **immature** for a retention window if `today < conversion_date + window_days`.
Do not report immature cohorts as churned. Label them as immature.

---

## 6. fact_revenue_events

One row per revenue event per subscription. Grain: revenue_event_id.

| Column | Type | Description |
|--------|------|-------------|
| `revenue_event_id` | string | Unique revenue event identifier |
| `account_id` | string | Foreign key to dim_trial_accounts |
| `subscription_id` | string | Foreign key to fact_subscriptions |
| `event_date` | string (ISO 8601 date) | Date this revenue was recognized |
| `event_type` | string | `MRR` (recurring monthly charge) or `EXPANSION` (additional location) |
| `amount_usd` | float | Revenue amount in USD |
| `month_num` | integer | 0-based subscription month (0 = first month) |
| `location_count` | integer | Number of locations billed at this event |
| `data_origin` | string | Always `SYNTHETIC` |

### MRR formula

```
Account MRR = monthly_price_usd × location_count
Total MRR (month) = SUM(amount_usd) WHERE event_type = 'MRR' AND event_date IN [month_start, month_end)
```

### LTV calculation

**Observed LTV to date:**
```
Observed LTV = SUM(amount_usd) for all revenue events for an account up to observation date
```

**Projected LTV (simplified):**
```
Projected LTV = Monthly MRR × (1 / monthly_churn_rate)

Where monthly_churn_rate is estimated from the cohort's observed retention curve.
```

Observed and projected LTV must be stored and labeled separately. Do not combine
them into an unlabeled `ltv` field.

---

## 7. Attribution Assumptions

- **Attribution window:** 7-day click, 1-day view (simulated convention matching Meta default).
- **Attribution model:** Last-click within window (simplified for synthetic data).
- **Missing attribution:** 8% of trials have NULL campaign_id and creative_id,
  representing direct or organic traffic that entered the funnel without a tracked click.
- **Conversion delay window:** Subscriptions may start up to 14 days after the trial end.
  All revenue and retention analysis should account for delayed conversions.

---

## 8. Data Quality Issues

| Issue | Location | Description | Detectability |
|-------|----------|-------------|---------------|
| Clicks > Impressions | `ag_google_002_002`, week 7 (2026-02-16 – 2026-02-22) | Tracking pixel misconfiguration caused 3 days of inflated click counts | `test_clicks_never_exceed_impressions` in `tests/data/test_data_quality.py` |

---

## 9. Known Limitations

- Synthetic behavior does not prove real market response.
- Retention rates are modeled, not observed.
- The attribution model is a simplification; real multi-touch attribution would differ.
- LTV projections use a simplified steady-state formula; real LTV requires longer cohort observation.
- Creative IDs use a sequential naming convention that does not reflect real Meta creative IDs.
- All monetary values are in USD; no multi-currency support in v1.
- The data covers 12 weeks (January–March 2026); cohort maturity for M6 is not yet observable within this window.
