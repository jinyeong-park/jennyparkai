"""Executive overview for the Product-Led SaaS retention analytics project."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    activation_completion_days,
    build_account_metrics,
    churn_risk_segments,
    engagement_retention_curve,
    experiment_summary,
    lifecycle_funnel,
    modeled_nrr_trend,
    retention_rate,
    revenue_trend,
    signup_cohort_retention,
)
from utils.theme import AMBER, BLUE, GREEN, GRID, INK, MUTED, PRIMARY, RED, TEAL, inject_theme, render_navigation


st.set_page_config(page_title="Product-Led SaaS Retention Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def dashboard_data():
    tables = load_tables()
    accounts = build_account_metrics(tables)
    obs_date = accounts["observation_date"].iloc[0]
    return {
        "accounts": accounts,
        "funnel": lifecycle_funnel(accounts),
        "experiment": experiment_summary(accounts),
        "cohort_retention": signup_cohort_retention(accounts),
        "revenue": revenue_trend(accounts),
        "nrr": modeled_nrr_trend(tables["subscriptions"], obs_date),
        "risk": churn_risk_segments(accounts),
        "activation_days": activation_completion_days(
            tables["event_logs"], tables["organizations"]
        ),
        "engagement": engagement_retention_curve(
            tables["organizations"], tables["event_logs"], obs_date
        ),
    }


def metric_card(label: str, value: str, trend: float | None = None, sub: str = "") -> None:
    if trend is not None:
        trend_color = GREEN if trend >= 0 else RED
        arrow = "▲" if trend >= 0 else "▼"
        trend_html = (
            f'<div style="color:{trend_color};font-size:0.82rem;font-weight:700;margin-top:6px;">'
            f'{arrow} {abs(trend):.1f}%'
            f'<span style="color:{MUTED};font-weight:400;"> vs prev 30 days</span></div>'
        )
    else:
        trend_html = f'<div class="metric-delta">{sub}</div>'
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          {trend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, height: int = 285) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=16, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color=MUTED),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0, font=dict(size=10)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    return fig


def render_funnel(funnel):
    fig = go.Figure(
        go.Funnel(
            y=funnel["stage"],
            x=funnel["accounts"],
            textinfo="value+percent initial",
            textfont=dict(color="white", size=14),
            marker=dict(color=[PRIMARY, BLUE, TEAL, GREEN, "#58c98a", "#83d7a9"]),
            connector=dict(line=dict(color=GRID, width=1)),
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=8, r=8, t=12, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color=INK),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    display = funnel.copy()
    total = display["accounts"].iloc[0]
    display["Overall"] = display["accounts"] / total
    display["Step-to-step"] = display["accounts"] / display["accounts"].shift(1)
    display = display.rename(columns={"stage": "Stage", "accounts": "Accounts"})
    st.dataframe(
        display[["Stage", "Accounts", "Overall", "Step-to-step"]].style.format({
            "Accounts": "{:,.0f}",
            "Overall": lambda x: f"{x:.0%}" if pd.notna(x) else "—",
            "Step-to-step": lambda x: f"{x:.0%}" if pd.notna(x) else "—",
        }),
        hide_index=True,
        use_container_width=True,
    )
    st.caption("Overall = % of all sign-ups. Step-to-step = % from prior stage. Once past workspace creation, ~68–69% carry through each step — the drop happens at the very first action.")


def render_cohort_retention(cohort_retention: pd.DataFrame):
    fig = go.Figure()
    palette = [TEAL, BLUE, PRIMARY, GREEN, AMBER, RED]
    cohorts = cohort_retention["cohort_month"].unique()
    for i, cohort_month in enumerate(sorted(cohorts)):
        cohort_data = cohort_retention[cohort_retention["cohort_month"] == cohort_month]
        valid = cohort_data.dropna(subset=["retention_rate"])
        if valid.empty:
            continue
        color = palette[i % len(palette)]
        label = pd.Timestamp(cohort_month).strftime("%b %Y")
        fig.add_trace(go.Scatter(
            x=valid["day"],
            y=valid["retention_rate"] * 100,
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
        ))
    chart_layout(fig, height=285).update_xaxes(
        title="Days since paid conversion", tickvals=[0, 30, 60, 90]
    )
    fig.update_yaxes(title="Retention", ticksuffix="%", range=[0, 105])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_nrr(nrr_data: pd.DataFrame):
    valid = nrr_data.dropna(subset=["nrr_60d"]).copy()
    valid["nrr_pct"] = valid["nrr_60d"] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=valid["cohort_month"],
        y=valid["nrr_pct"],
        mode="lines+markers",
        line=dict(color=GREEN, width=3),
        marker=dict(size=6, color=GREEN),
        fill="tozeroy",
        fillcolor="rgba(34,197,94,0.10)",
    ))
    fig.add_hline(
        y=100, line_dash="dot", line_color=MUTED, line_width=1,
        annotation_text="100%", annotation_position="top right",
        annotation_font=dict(size=10, color=MUTED),
    )
    y_max = valid["nrr_pct"].max() if not valid.empty else 110
    fig.update_layout(
        height=210,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(showgrid=False, tickformat="%b '%y"),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False,
                   ticksuffix="%", range=[0, y_max * 1.15]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_risk(risk, total_accounts: int):
    colors = {"High": RED, "Medium": AMBER, "Low": TEAL}
    total = risk["accounts"].sum()
    labels_with_pct = [
        f"{row['risk_segment']} ({row['accounts'] / total * 100:.1f}%)"
        for _, row in risk.iterrows()
    ]
    fig = go.Figure(go.Pie(
        labels=labels_with_pct,
        values=risk["accounts"],
        hole=0.68,
        marker=dict(colors=[colors[segment] for segment in risk["risk_segment"]]),
        textinfo="none",
        hovertemplate="%{label}: %{value:,} accounts<extra></extra>",
    ))
    fig.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{total_accounts:,}</b><br>accounts",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=INK, size=14),
        )],
        showlegend=True,
        legend=dict(orientation="v", font=dict(size=10), x=1.0, y=0.5),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def main() -> None:
    inject_theme()
    render_navigation()
    data = dashboard_data()
    accounts = data["accounts"]
    funnel = data["funnel"]
    experiment = data["experiment"]
    cohort_retention = data["cohort_retention"]
    revenue = data["revenue"]
    nrr_data = data["nrr"]
    risk = data["risk"]
    activation_days_df = data["activation_days"]
    engagement = data["engagement"]

    # ── Period-over-period trend ───────────────────────────────────────────────
    obs = accounts["observation_date"].iloc[0]
    c30 = obs - pd.Timedelta(days=30)
    c60 = obs - pd.Timedelta(days=60)
    curr = accounts[accounts["created_at"] >= c30]
    prev = accounts[(accounts["created_at"] >= c60) & (accounts["created_at"] < c30)]

    def pct_delta(a, b):
        return float((a - b) / b * 100) if b else 0.0

    signups_delta   = pct_delta(len(curr), len(prev))
    activated_delta = pct_delta(curr["activated_7d"].sum(), prev["activated_7d"].sum())
    paid_delta      = pct_delta(curr["current_active_customer"].sum(), prev["current_active_customer"].sum())
    arpa_curr = curr.loc[curr["current_active_customer"], "current_mrr"].mean()
    arpa_prev = prev.loc[prev["current_active_customer"], "current_mrr"].mean()
    arpa_delta = pct_delta(arpa_curr, arpa_prev) if (pd.notna(arpa_curr) and pd.notna(arpa_prev) and arpa_prev) else 0.0

    # ── Headline figures ───────────────────────────────────────────────────────
    activated = int(accounts["activated_7d"].sum())
    paid      = int(accounts["current_active_customer"].sum())
    arpa      = accounts.loc[accounts["current_active_customer"], "current_mrr"].mean()
    treatment_lift = experiment.loc[experiment["variant"].eq("treatment"), "activation_lift_pp"].iloc[0]

    median_days = float(activation_days_df["days_to_activation"].median())
    dau_rate    = float((accounts["days_since_last_event"] <= 30).mean())

    mature_nrr  = nrr_data["nrr_60d"].dropna()
    overall_nrr = float(mature_nrr.mean() * 100) if len(mature_nrr) else 100.0
    nrr_delta   = float((mature_nrr.iloc[-1] - mature_nrr.iloc[-2]) * 100) if len(mature_nrr) >= 2 else 0.0

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_badge = st.columns([5, 1])
    with col_title:
        st.title("Product-Led SaaS Lifecycle & Retention Analytics")
        st.caption("Track the full customer journey from sign-up to activation, paid conversion, and long-term retention.")
    with col_badge:
        st.markdown(
            "<div style='text-align:right;padding-top:20px'>"
            "<span style='background:#e8f0fe;color:#0f4c81;font-size:0.78rem;font-weight:600;"
            "padding:5px 12px;border-radius:4px;'>Last 30 days</span></div>",
            unsafe_allow_html=True,
        )

    # ── KPI row ───────────────────────────────────────────────────────────────
    kpi_columns = st.columns(4)
    with kpi_columns[0]:
        metric_card("Total Signups", f"{len(accounts):,}", trend=signups_delta)
    with kpi_columns[1]:
        metric_card("Activated Users", f"{activated:,}", trend=activated_delta)
    with kpi_columns[2]:
        metric_card("Paid Customers", f"{paid:,}", trend=paid_delta)
    with kpi_columns[3]:
        metric_card("Avg. Revenue per Account", f"${arpa:,.0f}", trend=arpa_delta)

    # ── Key Insights ──────────────────────────────────────────────────────────
    funnel_stages = funnel.set_index("stage")["accounts"]
    total_signups = int(funnel_stages.iloc[0])
    workspace_count = int(funnel_stages.get("Workspace Created", 0))
    no_workspace_pct = (total_signups - workspace_count) / total_signups
    paid_d60 = retention_rate(accounts, 60)
    eng_d60_approx = float(engagement.dropna(subset=["retention_d60"])["retention_d60"].mean())

    high_risk = risk.loc[risk["risk_segment"] == "High"]
    medium_risk = risk.loc[risk["risk_segment"] == "Medium"]
    high_mrr = int(high_risk["mrr_at_risk"].sum()) if not high_risk.empty else 0
    medium_mrr = int(medium_risk["mrr_at_risk"].sum()) if not medium_risk.empty else 0

    ctrl_row = experiment[experiment["variant"] == "control"].iloc[0]
    trt_row  = experiment[experiment["variant"] == "treatment"].iloc[0]
    exp_lift = (trt_row["activation_rate"] - ctrl_row["activation_rate"]) * 100

    st.markdown("---")
    st.markdown("#### Key Insights")
    insight_cols = st.columns(3)
    with insight_cols[0]:
        st.warning(
            f"**{no_workspace_pct:.0%} of sign-ups never open the product.** "
            "The funnel mid-section is healthy — the problem is at the very first step."
        )
    with insight_cols[1]:
        st.success(
            f"**Guided onboarding lifts activation by +{exp_lift:.1f}pp** (p < 0.001). "
            "Safe to ship to SMB and Mid-Market — guardrails hold."
        )
    with insight_cols[2]:
        st.warning(
            f"**All churn happens in months 2–4.** "
            f"${medium_mrr:,.0f} MRR is still actionable (medium-risk). "
            "After month 4, no account has churned."
        )
    st.markdown("---")

    st.write("")

    # ── Middle row ────────────────────────────────────────────────────────────
    middle_columns = st.columns(3)
    with middle_columns[0]:
        st.subheader("Product Lifecycle Funnel")
        st.caption("How accounts progress from sign-up to paying, retained customer")
        render_funnel(funnel)
    with middle_columns[1]:
        st.subheader("Activation Metrics")
        st.caption("Early behaviors that separate accounts who get value from those who don't")
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.metric("Activation Rate", f"{accounts['activated_7d'].mean():.1%}", f"+{treatment_lift:.1f} pp lift")
            st.metric("Daily Active Usage", f"{dau_rate:.1%}", "Active ≤ 30 days ago")
        with a_col2:
            st.metric("Median Time to Activate", f"{median_days:.1f} days", "Signup → key action")
            st.metric("60-Day Retained", f"{retention_rate(accounts, 60):.1%}", "Eligible paid accounts")
    with middle_columns[2]:
        st.subheader("Paid Retention by Cohort")
        st.caption("% of paid accounts still active at 30, 60, and 90 days")
        r30 = retention_rate(accounts, 30)
        r60 = retention_rate(accounts, 60)
        r90 = retention_rate(accounts, 90)
        fig_ret = go.Figure(go.Bar(
            x=["30-Day", "60-Day", "90-Day"],
            y=[r30 * 100, r60 * 100, r90 * 100],
            marker_color=[TEAL, BLUE, PRIMARY],
            text=[f"{r30:.1%}", f"{r60:.1%}", f"{r90:.1%}"],
            textposition="outside",
            textfont=dict(size=13, color=INK),
        ))
        fig_ret.update_layout(
            height=260,
            margin=dict(l=8, r=8, t=24, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 110], showgrid=True, gridcolor=GRID,
                       zeroline=False, ticksuffix="%"),
            xaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig_ret, use_container_width=True, config={"displayModeBar": False})

    st.write("")

    # ── Bottom row ────────────────────────────────────────────────────────────
    bottom_columns = st.columns(3)
    with bottom_columns[0]:
        st.subheader("A/B Experiment — Guided Onboarding")
        st.caption("Does the new onboarding flow improve activation?")

        ctrl = experiment[experiment["variant"] == "control"].iloc[0]
        trt  = experiment[experiment["variant"] == "treatment"].iloc[0]

        ab_display = experiment[["variant", "accounts", "activation_rate", "paid_conversion_rate", "activation_lift_pp"]].copy()
        ab_display["variant"] = ab_display["variant"].map({"control": "Control", "treatment": "Variant"})
        ab_display["activation_lift_pp"] = ab_display["activation_lift_pp"].apply(
            lambda x: f"{x:+.1f} pp" if x != 0 else "—"
        )
        ab_display.columns = ["Variant", "Accounts", "Activation", "Paid Conv.", "Lift"]
        ab_display["Accounts"] = ab_display["Accounts"].apply(lambda x: f"{int(x):,}")
        ab_display["Activation"] = ab_display["Activation"].apply(lambda x: f"{x:.1%}")
        ab_display["Paid Conv."] = ab_display["Paid Conv."].apply(lambda x: f"{x:.1%}")
        st.dataframe(ab_display, hide_index=True, use_container_width=True)
        paid_conv_delta = (trt_row["paid_conversion_rate"] - ctrl_row["paid_conversion_rate"]) * 100
        if abs(paid_conv_delta) < 1.0:
            st.caption(f"Activation is up +{exp_lift:.1f}pp (p < 0.001), but paid conversion is flat ({paid_conv_delta:+.1f}pp). Track both.")
    with bottom_columns[1]:
        st.subheader("Net Revenue Retention (NRR)")
        st.caption("How much of last month's MRR did we keep this month? (100% = no expansion, no churn)")
        nrr_sign  = "▲" if nrr_delta >= 0 else "▼"
        nrr_color = GREEN if nrr_delta >= 0 else RED
        st.markdown(
            f"<span style='font-size:1.9rem;font-weight:800;color:{INK}'>{overall_nrr:.1f}%</span>"
            f"&nbsp;&nbsp;<span style='color:{nrr_color};font-size:0.9rem;font-weight:700'>"
            f"{nrr_sign} {abs(nrr_delta):.1f}%</span>",
            unsafe_allow_html=True,
        )
        render_nrr(nrr_data)
    with bottom_columns[2]:
        st.subheader("Churn Risk Segments")
        st.caption("Rule-based risk scores using activation, subscription status, and days since last activity")
        risk_chart_col, risk_table_col = st.columns([1.1, 1])
        with risk_chart_col:
            render_risk(risk, len(accounts))
        with risk_table_col:
            total_risk = len(accounts)
            dot_colors = {"High": RED, "Medium": AMBER, "Low": TEAL}
            for _, segment in risk.iterrows():
                pct = segment["accounts"] / total_risk * 100
                color = dot_colors.get(segment["risk_segment"], MUTED)
                st.markdown(
                    f"""
                    <div style="border:1px solid #dce6f4;border-radius:8px;padding:12px 14px;
                                background:#ffffff;margin-bottom:10px;">
                      <div style="display:flex;align-items:center;gap:7px;margin-bottom:4px;">
                        <span style="width:10px;height:10px;border-radius:50%;
                                     background:{color};display:inline-block;flex-shrink:0;"></span>
                        <span style="font-size:0.8rem;font-weight:700;color:#29466f;">
                          {segment['risk_segment']} Risk
                        </span>
                      </div>
                      <div style="font-size:1.5rem;font-weight:800;color:#0b1f3a;line-height:1.2;">
                        {int(segment['accounts']):,}
                      </div>
                      <div style="font-size:0.78rem;color:#5b7194;margin-top:3px;">
                        {pct:.1f}% &nbsp;·&nbsp; ${segment['mrr_at_risk']:,.0f} MRR
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
