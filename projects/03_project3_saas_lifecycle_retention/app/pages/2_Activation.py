"""Activation behavior detail page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import KEY_ACTION_EVENTS, activation_completion_days, build_account_metrics
from utils.theme import BLUE, GREEN, PRIMARY, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Activation | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    return build_account_metrics(tables), tables["event_logs"], tables["organizations"]


def chart_style(fig, height: int = 320):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
    fig.update_yaxes(gridcolor="#dce6f4", zeroline=False)
    return fig


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, events, organizations = page_data()
    activation_by_size = accounts.groupby("company_size", as_index=False).agg(activation_rate=("activated_7d", "mean"))
    activation_by_source = accounts.groupby("acquisition_source", as_index=False).agg(activation_rate=("activated_7d", "mean")).sort_values("activation_rate")

    st.title("Activation")
    st.caption("Identify the early behaviors that help new accounts reach value quickly.")
    st.info("Activation is measured as account activation rate within 7 days of signup. The lifecycle framework defines it around workspace creation and a key product action.")

    kpis = st.columns(3)
    with kpis[0]:
        st.metric("Activation rate", f"{accounts['activated_7d'].mean():.1%}")
    with kpis[1]:
        st.metric("Workspace creation", f"{accounts['workspace_created'].mean():.1%}")
    with kpis[2]:
        completion = activation_completion_days(events, organizations)
        st.metric("Median time to activation", f"{completion['days_to_activation'].median():.1f} days")

    left, right = st.columns(2)
    with left:
        fig = px.bar(activation_by_size, x="company_size", y="activation_rate", color_discrete_sequence=[PRIMARY], text_auto=".1%")
        fig.update_layout(title="Activation rate by company size")
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(chart_style(fig), width="stretch", config={"displayModeBar": False})
    with right:
        fig = px.bar(activation_by_source, x="activation_rate", y="acquisition_source", orientation="h", color_discrete_sequence=[TEAL], text_auto=".1%")
        fig.update_layout(title="Activation rate by acquisition source")
        fig.update_xaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(chart_style(fig), width="stretch", config={"displayModeBar": False})

    st.subheader("Early product action adoption")
    action_names = ["workspace_created", *sorted(KEY_ACTION_EVENTS)]
    early_events = events.merge(organizations[["org_id", "created_at"]], on="org_id")
    early_events["days_from_signup"] = (early_events["event_timestamp"] - early_events["created_at"]).dt.total_seconds().div(86_400)
    adoption = early_events.loc[early_events["event_name"].isin(action_names) & early_events["days_from_signup"].between(0, 7)].groupby("event_name")["org_id"].nunique().reindex(action_names, fill_value=0).div(len(accounts)).rename("adoption_rate").reset_index()
    adoption["event_name"] = adoption["event_name"].str.replace("_", " ").str.title()
    fig = px.bar(adoption, x="event_name", y="adoption_rate", color_discrete_sequence=[GREEN], text_auto=".1%")
    fig.update_layout(title="Share of accounts completing each action in the first 7 days")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(chart_style(fig, 300), width="stretch", config={"displayModeBar": False})


if __name__ == "__main__":
    main()
