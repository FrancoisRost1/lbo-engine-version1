"""
style.py — Bloomberg dark mode CSS injection for Streamlit.

Call inject_css() once at the top of the main app to apply the theme.
"""

import streamlit as st

_CSS = """
<style>
/* === BASE === */
html, body, [class*="css"], .stApp {
    background-color: #0a0a0a !important;
    color: #e8e8e8 !important;
    font-size: 13px !important;
}

/* === TYPOGRAPHY === */
h1, h2, h3 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* === METRICS === */
[data-testid="metric-container"] {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 2px !important;
    padding: 8px 12px !important;
}
[data-testid="metric-container"] label {
    font-size: 10px !important;
    color: #bbbbbb !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="metric-container"] [data-testid="metric-value"] {
    font-size: 18px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
}

/* === INPUTS === */
[data-testid="stNumberInput"] input {
    background-color: #111111 !important;
    color: #e8e8e8 !important;
    border: 1px solid #222222 !important;
    border-radius: 0px !important;
    padding: 4px 8px !important;
    font-size: 12px !important;
}
[data-testid="stNumberInput"] label {
    color: #aaa !important;
    font-size: 11px !important;
}

/* === DATAFRAME === */
[data-testid="stDataFrame"] {
    background: #1a1a1a !important;
}

/* === GENERAL TEXT === */
p, span, div, label, small {
    color: #cccccc !important;
}

/* === DIVIDERS === */
hr {
    margin: 0.5rem 0 !important;
    border-color: #2a2a2a !important;
}

/* === LAYOUT === */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
    background-color: #0a0a0a !important;
}

/* === SIDEBAR / COLUMNS background === */
section[data-testid="stSidebar"],
[data-testid="column"] {
    background-color: #0a0a0a !important;
}

/* === COMPACT SPACING === */
.element-container { margin-bottom: 0.2rem !important; }
.stMetric { padding: 6px 10px !important; }
[data-testid="stVerticalBlock"] { gap: 0.3rem !important; }

/* === HIDE +/- STEPPER BUTTONS === */
[data-testid="stNumberInput"] button {
    display: none !important;
}
</style>
"""


def inject_css() -> None:
    """Inject Bloomberg dark-mode CSS into the Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
