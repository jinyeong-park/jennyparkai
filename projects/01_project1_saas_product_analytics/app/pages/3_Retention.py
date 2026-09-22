"""Retention cohort and segment detail page."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    build_account_metrics,
    engagement_retention_curve,
    retention_rate,
    retention_rates_by_segment,
    signup_cohort_retention,
)
from utils.theme import BLUE, GREEN, PRIMARY, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Retention | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    return build_account_metrics(tables), tables["organizations"], tables["event_logs"]


def segment_rates(accounts: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return retention_rates_by_segment(accounts, dimension)


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, organizations, event_logs = page_data()

    # Pre-compute for Key Findings
    obs_date = accounts["observation_date"].max()
    paid_d30 = retention_rate(accounts, 30)
    paid_d60 = retention_rate(accounts, 60)
    paid_d90 = retention_rate(accounts, 90)
    engagement = engagement_retention_curve(organizations, event_logs, obs_date)
    eng_d60 = float(engagement.dropna(subset=["retention_d60"])["retention_d60"].mean())
    best_plan = retention_rates_by_segment(accounts, "plan_type")["60D"].dropna().idxmax()
    best_plan_rate = retention_rates_by_segment(accounts, "plan_type")["60D"].dropna().max()

    st.title("Retention")
    st.caption("See which segments, channels, and behaviors lead to accounts that actually stick around.")

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.info(
            f"**Paid retention: {paid_d30:.0%} → {paid_d60:.0%} → {paid_d90:.0%}** (D30/D60/D90)  \n"
            f"Drops steepest between D30 and D60. After D60, it flattens — whoever is still active tends to stay."
        )
        c2.warning(
            f"**Engagement retention at D60: {eng_d60:.0%}** across all sign-ups  \n"
            f"Paid retention ({paid_d60:.0%}) only counts converted accounts. "
            f"Nearly half the sign-up base has gone dark before ever paying."
        )
        c3.success(
            f"**Best-retaining plan: {best_plan}** ({best_plan_rate:.0%} at D60)  \n"
            f"Activated accounts retain significantly better. "
            f"The D14–21 window is the highest-leverage point for re-engagement nudges."
        )
    st.write("")

    dimensions = [("Activation status", "activated_7d"), ("Acquisition source", "acquisition_source"), ("Company size", "company_size"), ("Plan", "plan_type")]
    metric_columns = st.columns(4)
    for column, (label, field) in zip(metric_columns, dimensions):
        grouped = retention_rates_by_segment(accounts, field)["60D"].dropna()
        with column:
            st.metric(f"Best {label.lower()}", f"{grouped.max():.1%}", grouped.idxmax())

    st.subheader("Paid retention by lifecycle segment")
    selection = st.selectbox("Break down retention by", [label for label, _ in dimensions])
    field = dict(dimensions)[selection]
    rates = segment_rates(accounts, field)
    rates.index = rates.index.map(lambda value: "Activated" if value is True else "Not activated" if value is False else value)
    st.caption("Each horizon uses only accounts old enough to have reached it.")
    st.dataframe(rates.style.format("{:.1%}").background_gradient(cmap="Blues", axis=None, vmin=0, vmax=1), use_container_width=True)

    st.subheader("Paid retention by signup cohort")
    cohort_data = signup_cohort_retention(accounts)
    fig = go.Figure()
    colors = [PRIMARY, TEAL, BLUE, GREEN]
    for index, (cohort_month, cohort) in enumerate(cohort_data.groupby("cohort_month")):
        cohort = cohort.dropna(subset=["retention_rate"])
        fig.add_trace(go.Scatter(x=cohort["day"], y=cohort["retention_rate"], mode="lines+markers", name=cohort_month.strftime("%b %Y"), line=dict(width=3, color=colors[index % len(colors)])))
    fig.update_layout(height=330, margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
    fig.update_xaxes(title="Days since paid conversion", tickvals=[0, 30, 60, 90])
    fig.update_yaxes(title="Retention rate", tickformat=".0%", range=[0, 1], gridcolor="#dce6f4")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.subheader("Product engagement retention — still using it, not just still paying?")
    st.caption(
        "Paid retention (above) only asks: is the subscription still active? "
        "This chart asks a harder question: did the account have *any* product activity at 30, 60, and 90 days after signup — "
        "across all sign-ups, not just paid ones. Day 0 is excluded because activity on signup day is onboarding, not a return visit."
    )
    engagement = engagement_retention_curve(
        organizations, event_logs, accounts["observation_date"].max()
    )
    engagement_long = engagement.melt(
        id_vars=["cohort_month", "cohort_size"],
        value_vars=["retention_d30", "retention_d60", "retention_d90"],
        var_name="horizon",
        value_name="retention_rate",
    ).dropna(subset=["retention_rate"])
    engagement_long["day"] = engagement_long["horizon"].map(
        {"retention_d30": 30, "retention_d60": 60, "retention_d90": 90}
    )
    fig = go.Figure()
    for index, (cohort_month, cohort) in enumerate(engagement_long.groupby("cohort_month")):
        fig.add_trace(
            go.Scatter(
                x=cohort["day"],
                y=cohort["retention_rate"],
                mode="lines+markers",
                name=cohort_month.strftime("%b %Y"),
                line=dict(width=3, color=colors[index % len(colors)]),
            )
        )
    fig.update_layout(height=330, margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
    fig.update_xaxes(title="Days since signup", tickvals=[30, 60, 90])
    fig.update_yaxes(title="Retention rate", tickformat=".0%", range=[0, 1], gridcolor="#dce6f4")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    mature_engagement = engagement.dropna(subset=["retention_d60"])
    engagement_d60_avg = mature_engagement["retention_d60"].mean()
    paid_d60_avg = retention_rate(accounts, 60)
    st.caption(
        f"Across mature cohorts, D60 product engagement retention averages {engagement_d60_avg:.0%} of "
        f"**all signups**, versus {paid_d60_avg:.0%} D60 retention among **paid** accounts only. The gap is "
        "expected — most signups never convert to paid at all — but the size of it shows how much usage "
        "drop-off happens before or outside the subscription relationship, which subscription-status "
        "tracking alone would never surface."
    )

    st.divider()
    st.subheader("Recommendations")

    st.warning(
        f"**Paid retention ({paid_d60_avg:.0%} at D60) is hiding a bigger problem.** "
        f"Only {engagement_d60_avg:.0%} of all sign-ups still have product activity at D60 — "
        "nearly half the sign-up base has gone dark before ever becoming a paying customer. "
        "If you only track paid retention, you'll never see this dropout. "
        "**Start tracking engagement retention (D30/D60/D90) alongside paid retention.**"
    )
    st.success(
        "**Where to act:** The biggest drop happens between D30 and D60. "
        "After D60, things stabilize — whoever's still active tends to stay. "
        "Focus re-engagement on accounts in their first 60 days. "
        "A targeted in-product nudge or check-in at day 14–21 is the highest-leverage intervention point."
    )


if __name__ == "__main__":
    main()
