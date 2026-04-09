"""
tab_analysis.py — Tab 3: Scenario Analysis + Sensitivity Table.
"""

import streamlit as st
import pandas as pd

# --- Sensitivity table axes ---
SENS_EXIT_MULTIPLES  = tuple(round(6.0 + i * 0.5, 1) for i in range(13))  # 6.0 … 12.0
SENS_LEVERAGE_RATIOS = tuple(range(30, 75, 10))                             # 30 … 70


def _irr_cell_color(val: float) -> str:
    """Return CSS background-color string for a given IRR percentage."""
    if val > 25:
        bg = "#0a3d1f"
    elif val > 20:
        bg = "#1a5c36"
    elif val > 15:
        bg = "#4a5c1a"
    elif val > 10:
        bg = "#5c4a00"
    else:
        bg = "#5c1a1a"
    return f"background-color: {bg}; color: #e8e8e8"


def render(r: dict, sens_grid: list) -> None:
    """
    Render the ANALYSIS tab content.

    Args:
        r (dict): Pipeline results from run_pipeline().
        sens_grid (list): 2D IRR grid from run_sensitivity().
    """
    # Scenario Analysis
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

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Sensitivity Analysis
    st.subheader("Sensitivity Analysis — IRR (%) vs Exit Multiple & Leverage")

    sens_df = pd.DataFrame(
        sens_grid,
        index=[f"{m:.1f}x" for m in SENS_EXIT_MULTIPLES],
        columns=[f"{lev}% Lev" for lev in SENS_LEVERAGE_RATIOS],
    )
    sens_df.index.name = "Exit Multiple"
    styled_sens = sens_df.style.map(_irr_cell_color).format("{:.1f}%")
    st.dataframe(styled_sens, use_container_width=True)
