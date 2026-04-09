"""
monte_carlo.py — Monte Carlo simulation for the LBO engine.

Runs the full LBO pipeline 1000+ times with randomised key inputs to
produce a probability distribution of investor returns and covenant risk.
"""

import logging

import numpy as np

from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.covenants import check_covenants

logger = logging.getLogger(__name__)


def run_monte_carlo(base_config: dict, n_simulations: int = None) -> list:
    """
    Run the full LBO pipeline n_simulations times with randomised inputs.

    Three inputs are drawn from clipped Normal distributions each iteration:
    revenue_growth, ebitda_margin, exit_multiple. Distribution parameters
    are loaded from cfg["monte_carlo"].

    DealModel is instantiated once before the loop — sponsor equity and
    debt raised are fixed at entry and do not vary across simulations.

    Args:
        base_config (dict): Full config dict loaded from config.yaml.
        n_simulations (int, optional): Override for number of iterations.
            Defaults to monte_carlo.n_simulations from config (or 1000).

    Returns:
        list[dict]: One dict per successful simulation with keys:
            revenue_growth, ebitda_margin, exit_multiple,
            exit_ev, equity_at_exit, moic, irr, ending_debt, any_covenant_breach.
            Failed simulations are logged and skipped.
    """
    mc_cfg = base_config.get("monte_carlo", {})
    if n_simulations is None:
        n_simulations = mc_cfg.get("n_simulations", 1000)

    rg_cfg = mc_cfg.get("revenue_growth", {})
    em_cfg = mc_cfg.get("ebitda_margin", {})
    ex_cfg = mc_cfg.get("exit_multiple", {})

    rg_mean, rg_std = rg_cfg.get("mean", 0.06), rg_cfg.get("std", 0.02)
    rg_min, rg_max = rg_cfg.get("min", -0.05), rg_cfg.get("max", 0.20)
    em_mean, em_std = em_cfg.get("mean", 0.25), em_cfg.get("std", 0.02)
    em_min, em_max = em_cfg.get("min", 0.10), em_cfg.get("max", 0.50)
    ex_mean, ex_std = ex_cfg.get("mean", 9.0), ex_cfg.get("std", 1.0)
    ex_min, ex_max = ex_cfg.get("min", 4.0), ex_cfg.get("max", 16.0)

    deal = DealModel(
        entry_ebitda=base_config["entry_ebitda"],
        purchase_multiple=base_config["purchase_multiple"],
        leverage_ratio=base_config["leverage_ratio"],
        fee_pct=base_config["fee_pct"],
    )

    results = []

    for _ in range(n_simulations):
        rg = float(np.clip(np.random.normal(rg_mean, rg_std), rg_min, rg_max))
        em = float(np.clip(np.random.normal(em_mean, em_std), em_min, em_max))
        ex = float(np.clip(np.random.normal(ex_mean, ex_std), ex_min, ex_max))

        try:
            op = OperatingModel(
                revenue_initial=base_config["revenue_initial"],
                revenue_growth=rg,
                ebitda_margin=em,
                capex_pct=base_config["capex_pct"],
                nwc_pct=base_config["nwc_pct"],
                tax_rate=base_config["tax_rate"],
                holding_period=base_config["holding_period"],
            )

            debt = DebtSchedule(
                debt_raised=deal.debt_raised,
                fcf_series=op.get_fcf_series(),
                interest_rate=base_config["interest_rate"],
                amortization_rate=base_config["amortization_rate"],
                cash_sweep=base_config["cash_sweep"],
            )

            ret = Returns(
                exit_ebitda=op.get_ebitda_by_year(base_config["holding_period"]),
                exit_multiple=ex,
                ending_debt=debt.get_ending_debt(base_config["holding_period"]),
                sponsor_equity=deal.sponsor_equity,
                holding_period=base_config["holding_period"],
            )

            covenants = check_covenants(debt, op, cfg=base_config)
            any_breach = any(r["any_breach"] for r in covenants)

            results.append({
                "revenue_growth":      rg,
                "ebitda_margin":       em,
                "exit_multiple":       ex,
                "exit_ev":             ret.exit_ev,
                "equity_at_exit":      ret.equity_at_exit,
                "moic":                ret.moic,
                "irr":                 ret.irr,
                "ending_debt":         ret.ending_debt,
                "any_covenant_breach": any_breach,
            })

        except (ValueError, ZeroDivisionError, FloatingPointError) as e:
            logger.debug("MC simulation skipped: %s", e)
            continue

    return results
