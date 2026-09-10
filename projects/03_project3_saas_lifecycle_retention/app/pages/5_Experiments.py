"""Onboarding experiment readout page."""

from __future__ import annotations

from statistics import NormalDist

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import build_account_metrics, experiment_summary, retention_rate
from utils.theme import BLUE, GREEN, PRIMARY, inject_theme, render_navigation


st.set_page_config(page_title="Experiments | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data() -> pd.DataFrame:
    return build_account_metrics(load_tables())


def two_proportion_p_value(control_successes: int, control_total: int, treatment_successes: int, treatment_total: int) -> float:
    pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
    standard_error = (pooled * (1 - pooled) * (1 / control_total + 1 / treatment_total)) ** 0.5
    if standard_error == 0:
        return 1.0
    z_score = (treatment_successes / treatment_total - control_successes / control_total) / standard_error
    return 2 * (1 - NormalDist().cdf(abs(z_score)))


def main() -> None:
    inject_theme()
    render_navigation()
    accounts = page_data()
    summary = experiment_summary(accounts)
    control = accounts.loc[accounts["variant"].eq("control")]
    treatment = accounts.loc[accounts["variant"].eq("treatment")]
    lift = treatment["activated_7d"].mean() - control["activated_7d"].mean()
    p_value = two_proportion_p_value(int(control["activated_7d"].sum()), len(control), int(treatment["activated_7d"].sum()), len(treatment))

    st.title("Experiment Readout")
    st.caption("Assess whether guided onboarding improves activation without degrading downstream lifecycle outcomes.")
    kpis = st.columns(4)
    with kpis[0]:
        st.metric("Control activation", f"{control['activated_7d'].mean():.1%}")
    with kpis[1]:
        st.metric("Variant activation", f"{treatment['activated_7d'].mean():.1%}")
    with kpis[2]:
        st.metric("Activation lift", f"{lift * 100:+.1f} pp")
    with kpis[3]:
        st.metric("Two-proportion p-value", f"{p_value:.4f}")

    left, right = st.columns(2)
    with left:
        display = summary[["variant", "accounts", "activation_rate", "paid_conversion_rate", "retention_60d_rate"]].copy()
        display.columns = ["Variant", "Accounts", "Activation", "Paid conversion", "60D retention"]
        for column in ["Activation", "Paid conversion", "60D retention"]:
            display[column] = display[column].map("{:.1%}".format)
        display["Variant"] = display["Variant"].map({"control": "Control", "treatment": "Variant"})
        st.subheader("Primary and downstream metrics")
        st.dataframe(display, hide_index=True, width="stretch")
    with right:
        guardrails = pd.DataFrame({"Metric": ["Workspace creation", "Trial start", "60-day retention"], "Control": [control["workspace_created"].mean(), control["trial_started"].mean(), retention_rate(control, 60)], "Variant": [treatment["workspace_created"].mean(), treatment["trial_started"].mean(), retention_rate(treatment, 60)]})
        guardrails["Difference"] = guardrails["Variant"] - guardrails["Control"]
        for column in ["Control", "Variant", "Difference"]:
            guardrails[column] = guardrails[column].map("{:+.1%}".format if column == "Difference" else "{:.1%}".format)
        st.subheader("Guardrail metrics")
        st.dataframe(guardrails, hide_index=True, width="stretch")

    st.subheader("Segment-level treatment effect")
    segments = accounts.groupby(["company_size", "variant"], as_index=False).agg(activation_rate=("activated_7d", "mean"))
    segments["variant_label"] = segments["variant"].map({"control": "Control", "treatment": "Variant"})
    fig = px.bar(segments, x="company_size", y="activation_rate", color="variant_label", barmode="group", color_discrete_map={"Control": PRIMARY, "Variant": GREEN})
    fig.update_layout(height=330, margin=dict(l=8, r=8, t=24, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
    fig.update_yaxes(tickformat=".0%", range=[0, 1], gridcolor="#dce6f4")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


if __name__ == "__main__":
    main()
