"""
monte_carlo.py — Monte Carlo simulation for the LBO engine.

Runs the full LBO pipeline 1000+ times with randomised key inputs to
produce a probability distribution of investor returns and covenant risk.
"""

import numpy as np

from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.covenants import check_covenants

# --- Random input distributions (Normal, clipped to avoid absurd values) ---
RG_MEAN, RG_STD, RG_MIN, RG_MAX = 0.06, 0.02, -0.05, 0.20   # revenue_growth
EM_MEAN, EM_STD, EM_MIN, EM_MAX = 0.25, 0.02,  0.10, 0.50   # ebitda_margin
EX_MEAN, EX_STD, EX_MIN, EX_MAX = 9.0,  1.0,   4.0,  16.0   # exit_multiple

# --- Return hurdles for probability metrics ---
IRR_HURDLE  = 0.20   # 20% IRR target
MOIC_HURDLE = 2.0    # 2.0x MOIC target


def run_monte_carlo(base_config: dict, n_simulations: int = 1000) -> list:
    """
    Run the full LBO pipeline n_simulations times with randomised inputs.

    Three inputs are drawn from clipped Normal distributions each iteration:
    revenue_growth, ebitda_margin, exit_multiple. All other parameters
    remain fixed from base_config.

    DealModel is instantiated once before the loop — sponsor equity and
    debt raised are fixed at entry and do not vary across simulations.

    Args:
        base_config (dict): Full config dict loaded from config.yaml.
        n_simulations (int): Number of Monte Carlo iterations (default 1000).

    Returns:
        list[dict]: One dict per successful simulation with keys:
            revenue_growth, ebitda_margin, exit_multiple,
            exit_ev, equity_at_exit, moic, irr, ending_debt, any_covenant_breach.
            Failed simulations (e.g. IRR non-convergence) are silently skipped.
    """
    deal = DealModel(
        entry_ebitda=base_config["entry_ebitda"],
        purchase_multiple=base_config["purchase_multiple"],
        leverage_ratio=base_config["leverage_ratio"],
        fee_pct=base_config["fee_pct"],
    )

    results = []

    for _ in range(n_simulations):
        rg = float(np.clip(np.random.normal(RG_MEAN, RG_STD), RG_MIN, RG_MAX))
        em = float(np.clip(np.random.normal(EM_MEAN, EM_STD), EM_MIN, EM_MAX))
        ex = float(np.clip(np.random.normal(EX_MEAN, EX_STD), EX_MIN, EX_MAX))

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

            covenants = check_covenants(debt, op)
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

        except Exception:
            # Silently skip simulations where IRR fails to converge or other errors occur
            continue

    return results


def compute_mc_statistics(results: list) -> dict:
    """
    Compute summary statistics from Monte Carlo simulation results.

    Args:
        results (list[dict]): Output of run_monte_carlo().

    Returns:
        dict: Summary statistics including IRR/MOIC distributions and
              probability metrics for hurdle rates and covenant breaches.
    """
    irr_arr   = np.array([r["irr"]  for r in results])
    moic_arr  = np.array([r["moic"] for r in results])
    breach_arr = np.array([r["any_covenant_breach"] for r in results], dtype=float)

    return {
        "n_simulations":       len(results),
        "mean_irr":            float(np.mean(irr_arr)),
        "median_irr":          float(np.median(irr_arr)),
        "p5_irr":              float(np.percentile(irr_arr, 5)),
        "p95_irr":             float(np.percentile(irr_arr, 95)),
        "mean_moic":           float(np.mean(moic_arr)),
        "median_moic":         float(np.median(moic_arr)),
        "prob_irr_above_20":   float(np.mean(irr_arr > IRR_HURDLE)),
        "prob_moic_above_2":   float(np.mean(moic_arr > MOIC_HURDLE)),
        "prob_covenant_breach": float(np.mean(breach_arr)),
    }


def print_mc_summary(stats: dict) -> None:
    """
    Print a formatted Monte Carlo results summary to the terminal.

    Args:
        stats (dict): Output of compute_mc_statistics().
    """
    sep = "─" * 44

    print(f"\n{'MONTE CARLO SIMULATION':^44}")
    print(f"  {'Simulations run':<30} {stats['n_simulations']:>10,}")
    print(sep)

    print(f"\n  {'IRR DISTRIBUTION'}")
    print(f"  {'Mean IRR':<30} {stats['mean_irr']*100:>9.1f}%")
    print(f"  {'Median IRR':<30} {stats['median_irr']*100:>9.1f}%")
    print(f"  {'5th Percentile IRR':<30} {stats['p5_irr']*100:>9.1f}%")
    print(f"  {'95th Percentile IRR':<30} {stats['p95_irr']*100:>9.1f}%")

    print(f"\n  {'MOIC DISTRIBUTION'}")
    print(f"  {'Mean MOIC':<30} {stats['mean_moic']:>9.2f}x")
    print(f"  {'Median MOIC':<30} {stats['median_moic']:>9.2f}x")

    print(f"\n  {'PROBABILITY METRICS'}")
    print(f"  {'P(IRR > 20%)':<30} {stats['prob_irr_above_20']*100:>9.1f}%")
    print(f"  {'P(MOIC > 2.0x)':<30} {stats['prob_moic_above_2']*100:>9.1f}%")
    print(f"  {'P(Covenant Breach)':<30} {stats['prob_covenant_breach']*100:>9.1f}%")

    print(f"\n{sep}\n")
