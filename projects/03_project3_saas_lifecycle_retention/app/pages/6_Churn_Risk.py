"""Churn risk and customer-success prioritization page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import build_account_metrics, churn_risk_segments
from utils.theme import AMBER, RED, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Churn Risk | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data() -> pd.DataFrame:
    return build_account_metrics(load_tables())


def main() -> None:
    inject_theme()
    render_navigation()
    accounts = page_data()
    risk = churn_risk_segments(accounts)
    st.title("Churn Risk")
    st.caption("Prioritize customer-success outreach using transparent behavioral and subscription risk signals.")

    left, right = st.columns([1, 1.5])
    with left:
        colors = {"High": RED, "Medium": AMBER, "Low": TEAL}
        fig = px.pie(risk, values="accounts", names="risk_segment", hole=0.62, color="risk_segment", color_discrete_map=colors)
        fig.update_layout(height=310, margin=dict(l=8, r=8, t=20, b=8), paper_bgcolor="rgba(0,0,0,0)", legend_title_text="")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with right:
        st.subheader("Risk segment counts")
        display = risk.copy()
        display["mrr_at_risk"] = display["mrr_at_risk"].map("${:,.0f}".format)
        display["average_risk_score"] = display["average_risk_score"].map("{:.0f}".format)
        display.columns = ["Risk segment", "Accounts", "MRR exposure", "Average score"]
        st.dataframe(display, hide_index=True, width="stretch")
        st.subheader("Risk drivers")
        st.write("High risk combines churned or non-subscribed status, no 7-day activation, failed 60-day retention for horizon-eligible accounts, and long gaps since the last product event. Scores are rules-based for transparent prioritization, not a predictive churn model.")

    st.subheader("At-risk accounts")
    at_risk = accounts.loc[accounts["risk_segment"].isin(["High", "Medium"]), ["org_id", "company_size", "acquisition_source", "plan_type", "status", "activated_7d", "days_since_last_event", "current_mrr", "risk_score", "risk_segment"]].sort_values(["risk_score", "current_mrr"], ascending=False)
    display = at_risk.copy()
    display.columns = ["Org ID", "Segment", "Source", "Plan", "Subscription status", "Activated", "Days since last event", "Current MRR", "Risk score", "Risk segment"]
    display["Activated"] = display["Activated"].map({True: "Yes", False: "No"})
    display["Current MRR"] = display["Current MRR"].map("${:,.0f}".format)
    st.dataframe(display, hide_index=True, width="stretch", height=400)

    st.subheader("Recommended customer success actions")
    actions = pd.DataFrame({"Risk segment": ["High", "Medium", "Low"], "Recommended action": ["Start a proactive save play: confirm business value, address the activation gap, and schedule an executive check-in for paid accounts.", "Run a scaled re-engagement sequence with a use-case reminder, training offer, and product-adoption review.", "Maintain lifecycle education and identify expansion signals; no immediate retention intervention required."]})
    st.dataframe(actions, hide_index=True, width="stretch")


if __name__ == "__main__":
    main()
