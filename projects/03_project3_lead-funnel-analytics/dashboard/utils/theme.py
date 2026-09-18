"""
theme.py  —  Lead Funnel Analytics Dashboard
Design tokens, CSS, and formatting utilities.
Follows the Data Visualization Skill: hierarchy → insight → color discipline.
"""

# ── Colour palette ─────────────────────────────────────────────────────────────
C_CANVAS  = "#F7F8FA"
C_SURFACE = "#FFFFFF"
C_BORDER  = "#E2E8F0"

# ── Primary data colour ────────────────────────────────────────────────────────
C_NAVY    = "#1E3A5F"   # the ONE strong colour — all primary bars/lines
C_BLUE    = "#2C6FAC"   # secondary (for grouped 2-colour charts)
C_TEAL    = "#17829E"   # occasional accent when hue variety is needed

# ── Muted / background ────────────────────────────────────────────────────────
C_MUTED   = "#CBD5E1"   # non-highlighted series, comparison bars
C_SUBTLE  = "#E8EDF3"   # very light fill, background series
C_GRAY    = "#64748B"   # labels, captions, secondary text

# ── Semantic colours — status only, not for data categories ───────────────────
C_GREEN   = "#0F7A5A"
C_AMBER   = "#9A5B00"
C_RED     = "#B83345"

C_GREEN_BG = "#E6F6EF"
C_AMBER_BG = "#FDF3E7"
C_RED_BG   = "#FDEAED"
C_BLUE_BG  = "#EAF1FB"

# ── Aliases — map legacy names to new system ──────────────────────────────────
C_STEEL   = "#2C6FAC"   # alias → C_BLUE
C_SKY     = "#5A8FBA"
C_TEAL2   = "#17829E"   # alias → C_TEAL
C_SLATE   = "#64748B"   # alias → C_GRAY
C_PALE    = "#94AFCA"
C_PURPLE  = "#1E3A5F"   # remove purple — map to navy so any reference still works

# ── Channel colours — tight blue-to-slate range, all same family ──────────────
# Rule: channels are categories of similar importance → small hue, lightness varies
CHANNEL_COLORS = {
    "google":    "#1E3A5F",   # darkest — largest paid channel
    "meta":      "#2C6FAC",   # medium blue
    "affiliate": "#17829E",   # teal-blue
    "organic":   "#5A8FBA",   # muted mid-blue
    "direct":    "#94AFCA",   # lightest — least emphasis
}

# ── Funnel stage colours — single hue, dark→light (top→bottom) ───────────────
FUNNEL_COLORS = {
    "sessions":          "#1E3A5F",
    "quote_starts":      "#2C6FAC",
    "quote_completions": "#3D85C0",
    "leads_submitted":   "#5A8FBA",
    "valid_leads":       "#94AFCA",
}

# ── Multi-series palette — smooth blue gradient ────────────────────────────────
# For 5–10 partner/campaign lines. Same hue, varying lightness only.
PALETTE = [
    "#1E3A5F",   # darkest
    "#24527A",
    "#2C6FAC",
    "#3D85C0",
    "#5A8FBA",
    "#17829E",   # teal accent (slight hue variation)
    "#4A9AAE",
    "#7AB0C4",   # lightest
]

# ── Chart layout defaults ──────────────────────────────────────────────────────
# Vertical legend — right side, one item per line, colored circle markers
LEGEND_V = dict(
    orientation="v",
    yanchor="top", y=1,
    xanchor="left", x=1.02,
    font=dict(size=11),
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor=C_BORDER,
    borderwidth=1,
    itemsizing="constant",
    tracegroupgap=6,
)

CHART_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter, Segoe UI, Arial", size=11, color="#2D3142"),
    margin=dict(l=10, r=10, t=8, b=20),
    legend=LEGEND_V,
    xaxis=dict(showgrid=False, linecolor="#E2E8F0", tickfont=dict(size=10)),
    yaxis=dict(showgrid=True, gridcolor="#E2E8F0", linecolor="#E2E8F0",
               tickfont=dict(size=10), zeroline=False),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E2E8F0",
                    font=dict(size=11, color="#2D3142")),
)

# ── Number formatting utilities ────────────────────────────────────────────────
def fmt_compact(n, prefix="$"):
    """Format large numbers compactly: 221476 → $221K, 1234567 → $1.2M"""
    if n is None:
        return "—"
    abs_n = abs(n)
    sign  = "-" if n < 0 else ""
    if abs_n >= 1_000_000:
        return f"{sign}{prefix}{abs_n/1_000_000:.1f}M"
    elif abs_n >= 1_000:
        return f"{sign}{prefix}{abs_n/1_000:.0f}K"
    else:
        return f"{sign}{prefix}{abs_n:.0f}"

def fmt_pct(n, decimals=1):
    """Format as percentage: 0.752 → 75.2%"""
    if n is None:
        return "—"
    return f"{n*100:.{decimals}f}%"

def fmt_delta(n, pct=False, good_direction="up"):
    """Return (formatted_string, color) for a delta value."""
    if n is None:
        return "—", C_GRAY
    if pct:
        label = f"{'+' if n >= 0 else ''}{n*100:.1f} pp"
    else:
        label = f"{'+' if n >= 0 else ''}{n:.1f}%"
    if good_direction == "up":
        color = C_GREEN if n > 0 else C_RED if n < 0 else C_GRAY
    else:
        color = C_RED if n > 0 else C_GREEN if n < 0 else C_GRAY
    arrow = "▲" if n > 0 else "▼" if n < 0 else "—"
    return f"{arrow} {label}", color


def chart_label(text: str):
    """Render a small chart subtitle above a plotly chart."""
    import streamlit as st
    st.markdown(
        f"<p style='font-size:0.78rem;font-weight:600;color:#4E5B6B;"
        f"margin:4px 0 2px 0;line-height:1.3'>{text}</p>",
        unsafe_allow_html=True,
    )


def bar_legend_circles(fig, items: list):
    """
    Add colored circle legend entries for multi-trace bar charts.
    Call AFTER adding all bar traces (with showlegend=False).
    items: [(name, color), ...]
    """
    import plotly.graph_objects as go
    for name, color in items:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(symbol="circle", size=11, color=color,
                        line=dict(width=0)),
            name=name,
            showlegend=True,
        ))


# ── CSS injection ──────────────────────────────────────────────────────────────
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ── */
[data-testid="stAppViewContainer"] {{
    background-color: {C_CANVAS};
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
}}
[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {{
    visibility: hidden;
    height: 0;
}}
.block-container {{
    padding-top: 3rem;
}}
[data-testid="stSidebar"] {{
    background-color: {C_NAVY};
}}
[data-testid="stSidebar"] * {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] a {{
    color: #A8C4E0 !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: #EAF1FB !important;
    border: 1px solid #A8C4E0 !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] span {{
    color: {C_NAVY} !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] svg {{
    fill: {C_NAVY} !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: #F8FAFC !important;
    border-color: #A8C4E0 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div {{
    color: {C_NAVY} !important;
}}
[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {{
    background-color: {C_BLUE} !important;
    border-color: {C_BLUE} !important;
}}
[data-testid="stSidebar"] [data-baseweb="slider"] div {{
    color: #FFFFFF !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 16px 18px 13px;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.8rem !important;
    font-weight: 700;
    color: {C_NAVY};
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.68rem !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {C_GRAY};
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.78rem !important;
    font-weight: 500;
}}

/* ── Typography ── */
h1 {{ color: {C_NAVY}; font-weight: 700; font-size: 1.8rem; letter-spacing: -0.02em; }}
h2 {{ color: {C_NAVY}; font-weight: 700; font-size: 1.2rem; margin-bottom: 2px; }}
h3 {{ color: {C_NAVY}; font-weight: 600; font-size: 0.95rem; margin-bottom: 4px; }}
hr {{ border-color: {C_BORDER}; margin: 8px 0; }}

/* ── Hero block ── */
.hero-block {{
    background: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-left: 3px solid {C_NAVY};
    border-radius: 6px;
    padding: 18px 22px;
    margin-bottom: 20px;
}}
.hero-block .hero-label {{
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {C_GRAY};
    margin: 0 0 6px 0;
}}
.hero-block .hero-metric {{
    font-size: 2.2rem;
    font-weight: 700;
    color: {C_NAVY};
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.03em;
    margin: 0 0 4px 0;
    line-height: 1.1;
}}
.hero-block .hero-insight {{
    font-size: 0.98rem;
    font-weight: 500;
    color: #18202B;
    margin: 0 0 6px 0;
    line-height: 1.4;
}}
.hero-block .hero-sub {{
    font-size: 0.82rem;
    color: {C_GRAY};
    margin: 0;
    line-height: 1.6;
}}

/* ── Section headers (numbered) ── */
.section-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin: 32px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid {C_BORDER};
}}
.section-num {{
    font-size: 0.65rem;
    font-weight: 700;
    color: {C_BLUE};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    flex-shrink: 0;
}}
.section-title {{
    font-size: 0.98rem;
    font-weight: 600;
    color: {C_NAVY};
    margin: 0;
}}

/* ── Insight callout ── */
.insight-callout {{
    background: {C_BLUE_BG};
    border-left: 3px solid {C_BLUE};
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 0.82rem;
    color: #18202B;
    margin-bottom: 12px;
    line-height: 1.5;
}}
.insight-callout.warning {{
    background: {C_AMBER_BG};
    border-left-color: {C_AMBER};
}}
.insight-callout.alert {{
    background: {C_RED_BG};
    border-left-color: {C_RED};
}}
.insight-callout.positive {{
    background: {C_GREEN_BG};
    border-left-color: {C_GREEN};
}}

/* ── Status pill ── */
.status-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
}}
.status-green {{ background: {C_GREEN_BG}; color: {C_GREEN}; }}
.status-amber {{ background: {C_AMBER_BG}; color: {C_AMBER}; }}
.status-red   {{ background: {C_RED_BG};   color: {C_RED};   }}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
}}

/* ── Provenance footer ── */
.provenance {{
    font-size: 0.65rem;
    color: {C_GRAY};
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid {C_BORDER};
    line-height: 1.7;
}}
</style>
"""


def apply_theme():
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    import streamlit as st
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p style='color:#6B7788;margin-top:-10px;font-size:0.85rem'>{subtitle}</p>",
                    unsafe_allow_html=True)
    st.markdown("---")


def hero_block(label: str, metric: str, insight: str, subtext: str = "",
               border_color: str = None):
    """Render the hero block: editorial intro with dominant metric."""
    import streamlit as st
    bc = border_color or C_NAVY
    html = f"""
    <div class="hero-block" style="border-left-color:{bc}">
        <div class="hero-label">{label}</div>
        <div class="hero-metric">{metric}</div>
        <div class="hero-insight">{insight}</div>
        {"<div class='hero-sub'>" + subtext + "</div>" if subtext else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section_header(num: str, title: str):
    """Render a numbered section header."""
    import streamlit as st
    st.markdown(
        f"""<div class="section-header">
            <span class="section-num">{num}</span>
            <span class="section-title">{title}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def insight_callout(text: str, kind: str = "info"):
    """Render an inline insight callout (info / warning / alert / positive)."""
    import streamlit as st
    cls_map = {"info": "", "warning": " warning", "alert": " alert", "positive": " positive"}
    cls = cls_map.get(kind, "")
    st.markdown(
        f'<div class="insight-callout{cls}">{text}</div>',
        unsafe_allow_html=True,
    )


def provenance(source: str = "Synthetic data · 6 months",
               grain: str = "Lead-level → 5 mart tables",
               refresh: str = "Jan 2025 – Jun 2025"):
    import streamlit as st
    st.markdown(
        f'<p class="provenance"><b>Source:</b> {source} &nbsp;·&nbsp; '
        f'<b>Grain:</b> {grain} &nbsp;·&nbsp; '
        f'<b>Period:</b> {refresh}</p>',
        unsafe_allow_html=True,
    )
