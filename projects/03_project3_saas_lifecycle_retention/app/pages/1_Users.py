"""User and account acquisition detail page."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import build_account_metrics
from utils.theme import BLUE, GREEN, PRIMARY, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Users | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    return build_account_metrics(tables), tables["users"]


def chart_style(fig, height: int = 310):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=32, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#dce6f4", zeroline=False)
    return fig


def sort_account_directory(accounts):
    """Apply the operational directory's numeric risk and MRR ordering."""
    return accounts.sort_values(["risk_score", "current_mrr"], ascending=[False, False])


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, users = page_data()
    user_counts = users.groupby("org_id").size().rename("users").reset_index()
    accounts = accounts.merge(user_counts, on="org_id", how="left")
    accounts["users"] = accounts["users"].fillna(0).astype(int)

    st.title("Users & Acquisition")
    st.caption("Assess which acquisition channels and account profiles create the strongest lifecycle entry point.")

    source, size, region = st.columns(3)
    with source:
        source_data = accounts.groupby("acquisition_source", as_index=False).agg(signups=("org_id", "size")).sort_values("signups")
        fig = px.bar(source_data, x="signups", y="acquisition_source", orientation="h", color_discrete_sequence=[PRIMARY])
        fig.update_layout(title="Signup volume by acquisition source")
        st.plotly_chart(chart_style(fig), width="stretch", config={"displayModeBar": False})
    with size:
        size_data = accounts.groupby("company_size", as_index=False).agg(signups=("org_id", "size")).sort_values("signups")
        fig = px.bar(size_data, x="company_size", y="signups", color_discrete_sequence=[BLUE])
        fig.update_layout(title="Signup volume by company size")
        st.plotly_chart(chart_style(fig), width="stretch", config={"displayModeBar": False})
    with region:
        region_data = accounts.groupby("region", as_index=False).agg(signups=("org_id", "size")).sort_values("signups")
        fig = px.bar(region_data, x="signups", y="region", orientation="h", color_discrete_sequence=[TEAL])
        fig.update_layout(title="Signup volume by region")
        st.plotly_chart(chart_style(fig), width="stretch", config={"displayModeBar": False})

    st.subheader("Account directory")
    st.caption("Use this operational view to connect acquisition context with activation, monetization, and current risk.")
    display = sort_account_directory(accounts)[["org_id", "created_at", "company_size", "acquisition_source", "users", "activated_7d", "current_active_customer", "current_mrr", "risk_segment"]].copy()
    display.columns = ["Org ID", "Created", "Segment", "Source", "Users", "Activated", "Current paid customer", "Current MRR", "Risk segment"]
    display["Created"] = display["Created"].dt.strftime("%Y-%m-%d")
    display["Activated"] = display["Activated"].map({True: "Yes", False: "No"})
    display["Current paid customer"] = display["Current paid customer"].map({True: "Yes", False: "No"})
    display["Current MRR"] = display["Current MRR"].map("${:,.0f}".format)
    st.dataframe(display, hide_index=True, width="stretch", height=500)


if __name__ == "__main__":
    main()
