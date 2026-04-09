"""
mc_stats.py — Summary statistics and display for Monte Carlo simulation results.

Separated from monte_carlo.py to keep each module under 150 lines.
"""

import numpy as np


def compute_mc_statistics(results: list, cfg: dict = None) -> dict:
    """
    Compute summary statistics from Monte Carlo simulation results.

    Args:
        results (list[dict]): Output of run_monte_carlo().
        cfg (dict, optional): Config dict; hurdles read from monte_carlo.hurdles.

    Returns:
        dict: Summary statistics including IRR/MOIC distributions and
              probability metrics for hurdle rates and covenant breaches.
    """
    if not results:
        return {k: 0 for k in (
            "n_simulations", "mean_irr", "median_irr", "p5_irr", "p95_irr",
            "mean_moic", "median_moic", "prob_irr_above_20",
            "prob_moic_above_2", "prob_covenant_breach",
        )}

    mc_cfg = (cfg or {}).get("monte_carlo", {})
    hurdles = mc_cfg.get("hurdles", {})
    irr_hurdle = hurdles.get("irr", 0.20)
    moic_hurdle = hurdles.get("moic", 2.0)

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
        "prob_irr_above_20":   float(np.mean(irr_arr > irr_hurdle)),
        "prob_moic_above_2":   float(np.mean(moic_arr > moic_hurdle)),
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
