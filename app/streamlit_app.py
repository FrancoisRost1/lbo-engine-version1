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
        # Deal
        "entry_ebitda":   deal.entry_ebitda,
        "entry_ev":       deal.entry_ev,
        "fees":           deal.fees,
        "total_uses":     deal.total_uses,
        "debt_raised":    deal.debt_raised,
        "sponsor_equity": deal.sponsor_equity,
        "leverage_ratio": deal.leverage_ratio,
        # Returns
        "moic":           ret.moic,
        "irr":            ret.irr,
        "exit_ebitda":    ret.exit_ebitda,
        "exit_multiple":  ret.exit_multiple,
        "exit_ev":        ret.exit_ev,
        "ending_debt":    ret.ending_debt,
        "equity_at_exit": ret.equity_at_exit,
        # Debt schedule
        "debt_years":     debt.schedule["Year"].tolist(),
        "debt_ending":    debt.schedule["Ending_Debt"].tolist(),
        "initial_debt":   deal.debt_raised,
        # Cash flow waterfall
        "cf_years":       op.projection["Year"].tolist(),
        "cf_ebitda":      op.projection["EBITDA"].tolist(),
        "cf_capex":       op.projection["Capex"].tolist(),
        "cf_taxes":       op.projection["Taxes"].tolist(),
        "cf_nwc":         op.projection["Delta_NWC"].tolist(),
        "cf_fcf":         op.projection["FCF"].tolist(),
        "cf_interest":    debt.schedule["Interest"].tolist(),
        "cf_mandatory":   debt.schedule["Mandatory_Repayment"].tolist(),
        "cf_optional":    debt.schedule["Optional_Repayment"].tolist(),
        # Scenarios & MC
        "scenarios":      scenarios,
        "mc_stats":       mc_stats,
        "mc_irr_list":    mc_irr_list,
    }


# --- Page config ---
st.set_page_config(page_title="LBO Engine", layout="wide")

st.markdown("""
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
    background-color: #1a1a1a !important;
    color: #e8e8e8 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 2px !important;
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
</style>
""", unsafe_allow_html=True)

st.markdown("### LBO SIMULATION ENGINE")
st.markdown("<small style='color:#666'>CFA Portfolio Project — Private Equity Returns Model</small>",
            unsafe_allow_html=True)

# --- Layout ---
left, right = st.columns([1, 2])

# ── LEFT COLUMN: Sliders ──────────────────────────────────────────────────────
with left:
    st.markdown("**DEAL PARAMETERS**")
    entry_ebitda      = st.number_input("Entry EBITDA ($M)",      min_value=10.0,  max_value=200.0, value=50.0,  step=5.0)
    purchase_multiple = st.number_input("Purchase Multiple (x)",  min_value=5.0,   max_value=20.0,  value=8.0,   step=0.5)
    leverage_ratio    = st.number_input("Leverage Ratio (%)",     min_value=20,    max_value=80,    value=50,    step=5)

    st.markdown("**OPERATING ASSUMPTIONS**")
    revenue_initial   = st.number_input("Revenue Initial ($M)",   min_value=50,    max_value=500,   value=200,   step=10)
    revenue_growth    = st.number_input("Revenue Growth (%)",     min_value=0,     max_value=20,    value=8,     step=1)
    ebitda_margin     = st.number_input("EBITDA Margin (%)",      min_value=10,    max_value=50,    value=27,    step=1)

    st.markdown("**EXIT ASSUMPTIONS**")
    exit_multiple     = st.number_input("Exit Multiple (x)",      min_value=4.0,   max_value=20.0,  value=10.0,  step=0.5)
    holding_period    = st.number_input("Holding Period (years)",  min_value=3,     max_value=7,     value=5,     step=1)

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
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Entry EV",       f"${r['entry_ev']:.0f}M")
    c2.metric("Debt Raised",    f"${r['debt_raised']:.0f}M")
    c3.metric("Sponsor Equity", f"${r['sponsor_equity']:.0f}M")
    c4.metric("Debt / EV",      f"{r['debt_raised'] / r['entry_ev'] * 100:.0f}%")
    c5.metric("Debt / EBITDA",  f"{r['debt_raised'] / r['entry_ebitda']:.1f}x")

    st.divider()

    # Section 2 — Sources & Uses
    st.subheader("Sources & Uses")
    uses_col, sources_col = st.columns(2)
    with uses_col:
        st.markdown("**USES**")
        st.markdown(f"Purchase Price &nbsp;&nbsp;&nbsp;&nbsp; **${r['entry_ev']:.1f}M**")
        st.markdown(f"Transaction Fees &nbsp;&nbsp; **${r['fees']:.1f}M**")
        st.markdown("---")
        st.markdown(f"**Total Uses** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['total_uses']:.1f}M**")
    with sources_col:
        st.markdown("**SOURCES**")
        st.markdown(f"Debt Raised &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['debt_raised']:.1f}M**")
        st.markdown(f"Sponsor Equity &nbsp;&nbsp;&nbsp;&nbsp; **${r['sponsor_equity']:.1f}M**")
        st.markdown("---")
        st.markdown(f"**Total Sources** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['total_uses']:.1f}M**")

    st.divider()

    # Section 3 — Returns
    st.subheader("Investor Returns")
    irr = r["irr"]
    irr_color = "#0a5c36" if irr > 0.20 else "#7a6000" if irr > 0.10 else "#8b0000"
    rc1, rc2 = st.columns(2)
    rc1.metric("MOIC", f"{r['moic']:.2f}x")
    with rc2:
        st.markdown(f"**IRR**")
        st.markdown(
            f"<h2 style='color:{irr_color}; margin-top:0'>{irr*100:.1f}%</h2>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Section 4 — Exit Analysis
    st.subheader("Exit Analysis")
    e1, e2, e3, e4, e5 = st.columns(5)
    e1.metric("Exit EBITDA ($M)",    f"${r['exit_ebitda']:.1f}M")
    e2.metric("Exit Multiple (x)",   f"{r['exit_multiple']:.1f}x")
    e3.metric("Exit EV ($M)",        f"${r['exit_ev']:.1f}M")
    e4.metric("Net Debt at Exit ($M)", f"${r['ending_debt']:.1f}M")
    e5.metric("Equity at Exit ($M)", f"${r['equity_at_exit']:.1f}M")

    st.divider()

    # Section 5 — Debt Paydown Chart
    st.subheader("Debt Paydown")
    fig_debt = go.Figure()
    fig_debt.add_trace(go.Bar(
        x=r["debt_years"],
        y=r["debt_ending"],
        name="Ending Debt",
        marker_color="#1a3a5c",
    ))
    fig_debt.add_hline(
        y=r["initial_debt"],
        line_dash="dot",
        line_color="#444",
        annotation_text=f"Initial Debt ${r['initial_debt']:.0f}M",
        annotation_position="top right",
    )
    fig_debt.update_layout(
        xaxis_title="Year",
        yaxis_title="Ending Debt ($M)",
        height=280,
        margin=dict(t=20, b=20),
        showlegend=False,
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#e8e8e8"),
    )
    fig_debt.update_xaxes(gridcolor="#1a1a1a", color="#888")
    fig_debt.update_yaxes(gridcolor="#1a1a1a", color="#888")
    st.plotly_chart(fig_debt, use_container_width=True)

    st.divider()

    # Section 6 — Cash Flow Waterfall
    st.subheader("Cash Flow Waterfall")

    def fmt(v, negative=False):
        """Format a float as accounting-style $M string."""
        if negative:
            return f"(${v:.1f}M)"
        return f"${v:.1f}M"

    years = r["cf_years"]
    col_names = [f"Year {y}" for y in years]

    residual = [
        fcf - i - m - o
        for fcf, i, m, o in zip(
            r["cf_fcf"], r["cf_interest"], r["cf_mandatory"], r["cf_optional"]
        )
    ]

    waterfall_data = {
        "Line Item": [
            "EBITDA",
            "(-) Capex",
            "(-) Taxes",
            "(-) ΔNWC",
            "= Free Cash Flow",
            "(-) Interest",
            "(-) Mandatory Repayment",
            "(-) Optional Repayment",
            "= Residual Cash",
        ],
    }
    rows = [
        [fmt(v)          for v in r["cf_ebitda"]],
        [fmt(v, True)    for v in r["cf_capex"]],
        [fmt(v, True)    for v in r["cf_taxes"]],
        [fmt(v, True)    for v in r["cf_nwc"]],
        [fmt(v)          for v in r["cf_fcf"]],
        [fmt(v, True)    for v in r["cf_interest"]],
        [fmt(v, True)    for v in r["cf_mandatory"]],
        [fmt(v, True)    for v in r["cf_optional"]],
        [fmt(v) if v >= 0 else fmt(abs(v), True) for v in residual],
    ]
    for col, vals in zip(col_names, zip(*rows)):
        waterfall_data[col] = list(vals)

    wf_df = pd.DataFrame(waterfall_data).set_index("Line Item")
    st.dataframe(wf_df, use_container_width=True)

    st.divider()

    # Section 7 — Scenario Comparison
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
        marker_color="#1a3a5c",
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
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#e8e8e8"),
    )
    fig_mc.update_xaxes(gridcolor="#1a1a1a", color="#888")
    fig_mc.update_yaxes(gridcolor="#1a1a1a", color="#888")
    st.plotly_chart(fig_mc, use_container_width=True)
