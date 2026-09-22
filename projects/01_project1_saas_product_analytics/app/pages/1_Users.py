"""User and account acquisition detail page."""

from __future__ import annotations

import pandas as pd
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
    st.caption("See which channels and account types actually turn into paying customers — not just sign-ups.")

    # ── Per-dimension aggregations ─────────────────────────────────────────────
    def channel_quality(df, dim):
        g = df.groupby(dim, as_index=False).agg(
            signups=("org_id", "size"),
            paid_customers=("current_active_customer", "sum"),
            paid_conversion_rate=("current_active_customer", "mean"),
            total_mrr=("current_mrr", "sum"),
        )
        g["arpa"] = g["total_mrr"] / g["paid_customers"].replace(0, float("nan"))
        return g.sort_values("total_mrr", ascending=False)

    source_data = channel_quality(accounts, "acquisition_source")
    size_data   = channel_quality(accounts, "company_size")
    region_data = channel_quality(accounts, "region")

    # ── Key Findings ─────────────────────────────────────────────────────────────────
    top_source    = source_data.sort_values("paid_conversion_rate", ascending=False).iloc[0]
    bottom_source = source_data.sort_values("paid_conversion_rate").iloc[0]
    top_size      = size_data.sort_values("arpa", ascending=False).iloc[0]
    overall_paid_rate = accounts["current_active_customer"].mean()

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.info(
            f"**{len(accounts):,} total sign-ups → {int(accounts['current_active_customer'].sum()):,} paying customers** ({overall_paid_rate:.0%} overall paid conversion)  \n"
            f"Sign-up volume and revenue contribution don't always match — check each segment below."
        )
        c2.success(
            f"**Best-converting channel: {top_source['acquisition_source']}** ({top_source['paid_conversion_rate']:.0%} paid conversion)  \n"
            f"Invest here before scaling other channels. "
            f"**Lowest: {bottom_source['acquisition_source']}** ({bottom_source['paid_conversion_rate']:.0%}) — diagnose whether it's traffic quality or onboarding friction."
        )
        c3.warning(
            f"**Enterprise ARPA (${size_data.loc[size_data['company_size']=='Enterprise','arpa'].values[0]:,.0f}) is 3.7× SMB (${size_data.loc[size_data['company_size']=='SMB','arpa'].values[0]:,.0f})**  \n"
            f"Segment mix has a bigger impact on total MRR than conversion rate alone — shifting toward larger accounts compounds revenue quickly."
        )
    st.write("")

    # ── Summary table ──────────────────────────────────────────────────────────
    st.subheader("Volume vs. revenue by segment")
    st.caption(
        "More sign-ups doesn't mean more revenue. A channel can drive lots of traffic but still convert poorly. "
        "Compare sign-ups with paid conversion rate and total MRR to find channels that look busy but don't pay off."
    )

    tab1, tab2, tab3 = st.tabs(["By acquisition source", "By company size", "By region"])

    def render_quality_table(df, dim):
        display = df.copy()
        display["Signups"] = display["signups"].map("{:,.0f}".format)
        display["Paid customers"] = display["paid_customers"].map("{:,.0f}".format)
        display["Paid conversion"] = display["paid_conversion_rate"].map("{:.1%}".format)
        display["Avg MRR / account"] = display["arpa"].map(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        display["Total MRR"] = display["total_mrr"].map("${:,.0f}".format)
        col = dim.replace("_", " ").title()
        display = display.rename(columns={dim: col})
        st.dataframe(
            display[[col, "Signups", "Paid customers", "Paid conversion", "Avg MRR / account", "Total MRR"]],
            hide_index=True,
            use_container_width=True,
        )

    with tab1:
        render_quality_table(source_data, "acquisition_source")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                source_data.sort_values("signups"),
                x="signups", y="acquisition_source", orientation="h",
                color_discrete_sequence=[PRIMARY], text_auto=True,
            )
            fig.update_layout(title="Signups")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})
        with col2:
            fig = px.bar(
                source_data.sort_values("total_mrr"),
                x="total_mrr", y="acquisition_source", orientation="h",
                color_discrete_sequence=[TEAL], text_auto="$.2s",
            )
            fig.update_layout(title="Total MRR")
            fig.update_xaxes(tickprefix="$")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})

    with tab2:
        render_quality_table(size_data, "company_size")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(size_data.sort_values("signups"), x="company_size", y="signups", color_discrete_sequence=[PRIMARY], text_auto=True)
            fig.update_layout(title="Signups")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})
        with col2:
            fig = px.bar(size_data.sort_values("total_mrr"), x="company_size", y="total_mrr", color_discrete_sequence=[TEAL], text_auto="$.2s")
            fig.update_layout(title="Total MRR")
            fig.update_yaxes(tickprefix="$")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})

    with tab3:
        render_quality_table(region_data, "region")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(region_data.sort_values("signups"), x="signups", y="region", orientation="h", color_discrete_sequence=[PRIMARY], text_auto=True)
            fig.update_layout(title="Signups")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})
        with col2:
            fig = px.bar(region_data.sort_values("total_mrr"), x="total_mrr", y="region", orientation="h", color_discrete_sequence=[TEAL], text_auto="$.2s")
            fig.update_layout(title="Total MRR")
            fig.update_xaxes(tickprefix="$")
            st.plotly_chart(chart_style(fig, 260), use_container_width=True, config={"displayModeBar": False})

    st.subheader("Account directory")
    st.caption("Full account list with acquisition source, activation status, current plan, and risk level.")
    display = sort_account_directory(accounts)[["org_id", "created_at", "company_size", "acquisition_source", "users", "activated_7d", "current_active_customer", "current_mrr", "risk_segment"]].copy()
    display.columns = ["Org ID", "Created", "Segment", "Source", "Users", "Activated", "Current paid customer", "Current MRR", "Risk segment"]
    display["Created"] = display["Created"].dt.strftime("%Y-%m-%d")
    display["Activated"] = display["Activated"].map({True: "Yes", False: "No"})
    display["Current paid customer"] = display["Current paid customer"].map({True: "Yes", False: "No"})
    display["Current MRR"] = display["Current MRR"].map("${:,.0f}".format)
    st.dataframe(display, hide_index=True, use_container_width=True, height=500)

    st.divider()
    st.subheader("Recommendations")

    by_source = accounts.groupby("acquisition_source").agg(
        signups=("org_id", "size"),
        activation_rate=("activated_7d", "mean"),
        paid_rate=("current_active_customer", "mean"),
    ).reset_index().sort_values("paid_rate", ascending=False)

    top_source = by_source.iloc[0]
    bottom_source = by_source.iloc[-1]
    high_vol_low_paid = by_source.sort_values("signups", ascending=False).iloc[0]

    st.success(
        f"**Focus on quality, not just volume.** "
        f"**{top_source['acquisition_source']}** converts best ({top_source['paid_rate']:.0%} paid conversion) "
        f"— double down here before scaling spend elsewhere. "
        f"**{bottom_source['acquisition_source']}** has the lowest paid conversion ({bottom_source['paid_rate']:.0%}) "
        f"— before investing more here, find out whether it's a traffic-quality issue or an onboarding friction issue."
    )
    st.info(
        "**Next step:** Go to the Activation page to see where each channel drops off — "
        "sign-up volume alone won't tell you which channels bring customers worth keeping."
    )


if __name__ == "__main__":
    main()
