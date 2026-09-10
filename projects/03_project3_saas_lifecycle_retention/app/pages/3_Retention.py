"""Retention cohort and segment detail page."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    build_account_metrics,
    retention_rates_by_segment,
    signup_cohort_retention,
)
from utils.theme import BLUE, GREEN, PRIMARY, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Retention | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data() -> pd.DataFrame:
    return build_account_metrics(load_tables())


def segment_rates(accounts: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return retention_rates_by_segment(accounts, dimension)


def main() -> None:
    inject_theme()
    render_navigation()
    accounts = page_data()
    st.title("Retention")
    st.caption("Compare 30/60/90-day retention across the acquisition and product behaviors that shape durable value.")

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
    st.dataframe(rates.style.format("{:.1%}").background_gradient(cmap="Blues", axis=None, vmin=0, vmax=1), width="stretch")

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
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


if __name__ == "__main__":
    main()
