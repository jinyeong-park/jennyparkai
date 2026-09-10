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
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


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
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


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
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


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
        st.caption("Understand how accounts find value, activate, and stay so product teams can grow revenue and reduce churn.")
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

    st.write("")

    # ── Middle row ────────────────────────────────────────────────────────────
    middle_columns = st.columns(3)
    with middle_columns[0]:
        st.subheader("Product Lifecycle Funnel")
        st.caption("From signup through 60-day retained accounts")
        render_funnel(funnel)
    with middle_columns[1]:
        st.subheader("Activation Metrics")
        st.caption("Early behaviors tied to durable customer value")
        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.metric("Activation Rate", f"{accounts['activated_7d'].mean():.1%}", f"+{treatment_lift:.1f} pp lift")
            st.metric("Daily Active Usage", f"{dau_rate:.1%}", "Active ≤ 30 days ago")
        with a_col2:
            st.metric("Median Time to Activate", f"{median_days:.1f} days", "Signup → key action")
            st.metric("60-Day Retained", f"{retention_rate(accounts, 60):.1%}", "Eligible paid accounts")
    with middle_columns[2]:
        st.subheader("Cohort Retention")
        st.caption("Paid accounts retained at each horizon")
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
        st.subheader("A/B Experiment Performance")
        st.caption("Onboarding treatment impact on account activation")

        ctrl = experiment[experiment["variant"] == "control"].iloc[0]
        trt  = experiment[experiment["variant"] == "treatment"].iloc[0]

        def status_badge(lift):
            if lift > 0:
                return f'<span style="background:#dcfce7;color:#16a34a;font-size:0.72rem;font-weight:700;padding:2px 9px;border-radius:20px;">Growing</span>'
            return f'<span style="background:#f1f5f9;color:#64748b;font-size:0.72rem;font-weight:700;padding:2px 9px;border-radius:20px;">Baseline</span>'

        def lift_html(val):
            if val == 0:
                return '<span style="color:#94a3b8;">—</span>'
            color = GREEN if val > 0 else RED
            return f'<span style="color:{color};font-weight:700;">{val:+.1f} pp</span>'

        rows = [
            ("Control",  ctrl["accounts"], ctrl["activation_rate"], ctrl["paid_conversion_rate"], ctrl["activation_lift_pp"]),
            ("Variant",  trt["accounts"],  trt["activation_rate"],  trt["paid_conversion_rate"],  trt["activation_lift_pp"]),
        ]

        table_html = """
        <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
          <thead>
            <tr style="border-bottom:2px solid #dce6f4;">
              <th style="text-align:left;padding:6px 8px;color:#5b7194;font-weight:600;">Variant</th>
              <th style="text-align:right;padding:6px 8px;color:#5b7194;font-weight:600;">Accounts</th>
              <th style="text-align:right;padding:6px 8px;color:#5b7194;font-weight:600;">Activation</th>
              <th style="text-align:right;padding:6px 8px;color:#5b7194;font-weight:600;">Conv. Rate</th>
              <th style="text-align:right;padding:6px 8px;color:#5b7194;font-weight:600;">Lift</th>
              <th style="text-align:center;padding:6px 8px;color:#5b7194;font-weight:600;">Status</th>
            </tr>
          </thead>
          <tbody>
        """
        for i, (label, n_acct, act, conv, lft) in enumerate(rows):
            bg = "#f8faff" if i % 2 == 0 else "#ffffff"
            table_html += f"""
            <tr style="border-bottom:1px solid #eef2f8;background:{bg};">
              <td style="padding:10px 8px;font-weight:700;color:#0b1f3a;">{label}</td>
              <td style="padding:10px 8px;text-align:right;color:#29466f;">{int(n_acct):,}</td>
              <td style="padding:10px 8px;text-align:right;color:#0b1f3a;font-weight:600;">{act:.1%}</td>
              <td style="padding:10px 8px;text-align:right;color:#0b1f3a;font-weight:600;">{conv:.1%}</td>
              <td style="padding:10px 8px;text-align:right;">{lift_html(lft)}</td>
              <td style="padding:10px 8px;text-align:center;">{status_badge(lft)}</td>
            </tr>
            """
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
    with bottom_columns[1]:
        st.subheader("Net Revenue Retention (NRR)")
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
        st.caption("Accounts prioritized by product and subscription risk signals")
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
