"""Theme constants and helpers for Tablr Growth Intelligence Dashboard.

— all data in this dashboard is simulated.
"""

import streamlit as st

PRIMARY = "#0f4c81"
BLUE = "#1a6fbe"
TEAL = "#0d9488"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
MUTED = "#64748b"
MUTED_BAR = "#D4DCE8"   # muted data bar — use for non-focal categories
INK = "#0b1f3a"
GRID = "#e2e8f0"
BG = "#f8faff"

SYNTHETIC_BADGE = (
    "<span style='background:#fef3c7;color:#92400e;font-size:0.75rem;"
    "font-weight:600;padding:3px 10px;border-radius:4px;'>&#9888; SYNTHETIC DATA</span>"
)


def inject_theme() -> None:
    """Inject CSS for metric cards and layout."""
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; max-width: 1400px;}
        [data-testid="stSidebar"] {background: #f0f4fa;}
        [data-testid="stSidebarNav"] {display: none;}
        .metric-card {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 18px 22px;
            background: #ffffff;
            box-shadow: 0 4px 16px rgba(15, 76, 129, 0.06);
            margin-bottom: 0.5rem;
        }
        .metric-label {
            color: #29466f;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-value {
            color: #0b1f3a;
            font-size: 1.9rem;
            font-weight: 800;
            margin-top: 0.3rem;
            line-height: 1.1;
        }
        .metric-delta {
            color: #16a34a;
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 0.4rem;
        }
        .metric-delta-neg {
            color: #dc2626;
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 0.4rem;
        }
        .state-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .section-header {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f4c81;
            margin-bottom: 0.5rem;
            border-left: 4px solid #1a6fbe;
            padding-left: 10px;
        }
        .hero-block {
            background: linear-gradient(135deg, #0f4c81 0%, #1a6fbe 100%);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
            color: #ffffff;
        }
        .hero-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #93c5fd;
            margin-bottom: 6px;
        }
        .hero-statement {
            font-size: 1.25rem;
            font-weight: 800;
            line-height: 1.4;
            color: #ffffff;
            margin-bottom: 12px;
        }
        .hero-supporting {
            font-size: 0.84rem;
            color: #bfdbfe;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> None:
    """Render sidebar navigation with page links."""
    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.1rem;font-weight:800;color:#0f4c81;"
            "margin-bottom:0.8rem;'>Tablr Growth Intelligence</div>",
            unsafe_allow_html=True,
        )
        pages = [
            ("Summary.py", "Executive Summary", ":material/dashboard:"),
            ("pages/1_Acquisition.py", "Acquisition", ":material/ads_click:"),
            ("pages/2_Creative.py", "Creative Intelligence", ":material/palette:"),
            ("pages/3_Retention.py", "Retention", ":material/trending_up:"),
            ("pages/4_LTV_Budget.py", "LTV & Budget", ":material/attach_money:"),
            ("pages/5_Experiments.py", "Experiments", ":material/science:"),
            ("pages/6_Recommendations.py", "Recommendations", ":material/recommend:"),
            ("pages/7_Real_Data_Guide.py", "Real Data Guide", ":material/database:"),
        ]
        for page, label, icon in pages:
            st.page_link(page, label=label, icon=icon)
        st.markdown("---")
        st.markdown(SYNTHETIC_BADGE, unsafe_allow_html=True)
        st.caption("12-week simulation | Sep 2026")
