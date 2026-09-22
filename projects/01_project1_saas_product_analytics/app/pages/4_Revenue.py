"""Revenue and business-impact detail page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
import pandas as pd

from utils.metrics import (
    build_account_metrics,
    channel_ltv,
    modeled_nrr_trend,
    revenue_trend,
    targeted_rollout_impact,
)
from utils.theme import GREEN, PRIMARY, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Revenue | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    accounts = build_account_metrics(tables)
    return accounts, revenue_trend(accounts), tables["subscriptions"], tables["organizations"]


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, trend, subscriptions, organizations = page_data()
    paid = accounts.loc[accounts["current_active_customer"]]
    arpa = paid["current_mrr"].mean()
    rollout = targeted_rollout_impact(accounts)
    incremental_activated = rollout["incremental_activated"].sum()
    estimated_incremental_mrr = rollout["estimated_incremental_mrr"].sum()

    st.title("Revenue")
    st.caption("Translate activation and retention into MRR, LTV, and the estimated revenue impact of rolling out the guided onboarding experiment.")

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.info(
            f"**Current MRR: ${paid['current_mrr'].sum():,.0f}** across {len(paid):,} paid accounts  \n"
            f"ARPA: ${arpa:,.0f}/mo. Enterprise ARPA (~$525) is 3.7× SMB (~$143) — "
            f"segment mix has a bigger impact on revenue than conversion rate alone."
        )
        c2.success(
            f"**Experiment rollout could add ${estimated_incremental_mrr:,.0f}/mo**  \n"
            f"SMB + Mid-Market only. Based on observed activation lift × activated-to-paid rate × current ARPA per segment."
        )
        c3.warning(
            f"**LTV ranking across channels is not statistically meaningful.**  \n"
            f"Monthly churn is 2–3% in every channel. The spread is driven by ARPA, not churn. "
            f"Don't reallocate budget based on LTV ranking alone — get CAC data first."
        )
    st.write("")

    kpis = st.columns(4)
    with kpis[0]:
        st.metric("Current paid customers", f"{len(paid):,}")
    with kpis[1]:
        st.metric("Current ARPA", f"${arpa:,.0f}")
    with kpis[2]:
        st.metric("Current paid MRR", f"${paid['current_mrr'].sum():,.0f}")
    with kpis[3]:
        st.metric("Estimated incremental MRR", f"${estimated_incremental_mrr:,.0f}", "Treatment rollout model")

    observation_date = accounts["observation_date"].max()
    nrr = modeled_nrr_trend(subscriptions, observation_date)
    nrr_long = nrr.melt(id_vars="cohort_month", value_vars=["nrr_30d", "nrr_60d", "nrr_90d"], var_name="horizon", value_name="modeled_nrr")
    nrr_long = nrr_long.dropna(subset=["modeled_nrr"])
    nrr_long["horizon"] = nrr_long["horizon"].str.replace("nrr_", "").str.upper()
    left, right = st.columns(2)
    with left:
        fig = px.line(nrr_long, x="cohort_month", y="modeled_nrr", color="horizon", markers=True, color_discrete_sequence=[GREEN, PRIMARY, TEAL])
        fig.update_layout(title="Modeled NRR (no expansion events)", height=320, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="Cohort age")
        fig.update_yaxes(title="Retained MRR / beginning MRR", tickformat=".0%", gridcolor="#dce6f4")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Each point includes only subscriptions old enough to reach that horizon. Retained MRR excludes subscriptions that ended earlier; expansion and contraction events are not modeled.")
    with right:
        plan_mix = paid.groupby("plan_type", as_index=False).agg(customers=("org_id", "size"), mrr=("current_mrr", "sum")).sort_values("mrr", ascending=False)
        fig = px.bar(plan_mix, x="plan_type", y="mrr", color_discrete_sequence=[PRIMARY], text_auto="$.2s")
        fig.update_layout(title="Paid MRR by plan", height=320, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(title="MRR", tickprefix="$", gridcolor="#dce6f4")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.subheader("What happens to MRR if we ship the guided onboarding to everyone?")
    rollout_display = rollout.copy()
    rollout_display["Activation lift"] = rollout_display["activation_lift"].map("{:+.1%}".format)
    rollout_display["Activated to current paid"] = rollout_display["activated_to_paid_rate"].map("{:.1%}".format)
    rollout_display["Current ARPA"] = rollout_display["current_arpa"].map("${:,.0f}".format)
    rollout_display["Estimated incremental MRR"] = rollout_display["estimated_incremental_mrr"].map("${:,.0f}".format)
    rollout_display = rollout_display.rename(columns={"company_size": "Segment", "eligible_accounts": "Eligible accounts"})
    st.dataframe(
        rollout_display[["Segment", "Eligible accounts", "Activation lift", "Activated to current paid", "Current ARPA", "Estimated incremental MRR"]],
        hide_index=True,
        use_container_width=True,
    )
    st.write(f"Rolling out to **SMB and Mid-Market only** (Enterprise excluded — smaller, uncertain lift) would activate an estimated **{incremental_activated:,.0f}** additional accounts and add **${estimated_incremental_mrr:,.0f}** in monthly recurring revenue.")

    st.subheader("Customer LTV by channel — and what it can and can't tell us")
    st.caption(
        "LTV = ARPA ÷ monthly churn rate. Still-active subscriptions are treated as censored (ongoing exposure, not churned). "
        "There's no spend data here, so this can't be LTV:CAC — but the last column shows the maximum you could spend per account "
        "and still hit the target LTV:CAC ratio."
    )
    controls = st.columns(3)
    with controls[0]:
        dimension = st.selectbox("Segment by", ["acquisition_source", "company_size"])
    with controls[1]:
        horizon = st.slider("LTV horizon (months)", 12, 36, 24, step=6)
    with controls[2]:
        target_ratio = st.slider("Target LTV:CAC", 2.0, 5.0, 3.0, step=0.5)
    ltv = channel_ltv(subscriptions, organizations, observation_date, dimension=dimension, horizon_months=horizon, target_ltv_to_cac=target_ratio)

    ltv_chart = ltv.assign(
        err_up=ltv["ltv_capped_high"] - ltv["ltv_capped"], err_down=ltv["ltv_capped"] - ltv["ltv_capped_low"]
    )
    fig = px.bar(ltv_chart, x=dimension, y="ltv_capped", error_y="err_up", error_y_minus="err_down", color_discrete_sequence=[PRIMARY])
    fig.update_layout(title=f"{horizon}-month LTV with 95% interval (resampling accounts: ARPA and churn)", height=320, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(title="Capped LTV", tickprefix="$", gridcolor="#dce6f4")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    ltv_display = ltv[[dimension, "paid_accounts", "arpa", "churn_events", "monthly_churn", "lifetime_months", "ltv", "ltv_capped", "max_cac"]].rename(
        columns={
            "paid_accounts": "Paid accounts", "arpa": "ARPA", "churn_events": "Churn events", "monthly_churn": "Monthly churn",
            "lifetime_months": "Implied lifetime (mo)", "ltv": "Uncapped LTV", "ltv_capped": f"{horizon}-mo LTV", "max_cac": f"Max CAC @ {target_ratio:g}:1",
        }
    ).set_index(dimension)
    st.dataframe(
        ltv_display.style.format(
            {"Paid accounts": "{:,.0f}", "ARPA": "${:,.0f}", "Churn events": "{:,.0f}", "Monthly churn": "{:.2%}", "Implied lifetime (mo)": "{:.0f}",
             "Uncapped LTV": "${:,.0f}", f"{horizon}-mo LTV": "${:,.0f}", f"Max CAC @ {target_ratio:g}:1": "${:,.0f}"}
        ),
        use_container_width=True,
    )
    observed_months = (observation_date - subscriptions.loc[subscriptions["mrr_amount"].gt(0), "start_date"].min()).days / 30.4375
    overlap = ltv["ltv_capped_low"].max() <= ltv["ltv_capped_high"].min()  # every interval shares a common region
    st.caption(
        f"Two things to keep in mind. "
        f"(1) The model implies lifetimes of {ltv['lifetime_months'].min():.0f}–{ltv['lifetime_months'].max():.0f} months, but the longest subscription observed is only ~{observed_months:.0f} months — "
        f"uncapped LTV is extrapolating well beyond the data. Use the capped figure. Also, churn is front-loaded here (all of it happens in months 2–4; see Churn Risk), so even the capped LTV slightly understates true 24-month LTV. "
        f"(2) The confidence intervals "
        + ("overlap across all segments, so the ranking is not statistically meaningful — the spread is driven by ARPA differences, not churn differences." if overlap else "don't fully overlap, so at least some segments are genuinely different.")
    )


if __name__ == "__main__":
    main()
