"""
streamlit_app.py — Interactive web UI for the LBO simulation engine.

All financial logic lives in lbo/ modules. This file handles only layout,
sliders, and visualisation.

Run with: streamlit run app/streamlit_app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.covenants import check_covenants
from lbo.scenarios import run_scenarios
from lbo.monte_carlo import run_monte_carlo, compute_mc_statistics

# --- Fixed parameters (not exposed as sliders) ---
FIXED = {
    "fee_pct":          0.02,
    "capex_pct":        0.03,
    "nwc_pct":          0.02,
    "tax_rate":         0.25,
    "interest_rate":    0.08,
    "amortization_rate": 0.05,
    "cash_sweep":       1.0,
}


@st.cache_data
def run_pipeline(
    entry_ebitda: float,
    purchase_multiple: float,
    leverage_ratio: float,
    revenue_initial: float,
    revenue_growth: float,
    ebitda_margin: float,
    exit_multiple: float,
    holding_period: int,
) -> dict:
    """
    Run the full LBO pipeline from scalar inputs and return plain Python results.

    Cached by Streamlit — reruns only when slider values change.
    Returns only primitive types (floats, lists, dicts) for cache compatibility.
    """
    config = {
        "entry_ebitda":     entry_ebitda,
        "purchase_multiple": purchase_multiple,
        "leverage_ratio":   leverage_ratio / 100,
        "revenue_initial":  revenue_initial,
        "revenue_growth":   revenue_growth / 100,
        "ebitda_margin":    ebitda_margin / 100,
        "exit_multiple":    exit_multiple,
        "holding_period":   holding_period,
        **FIXED,
    }

    deal = DealModel(
        entry_ebitda=config["entry_ebitda"],
        purchase_multiple=config["purchase_multiple"],
        leverage_ratio=config["leverage_ratio"],
        fee_pct=config["fee_pct"],
    )

    op = OperatingModel(
        revenue_initial=config["revenue_initial"],
        revenue_growth=config["revenue_growth"],
        ebitda_margin=config["ebitda_margin"],
        capex_pct=config["capex_pct"],
        nwc_pct=config["nwc_pct"],
        tax_rate=config["tax_rate"],
        holding_period=config["holding_period"],
    )

    debt = DebtSchedule(
        debt_raised=deal.debt_raised,
        fcf_series=op.get_fcf_series(),
        interest_rate=config["interest_rate"],
        amortization_rate=config["amortization_rate"],
        cash_sweep=config["cash_sweep"],
    )

    ret = Returns(
        exit_ebitda=op.get_ebitda_by_year(config["holding_period"]),
        exit_multiple=config["exit_multiple"],
        ending_debt=debt.get_ending_debt(config["holding_period"]),
        sponsor_equity=deal.sponsor_equity,
        holding_period=config["holding_period"],
    )

    scenarios = run_scenarios(config)

    mc_results = run_monte_carlo(config, n_simulations=500)
    mc_stats = compute_mc_statistics(mc_results)
    mc_irr_list = [r["irr"] * 100 for r in mc_results]

    return {
        "entry_ev":       deal.entry_ev,
        "debt_raised":    deal.debt_raised,
        "sponsor_equity": deal.sponsor_equity,
        "leverage_ratio": deal.leverage_ratio,
        "moic":           ret.moic,
        "irr":            ret.irr,
        "debt_years":     debt.schedule["Year"].tolist(),
        "debt_ending":    debt.schedule["Ending_Debt"].tolist(),
        "initial_debt":   deal.debt_raised,
        "scenarios":      scenarios,
        "mc_stats":       mc_stats,
        "mc_irr_list":    mc_irr_list,
    }


# --- Page config ---
st.set_page_config(page_title="LBO Engine", layout="wide")
st.title("LBO Simulation Engine")
st.caption("CFA Portfolio Project — Leveraged Buyout model with scenario and Monte Carlo analysis")

# --- Layout ---
left, right = st.columns([1, 2])

# ── LEFT COLUMN: Sliders ──────────────────────────────────────────────────────
with left:
    st.subheader("Deal Parameters")
    entry_ebitda     = st.slider("Entry EBITDA ($M)",       10.0, 200.0, 50.0,  5.0)
    purchase_multiple = st.slider("Purchase Multiple (x)",   5.0,  20.0,  10.0,  0.5)
    leverage_ratio   = st.slider("Leverage Ratio (%)",       20,   80,    60,    5)

    st.subheader("Operating Assumptions")
    revenue_initial  = st.slider("Revenue Initial ($M)",     50,   500,   200,   10)
    revenue_growth   = st.slider("Revenue Growth (%)",       0,    20,    6,     1)
    ebitda_margin    = st.slider("EBITDA Margin (%)",        10,   50,    25,    1)

    st.subheader("Exit Assumptions")
    exit_multiple    = st.slider("Exit Multiple (x)",        4.0,  20.0,  9.0,   0.5)
    holding_period   = st.slider("Holding Period (years)",   3,    7,     5,     1)

# --- Run pipeline ---
r = run_pipeline(
    entry_ebitda, purchase_multiple, leverage_ratio,
    revenue_initial, revenue_growth, ebitda_margin,
    exit_multiple, holding_period,
)

# ── RIGHT COLUMN: Results ─────────────────────────────────────────────────────
with right:

    # Section 1 — Deal Summary
    st.subheader("Deal Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entry EV",      f"${r['entry_ev']:.0f}M")
    c2.metric("Debt Raised",   f"${r['debt_raised']:.0f}M")
    c3.metric("Sponsor Equity", f"${r['sponsor_equity']:.0f}M")
    c4.metric("Leverage",      f"{r['leverage_ratio']*100:.0f}%")

    st.divider()

    # Section 2 — Returns
    st.subheader("Investor Returns")
    irr = r["irr"]
    irr_color = "green" if irr > 0.20 else "orange" if irr > 0.10 else "red"
    rc1, rc2 = st.columns(2)
    rc1.metric("MOIC", f"{r['moic']:.2f}x")
    with rc2:
        st.markdown(f"**IRR**")
        st.markdown(
            f"<h2 style='color:{irr_color}; margin-top:0'>{irr*100:.1f}%</h2>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Section 3 — Debt Paydown Chart
    st.subheader("Debt Paydown")
    fig_debt = go.Figure()
    fig_debt.add_trace(go.Bar(
        x=r["debt_years"],
        y=r["debt_ending"],
        name="Ending Debt",
        marker_color="#3b82f6",
    ))
    fig_debt.add_hline(
        y=r["initial_debt"],
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Initial Debt ${r['initial_debt']:.0f}M",
        annotation_position="top right",
    )
    fig_debt.update_layout(
        xaxis_title="Year",
        yaxis_title="Ending Debt ($M)",
        height=280,
        margin=dict(t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig_debt, use_container_width=True)

    st.divider()

    # Section 4 — Scenario Comparison
    st.subheader("Scenario Analysis")
    sc = r["scenarios"]
    scenario_df = pd.DataFrame({
        "Metric": ["Exit EV ($M)", "Equity at Exit ($M)", "MOIC (x)", "IRR (%)", "Covenant Breach"],
        "Downside": [
            f"{sc['Downside']['exit_ev']:.1f}",
            f"{sc['Downside']['equity_at_exit']:.1f}",
            f"{sc['Downside']['moic']:.2f}x",
            f"{sc['Downside']['irr']*100:.1f}%",
            "⚠ YES" if sc["Downside"]["any_covenant_breach"] else "NO",
        ],
        "Base": [
            f"{sc['Base']['exit_ev']:.1f}",
            f"{sc['Base']['equity_at_exit']:.1f}",
            f"{sc['Base']['moic']:.2f}x",
            f"{sc['Base']['irr']*100:.1f}%",
            "⚠ YES" if sc["Base"]["any_covenant_breach"] else "NO",
        ],
        "Upside": [
            f"{sc['Upside']['exit_ev']:.1f}",
            f"{sc['Upside']['equity_at_exit']:.1f}",
            f"{sc['Upside']['moic']:.2f}x",
            f"{sc['Upside']['irr']*100:.1f}%",
            "⚠ YES" if sc["Upside"]["any_covenant_breach"] else "NO",
        ],
    }).set_index("Metric")
    st.dataframe(scenario_df, use_container_width=True)

    st.divider()

    # Section 5 — Monte Carlo
    st.subheader("Monte Carlo Analysis (500 simulations)")
    ms = r["mc_stats"]
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Mean IRR",    f"{ms['mean_irr']*100:.1f}%")
    m2.metric("Median IRR",  f"{ms['median_irr']*100:.1f}%")
    m3.metric("P5 / P95",   f"{ms['p5_irr']*100:.1f}% / {ms['p95_irr']*100:.1f}%")
    m4.metric("P(IRR>20%)", f"{ms['prob_irr_above_20']*100:.1f}%")
    m5.metric("P(Breach)",  f"{ms['prob_covenant_breach']*100:.1f}%")

    fig_mc = go.Figure()
    fig_mc.add_trace(go.Histogram(
        x=r["mc_irr_list"],
        nbinsx=40,
        name="IRR",
        marker_color="#6366f1",
        opacity=0.8,
    ))
    fig_mc.add_vline(x=ms["mean_irr"] * 100,  line_dash="dash", line_color="white",
                     annotation_text="Mean", annotation_position="top left")
    fig_mc.add_vline(x=20, line_dash="dot", line_color="orange",
                     annotation_text="20% hurdle", annotation_position="top right")
    fig_mc.update_layout(
        xaxis_title="IRR (%)",
        yaxis_title="Count",
        height=280,
        margin=dict(t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig_mc, use_container_width=True)
