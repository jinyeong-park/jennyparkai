"""
Shared visual design tokens and HTML components for the Growth Attribution dashboard.
Single source of truth for all colors, layout settings, and reusable UI blocks.
"""

# ── Color tokens ──────────────────────────────────────────────────────────────
C_NAVY   = "#1F3864"
C_BLUE   = "#2E75B6"
C_GREEN  = "#087F5B"
C_RED    = "#C53A4A"
C_AMBER  = "#A15C00"
C_MUTED  = "#D4DCE8"
C_GRAY   = "#6B7788"
C_BORDER = "#D9DEE7"

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* Typography */
h1 { font-size: 1.6rem !important; font-weight: 700 !important; color: #18202B !important; letter-spacing: -0.02em; }
h2 { font-size: 1.1rem !important; font-weight: 700 !important; color: #18202B !important; }
h3 { font-size: 0.95rem !important; font-weight: 600 !important; color: #18202B !important; }

/* KPI cards */
.kpi-card {
  background: #fff;
  border: 1px solid #D9DEE7;
  border-radius: 4px;
  padding: 16px 20px 14px;
}
.kpi-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B7788;
  margin-bottom: 4px;
}
.kpi-value {
  font-size: 1.9rem;
  font-weight: 700;
  color: #18202B;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.kpi-context {
  font-size: 0.72rem;
  color: #6B7788;
  margin-top: 4px;
}
.kpi-value--good { color: #087F5B; }
.kpi-value--bad  { color: #C53A4A; }
.kpi-value--warn { color: #A15C00; }

/* Hero */
.hero-block {
  background: #F7F8FA;
  border-left: 4px solid #1F3864;
  padding: 20px 24px 18px;
  border-radius: 0 4px 4px 0;
  margin-bottom: 24px;
}
.hero-headline {
  font-size: 1.05rem;
  font-weight: 700;
  color: #18202B;
  line-height: 1.4;
  margin-bottom: 6px;
}
.hero-metric {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1F3864;
  margin-bottom: 4px;
}
.hero-subtext {
  font-size: 0.75rem;
  color: #6B7788;
  line-height: 1.5;
}

/* Insight callout */
.insight-box {
  background: #EEF2F8;
  border-left: 3px solid #2E75B6;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
  font-size: 0.82rem;
  color: #18202B;
  line-height: 1.55;
  margin-bottom: 16px;
}

/* Alert */
.alert-danger {
  background: #FDF2F3;
  border-left: 3px solid #C53A4A;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
  font-size: 0.82rem;
  color: #18202B;
  line-height: 1.55;
  margin-bottom: 16px;
}
.alert-warning {
  background: #FDF5EC;
  border-left: 3px solid #A15C00;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
  font-size: 0.82rem;
  color: #18202B;
  line-height: 1.55;
  margin-bottom: 16px;
}
.alert-success {
  background: #EDF7F3;
  border-left: 3px solid #087F5B;
  padding: 12px 16px;
  border-radius: 0 4px 4px 0;
  font-size: 0.82rem;
  color: #18202B;
  line-height: 1.55;
  margin-bottom: 16px;
}

/* Story step */
.story-step {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6B7788;
  padding: 8px 0 4px;
}
.story-step-q {
  font-size: 1.0rem;
  font-weight: 700;
  color: #18202B;
  margin-bottom: 12px;
}

/* Action box */
.action-box {
  background: #F7F8FA;
  border: 1px solid #D9DEE7;
  border-radius: 4px;
  padding: 18px 22px;
  margin-top: 8px;
}
.action-box-title {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6B7788;
  margin-bottom: 10px;
}
.action-item {
  font-size: 0.82rem;
  color: #18202B;
  padding: 5px 0;
  border-bottom: 1px solid #D9DEE7;
  line-height: 1.4;
}
.action-item:last-child { border-bottom: none; }
</style>
"""

def inject_css(st):
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Component functions ───────────────────────────────────────────────────────

def hero(headline: str, metric: str, subtext: str) -> str:
    return (
        f'<div class="hero-block">'
        f'<div class="hero-headline">{headline}</div>'
        f'<div class="hero-metric">{metric}</div>'
        f'<div class="hero-subtext">{subtext}</div>'
        f'</div>'
    )


def kpi(label: str, value: str, context: str = "", status: str = "neutral") -> str:
    val_class = {"good": "kpi-value--good", "bad": "kpi-value--bad", "warn": "kpi-value--warn"}.get(status, "")
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {val_class}">{value}</div>'
        f'<div class="kpi-context">{context}</div>'
        f'</div>'
    )


def insight(text: str) -> str:
    return f'<div class="insight-box">{text}</div>'


def alert(text: str, level: str = "warning") -> str:
    cls = {"danger": "alert-danger", "success": "alert-success"}.get(level, "alert-warning")
    return f'<div class="{cls}">{text}</div>'


def story_step(num: str, question: str) -> str:
    return (
        f'<div class="story-step">Step {num}</div>'
        f'<div class="story-step-q">{question}</div>'
    )


def action_box(items: list[str]) -> str:
    rows = "".join(f'<div class="action-item">→ {item}</div>' for item in items)
    return (
        f'<div class="action-box">'
        f'<div class="action-box-title">Recommended Actions</div>'
        f'{rows}'
        f'</div>'
    )


def base_layout(height: int = 340, margin: dict = None, show_legend: bool = True) -> dict:
    if margin is None:
        margin = dict(t=44, b=20, l=8, r=8)
    layout = dict(
        height=height,
        margin=margin,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="system-ui, sans-serif", size=12, color="#4E5B6B"),
        hoverlabel=dict(bgcolor="#fff", bordercolor="#D9DEE7", font_size=12),
        showlegend=show_legend,
    )
    if show_legend:
        layout["legend"] = dict(orientation="h", x=0, y=-0.22, font=dict(size=11))
    return layout
