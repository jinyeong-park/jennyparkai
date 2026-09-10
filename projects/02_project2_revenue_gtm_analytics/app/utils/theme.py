"""
theme.py
========
Shared design tokens and CSS injection for the Revenue Intelligence dashboard.
Targets a Tableau / Power BI aesthetic: clean white canvas, dense data layout,
muted professional palette, no decorative elements.
"""

# ── Colour palette ─────────────────────────────────────────────────────────────
# Canvas / surface tokens (expert calibrated)
C_CANVAS  = "#F7F8FA"   # page background
C_SURFACE = "#FFFFFF"   # chart/card background
C_BORDER  = "#D9DEE7"   # grid lines, dividers

# Primary brand colours
C_NAVY    = "#1F3864"   # dark navy — headers, primary bars
C_BLUE    = "#2E75B6"   # mid blue — secondary series
C_STEEL   = "#4472C4"   # steel blue — tertiary
C_TEAL    = "#17829E"   # teal — accent / positive

# Semantic colours — WCAG 2.2 calibrated (expert playbook palette)
C_GREEN   = "#087F5B"   # positive / healthy
C_AMBER   = "#A15C00"   # warning / medium risk
C_RED     = "#C53A4A"   # negative / high risk / churn
C_GRAY    = "#6B7788"   # neutral / unknown

# Muted / de-emphasis (for "highlight the exception" charts)
C_MUTED   = "#D4DCE8"   # muted blue-grey — background bars, non-focal categories

# Light fills (for backgrounds of colored cards)
C_GREEN_BG = "#E6F6EF"
C_AMBER_BG = "#FDF3E7"
C_RED_BG   = "#FDEAED"
C_BLUE_BG  = "#EAF1FB"

# Chart series palette (ordered)
PALETTE = [C_NAVY, C_BLUE, C_TEAL, C_AMBER, C_RED, C_STEEL, C_GRAY]

# Per-dimension palettes
SEGMENT_COLORS = {
    "Enterprise":  C_NAVY,
    "Mid-Market":  C_BLUE,
    "SMB":         C_TEAL,
    "Unknown":     C_GRAY,
}

RISK_COLORS = {
    "High Risk":   C_RED,
    "Medium Risk": C_AMBER,
    "On Track":    C_GREEN,
}

HEALTH_COLORS = {
    "Healthy":          C_GREEN,
    "Needs Attention":  C_AMBER,
    "At Risk":          C_RED,
    "Unknown":          C_GRAY,
}

PAYMENT_COLORS = {
    "Paid":    C_GREEN,
    "Pending": C_AMBER,
    "Failed":  C_RED,
}

STAGE_COLORS = {
    "Collected":     C_GREEN,
    "Billed":        C_BLUE,
    "Contracted":    C_AMBER,
    "Booking Only":  C_RED,
}

NRR_COLORS = {
    "Retained":  C_NAVY,
    "Expansion": C_GREEN,
    "Churned":   C_RED,
}


# ── Chart layout defaults ──────────────────────────────────────────────────────
CHART_FONT = dict(family="Segoe UI, Arial, sans-serif", size=11, color="#18202B")

def base_layout(height=300, margin=None, show_legend=True):
    """Return a base Plotly layout dict matching the BI dashboard aesthetic."""
    m = margin or dict(t=32, b=24, l=8, r=8)
    return dict(
        height=height,
        margin=m,
        plot_bgcolor=C_SURFACE,
        paper_bgcolor=C_SURFACE,
        font=CHART_FONT,
        showlegend=show_legend,
        legend=dict(
            orientation="h", x=0, y=-0.18,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER, zeroline=False),
        yaxis=dict(gridcolor=C_BORDER, linecolor=C_BORDER, zeroline=False),
    )


# ── CSS injection ──────────────────────────────────────────────────────────────
CSS = """
<style>
/* ── Global typography ─────────────────────── */
html, body, [class*="css"] {
    font-family: "Segoe UI", Arial, sans-serif !important;
    color: #18202B !important;
}

/* ── Canvas background ─────────────────────── */
.main, .stApp {
    background-color: #F7F8FA !important;
}

/* ── Block container — generous breathing room */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px;
}

/* ── Page title ────────────────────────────── */
h1 {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #6B7788 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.5rem !important;
}

/* ── Section headers ───────────────────────── */
h2 {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #1F3864 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 1.6rem !important;
    margin-bottom: 0.4rem !important;
    border-bottom: 2px solid #2E75B6;
    padding-bottom: 4px;
}

h3 {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #4E5B6B !important;
    margin-top: 0.6rem !important;
    margin-bottom: 0.2rem !important;
}

/* ── Sidebar ───────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #1F3864 !important;
    min-width: 210px !important;
    max-width: 210px !important;
}
section[data-testid="stSidebar"] * {
    color: #D6E4F7 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #3A5A8A !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] h2 {
    color: #FFFFFF !important;
    border-bottom: 1px solid #3A5A8A !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem !important;
}
section[data-testid="stSidebar"] a {
    color: #90BEE8 !important;
    text-decoration: none;
}
section[data-testid="stSidebar"] a:hover {
    color: #FFFFFF !important;
}

/* ── KPI cards ─────────────────────────────── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #D9DEE7;
    border-radius: 3px;
    padding: 20px 20px 16px 20px;
    margin-bottom: 4px;
    height: 100%;
}
.kpi-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: #6B7788;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 2.4rem;
    font-weight: 700;
    color: #1F3864;
    line-height: 1.0;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
    margin-bottom: 8px;
}
.kpi-delta {
    font-size: 0.72rem;
    color: #6B7788;
    line-height: 1.4;
    border-top: 1px solid #F0F2F5;
    padding-top: 8px;
    margin-top: 4px;
}
.kpi-delta.good { color: #087F5B; }
.kpi-delta.bad  { color: #C53A4A; }

/* ── Alert / callout box ───────────────────── */
.bi-alert {
    padding: 12px 16px;
    border-radius: 3px;
    font-size: 0.8rem;
    line-height: 1.6;
    margin: 8px 0;
}
.bi-alert.info    { background:#EAF1FB; border-left:4px solid #2E75B6; color:#1A3A5C; }
.bi-alert.warning { background:#FDF3E7; border-left:4px solid #A15C00; color:#5C3400; }
.bi-alert.danger  { background:#FDEAED; border-left:4px solid #C53A4A; color:#6E1A26; }
.bi-alert.success { background:#E6F6EF; border-left:4px solid #087F5B; color:#054D37; }

/* ── Dataframe tweaks ──────────────────────── */
.stDataFrame { border: 1px solid #D9DEE7 !important; border-radius: 3px; }
.stDataFrame thead th {
    background: #F0F4FA !important;
    color: #1F3864 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Selectbox / slider ────────────────────── */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    color: #6B7788 !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

/* ── Divider ───────────────────────────────── */
hr { border: none; border-top: 1px solid #D9DEE7; margin: 2rem 0; }

/* ── Caption ───────────────────────────────── */
.stCaption, caption, small {
    font-size: 0.67rem !important;
    color: #98A3B2 !important;
}
</style>
"""


def inject_css(st):
    """Call at the top of every page: inject_css(st)"""
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(label: str, value: str, delta: str = "", delta_type: str = "neutral") -> str:
    """Return HTML for a KPI card with large number and status-aware accent bar.
    delta_type: 'good' | 'bad' | 'neutral'
    """
    accent = {"good": "#087F5B", "bad": "#C53A4A"}.get(delta_type, "#2E75B6")
    delta_class = {"good": "good", "bad": "bad"}.get(delta_type, "")
    arrow = {"good": "▲ ", "bad": "▼ "}.get(delta_type, "")
    delta_html = (
        f'<div class="kpi-delta {delta_class}">{arrow}{delta}</div>' if delta else ""
    )
    return (
        f'<div class="kpi-card" style="border-top:4px solid {accent};">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def alert(text: str, kind: str = "info") -> str:
    """Return HTML for a styled callout box. kind: info | warning | danger | success"""
    return f'<div class="bi-alert {kind}">{text}</div>'


def hero(headline: str, metric: str = "", subtext: str = "") -> str:
    """
    Editorial hero block — dominant opening statement.
    Large metric number commands attention; headline gives context; subtext is quiet.
    """
    metric_html = (
        f'<div style="font-size:3.2rem;font-weight:700;color:#1F3864;'
        f'line-height:1.0;margin:16px 0 10px;letter-spacing:-0.03em;'
        f'font-variant-numeric:tabular-nums;">{metric}</div>'
    ) if metric else ""
    sub_html = (
        f'<div style="font-size:0.78rem;color:#6B7788;line-height:1.7;'
        f'border-top:1px solid #D9DEE7;padding-top:10px;margin-top:4px;">{subtext}</div>'
    ) if subtext else ""
    return (
        f'<div style="padding:32px 36px 28px;background:#FFFFFF;'
        f'border-left:6px solid #1F3864;border-radius:3px;'
        f'margin:4px 0 28px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
        f'<div style="font-size:1.05rem;font-weight:600;color:#4E5B6B;'
        f'line-height:1.5;max-width:800px;">{headline}</div>'
        f'{metric_html}{sub_html}'
        f'</div>'
    )


def story_step(number: str, question: str) -> str:
    """
    Section header with numbered badge — creates explicit narrative flow.
    01 → 02 → 03 guides the eye down the page.
    """
    return (
        f'<div style="display:flex;align-items:center;gap:14px;margin:40px 0 16px;">'
        f'<div style="background:#1F3864;color:white;border-radius:50%;'
        f'min-width:32px;height:32px;display:flex;align-items:center;'
        f'justify-content:center;font-size:0.7rem;font-weight:700;'
        f'flex-shrink:0;letter-spacing:0.03em;">{number}</div>'
        f'<div style="font-size:1.05rem;font-weight:700;color:#1F3864;">'
        f'{question}</div>'
        f'</div>'
        f'<div style="border-bottom:2px solid #E8ECF2;margin-bottom:16px;"></div>'
    )


def insight(text: str) -> str:
    """Key insight callout — stands out from surrounding content."""
    return (
        f'<div style="background:#F0F4FB;border-left:4px solid #1F3864;'
        f'padding:14px 18px;border-radius:3px;margin:12px 0 16px;'
        f'font-size:0.83rem;color:#18202B;line-height:1.65;">'
        f'<div style="font-weight:700;text-transform:uppercase;letter-spacing:0.08em;'
        f'font-size:0.63rem;color:#4E5B6B;margin-bottom:6px;">Key Insight</div>'
        f'{text}</div>'
    )


def action_box(items: list) -> str:
    """Recommended Actions box — clear next steps at the bottom of every page."""
    bullets = "".join(
        f'<li style="margin-bottom:8px;line-height:1.5;">{item}</li>'
        for item in items
    )
    return (
        f'<div style="background:#FFFFFF;border:1px solid #D9DEE7;'
        f'border-left:5px solid #1F3864;padding:20px 24px;border-radius:3px;'
        f'margin-top:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:#6B7788;margin-bottom:12px;">Recommended Actions</div>'
        f'<ul style="margin:0;padding-left:20px;font-size:0.82rem;color:#18202B;">'
        f'{bullets}</ul>'
        f'</div>'
    )


def provenance(source: str = "Synthetic B2B dataset · dbt + Python", as_of: str = "Sept 2026") -> str:
    """Return HTML for a data provenance footer line."""
    return (
        f'<div style="font-size:0.65rem;color:#AAAAAA;margin-top:8px;padding-top:6px;'
        f'border-top:1px solid #EBEBEB;">Source: {source} &nbsp;·&nbsp; As of {as_of}</div>'
    )
