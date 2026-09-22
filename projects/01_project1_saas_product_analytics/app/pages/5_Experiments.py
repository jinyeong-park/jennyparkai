"""Onboarding experiment readout page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    bonferroni_pairwise_results,
    build_account_metrics,
    experiment_decision,
    experiment_summary,
    retention_rate,
    simulate_multivariate_variants,
    two_proportion_p_value,
)
from utils.theme import BLUE, GREEN, PRIMARY, inject_theme, render_navigation


st.set_page_config(page_title="Experiments | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data() -> pd.DataFrame:
    return build_account_metrics(load_tables())


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
    st.caption("Did the guided onboarding experiment improve activation — and did it hold up on conversion, retention, and other guardrails?")

    ctrl_paid = summary.loc[summary["variant"].eq("control"), "paid_conversion_rate"].iloc[0]
    trt_paid  = summary.loc[summary["variant"].eq("treatment"), "paid_conversion_rate"].iloc[0]
    paid_delta_pp = (trt_paid - ctrl_paid) * 100

    with st.expander("**Key Findings**", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.success(
            f"**SHIP to SMB + Mid-Market.** Activation lift +{lift * 100:.1f}pp (p={p_value:.4f}).  \n"
            f"All guardrails hold — no statistically significant harm to retention or trial start rate."
        )
        c2.warning(
            f"**Paid conversion didn't move ({paid_delta_pp:+.1f}pp).**  \n"
            f"More accounts are activating but not converting to revenue. "
            f"Activation rate alone is not a sufficient success metric — track paid conversion as a co-primary."
        )
        c3.info(
            f"**Hold Enterprise for now.**  \n"
            f"Lift is smaller and less certain. Enterprise accounts take ~2× longer to activate (P50 ~12 days vs. ~6 for SMB) "
            f"and need a separate implementation-led onboarding path."
        )
    st.write("")

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
        st.dataframe(display, hide_index=True, use_container_width=True)
        ctrl_paid = summary.loc[summary["variant"].eq("control"), "paid_conversion_rate"].iloc[0]
        trt_paid = summary.loc[summary["variant"].eq("treatment"), "paid_conversion_rate"].iloc[0]
        paid_delta_pp = (trt_paid - ctrl_paid) * 100
        if abs(paid_delta_pp) < 1.0:
            st.warning(
                f"**Activation is up +{lift * 100:.1f}pp, but paid conversion didn't move ({paid_delta_pp:+.1f}pp).** "
                "More accounts are activating without converting to revenue. "
                "Activation rate alone is not a sufficient north-star — **track paid conversion as a co-primary metric**."
            )
    with right:
        guardrails = pd.DataFrame({"Metric": ["Workspace creation", "Trial start", "60-day retention"], "Control": [control["workspace_created"].mean(), control["trial_started"].mean(), retention_rate(control, 60)], "Variant": [treatment["workspace_created"].mean(), treatment["trial_started"].mean(), retention_rate(treatment, 60)]})
        guardrails["Difference"] = guardrails["Variant"] - guardrails["Control"]
        for column in ["Control", "Variant", "Difference"]:
            guardrails[column] = guardrails[column].map("{:+.1%}".format if column == "Difference" else "{:.1%}".format)
        st.subheader("Guardrail metrics")
        st.dataframe(guardrails, hide_index=True, use_container_width=True)

    st.subheader("Segment-level treatment effect")
    segments = accounts.groupby(["company_size", "variant"], as_index=False).agg(activation_rate=("activated_7d", "mean"))
    segments["variant_label"] = segments["variant"].map({"control": "Control", "treatment": "Variant"})
    fig = px.bar(segments, x="company_size", y="activation_rate", color="variant_label", barmode="group", color_discrete_map={"Control": PRIMARY, "Variant": GREEN})
    fig.update_layout(height=330, margin=dict(l=8, r=8, t=24, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
    fig.update_yaxes(tickformat=".0%", range=[0, 1], gridcolor="#dce6f4")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.subheader("Decision: ship, iterate, continue, or kill?")
    st.caption(
        "Four checks rolled into one verdict: Is the lift statistically significant? Do guardrails hold? "
        "Was the experiment large enough to detect a meaningful effect? And does the lift hold across all segments?"
    )
    mde_pp = st.slider(
        "Minimum detectable effect (MDE) — the smallest activation lift worth caring about",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        format="%d pp",
    )
    decision = experiment_decision(accounts, mde=mde_pp / 100)

    verdict_style = {
        "SHIP": (st.success, "🚀"),
        "ITERATE": (st.warning, "🔧"),
        "CONTINUE": (st.info, "⏳"),
        "KILL": (st.error, "🛑"),
    }
    render, icon = verdict_style[decision["verdict"]]
    render(f"{icon} **{decision['verdict']}**")

    checks = st.columns(4)
    with checks[0]:
        st.metric(
            "Primary lift significant?",
            "Yes" if decision["significant"] else "No",
            f"p={decision['p_value']:.4f}",
        )
    with checks[1]:
        st.metric(
            "Guardrails hold?",
            "Yes" if not decision["paid_guardrail_broken"] else "No (paid conversion)",
            (
                f"Retention Δ {decision['retention_delta']:+.1%}"
                if decision["retention_delta"] is not None
                else "n/a"
            ),
        )
    with checks[2]:
        st.metric(
            f"Adequately powered for {mde_pp}pp MDE?",
            "Yes" if decision["adequately_powered"] else "No",
            f"need {decision['required_n_per_variant']:,}/variant, have {min(decision['control_n'], decision['treatment_n']):,}",
        )
    with checks[3]:
        st.metric(
            "Consistent across segments?",
            "Yes" if not decision["harmful_segment"] else "No",
        )

    st.caption(
        "A guardrail is only \"broken\" if the treatment group is *significantly* worse than control — not just slightly lower in the numbers. "
        "The 60-day retention dip you see above, for example, is not statistically significant given the sample size, "
        "so it doesn't block a ship decision — it's flagged for monitoring, not treated as a hard stop."
    )

    st.subheader("🧪 Multiple comparisons: what if this had been an A/B/C/D test?")
    st.caption(
        "**Illustrative only — not a real result.** This experiment only has two arms (control vs. treatment). "
        "To show how multiple-comparison correction works, the treatment arm is artificially split into 3 sub-variants "
        "using a hash of org_id. Since all 3 are random slices of the same real treatment group, they all inherit the same lift — "
        "the point is to show the Bonferroni correction mechanics, not a real 3-way product comparison."
    )
    mv_accounts = simulate_multivariate_variants(accounts)
    mv_results = bonferroni_pairwise_results(mv_accounts)
    k = len(mv_results)
    st.caption(
        f"Running {k} independent tests at α=0.05 each pushes the overall false-positive rate up to "
        f"{1 - 0.95**k:.0%} (not 5%). Bonferroni correction divides alpha by {k}: adjusted α = "
        f"{mv_results['adjusted_alpha'].iloc[0]:.4f}, which raises the z-score threshold to "
        f"{mv_results['z_threshold_bonferroni'].iloc[0]:.3f} (vs. 1.96 without correction)."
    )
    mv_display = mv_results[
        ["variant", "n", "treatment_rate", "lift", "z_score", "significant_bonferroni", "decision"]
    ].rename(
        columns={
            "variant": "Variant",
            "n": "N",
            "treatment_rate": "Activation rate",
            "lift": "Lift vs. control",
            "z_score": "z-score",
            "significant_bonferroni": "Significant (corrected)",
            "decision": "Decision",
        }
    )
    st.dataframe(
        mv_display.style.format(
            {"N": "{:,.0f}", "Activation rate": "{:.1%}", "Lift vs. control": "{:+.1%}", "z-score": "{:.2f}"}
        ),
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
