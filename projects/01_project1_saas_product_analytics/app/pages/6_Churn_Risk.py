"""Churn risk and customer-success prioritization page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables, load_usage
from utils.metrics import (
    auc_score,
    build_account_metrics,
    churn_by_feature,
    churn_risk_segments,
    paid_survival_curve,
    prospective_engagement_dataset,
    prospective_usage_dataset,
)
from utils.theme import AMBER, RED, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Churn Risk | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    return build_account_metrics(tables), tables["event_logs"], tables["organizations"], tables["subscriptions"], load_usage()


@st.cache_data(show_spinner=False)
def usage_dataset(horizon_days: int):
    accounts, _, organizations, subscriptions, usage = page_data()
    observation_date = accounts["observation_date"].max()
    cutoffs = list(pd.date_range("2025-04-28", observation_date, freq="7D"))
    return prospective_usage_dataset(usage, organizations, subscriptions, observation_date, cutoffs, horizon_days=horizon_days)


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, event_logs, organizations, subscriptions, _usage = page_data()
    risk = churn_risk_segments(accounts)

    medium_risk = risk.loc[risk["risk_segment"] == "Medium"].iloc[0]
    high_risk = risk.loc[risk["risk_segment"] == "High"].iloc[0]
    observation_date = accounts["observation_date"].max()
    survival = paid_survival_curve(subscriptions, observation_date).dropna(subset=["hazard"])
    last_churn_month = int(survival.loc[survival["churned"].gt(0), "month_since_paid"].max())
    actionable = accounts.loc[
        accounts["current_active_customer"]
        & accounts["paid_conversion_date"].gt(observation_date - pd.Timedelta(days=30.4375 * last_churn_month))
    ]

    st.title("Churn Risk")
    st.caption("Identify which accounts are most at risk and where customer success should focus its attention.")

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.warning(
            f"**{int(high_risk['accounts']):,} high-risk accounts** (${int(high_risk['mrr_at_risk']):,} MRR)  \n"
            f"These are already gone or dark — belongs in a win-back campaign, not a save queue. "
            f"Medium-risk ({int(medium_risk['accounts']):,} accounts, ${int(medium_risk['mrr_at_risk']):,} MRR) is where CS can still act."
        )
        c2.info(
            f"**All churn happens in months 2–{last_churn_month}** after first payment  \n"
            f"After month {last_churn_month}, no account has churned. "
            f"**{len(actionable):,} paying accounts (${actionable['current_mrr'].sum():,.0f} MRR)** are still inside the risk window."
        )
        c3.success(
            f"**Engagement doesn't predict churn here** — at least not in the core tables.  \n"
            f"The planted-signal test (usage_weekly) shows a usage *drop* in the 3–6 weeks before churn is detectable. "
            f"Trend matters more than level."
        )
    st.write("")

    left, right = st.columns([1, 1.5])
    with left:
        colors = {"High": RED, "Medium": AMBER, "Low": TEAL}
        fig = px.pie(risk, values="accounts", names="risk_segment", hole=0.62, color="risk_segment", color_discrete_map=colors)
        fig.update_layout(height=310, margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.subheader("Risk segment counts")
        display = risk.copy()
        display["mrr_at_risk"] = display["mrr_at_risk"].map("${:,.0f}".format)
        display["average_risk_score"] = display["average_risk_score"].map("{:.0f}".format)
        display.columns = ["Risk segment", "Accounts", "MRR exposure", "Average score"]
        st.dataframe(display, hide_index=True, use_container_width=True)
        st.subheader("How risk scores work")
        st.write("High risk = no activation within 7 days, no paid subscription (or already churned), and a long gap since the last product event. Scores are rule-based — transparent and easy to audit — not a machine-learning churn model.")

    st.subheader("At-risk accounts — actionable only (excludes already churned)")
    st.caption(
        "Filtered to accounts where intervention is still possible: `status != 'churned'`. "
        "Already-churned accounts are excluded — they belong in a win-back campaign, not a CS save queue. "
        f"**{(accounts['risk_segment'].isin(['High', 'Medium']) & (accounts['status'] == 'churned')).sum():,} already-churned accounts** "
        "are excluded from this table."
    )
    at_risk = accounts.loc[
        accounts["risk_segment"].isin(["High", "Medium"]) & (accounts["status"] != "churned"),
        ["org_id", "company_size", "acquisition_source", "plan_type", "status", "activated_7d", "days_since_last_event", "current_mrr", "risk_score", "risk_segment"]
    ].sort_values(["risk_score", "current_mrr"], ascending=False)
    display = at_risk.copy()
    display.columns = ["Org ID", "Segment", "Source", "Plan", "Subscription status", "Activated", "Days since last event", "Current MRR", "Risk score", "Risk segment"]
    display["Activated"] = display["Activated"].map({True: "Yes", False: "No"})
    display["Current MRR"] = display["Current MRR"].map("${:,.0f}".format)
    st.dataframe(display, hide_index=True, use_container_width=True, height=400)

    st.subheader("Recommended customer success actions")
    actions = pd.DataFrame({"Risk segment": ["High", "Medium", "Low"], "Recommended action": ["Start a proactive save play: confirm business value, address the activation gap, and schedule an executive check-in for paid accounts.", "Run a scaled re-engagement sequence with a use-case reminder, training offer, and product-adoption review.", "Maintain lifecycle education and identify expansion signals; no immediate retention intervention required."]})
    st.dataframe(actions, hide_index=True, use_container_width=True)

    observation_date = accounts["observation_date"].max()
    st.subheader("When does churn actually happen?")
    st.caption(
        "Monthly churn rate by months since first payment. Still-active accounts are treated as censored (ongoing, not churned). "
        "The standard LTV formula assumes churn is flat every month — this chart shows whether that's actually true."
    )
    survival = paid_survival_curve(subscriptions, observation_date).dropna(subset=["hazard"])
    survival = survival.loc[survival["at_risk"].ge(30)]
    fig = px.bar(survival, x="month_since_paid", y="hazard", color_discrete_sequence=[RED], text_auto=".1%")
    fig.update_layout(title="Churn hazard by month since paid start", height=300, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(tickformat=".0%", gridcolor="#dce6f4")
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    last_churn_month = int(survival.loc[survival["churned"].gt(0), "month_since_paid"].max())
    plateau = survival["survival"].iloc[-1]
    in_window = accounts.loc[
        accounts["current_active_customer"]
        & accounts["paid_conversion_date"].gt(observation_date - pd.Timedelta(days=30.4375 * last_churn_month))
    ]
    st.caption(
        f"No churn is observed after month {last_churn_month}; survival plateaus at {plateau:.0%}. In this dataset "
        f"an account that gets past its first {last_churn_month} paying months does not churn, so the actionable "
        f"window is early: **{len(in_window):,} currently-paying accounts (${in_window['current_mrr'].sum():,.0f} MRR)** "
        "are still inside it."
    )

    st.subheader("Does engagement predict churn? A prospective test")
    st.caption(
        "To avoid circular reasoning, features are built from events *before* a cutoff date, and the outcome is whether the account churned in the *next* 90 days. "
        "We can't use current activity to predict current churn — a churned account has already stopped using the product, so that would be looking at the outcome to predict itself. "
        "Month-end cutoffs are pooled, so one account can appear in multiple rows."
    )
    cutoffs = list(pd.date_range("2025-04-30", observation_date, freq="ME"))
    dataset = prospective_engagement_dataset(event_logs, organizations, subscriptions, observation_date, cutoffs)
    dataset["Active in prior 28 days"] = dataset["active_days_recent"].gt(0).map({True: "Yes", False: "No"})
    dataset["Tenure"] = pd.cut(dataset["tenure_days"], [0, 60, 120, 240, 10_000], labels=["<60d", "60-120d", "120-240d", "240d+"])
    pooled = churn_by_feature(dataset, "Active in prior 28 days")
    within = churn_by_feature(dataset, "Active in prior 28 days", "Tenure").pivot(index="Tenure", columns="Active in prior 28 days", values="churn_rate").astype(float)
    tables = st.columns(2)
    with tables[0]:
        st.markdown("**Unadjusted**")
        st.dataframe(pooled.rename(columns={"observations": "Observations", "churn_rate": "90-day churn"}).style.format({"Observations": "{:,.0f}", "90-day churn": "{:.1%}"}), hide_index=True, use_container_width=True)
    with tables[1]:
        st.markdown("**Within tenure strata**")
        st.dataframe(within.style.format("{:.1%}", na_rep="n/a"), use_container_width=True)
    st.caption(
        "At first glance, recently-active accounts churn *more* — which seems backwards. "
        "The explanation is tenure: new accounts are both active (still in onboarding) and inside the early high-churn window. "
        "Once you control for tenure, activity level makes little difference. "
        "Neither feature depth (distinct event types) nor activation status show a signal either."
    )

    st.subheader("\U0001F9EA Engagement tiers on a usage table with a planted signal")
    st.caption(
        "**This is synthetic data with a planted signal — not a real finding.** "
        "The five core tables have no ongoing usage and churn is a random coin flip, so nothing in them can predict churn. "
        "`usage_weekly.csv` is generated separately with usage intentionally lower for future churners, and a decline in the 3–6 weeks before churn. "
        "Acquisition channel has no planted effect. "
        "This is a positive control: can the prospective method detect a signal that's really there, and stay quiet about one that isn't?"
    )
    horizon = st.select_slider("Churn horizon after the cutoff (days)", options=[30, 60, 90], value=30)
    tiered = usage_dataset(horizon)
    overall = tiered["churned_within_horizon"].mean()
    by_tier = tiered.groupby("tier")["churned_within_horizon"].agg(observations="size", churn_rate="mean").reset_index()
    by_tier["lift_vs_overall"] = by_tier["churn_rate"] / overall
    by_tier = by_tier.set_index("tier").reindex([tier for tier in ["power", "active", "at_risk", "dormant"] if tier in set(by_tier["tier"])])
    st.dataframe(
        by_tier.rename(columns={"observations": "Observations", "churn_rate": f"{horizon}-day churn", "lift_vs_overall": "Lift vs. overall"}).style.format(
            {"Observations": "{:,.0f}", f"{horizon}-day churn": "{:.1%}", "Lift vs. overall": "{:.1f}x"}
        ),
        use_container_width=True,
    )
    trend_auc = auc_score(tiered["churned_within_horizon"], -tiered["trend_ratio"])
    level_auc = auc_score(tiered["churned_within_horizon"], -tiered["recent_sessions"])
    metrics = st.columns(3)
    metrics[0].metric("AUC: usage trend (drop = risk)", f"{trend_auc:.2f}")
    metrics[1].metric("AUC: recent usage level", f"{level_auc:.2f}")
    metrics[2].metric("Distinct paying accounts", f"{tiered['org_id'].nunique():,}")
    tiered["Tenure"] = pd.cut(tiered["tenure_days"], [0, 60, 120, 240, 10_000], labels=["<60d", "60-120d", "120-240d", "240d+"])
    within = churn_by_feature(tiered, "tier", "Tenure").pivot(index="Tenure", columns="tier", values="churn_rate").astype(float)
    st.markdown("**Churn by tier within tenure bands** (so the tier isn't just standing in for account age)")
    st.dataframe(within.style.format("{:.1%}", na_rep="n/a"), use_container_width=True)
    channel = tiered.groupby("acquisition_source")["churned_within_horizon"].mean()
    st.caption(
        f"Reading it: AUC 0.5 means no signal. A *drop* in usage is a short-lead warning (planted at 3-6 weeks), so its AUC is "
        f"{trend_auc:.2f} at {horizon} days and fades toward 0.5 as the horizon grows, while the usage *level* keeps some signal. "
        f"Negative control: {horizon}-day churn by acquisition channel ranges only {channel.min():.1%} to {channel.max():.1%}; no channel "
        "effect was planted, and none is found. Cutoffs are a week apart, so observations repeat accounts; counts are not independent accounts."
    )


if __name__ == "__main__":
    main()
