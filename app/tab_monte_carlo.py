"""
tab_monte_carlo.py — Tab 4: Monte Carlo simulation results + histogram.
"""

import streamlit as st
import plotly.graph_objects as go


def render(r: dict) -> None:
    """
    Render the MONTE CARLO tab content.

    Args:
        r (dict): Pipeline results from run_pipeline().
    """
    n_sims = r["mc_stats"]["n_simulations"]
    st.subheader(f"Monte Carlo Analysis ({n_sims} simulations)")
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
    fig_mc.add_vline(x=ms["mean_irr"] * 100, line_dash="dash", line_color="white",
                     annotation_text="Mean", annotation_position="top left")
    fig_mc.add_vline(x=20, line_dash="dot", line_color="orange",
                     annotation_text="20% hurdle", annotation_position="top right")
    fig_mc.update_layout(
        xaxis_title="IRR (%)", yaxis_title="Count",
        height=280, margin=dict(t=20, b=20), showlegend=False,
        plot_bgcolor="#0a0a0a", paper_bgcolor="#0a0a0a",
        font=dict(color="#e8e8e8"),
    )
    fig_mc.update_xaxes(gridcolor="#1a1a1a", color="#888")
    fig_mc.update_yaxes(gridcolor="#1a1a1a", color="#888")
    st.plotly_chart(fig_mc, use_container_width=True)
