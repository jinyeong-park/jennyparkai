"""Activation behavior detail page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    KEY_ACTION_EVENTS,
    activation_completion_days,
    activation_speed_by_segment,
    build_account_metrics,
    first_key_action,
    funnel_by_channel,
    milestone_retention,
    mix_rate_decomposition,
    summarize_decomposition,
    time_to_activate_trend,
    two_proportion_p_value,
)
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
    st.caption("Find the early actions that separate accounts who get value from those who don't.")
    st.info("An account is 'activated' if it creates a workspace **and** completes a key product action within 7 days of signing up.")

    # ── Key Findings ─────────────────────────────────────────────────────────────────
    completion = activation_completion_days(events, organizations)
    overall_activation = accounts["activated_7d"].mean()
    best_source = accounts.groupby("acquisition_source")["activated_7d"].mean().idxmax()
    best_source_rate = accounts.groupby("acquisition_source")["activated_7d"].mean().max()
    channel_funnel_tldr = funnel_by_channel(accounts).set_index("acquisition_source")
    weakest_channel = channel_funnel_tldr["workspace_to_integration_rate"].idxmin()

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.success(
            f"**Overall activation rate: {overall_activation:.0%}**  \n"
            f"Median time to activate: {completion['days_to_activation'].median():.1f} days.  \n"
            f"Once accounts start onboarding, most complete it — the gap is getting them started."
        )
        c2.warning(
            f"**Biggest funnel leak: {weakest_channel}**  \n"
            f"Drops to {channel_funnel_tldr.loc[weakest_channel, 'workspace_to_integration_rate']:.0%} at the workspace → integration step.  \n"
            f"High intent — fix the friction, don't cut the channel."
        )
        c3.info(
            f"**Best-converting channel: {best_source}** ({best_source_rate:.0%} activation rate)  \n"
            f"Activation rate alone doesn't tell the full story — check the Activated → Paid column in the funnel table below."
        )
    st.write("")

    kpis = st.columns(3)
    with kpis[0]:
        st.metric("Activation rate", f"{accounts['activated_7d'].mean():.1%}")
    with kpis[1]:
        st.metric("Workspace creation", f"{accounts['workspace_created'].mean():.1%}")
    with kpis[2]:
        st.metric("Median time to activation", f"{completion['days_to_activation'].median():.1f} days")

    left, right = st.columns(2)
    with left:
        fig = px.bar(activation_by_size, x="company_size", y="activation_rate", color_discrete_sequence=[PRIMARY], text_auto=".1%")
        fig.update_layout(title="Activation rate by company size")
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(chart_style(fig), use_container_width=True, config={"displayModeBar": False})
    with right:
        fig = px.bar(activation_by_source, x="activation_rate", y="acquisition_source", orientation="h", color_discrete_sequence=[TEAL], text_auto=".1%")
        fig.update_layout(title="Activation rate by acquisition source")
        fig.update_xaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(chart_style(fig), use_container_width=True, config={"displayModeBar": False})

    st.subheader("Early product action adoption")
    action_names = ["workspace_created", *sorted(KEY_ACTION_EVENTS)]
    early_events = events.merge(organizations[["org_id", "created_at"]], on="org_id")
    early_events["days_from_signup"] = (early_events["event_timestamp"] - early_events["created_at"]).dt.total_seconds().div(86_400)
    adoption = early_events.loc[early_events["event_name"].isin(action_names) & early_events["days_from_signup"].between(0, 7)].groupby("event_name")["org_id"].nunique().reindex(action_names, fill_value=0).div(len(accounts)).rename("adoption_rate").reset_index()
    adoption["event_name"] = adoption["event_name"].str.replace("_", " ").str.title()
    fig = px.bar(adoption, x="event_name", y="adoption_rate", color_discrete_sequence=[GREEN], text_auto=".1%")
    fig.update_layout(title="Share of accounts completing each action in the first 7 days")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    st.plotly_chart(chart_style(fig, 300), use_container_width=True, config={"displayModeBar": False})

    st.subheader("Funnel drop-off by acquisition channel")
    st.caption(
        "Overall activation rate can hide *where* a channel loses people. "
        "Read left to right: Workspace (did they start onboarding?) → Workspace→Integration (did they clear the technical step?) → Activated→Paid (did they convert?). "
        "A channel that starts well but drops at the middle step points to onboarding friction. "
        "A channel that's weak at every step points to lower-quality traffic."
    )
    channel_funnel = funnel_by_channel(accounts).set_index("acquisition_source")
    display_funnel = channel_funnel[
        [
            "signups",
            "workspace_rate",
            "workspace_to_integration_rate",
            "activation_rate",
            "activated_to_paid_rate",
        ]
    ].rename(
        columns={
            "signups": "Signups",
            "workspace_rate": "Workspace",
            "workspace_to_integration_rate": "Workspace → Integration",
            "activation_rate": "Activated (7d)",
            "activated_to_paid_rate": "Activated → Paid",
        }
    )
    st.dataframe(
        display_funnel.style.format(
            {
                "Signups": "{:,.0f}",
                "Workspace": "{:.1%}",
                "Workspace → Integration": "{:.1%}",
                "Activated (7d)": "{:.1%}",
                "Activated → Paid": "{:.1%}",
            }
        ),
        use_container_width=True,
    )
    weakest_step = channel_funnel["workspace_to_integration_rate"].idxmin()
    st.caption(
        f"Biggest single-step leak: **{weakest_step}** loses the most accounts between workspace "
        f"creation and integration ({channel_funnel.loc[weakest_step, 'workspace_to_integration_rate']:.0%} "
        "carry through)."
    )

    first_actions = first_key_action(events, organizations)

    st.subheader("Which first action predicts retention best?")
    st.caption(
        "Grouped by the *first* key action each account completed — not whether they eventually did all of them. "
        "This isolates which single action matters most for retention."
    )
    milestones = milestone_retention(accounts, first_actions)
    fig = px.bar(
        milestones,
        x="first_action",
        y="retention_60d_rate",
        color_discrete_sequence=[BLUE],
        text_auto=".1%",
    )
    fig.update_layout(title="60-day retention by first activation milestone")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(chart_style(fig, 300), use_container_width=True, config={"displayModeBar": False})
    top_milestone = milestones.iloc[0]
    bottom_milestone = milestones.iloc[-1]
    spread_pp = (top_milestone["retention_60d_rate"] - bottom_milestone["retention_60d_rate"]) * 100
    st.caption(
        f"**{top_milestone['first_action']}** is the strongest signal: accounts whose first key action was "
        f"this one retain at {top_milestone['retention_60d_rate']:.0%} after 60 days, across "
        f"{int(top_milestone['orgs']):,} accounts."
    )
    st.warning(
        f"**Interpret with caution — this is correlation, not causation.** "
        f"The spread between best and worst first action is only {spread_pp:.1f}pp. "
        "More importantly, accounts that connect an integration on day 1 are likely already more committed buyers — "
        "the higher retention may reflect *who* they are, not *what* they did. "
        "A causal test would require randomizing which action the onboarding flow prompts first and "
        "comparing retention across arms. Without that, avoid re-ordering onboarding based on this chart alone."
    )

    st.subheader("Time-to-activate: is onboarding getting faster?")
    st.caption(
        "Median (P50) and P90 days from signup to first key action, by signup month. "
        "We use the median rather than the average — a few slow accounts would skew the average and hide the typical experience."
    )
    trend = time_to_activate_trend(accounts, first_actions)
    trend_long = trend.melt(
        id_vars=["signup_period", "activated_orgs"],
        value_vars=["p50_days", "p90_days"],
        var_name="percentile",
        value_name="days",
    )
    trend_long["percentile"] = trend_long["percentile"].map({"p50_days": "P50", "p90_days": "P90"})
    fig = px.line(
        trend_long,
        x="signup_period",
        y="days",
        color="percentile",
        color_discrete_sequence=[PRIMARY, TEAL],
        markers=True,
    )
    fig.update_layout(title="Days to first key action, by signup cohort")
    st.plotly_chart(chart_style(fig, 320), use_container_width=True, config={"displayModeBar": False})

    midpoint = len(trend) // 2
    earlier_p50 = trend["p50_days"].iloc[:midpoint].mean()
    later_p50 = trend["p50_days"].iloc[midpoint:].mean()
    delta = later_p50 - earlier_p50
    if abs(delta) < 1:
        trend_phrase = f"stable — the first- and second-half cohort average P50 differ by only {delta:+.1f} days"
    elif delta < 0:
        trend_phrase = f"getting **faster** — later cohorts activate {abs(delta):.1f} days sooner on average (P50)"
    else:
        trend_phrase = f"getting **slower** — later cohorts take {delta:.1f} more days on average (P50)"
    st.caption(
        f"P50 ranges {trend['p50_days'].min():.1f}–{trend['p50_days'].max():.1f} days across cohorts. "
        f"Onboarding speed looks {trend_phrase}."
    )

    st.subheader("Activation speed by company size")
    st.caption(
        "Activation rate alone can be misleading — a segment might activate just as often, but take much longer. "
        "This table pairs rate with speed (P50/P90 days) so both are visible."
    )
    speed_by_size = activation_speed_by_segment(accounts, first_actions, dimension="company_size").set_index(
        "company_size"
    )
    st.dataframe(
        speed_by_size.rename(
            columns={
                "signups": "Signups",
                "activation_rate": "Activation rate",
                "p50_days_to_first_action": "P50 days",
                "p90_days_to_first_action": "P90 days",
            }
        ).style.format(
            {
                "Signups": "{:,.0f}",
                "Activation rate": "{:.1%}",
                "P50 days": "{:.1f}",
                "P90 days": "{:.1f}",
            }
        ),
        use_container_width=True,
    )

    st.subheader("Root Cause Analysis — Rate vs. Mix Decomposition")
    st.caption(
        "When overall activation changes month over month, it could mean two different things: "
        "activation improved or worsened *within* a segment (**rate effect** — product/UX owns this), "
        "or the *mix* of who signed up shifted toward easier- or harder-to-activate segments (**mix effect** — acquisition owns this). "
        "An interaction term captures segments where both changed at once. The three effects always sum to the total observed change."
    )
    monthly = accounts.assign(month=accounts["created_at"].dt.to_period("M").dt.start_time)
    month_rates = monthly.groupby("month")["activated_7d"].agg(rate="mean", signups="size")
    month_rates["change"] = month_rates["rate"].diff()
    months = list(month_rates.index)
    default_prior = months[months.index(month_rates["change"].idxmin()) - 1]

    controls = st.columns(2)
    with controls[0]:
        prior_month = st.selectbox(
            "Compare month (prior)",
            months[:-1],
            index=months[:-1].index(default_prior),
            format_func=lambda value: value.strftime("%b %Y"),
            help="Defaults to the month before the largest month-over-month drop.",
        )
    with controls[1]:
        dimension = st.selectbox("Segment by", ["acquisition_source", "company_size"])
    current_month = months[months.index(prior_month) + 1]

    decomposition = mix_rate_decomposition(accounts, dimension, prior_month, current_month)
    summary = summarize_decomposition(decomposition)
    prior_frame = monthly.loc[monthly["month"].eq(prior_month)]
    current_frame = monthly.loc[monthly["month"].eq(current_month)]
    change_p_value = two_proportion_p_value(
        int(prior_frame["activated_7d"].sum()), len(prior_frame),
        int(current_frame["activated_7d"].sum()), len(current_frame),
    )

    kpis = st.columns(4)
    kpis[0].metric("Overall change", f"{summary['total_change'] * 100:+.1f} pp")
    kpis[1].metric("Rate effect", f"{summary['rate_effect'] * 100:+.1f} pp")
    kpis[2].metric("Mix effect", f"{summary['mix_effect'] * 100:+.1f} pp")
    kpis[3].metric("Interaction", f"{summary['interaction_effect'] * 100:+.1f} pp")
    st.markdown(f"**Diagnosis: {summary['diagnosis']}**")

    display = decomposition[
        [dimension, "prior_rate", "cur_rate", "prior_mix", "cur_mix", "rate_effect", "mix_effect", "interaction_effect", "total_contribution"]
    ].set_index(dimension)
    display.columns = ["Prior rate", "Current rate", "Prior mix", "Current mix", "Rate effect", "Mix effect", "Interaction", "Total contribution"]
    st.dataframe(display.style.format("{:.1%}"), use_container_width=True)

    comparisons = len(months) - 1
    st.caption(
        f"Before trusting any diagnosis, check the change itself is real: {prior_month.strftime('%b')} \u2192 "
        f"{current_month.strftime('%b %Y')} is {change_p_value:.3f} on a two-proportion test. But this looks at "
        f"the largest of {comparisons} month-over-month comparisons, so the multiple-comparisons bar applies "
        f"(Bonferroni: p < {0.05 / comparisons:.4f}). A drop that clears 0.05 but not that bar, or that "
        "rebounds the next month, may just be noise \u2014 decomposition tells you *where* a change came from, "
        "not whether it was real."
    )


if __name__ == "__main__":
    main()
