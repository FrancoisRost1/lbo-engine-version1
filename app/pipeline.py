"""
pipeline.py — Cached LBO pipeline runner for the Streamlit app.

run_pipeline() runs the full deal → returns → scenarios → Monte Carlo chain.
"""

import streamlit as st

from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.scenarios import run_scenarios
from lbo.monte_carlo import run_monte_carlo
from lbo.mc_stats import compute_mc_statistics


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
    fixed: dict,
    full_cfg: dict,
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
        **fixed,
        "scenarios":        full_cfg.get("scenarios", {}),
        "covenants":        full_cfg.get("covenants", {}),
        "monte_carlo":      full_cfg.get("monte_carlo", {}),
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

    mc_n = config.get("monte_carlo", {}).get("n_simulations", 500)
    mc_results = run_monte_carlo(config, n_simulations=mc_n)
    mc_stats = compute_mc_statistics(mc_results, cfg=config)
    mc_irr_list = [r["irr"] * 100 for r in mc_results]

    return {
        # Deal
        "entry_ebitda":     deal.entry_ebitda,
        "purchase_multiple": deal.purchase_multiple,
        "entry_ev":         deal.entry_ev,
        "fees":             deal.fees,
        "total_uses":       deal.total_uses,
        "debt_raised":      deal.debt_raised,
        "sponsor_equity":   deal.sponsor_equity,
        "leverage_ratio":   deal.leverage_ratio,
        # Returns
        "moic":             ret.moic,
        "irr":              ret.irr,
        "exit_ebitda":      ret.exit_ebitda,
        "exit_multiple":    ret.exit_multiple,
        "exit_ev":          ret.exit_ev,
        "ending_debt":      ret.ending_debt,
        "equity_at_exit":   ret.equity_at_exit,
        # Debt schedule
        "debt_years":       debt.schedule["Year"].tolist(),
        "debt_ending":      debt.schedule["Ending_Debt"].tolist(),
        "initial_debt":     deal.debt_raised,
        # Cash flow waterfall
        "cf_years":         op.projection["Year"].tolist(),
        "cf_ebitda":        op.projection["EBITDA"].tolist(),
        "cf_capex":         op.projection["Capex"].tolist(),
        "cf_taxes":         op.projection["Taxes"].tolist(),
        "cf_nwc":           op.projection["Delta_NWC"].tolist(),
        "cf_fcf":           op.projection["FCF"].tolist(),
        "cf_interest":      debt.schedule["Interest"].tolist(),
        "cf_mandatory":     debt.schedule["Mandatory_Repayment"].tolist(),
        "cf_optional":      debt.schedule["Optional_Repayment"].tolist(),
        # Value creation bridge
        "vc_entry_equity":  deal.entry_ev - deal.debt_raised,
        "vc_exit_equity":   ret.equity_at_exit,
        "vc_ebitda_growth": (ret.exit_ebitda - deal.entry_ebitda) * ret.exit_multiple,
        "vc_multiple_effect": deal.entry_ebitda * (ret.exit_multiple - deal.purchase_multiple),
        "vc_debt_paydown":  deal.debt_raised - ret.ending_debt,
        "vc_total":         (
            (ret.exit_ebitda - deal.entry_ebitda) * ret.exit_multiple
            + deal.entry_ebitda * (ret.exit_multiple - deal.purchase_multiple)
            + (deal.debt_raised - ret.ending_debt)
        ),
        # Scenarios & MC
        "scenarios":        scenarios,
        "mc_stats":         mc_stats,
        "mc_irr_list":      mc_irr_list,
    }
