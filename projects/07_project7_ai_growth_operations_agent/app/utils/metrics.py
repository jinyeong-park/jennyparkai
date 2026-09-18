"""Formatting utilities and color helpers for Tablr Growth Intelligence Dashboard.

"""

from __future__ import annotations

import math

import pandas as pd

from .theme import MUTED, GREEN, AMBER, RED, TEAL


def _is_missing(v) -> bool:
    """Return True for None, NaN, pandas NA, or inf."""
    if v is None:
        return True
    try:
        return pd.isna(v) or math.isinf(float(v))
    except (TypeError, ValueError):
        return True


def fmt_currency(v: float | None) -> str:
    """Format as '$1,234' or '—'."""
    if _is_missing(v):
        return "—"
    return f"${v:,.0f}"


def fmt_pct(v: float | None, decimals: int = 1) -> str:
    """Format as '25.6%' or '—'."""
    if _is_missing(v):
        return "—"
    return f"{v * 100:.{decimals}f}%"


def fmt_number(v: int | None) -> str:
    """Format as '5,000' or '—'."""
    if _is_missing(v):
        return "—"
    return f"{int(v):,}"


def fmt_ratio(v: float | None, decimals: int = 2) -> str:
    """Format as '0.23x' or '—'."""
    if _is_missing(v):
        return "—"
    return f"{v:.{decimals}f}x"


def channel_color(channel: str) -> str:
    """Return brand color for a channel."""
    return {
        "META": "#1877f2",
        "TIKTOK": "#000000",
        "GOOGLE_SEARCH": "#4285f4",
        "LINKEDIN": "#0077b5",
        "UNKNOWN": MUTED,
    }.get(channel.upper(), MUTED)


def recommendation_color(state: str) -> str:
    """Return color for a recommendation state badge."""
    return {
        "SCALE_CANDIDATE": GREEN,
        "HOLD": AMBER,
        "PAUSE_CANDIDATE": RED,
        "OBSERVE": TEAL,
        "INSUFFICIENT_DATA": MUTED,
    }.get(state, MUTED)


def recommendation_bg(state: str) -> str:
    """Return light background color for a recommendation state badge."""
    return {
        "SCALE_CANDIDATE": "#dcfce7",
        "HOLD": "#fef3c7",
        "PAUSE_CANDIDATE": "#fee2e2",
        "OBSERVE": "#ccfbf1",
        "INSUFFICIENT_DATA": "#f1f5f9",
    }.get(state, "#f1f5f9")


def state_badge_html(state: str) -> str:
    """Return HTML span for a colored recommendation state badge."""
    color = recommendation_color(state)
    bg = recommendation_bg(state)
    return (
        f"<span class='state-badge' style='background:{bg};color:{color};'>"
        f"{state}</span>"
    )


def experiment_state_color(state: str) -> str:
    """Return color for an experiment state."""
    return {
        "RUNNING": "#1a6fbe",
        "EVALUATING": "#d97706",
        "CONCLUDED": "#16a34a",
        "PAUSED": "#64748b",
    }.get(state.upper(), "#64748b")
