"""
tab_performance.py — Tab 2: Value Creation Bridge, Debt Paydown, Cash Flow Waterfall.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def _vc_color(val: float) -> str:
    """Return green for positive, red for negative value creation components."""
    return "#2d6a4f" if val >= 0 else "#8b0000"


def _fmt(v: float, negative: bool = False) -> str:
    """Format a float as accounting-style $M string."""
    if negative:
        return f"(${v:.1f}M)"
    return f"${v:.1f}M"


def _dark_layout(fig: go.Figure, **kwargs) -> None:
    """Apply Bloomberg dark theme to a plotly figure."""
    fig.update_layout(
        plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
        font=dict(color="#e8e8e8"), showlegend=False,
        **kwargs,
    )
    fig.update_xaxes(gridcolor="#1a1a1a", color="#888")
    fig.update_yaxes(gridcolor="#1a1a1a", color="#888")


def render(r: dict) -> None:
    """
    Render the PERFORMANCE tab content.

    Args:
        r (dict): Pipeline results from run_pipeline().
    """
    # Value Creation Bridge
    st.subheader("Value Creation Bridge")

    base_ebitda   = r["vc_entry_equity"]
    base_multiple = base_ebitda + r["vc_ebitda_growth"]
    base_debt     = base_multiple + r["vc_multiple_effect"]

    fig_vc = go.Figure()
    fig_vc.add_trace(go.Bar(
        x=["Entry Equity"], y=[r["vc_entry_equity"]],
        base=[0], marker_color="#1a3a5c",
        text=[f"${r['vc_entry_equity']:.0f}M"], textposition="outside",
    ))
    fig_vc.add_trace(go.Bar(
        x=["EBITDA Growth"], y=[r["vc_ebitda_growth"]],
        base=[base_ebitda], marker_color=_vc_color(r["vc_ebitda_growth"]),
        text=[f"${r['vc_ebitda_growth']:+.0f}M"], textposition="outside",
    ))
    fig_vc.add_trace(go.Bar(
        x=["Multiple Effect"], y=[r["vc_multiple_effect"]],
        base=[base_multiple], marker_color=_vc_color(r["vc_multiple_effect"]),
        text=[f"${r['vc_multiple_effect']:+.0f}M"], textposition="outside",
    ))
    fig_vc.add_trace(go.Bar(
        x=["Debt Paydown"], y=[r["vc_debt_paydown"]],
        base=[base_debt], marker_color="#2d6a4f",
        text=[f"${r['vc_debt_paydown']:+.0f}M"], textposition="outside",
    ))
    fig_vc.add_trace(go.Bar(
        x=["Exit Equity"], y=[r["vc_exit_equity"]],
        base=[0], marker_color="#1a3a5c",
        text=[f"${r['vc_exit_equity']:.0f}M"], textposition="outside",
    ))
    _dark_layout(fig_vc, height=280, margin=dict(t=30, b=20),
                 yaxis_title="Equity Value ($M)", barmode="overlay")
    st.plotly_chart(fig_vc, use_container_width=True)

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Debt Paydown
    st.subheader("Debt Paydown")
    fig_debt = go.Figure()
    fig_debt.add_trace(go.Bar(
        x=r["debt_years"], y=r["debt_ending"],
        name="Ending Debt", marker_color="#1a3a5c",
    ))
    fig_debt.add_hline(
        y=r["initial_debt"], line_dash="dot", line_color="#444",
        annotation_text=f"Initial Debt ${r['initial_debt']:.0f}M",
        annotation_position="top right",
    )
    _dark_layout(fig_debt, xaxis_title="Year", yaxis_title="Ending Debt ($M)",
                 height=280, margin=dict(t=20, b=20))
    st.plotly_chart(fig_debt, use_container_width=True)

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Cash Flow Waterfall
    st.subheader("Cash Flow Waterfall")

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
            "EBITDA", "(-) Capex", "(-) Taxes", "(-) ΔNWC",
            "= Free Cash Flow", "(-) Interest",
            "(-) Mandatory Repayment", "(-) Optional Repayment", "= Residual Cash",
        ],
    }
    rows = [
        [_fmt(v)       for v in r["cf_ebitda"]],
        [_fmt(v, True) for v in r["cf_capex"]],
        [_fmt(v, True) for v in r["cf_taxes"]],
        [_fmt(v, True) for v in r["cf_nwc"]],
        [_fmt(v)       for v in r["cf_fcf"]],
        [_fmt(v, True) for v in r["cf_interest"]],
        [_fmt(v, True) for v in r["cf_mandatory"]],
        [_fmt(v, True) for v in r["cf_optional"]],
        [_fmt(v) if v >= 0 else _fmt(abs(v), True) for v in residual],
    ]
    for col, vals in zip(col_names, zip(*rows)):
        waterfall_data[col] = list(vals)

    wf_df = pd.DataFrame(waterfall_data).set_index("Line Item")
    st.dataframe(wf_df, use_container_width=True)
