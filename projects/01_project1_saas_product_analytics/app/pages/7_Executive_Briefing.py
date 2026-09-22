"""Executive briefing — narrative summary of the full lifecycle analysis."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.data_loader import load_tables
from utils.metrics import (
    build_account_metrics,
    churn_risk_segments,
    engagement_retention_curve,
    experiment_summary,
    funnel_by_channel,
    lifecycle_funnel,
    retention_rate,
)
from utils.theme import inject_theme, render_navigation

st.set_page_config(page_title="Executive Briefing | Lifecycle Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def page_data():
    tables = load_tables()
    accounts = build_account_metrics(tables)
    return accounts, tables["organizations"], tables["event_logs"]


def main() -> None:
    inject_theme()
    render_navigation()
    accounts, organizations, event_logs = page_data()

    funnel = lifecycle_funnel(accounts)
    experiment = experiment_summary(accounts)
    risk = churn_risk_segments(accounts)
    channel_funnel = funnel_by_channel(accounts)

    total = int(funnel["accounts"].iloc[0])
    paid_count = int(funnel.loc[funnel["stage"] == "Paid Customers", "accounts"].iloc[0])
    retained_count = int(funnel.loc[funnel["stage"] == "Retained 60D", "accounts"].iloc[0])

    ctrl = experiment.loc[experiment["variant"].eq("control")].iloc[0]
    trt = experiment.loc[experiment["variant"].eq("treatment")].iloc[0]
    activation_lift = (trt["activation_rate"] - ctrl["activation_rate"]) * 100
    paid_delta = (trt["paid_conversion_rate"] - ctrl["paid_conversion_rate"]) * 100

    paid_d60 = retention_rate(accounts, 60)
    obs_date = accounts["observation_date"].max()
    engagement = engagement_retention_curve(organizations, event_logs, obs_date)
    eng_d60 = engagement.dropna(subset=["retention_d60"])["retention_d60"].mean()

    medium_risk = risk.loc[risk["risk_segment"].eq("Medium")].iloc[0]

    st.title("Executive Briefing")
    st.caption("The full lifecycle story in one page — funnel, activation, experiment results, retention, revenue, and churn risk.")

    # ── One-line summary ─────────────────────────────────────────────────────
    st.info(
        "**Bottom line:** We have an activation problem, and we've tested a fix that works — "
        "but activation alone isn't enough. Half the sign-up base is going dark before ever becoming a paying customer."
    )

    st.divider()

    # ── 1. Funnel ─────────────────────────────────────────────────────────────
    st.header("1. Where the Funnel Leaks — and Where It Doesn't")

    display = funnel.copy()
    display["Overall"] = display["accounts"] / display["accounts"].iloc[0]
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
    st.caption(
        "**Overall** = % of all sign-ups. **Step-to-step** = % who made it from the previous stage. "
        "Once an account creates a workspace, ~68–69% make it through each next step. The funnel mid-section holds up fine. "
        f"The real problem is at the very top: 35% of sign-ups ({total - int(funnel.loc[funnel['stage']=='Workspace Created','accounts'].iloc[0]):,} accounts) never create a workspace at all."
    )
    st.markdown(
        "> *\"Once someone starts onboarding, about 7 in 10 make it to each next step. "
        "The problem isn't in the middle of the funnel — it's at the door. A third of sign-ups never open the product.\"*"
    )

    st.divider()

    # ── 2. Channel breakdown ──────────────────────────────────────────────────
    st.header("2. Channel Breakdown — Same Activation Rate, Different Problems")

    ch = channel_funnel.set_index("acquisition_source")[
        ["workspace_to_integration_rate", "activated_to_paid_rate"]
    ].rename(columns={
        "workspace_to_integration_rate": "Workspace → Integration",
        "activated_to_paid_rate": "Activated → Paid",
    })
    st.dataframe(ch.style.format("{:.1%}"), use_container_width=True)

    st.markdown(
        "- **Content** — starts strong, but drops at the integration step (second-lowest workspace→integration rate). "
        "Accounts that push through this step convert to paid at the *highest* rate of any channel. Fix the friction, don't cut the spend.\n"
        "- **Product-Led** — second-highest activation rate, but lowest activated→paid rate. "
        "This channel looks better than it is if you only look at activation.\n"
        "- **Referral** — weak across every step. This looks like lower-intent traffic, not a fixable UX issue."
    )

    st.divider()

    # ── 3. Experiment ─────────────────────────────────────────────────────────
    st.header("3. The Experiment — We Tested a Fix, and It Works")

    exp_display = experiment[["variant", "accounts", "activation_rate", "paid_conversion_rate", "retention_60d_rate"]].copy()
    exp_display.columns = ["Variant", "Accounts", "Activation", "Paid conversion", "60D retention"]
    for col in ["Activation", "Paid conversion", "60D retention"]:
        exp_display[col] = exp_display[col].map("{:.1%}".format)
    exp_display["Variant"] = exp_display["Variant"].map({"control": "Control", "treatment": "Variant"})
    st.dataframe(exp_display, hide_index=True, use_container_width=True)

    st.success(f"**Verdict: SHIP** to SMB and Mid-Market. Activation lift +{activation_lift:.1f}pp (p < 0.001). The −1.5pp retention dip is not statistically significant (p = 0.35).")

    if abs(paid_delta) < 1.0:
        st.warning(
            f"**Activation is up +{activation_lift:.1f}pp, but paid conversion didn't move ({paid_delta:+.1f}pp).** "
            "More accounts are activating without converting to revenue. "
            "Activation rate alone is not a sufficient north-star — **track paid conversion as a co-primary metric**."
        )

    st.markdown(
        "**Hold on Enterprise for now.** The lift is smaller and less certain — and Enterprise accounts already take ~2× longer to activate "
        "(P50 12.6 days vs. 6.5 days for SMB). They need a separate, implementation-led onboarding path."
    )

    st.divider()

    # ── 4. Retention gap ─────────────────────────────────────────────────────
    st.header("4. The Retention Number Your Dashboard Is Probably Missing")

    ret_data = pd.DataFrame({
        "Horizon": ["D30", "D60", "D90"],
        "Paid retention (paid accounts only)": [retention_rate(accounts, 30), paid_d60, retention_rate(accounts, 90)],
        "Engagement retention (all signups)": [
            engagement.dropna(subset=["retention_d30"])["retention_d30"].mean(),
            eng_d60,
            engagement.dropna(subset=["retention_d90"])["retention_d90"].mean(),
        ],
    })
    st.dataframe(
        ret_data.style.format({
            "Paid retention (paid accounts only)": "{:.1%}",
            "Engagement retention (all signups)": "{:.1%}",
        }),
        hide_index=True,
        use_container_width=True,
    )
    st.markdown(
        f"Paid retention of {paid_d60:.0%} looks fine — but it only counts accounts that already converted to paid. "
        f"Zoom out to all sign-ups: only **{eng_d60:.0%} still have product activity at D60**. "
        "Half the sign-up base has gone dark before ever becoming a customer. "
        "The drop is steepest between D30 and D60. After D60, it flattens — whoever's still active tends to stay."
    )

    st.divider()

    # ── 5. Revenue ────────────────────────────────────────────────────────────
    st.header("5. Revenue — What the Data Says, and What to Be Careful About")

    paid_accounts = accounts.loc[accounts["current_active_customer"]]
    arpa = paid_accounts["current_mrr"].mean()
    mrr = paid_accounts["current_mrr"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("ARPA", f"${arpa:,.0f}/mo")
    col2.metric("Active MRR", f"${mrr:,.0f}")
    col3.metric("Paid customers", f"{len(paid_accounts):,}")

    st.markdown(
        "LTV differences across channels ($3,950–$5,221 over 24 months) are **within the margin of error** — "
        "monthly churn is nearly identical across all channels (2.4–3.0%). Don't shift budget based on this ranking. "
        "What's missing from this analysis is CAC (acquisition cost). "
        "At a 3:1 LTV:CAC target, the max you should spend per paid account is **$1,300–$1,750** — "
        "compare your actual spend against this number before making channel investment decisions."
    )

    st.divider()

    # ── 6. Churn risk ─────────────────────────────────────────────────────────
    st.header("6. Where Customer Success Should Focus Right Now")

    risk_display = risk.copy()
    risk_display["mrr_at_risk"] = risk_display["mrr_at_risk"].map("${:,.0f}".format)
    risk_display.columns = ["Risk segment", "Accounts", "MRR exposure", "Avg score"]
    st.dataframe(risk_display, hide_index=True, use_container_width=True)

    st.markdown(
        f"**Medium-risk is where to focus** — "
        f"{int(medium_risk['accounts']):,} accounts, ${medium_risk['mrr_at_risk']:,.0f} MRR at stake. "
        "High-risk accounts are already lost. Low-risk accounts are healthy and don't need intervention. "
        "The window to act is narrow: **all churn happens in months 2–4 after the first payment**. "
        "After month 4, no account in this data has churned."
    )

    st.divider()

    # ── Bottom line ───────────────────────────────────────────────────────────
    st.header("Bottom Line — Three Actions")

    actions = pd.DataFrame({
        "Priority": ["1", "2", "3"],
        "Action": [
            "Ship guided onboarding to SMB + Mid-Market immediately",
            "Build a separate Enterprise onboarding path (speed-focused, implementation-led)",
            f"Run re-engagement sequence on {int(medium_risk['accounts']):,} medium-risk accounts (${medium_risk['mrr_at_risk']:,.0f} MRR)",
        ],
        "Owner": ["Product", "Product + CS", "Customer Success"],
    })
    st.dataframe(actions, hide_index=True, use_container_width=True)

    st.warning(
        "**One measurement change needed:** Start tracking paid conversion alongside activation as a co-primary metric. "
        f"A +{activation_lift:.1f}pp activation lift with {paid_delta:+.1f}pp change in paid conversion is a warning sign — not a success story."
    )


if __name__ == "__main__":
    main()
