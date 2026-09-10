PRIMARY = "#0f4c81"
BLUE = "#2f80ed"
TEAL = "#17b8a6"
GREEN = "#22c55e"
AMBER = "#f5b942"
RED = "#ef5b5b"
INK = "#0b1f3a"
MUTED = "#5b7194"
PANEL_BG = "#ffffff"
GRID = "#dce6f4"


def render_navigation() -> None:
    import streamlit as st

    with st.sidebar:
        pages = [
            ("Summary.py", "Overview", ":material/dashboard:"),
            ("pages/1_Users.py", "Users", ":material/groups:"),
            ("pages/2_Activation.py", "Activation", ":material/bolt:"),
            ("pages/3_Retention.py", "Retention", ":material/trending_up:"),
            ("pages/4_Revenue.py", "Revenue", ":material/attach_money:"),
            ("pages/5_Experiments.py", "Experiments", ":material/science:"),
            ("pages/6_Churn_Risk.py", "Churn Risk", ":material/health_and_safety:"),
        ]
        for page, label, icon in pages:
            st.page_link(page, label=label, icon=icon)
        st.markdown("---")
        st.caption("Data refreshed from deterministic lifecycle tables")


def inject_theme() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; max-width: 1380px;}
        [data-testid="stSidebar"] {background: #f6f9ff;}
        [data-testid="stSidebarNav"] {display: none;}
        .metric-card {
            border: 1px solid #dce6f4;
            border-radius: 8px;
            padding: 18px 20px;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 76, 129, 0.05);
        }
        .metric-label {color: #29466f; font-size: 0.84rem; font-weight: 700;}
        .metric-value {color: #0b1f3a; font-size: 2rem; font-weight: 800; margin-top: 0.35rem;}
        .metric-delta {color: #00a67d; font-size: 0.9rem; font-weight: 700; margin-top: 0.5rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
