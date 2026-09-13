"""Experiments Dashboard — Experiment registry, status, and readouts.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import yaml
import pandas as pd
import streamlit as st

from utils.metrics import experiment_state_color, fmt_pct
from utils.theme import inject_theme, render_navigation, GREEN, AMBER, BLUE, TEAL, RED, MUTED, PRIMARY

st.set_page_config(
    page_title="Experiments — Tablr Growth",
    page_icon=":material/science:",
    layout="wide",
)
inject_theme()
render_navigation()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#0f4c81;font-size:1.6rem;font-weight:800;'>Experiment Registry</h1>",
    unsafe_allow_html=True,
)
st.caption("Active experiments · Statistical guardrails · Readouts · DRY_RUN=True — no budget changes applied automatically")

st.markdown("---")

# ── Load experiments.yaml ─────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parents[2] / "config" / "experiments.yaml"

try:
    with open(CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    experiments = raw.get("experiments", [])
except Exception as e:
    st.error(f"Could not load experiments.yaml: {e}")
    st.stop()

# ── Hero callout ──────────────────────────────────────────────────────────────
st.markdown(
    """<div style='background:#eff6ff;border-left:4px solid #1a6fbe;padding:12px 16px;
    border-radius:0 6px 6px 0;font-size:0.88rem;color:#1e3a5f;margin-bottom:16px;'>
    <b>Early signal from exp_001 (RUNNING):</b> CONTRAST hook shows +7.4pp absolute improvement
    in activation rate over OUTCOME hook (29.3% vs 24.0%). Experiment continues to minimum sample
    — do not act on preliminary data. Guardrail (M1 retention) not yet evaluated.
    </div>""",
    unsafe_allow_html=True,
)

# ── State summary ─────────────────────────────────────────────────────────────
state_counts = {}
for exp in experiments:
    s = exp.get("state", "UNKNOWN")
    state_counts[s] = state_counts.get(s, 0) + 1

cols = st.columns(len(state_counts) + 1)
cols[0].metric("Total Experiments", len(experiments))
for i, (state, count) in enumerate(sorted(state_counts.items())):
    color = experiment_state_color(state)
    cols[i + 1].markdown(
        f"""<div class='metric-card'>
        <div class='metric-label'>{state}</div>
        <div class='metric-value' style='color:{color};'>{count}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Experiment cards ──────────────────────────────────────────────────────────
STATE_COLORS = {
    "RUNNING": BLUE,
    "EVALUATING": AMBER,
    "CONCLUDED": GREEN,
    "PAUSED": MUTED,
}
STATE_BG = {
    "RUNNING": "#eff6ff",
    "EVALUATING": "#fef3c7",
    "CONCLUDED": "#dcfce7",
    "PAUSED": "#f1f5f9",
}

for exp in experiments:
    exp_id = exp.get("experiment_id", "")
    state = exp.get("state", "UNKNOWN")
    color = STATE_COLORS.get(state, MUTED)
    bg = STATE_BG.get(state, "#f8faff")

    with st.expander(
        f"**{exp_id}** — {exp.get('name', '')} [{state}]",
        expanded=(exp_id == "exp_001"),
    ):
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown(
                f"""<div style='background:{bg};border-left:4px solid {color};
                padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:12px;'>
                <div style='font-size:0.78rem;font-weight:700;color:{color};text-transform:uppercase;
                letter-spacing:0.05em;'>{state}</div>
                <div style='font-weight:700;color:#0b1f3a;font-size:1.0rem;margin-top:4px;'>
                {exp.get('name', '')}</div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown(f"**Hypothesis:** {exp.get('hypothesis', '')}")
            st.markdown(f"**Variable Tested:** `{exp.get('variable_tested', '')}`")

            primary = exp.get("primary_metric", {})
            st.markdown(
                f"**Primary Metric:** `{primary.get('name', '')}` "
                f"({primary.get('direction', '')}, "
                f"MDE={primary.get('minimum_detectable_effect', '')})"
            )

            guardrails = exp.get("guardrail_metrics", [])
            if guardrails:
                g = guardrails[0]
                st.markdown(
                    f"**Guardrail Metric:** `{g.get('name', '')}` "
                    f"({g.get('direction', '')}, threshold={g.get('minimum_detectable_effect', '')})"
                )

            if exp.get("notes"):
                st.markdown(f"*{exp['notes']}*")

        with col_right:
            arms = exp.get("arms", [])
            st.markdown("**Arms:**")
            for arm in arms:
                arm_role = "Control" if arm.get("is_control") else "Treatment"
                st.markdown(
                    f"""<div style='background:#ffffff;border:1px solid #e2e8f0;
                    border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:0.85rem;'>
                    <span style='font-weight:700;color:#0f4c81;'>{arm_role}</span>
                    &nbsp;·&nbsp;{arm.get('name', '')}<br>
                    <span style='color:#64748b;font-size:0.78rem;'>{arm.get('description', '')}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("**Config:**")
            config_data = {
                "Min trials / arm": exp.get("minimum_trials_per_arm", "—"),
                "Eval window": f"{exp.get('evaluation_window_days', '—')} days",
                "Start date": exp.get("start_date", "—"),
                "End date": exp.get("end_date", "ongoing"),
            }
            for k, v in config_data.items():
                st.markdown(
                    f"<span style='font-size:0.82rem;color:#475569;'><b>{k}:</b> {v}</span>",
                    unsafe_allow_html=True,
                )

        # exp_001 readout
        if exp_id == "exp_001":
            st.markdown("---")
            st.markdown("**Synthetic Readout — exp_001: Hook Type Test (RUNNING)**")

            readout_data = {
                "Arm": ["Outcome hook (control)", "Contrast hook (treatment)"],
                "Trials": [342, 358],
                "Activations": [82, 105],
                "Activation Rate": [fmt_pct(82 / 342), fmt_pct(105 / 358)],
                "Spend (USD)": ["$85,500", "$89,500"],
                "CPAO": ["$1,043", "$852"],
            }
            st.dataframe(pd.DataFrame(readout_data), use_container_width=True, hide_index=True)

            abs_diff = (105 / 358) - (82 / 342)
            rel_diff = abs_diff / (82 / 342)
            st.markdown(
                f"""<div style='background:#f0fdf4;border:1px solid #bbf7d0;
                border-radius:8px;padding:12px 14px;font-size:0.87rem;color:#14532d;'>
                <b>Preliminary signal:</b> Contrast hook shows +{fmt_pct(abs_diff)} absolute
                ({fmt_pct(rel_diff)} relative) improvement in activation rate over Outcome hook.
                Z-score not yet computed — experiment continues to minimum_trials_per_arm=200
                per arm before statistical evaluation. Guardrail (M1 retention) not yet evaluated.
                <br><br>
                <b>Status:</b> RUNNING — do not act on preliminary data.
                </div>""",
                unsafe_allow_html=True,
            )
            st.caption("Readout numbers are simulated for portfolio demonstration.")

st.markdown("---")
st.markdown(
    """<div style='background:#f8faff;border:1px solid #e2e8f0;border-radius:8px;
    padding:12px 14px;font-size:0.85rem;color:#475569;'>
    <b>Experiment governance:</b> All experiments use two-sample z-test for proportions.
    Minimum 95% confidence (z ≥ 1.96) + practical significance (|abs_diff| ≥ MDE) required
    before acting. Guardrail violations downgrade SCALE_CANDIDATE to HOLD.
    DRY_RUN=true — no budget or creative changes are applied automatically.
    </div>""",
    unsafe_allow_html=True,
)
