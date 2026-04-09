"""
streamlit_app.py — Interactive web UI for the LBO simulation engine.

All financial logic lives in lbo/ modules. Tab rendering is split across
app/tab_*.py files. This file handles page config, sidebar, KPI banner,
and tab routing.

Run with: streamlit run app/streamlit_app.py
"""

import math
import sys
from pathlib import Path

# Ensure the project root is importable (handles `streamlit run app/streamlit_app.py`
# from any working directory). Uses pathlib — no os.path manipulation.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st

from app.config_loader import load_config, get_fixed_params, get_scenario_presets
from app.style import inject_css
from app.pipeline import run_pipeline
from app.sensitivity import run_sensitivity
from app.tab_analysis import SENS_EXIT_MULTIPLES, SENS_LEVERAGE_RATIOS
from app import tab_overview, tab_performance, tab_analysis, tab_monte_carlo, tab_ic_memo

# --- Page config ---
st.set_page_config(page_title="LBO Engine", layout="wide")
inject_css()

# --- Load config ---
cfg = load_config()
FIXED = get_fixed_params(cfg)
SCENARIO_PRESETS = get_scenario_presets(cfg)

st.markdown("### LBO SIMULATION ENGINE")
st.markdown("<small style='color:#666'>CFA Portfolio Project — Private Equity Returns Model</small>",
            unsafe_allow_html=True)

# --- Layout ---
left, right = st.columns([1, 2])

# ── LEFT COLUMN: Sliders ─────────────────────────────────────────────────────
with left:
    scenario = st.radio("Scenario", list(SCENARIO_PRESETS.keys()), horizontal=True)
    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    st.markdown("**DEAL PARAMETERS**")
    entry_ebitda      = st.number_input("Entry EBITDA ($M)",      min_value=10.0,  max_value=200.0, value=50.0,  step=5.0)
    purchase_multiple = st.number_input("Purchase Multiple (x)",  min_value=5.0,   max_value=20.0,  value=8.0,   step=0.5)
    leverage_ratio    = st.number_input("Leverage Ratio (%)",     min_value=20,    max_value=80,    value=50,    step=5)

    st.markdown("**OPERATING ASSUMPTIONS**")
    revenue_initial   = st.number_input("Revenue Initial ($M)",   min_value=50,    max_value=500,   value=200,   step=10)
    revenue_growth    = st.number_input("Revenue Growth (%)",     min_value=0,     max_value=20,    value=SCENARIO_PRESETS[scenario]["revenue_growth"], step=1)
    ebitda_margin     = st.number_input("EBITDA Margin (%)",      min_value=10,    max_value=50,    value=SCENARIO_PRESETS[scenario]["ebitda_margin"],  step=1)

    st.markdown("**EXIT ASSUMPTIONS**")
    exit_multiple     = st.number_input("Exit Multiple (x)",      min_value=4.0,   max_value=20.0,  value=SCENARIO_PRESETS[scenario]["exit_multiple"],  step=0.5)
    holding_period    = st.number_input("Holding Period (years)",  min_value=3,     max_value=7,     value=5,     step=1)

# --- Run pipeline ---
r = run_pipeline(
    entry_ebitda, purchase_multiple, leverage_ratio,
    revenue_initial, revenue_growth, ebitda_margin,
    exit_multiple, holding_period,
    fixed=FIXED, full_cfg=cfg,
)

# --- Run sensitivity grid ---
sens_grid = run_sensitivity(
    entry_ebitda, purchase_multiple,
    revenue_initial, revenue_growth, ebitda_margin,
    holding_period,
    SENS_EXIT_MULTIPLES, SENS_LEVERAGE_RATIOS,
    fixed=FIXED,
)

# ── RIGHT COLUMN: Results ────────────────────────────────────────────────────
with right:

    # KPI Banner — always visible, outside tabs
    irr_pct = r["irr"] * 100 if not math.isnan(r["irr"]) else 0.0
    irr_color = "#00c97a" if irr_pct > 20 else "#f0a500" if irr_pct > 10 else "#e03c31"
    irr_bg    = "#0a2a0a"  if irr_pct > 20 else "#2a1a00"  if irr_pct > 10 else "#2a0a0a"
    k1, k2, k3, k4 = st.columns([1.5, 1, 1, 1])
    with k1:
        st.markdown(
            f"""<div style='background:{irr_bg};border:1px solid #2a2a2a;border-radius:2px;padding:10px 14px'>
            <div style='font-size:10px;color:#bbbbbb;text-transform:uppercase;letter-spacing:0.5px'>IRR</div>
            <div style='font-size:42px;font-weight:700;color:{irr_color};line-height:1.1;letter-spacing:-1px'>{irr_pct:.1f}%</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:2px;padding:10px 14px'>
            <div style='font-size:10px;color:#bbbbbb;text-transform:uppercase;letter-spacing:0.5px'>MOIC</div>
            <div style='font-size:24px;font-weight:700;color:#ffffff;line-height:1.1'>{r['moic']:.2f}x</div>
            </div>""",
            unsafe_allow_html=True,
        )
    k3.metric("Exit EV", f"${r['exit_ev']:.0f}M")
    k4.metric("Equity at Exit", f"${r['equity_at_exit']:.0f}M")
    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Tabs
    t1, t2, t3, t4, t5 = st.tabs(["OVERVIEW", "PERFORMANCE", "ANALYSIS", "MONTE CARLO", "IC MEMO"])
    with t1:
        tab_overview.render(r)
    with t2:
        tab_performance.render(r)
    with t3:
        tab_analysis.render(r, sens_grid)
    with t4:
        tab_monte_carlo.render(r)
    with t5:
        tab_ic_memo.render(r)
