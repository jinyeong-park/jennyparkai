"""Revenue and business-impact detail page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    build_account_metrics,
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
    return accounts, revenue_trend(accounts), tables["subscriptions"]


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, trend, subscriptions = page_data()
    paid = accounts.loc[accounts["current_active_customer"]]
    arpa = paid["current_mrr"].mean()
    rollout = targeted_rollout_impact(accounts)
    incremental_activated = rollout["incremental_activated"].sum()
    estimated_incremental_mrr = rollout["estimated_incremental_mrr"].sum()

    st.title("Revenue")
    st.caption("Connect product activation movement to paid conversion and estimated recurring revenue impact.")
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
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Each point includes only subscriptions old enough to reach that horizon. Retained MRR excludes subscriptions that ended earlier; expansion and contraction events are not modeled.")
    with right:
        plan_mix = paid.groupby("plan_type", as_index=False).agg(customers=("org_id", "size"), mrr=("current_mrr", "sum")).sort_values("mrr", ascending=False)
        fig = px.bar(plan_mix, x="plan_type", y="mrr", color_discrete_sequence=[PRIMARY], text_auto="$.2s")
        fig.update_layout(title="Paid MRR by plan", height=320, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(title="MRR", tickprefix="$", gridcolor="#dce6f4")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.subheader("Treatment rollout impact model")
    rollout_display = rollout.copy()
    rollout_display["Activation lift"] = rollout_display["activation_lift"].map("{:+.1%}".format)
    rollout_display["Activated to current paid"] = rollout_display["activated_to_paid_rate"].map("{:.1%}".format)
    rollout_display["Current ARPA"] = rollout_display["current_arpa"].map("${:,.0f}".format)
    rollout_display["Estimated incremental MRR"] = rollout_display["estimated_incremental_mrr"].map("${:,.0f}".format)
    rollout_display = rollout_display.rename(columns={"company_size": "Segment", "eligible_accounts": "Eligible accounts"})
    st.dataframe(
        rollout_display[["Segment", "Eligible accounts", "Activation lift", "Activated to current paid", "Current ARPA", "Estimated incremental MRR"]],
        hide_index=True,
        width="stretch",
    )
    st.write(f"Applying each segment's observed lift, activated-to-current-paid conversion, and current ARPA across **SMB and Mid-Market only** estimates **{incremental_activated:,.0f}** incremental activated accounts and **${estimated_incremental_mrr:,.0f}** in incremental monthly recurring revenue.")


if __name__ == "__main__":
    main()
