"""
sensitivity.py — 2D IRR sensitivity grid for the Streamlit app.

Computes IRR across a grid of exit multiples × leverage ratios,
holding all other parameters constant at current slider values.
"""

import streamlit as st

from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns


@st.cache_data
def run_sensitivity(
    entry_ebitda: float,
    purchase_multiple: float,
    revenue_initial: float,
    revenue_growth: float,
    ebitda_margin: float,
    holding_period: int,
    exit_multiples: tuple,
    leverage_ratios: tuple,
    fixed: dict,
) -> list:
    """
    Compute a 2D grid of IRR values for every (exit_multiple, leverage_ratio) pair.

    Returns a 2D list [row=exit_multiple][col=leverage_ratio] of IRR percentages.
    """
    results = []
    for exit_mult in exit_multiples:
        row = []
        for lev in leverage_ratios:
            lev_ratio = lev / 100
            deal = DealModel(
                entry_ebitda=entry_ebitda,
                purchase_multiple=purchase_multiple,
                leverage_ratio=lev_ratio,
                fee_pct=fixed["fee_pct"],
            )
            op = OperatingModel(
                revenue_initial=revenue_initial,
                revenue_growth=revenue_growth / 100,
                ebitda_margin=ebitda_margin / 100,
                capex_pct=fixed["capex_pct"],
                nwc_pct=fixed["nwc_pct"],
                tax_rate=fixed["tax_rate"],
                holding_period=holding_period,
            )
            debt = DebtSchedule(
                debt_raised=deal.debt_raised,
                fcf_series=op.get_fcf_series(),
                interest_rate=fixed["interest_rate"],
                amortization_rate=fixed["amortization_rate"],
                cash_sweep=fixed["cash_sweep"],
            )
            ret = Returns(
                exit_ebitda=op.get_ebitda_by_year(holding_period),
                exit_multiple=exit_mult,
                ending_debt=debt.get_ending_debt(holding_period),
                sponsor_equity=deal.sponsor_equity,
                holding_period=holding_period,
            )
            irr_val = ret.irr
            row.append(round(irr_val * 100, 1) if irr_val == irr_val else 0.0)
        results.append(row)
    return results
