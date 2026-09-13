"""Data loading utilities for Tablr Growth Intelligence Dashboard.

All queries use DuckDB directly against synthetic parquet files.
No imports from src/ — dashboard is self-contained.

— all data is simulated.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parents[2] / "data" / "synthetic"

_PERF = str(DATA_DIR / "fact_daily_performance.parquet")
_EVENTS = str(DATA_DIR / "fact_product_events.parquet")
_ACCOUNTS = str(DATA_DIR / "dim_trial_accounts.parquet")
_CREATIVES = str(DATA_DIR / "dim_creatives.parquet")
_SUBS = str(DATA_DIR / "fact_subscriptions.parquet")
_REVENUE = str(DATA_DIR / "fact_revenue_events.parquet")

_ACTIVATION_WINDOW = 14
_MATURITY_DATE = "2026-09-13"


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


@st.cache_data(show_spinner=False)
def load_channel_scorecard() -> pd.DataFrame:
    """Channel scorecard: impressions, clicks, CTR, CPM, spend, trials, trial CAC, activated, CPAO."""
    con = _con()
    df = con.execute(
        f"""
        WITH perf AS (
            SELECT
                channel,
                SUM(impressions)                                               AS impressions,
                SUM(clicks)                                                    AS clicks,
                SUM(spend_usd)                                                 AS spend_usd,
                SUM(trial_signups)                                             AS trial_signups,
                SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0)               AS ctr,
                SUM(spend_usd) * 1000.0 / NULLIF(SUM(impressions), 0)         AS cpm_usd,
                SUM(spend_usd) / NULLIF(SUM(trial_signups), 0)                AS trial_cac_usd
            FROM read_parquet('{_PERF}')
            GROUP BY channel
        ),
        trial_dates AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS signup_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'TRIAL_SIGNUP'
        ),
        campaigns AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS launch_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'CAMPAIGN_LAUNCHED'
        ),
        activated AS (
            SELECT DISTINCT t.account_id
            FROM trial_dates t
            JOIN campaigns c ON t.account_id = c.account_id
            WHERE c.launch_date - t.signup_date <= {_ACTIVATION_WINDOW}
        ),
        acct_channel AS (
            SELECT a.account_id, COALESCE(d.channel, 'UNKNOWN') AS channel
            FROM activated a
            LEFT JOIN read_parquet('{_ACCOUNTS}') d ON a.account_id = d.account_id
        ),
        act_counts AS (
            SELECT channel, COUNT(DISTINCT account_id) AS activated_owners
            FROM acct_channel
            GROUP BY channel
        )
        SELECT
            p.channel,
            p.impressions,
            p.clicks,
            p.ctr,
            p.cpm_usd,
            p.spend_usd,
            p.trial_signups,
            p.trial_cac_usd,
            COALESCE(a.activated_owners, 0)                              AS activated_owners,
            p.spend_usd / NULLIF(a.activated_owners, 0)                  AS cpao_usd
        FROM perf p
        LEFT JOIN act_counts a ON p.channel = a.channel
        ORDER BY p.spend_usd DESC
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_funnel() -> pd.DataFrame:
    """Funnel: trials, onboarding_completed, campaign_launched (activated), subscriptions."""
    con = _con()
    df = con.execute(
        f"""
        WITH trials AS (
            SELECT COUNT(DISTINCT account_id) AS cnt FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'TRIAL_SIGNUP'
        ),
        onboarding AS (
            SELECT COUNT(DISTINCT account_id) AS cnt FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'ONBOARDING_COMPLETED'
        ),
        trial_dates AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS signup_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'TRIAL_SIGNUP'
        ),
        campaigns AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS launch_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'CAMPAIGN_LAUNCHED'
        ),
        activated AS (
            SELECT COUNT(DISTINCT t.account_id) AS cnt
            FROM trial_dates t
            JOIN campaigns c ON t.account_id = c.account_id
            WHERE c.launch_date - t.signup_date <= {_ACTIVATION_WINDOW}
        ),
        subs AS (
            SELECT COUNT(DISTINCT account_id) AS cnt FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'SUBSCRIPTION_STARTED'
        )
        SELECT
            (SELECT cnt FROM trials)     AS trials,
            (SELECT cnt FROM onboarding) AS onboarding_completed,
            (SELECT cnt FROM activated)  AS activated_owners,
            (SELECT cnt FROM subs)       AS subscriptions
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_creative_performance() -> pd.DataFrame:
    """Creative-level performance joined with dim_creatives."""
    con = _con()
    df = con.execute(
        f"""
        SELECT
            f.creative_id,
            dc.channel,
            dc.hook_type,
            dc.creative_format,
            dc.persona_segment,
            SUM(f.impressions)                                             AS impressions,
            SUM(f.clicks)                                                  AS clicks,
            SUM(f.spend_usd)                                               AS spend_usd,
            SUM(f.trial_signups)                                           AS trial_signups,
            SUM(f.clicks) * 1.0 / NULLIF(SUM(f.impressions), 0)           AS ctr,
            SUM(f.spend_usd) / NULLIF(SUM(f.clicks), 0)                   AS cpc_usd,
            SUM(f.spend_usd) / NULLIF(SUM(f.trial_signups), 0)            AS trial_cac_usd
        FROM read_parquet('{_PERF}') f
        JOIN read_parquet('{_CREATIVES}') dc ON f.creative_id = dc.creative_id
        GROUP BY
            f.creative_id, dc.channel, dc.hook_type,
            dc.creative_format, dc.persona_segment
        ORDER BY spend_usd DESC
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_retention() -> pd.DataFrame:
    """M1/M3/M6 retention by channel."""
    con = _con()
    df = con.execute(
        f"""
        WITH subs AS (
            SELECT
                s.account_id,
                CAST(s.conversion_date AS DATE)  AS conv_date,
                CAST(s.churn_date AS DATE)         AS churn_dt,
                s.status,
                COALESCE(d.channel, 'UNKNOWN')    AS channel
            FROM read_parquet('{_SUBS}') s
            LEFT JOIN read_parquet('{_ACCOUNTS}') d ON s.account_id = d.account_id
        )
        SELECT
            channel,
            COUNT(*)                                                                 AS subscribers,
            SUM(CASE WHEN status = 'active' OR churn_dt > conv_date + 30
                     THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0)                AS m1_rate,
            SUM(CASE WHEN status = 'active' OR churn_dt > conv_date + 90
                     THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT(*), 0)                AS m3_rate,
            SUM(CASE
                WHEN (status = 'active' OR churn_dt > conv_date + 180)
                     AND conv_date + 180 <= DATE '{_MATURITY_DATE}'
                THEN 1 ELSE 0
            END) * 1.0 /
            NULLIF(SUM(CASE WHEN conv_date + 180 <= DATE '{_MATURITY_DATE}'
                            THEN 1 ELSE 0 END), 0)                                  AS m6_rate,
            SUM(CASE WHEN conv_date + 180 <= DATE '{_MATURITY_DATE}'
                     THEN 1 ELSE 0 END)                                              AS m6_eligible,
            COUNT(*) - SUM(CASE WHEN conv_date + 180 <= DATE '{_MATURITY_DATE}'
                                THEN 1 ELSE 0 END)                                   AS m6_immature
        FROM subs
        GROUP BY channel
        ORDER BY channel
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_ltv_cac() -> pd.DataFrame:
    """LTV:CAC analysis by channel — CPAO, observed LTV, ratio, payback."""
    con = _con()
    df = con.execute(
        f"""
        WITH trial_dates AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS signup_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'TRIAL_SIGNUP'
        ),
        campaigns AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS launch_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'CAMPAIGN_LAUNCHED'
        ),
        activated AS (
            SELECT DISTINCT t.account_id
            FROM trial_dates t
            JOIN campaigns c ON t.account_id = c.account_id
            WHERE c.launch_date - t.signup_date <= {_ACTIVATION_WINDOW}
        ),
        acct_channel AS (
            SELECT a.account_id, COALESCE(d.channel, 'UNKNOWN') AS channel
            FROM activated a
            LEFT JOIN read_parquet('{_ACCOUNTS}') d ON a.account_id = d.account_id
        ),
        act_counts AS (
            SELECT channel, COUNT(DISTINCT account_id) AS activated_owners
            FROM acct_channel
            GROUP BY channel
        ),
        spend AS (
            SELECT channel, SUM(spend_usd) AS total_spend
            FROM read_parquet('{_PERF}')
            GROUP BY channel
        ),
        rev_per_account AS (
            SELECT account_id, SUM(amount_usd) AS total_rev
            FROM read_parquet('{_REVENUE}')
            GROUP BY account_id
        ),
        sub_ltv AS (
            SELECT
                COALESCE(d.channel, 'UNKNOWN') AS channel,
                AVG(s.monthly_price_usd)        AS avg_monthly_price,
                AVG(COALESCE(r.total_rev, 0))   AS avg_observed_ltv,
                SUM(CASE WHEN s.status = 'churned' THEN 1 ELSE 0 END) * 1.0
                    / NULLIF(COUNT(*), 0)        AS churn_rate
            FROM read_parquet('{_SUBS}') s
            LEFT JOIN read_parquet('{_ACCOUNTS}') d ON s.account_id = d.account_id
            LEFT JOIN rev_per_account r ON s.account_id = r.account_id
            GROUP BY COALESCE(d.channel, 'UNKNOWN')
        )
        SELECT
            sp.channel,
            sp.total_spend,
            act.activated_owners,
            sp.total_spend / NULLIF(act.activated_owners, 0) AS cpao_usd,
            sl.avg_monthly_price,
            sl.avg_observed_ltv,
            sl.churn_rate,
            sl.avg_monthly_price / NULLIF(sl.churn_rate, 0)  AS projected_ltv,
            sl.avg_observed_ltv / NULLIF(sp.total_spend / NULLIF(act.activated_owners, 0), 0)
                AS ltv_cac_ratio_observed,
            (sp.total_spend / NULLIF(act.activated_owners, 0))
                / NULLIF(sl.avg_monthly_price, 0)             AS payback_months
        FROM spend sp
        LEFT JOIN act_counts act ON sp.channel = act.channel
        LEFT JOIN sub_ltv sl ON sp.channel = sl.channel
        ORDER BY cpao_usd ASC NULLS LAST
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_budget_allocation(total_budget: float = 150_000.0) -> pd.DataFrame:
    """Budget allocation at specified total. Uses 1/CPAO efficiency weighting."""
    scorecard = load_channel_scorecard()
    # Filter to channels with actual CPAO
    eff = scorecard[scorecard["cpao_usd"].notna() & (scorecard["cpao_usd"] > 0)].copy()
    exploration = scorecard[scorecard["cpao_usd"].isna() | (scorecard["cpao_usd"] <= 0)].copy()

    exploration_reserve_pct = 0.10
    eff_budget = total_budget * (1 - exploration_reserve_pct)
    exp_budget = total_budget * exploration_reserve_pct

    # Score = 1/CPAO
    eff["score"] = 1.0 / eff["cpao_usd"]
    total_score = eff["score"].sum()
    eff["raw_pct"] = eff["score"] / total_score

    # Apply min 5% / max 60% per channel
    min_pct = 0.05
    max_pct = 0.60
    eff["alloc_pct"] = eff["raw_pct"].clip(lower=min_pct, upper=max_pct)
    # Re-normalise
    eff["alloc_pct"] = eff["alloc_pct"] / eff["alloc_pct"].sum()
    eff["recommended_spend"] = eff["alloc_pct"] * eff_budget
    eff["is_exploration"] = False

    rows = []
    for _, r in eff.iterrows():
        rows.append({
            "channel": r["channel"],
            "cpao_usd": r["cpao_usd"],
            "recommended_spend": round(r["recommended_spend"], 0),
            "recommended_pct": r["recommended_spend"] / total_budget,
            "is_exploration": False,
        })

    # Exploration channels split equally
    n_exp = max(len(exploration), 1)
    for _, r in exploration.iterrows():
        spend = exp_budget / n_exp
        rows.append({
            "channel": r["channel"],
            "cpao_usd": r.get("cpao_usd"),
            "recommended_spend": round(spend, 0),
            "recommended_pct": spend / total_budget,
            "is_exploration": True,
        })

    if exploration.empty:
        # redistribute to eff channels
        extra = exp_budget / max(len(eff), 1)
        for row in rows:
            if not row["is_exploration"]:
                row["recommended_spend"] += extra
                row["recommended_pct"] = row["recommended_spend"] / total_budget

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_hook_type_performance() -> pd.DataFrame:
    """CTR and trial CAC by hook type."""
    con = _con()
    df = con.execute(
        f"""
        SELECT
            dc.hook_type,
            SUM(f.impressions)                                             AS impressions,
            SUM(f.clicks)                                                  AS clicks,
            SUM(f.trial_signups)                                           AS trial_signups,
            SUM(f.spend_usd)                                               AS spend_usd,
            SUM(f.clicks) * 1.0 / NULLIF(SUM(f.impressions), 0)           AS ctr,
            SUM(f.spend_usd) / NULLIF(SUM(f.trial_signups), 0)            AS trial_cac_usd
        FROM read_parquet('{_PERF}') f
        JOIN read_parquet('{_CREATIVES}') dc ON f.creative_id = dc.creative_id
        GROUP BY dc.hook_type
        ORDER BY trial_cac_usd ASC NULLS LAST
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_fatigue_signals(drop_threshold: float = 0.25) -> pd.DataFrame:
    """Creatives with CTR drop > threshold from peak (fatigue detection)."""
    con = _con()
    df = con.execute(
        f"""
        WITH min_date AS (
            SELECT MIN(CAST(date AS DATE)) AS start_date
            FROM read_parquet('{_PERF}')
        ),
        daily_with_week AS (
            SELECT
                f.creative_id,
                CAST(DATEDIFF('day', m.start_date, CAST(f.date AS DATE)) / 7 AS INTEGER) AS week_num,
                f.clicks,
                f.impressions
            FROM read_parquet('{_PERF}') f
            CROSS JOIN min_date m
        ),
        weekly_ctr AS (
            SELECT
                creative_id,
                week_num,
                SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0) AS ctr
            FROM daily_with_week
            GROUP BY creative_id, week_num
        ),
        peak AS (
            SELECT creative_id, MAX(ctr) AS peak_ctr, MAX_BY(week_num, ctr) AS peak_week
            FROM weekly_ctr GROUP BY creative_id
        ),
        latest AS (
            SELECT creative_id, MAX_BY(ctr, week_num) AS latest_ctr, MAX(week_num) AS latest_week
            FROM weekly_ctr GROUP BY creative_id
        )
        SELECT
            p.creative_id,
            dc.channel,
            dc.hook_type,
            p.peak_ctr,
            p.peak_week,
            l.latest_ctr,
            l.latest_week,
            (p.peak_ctr - l.latest_ctr) / NULLIF(p.peak_ctr, 0) AS ctr_drop_pct,
            CASE WHEN (p.peak_ctr - l.latest_ctr) / NULLIF(p.peak_ctr, 0) > {drop_threshold}
                 THEN true ELSE false END AS is_fatigued
        FROM peak p
        JOIN latest l ON p.creative_id = l.creative_id
        JOIN read_parquet('{_CREATIVES}') dc ON p.creative_id = dc.creative_id
        WHERE l.latest_week >= 3
        ORDER BY ctr_drop_pct DESC
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_cohort_by_week() -> pd.DataFrame:
    """Weekly cohort funnel: trials, onboarding, activated, subscribed."""
    con = _con()
    df = con.execute(
        f"""
        WITH signups AS (
            SELECT
                account_id,
                CAST(event_timestamp AS DATE) AS signup_date,
                strftime(CAST(event_timestamp AS DATE), '%G-W%V') AS cohort_week
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'TRIAL_SIGNUP'
        ),
        campaigns AS (
            SELECT account_id, CAST(event_timestamp AS DATE) AS launch_date
            FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'CAMPAIGN_LAUNCHED'
        ),
        onboarding AS (
            SELECT DISTINCT account_id FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'ONBOARDING_COMPLETED'
        ),
        subs_started AS (
            SELECT DISTINCT account_id FROM read_parquet('{_EVENTS}')
            WHERE event_type = 'SUBSCRIPTION_STARTED'
        )
        SELECT
            s.cohort_week,
            MIN(s.signup_date)                                              AS cohort_start,
            COUNT(DISTINCT s.account_id)                                    AS trials,
            COUNT(DISTINCT o.account_id)                                    AS onboarding_completed,
            COUNT(DISTINCT CASE
                WHEN c.launch_date - s.signup_date <= {_ACTIVATION_WINDOW}
                THEN s.account_id END)                                      AS activated_owners,
            COUNT(DISTINCT sub.account_id)                                  AS subscriptions
        FROM signups s
        LEFT JOIN campaigns c       ON s.account_id = c.account_id
        LEFT JOIN onboarding o      ON s.account_id = o.account_id
        LEFT JOIN subs_started sub  ON s.account_id = sub.account_id
        GROUP BY s.cohort_week
        ORDER BY s.cohort_week
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_subscription_tiers() -> pd.DataFrame:
    """Subscription tier breakdown: active vs churned counts."""
    con = _con()
    df = con.execute(
        f"""
        SELECT
            subscription_tier,
            status,
            COUNT(*) AS count,
            AVG(monthly_price_usd) AS avg_price
        FROM read_parquet('{_SUBS}')
        GROUP BY subscription_tier, status
        ORDER BY subscription_tier, status
        """
    ).df()
    con.close()
    return df


@st.cache_data(show_spinner=False)
def load_trials_by_persona() -> pd.DataFrame:
    """Trial signups by persona segment."""
    con = _con()
    df = con.execute(
        f"""
        SELECT
            COALESCE(d.persona_segment, 'UNKNOWN') AS persona_segment,
            COALESCE(d.channel, 'UNKNOWN') AS channel,
            COUNT(DISTINCT e.account_id) AS trials
        FROM read_parquet('{_EVENTS}') e
        LEFT JOIN read_parquet('{_ACCOUNTS}') d ON e.account_id = d.account_id
        WHERE e.event_type = 'TRIAL_SIGNUP'
        GROUP BY COALESCE(d.persona_segment, 'UNKNOWN'), COALESCE(d.channel, 'UNKNOWN')
        ORDER BY trials DESC
        """
    ).df()
    con.close()
    return df
