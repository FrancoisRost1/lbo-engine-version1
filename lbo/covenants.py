"""
covenants.py — Annual covenant compliance checks for an LBO.

Tests leverage and interest coverage covenants each year of the holding period.
A breach signals potential lender intervention or default risk.
"""

import numpy as np

from lbo.debt_schedule import DebtSchedule
from lbo.operating_model import OperatingModel


def check_covenants(debt_schedule: DebtSchedule, operating_model: OperatingModel,
                    cfg: dict = None) -> list:
    """
    Test leverage and coverage covenants for every year of the holding period.

    Leverage covenant : Opening_Debt / EBITDA  <= leverage_threshold
    Coverage covenant : EBITDA / Interest      >= coverage_threshold

    Thresholds are loaded from cfg["covenants"]. Falls back to 6.0x / 2.0x
    if cfg is not provided (backward compatibility).

    Args:
        debt_schedule (DebtSchedule): Built debt schedule object (provides Opening_Debt, Interest).
        operating_model (OperatingModel): Built operating model object (provides EBITDA).
        cfg (dict, optional): Config dict with covenants.leverage_threshold and
            covenants.coverage_threshold.

    Returns:
        list[dict]: One dict per year with keys:
            year, leverage_ratio, leverage_breach,
            coverage_ratio, coverage_breach, any_breach.
    """
    cov_cfg = (cfg or {}).get("covenants", {})
    leverage_threshold = cov_cfg.get("leverage_threshold", 6.0)
    coverage_threshold = cov_cfg.get("coverage_threshold", 2.0)

    results = []

    for _, debt_row in debt_schedule.schedule.iterrows():
        year = int(debt_row["Year"])
        ebitda = operating_model.get_ebitda_by_year(year)
        opening_debt = debt_row["Opening_Debt"]
        interest = debt_row["Interest"]

        # Guard: EBITDA <= 0 → leverage ratio is undefined
        if ebitda <= 0:
            leverage_ratio = np.nan
        else:
            leverage_ratio = opening_debt / ebitda

        # Guard: interest == 0 (debt fully repaid) → coverage is infinite (no breach)
        if interest == 0:
            coverage_ratio = np.nan
        else:
            coverage_ratio = ebitda / interest

        leverage_breach = (
            False if np.isnan(leverage_ratio) else leverage_ratio > leverage_threshold
        )
        coverage_breach = (
            False if np.isnan(coverage_ratio) else coverage_ratio < coverage_threshold
        )

        results.append({
            "year":             year,
            "leverage_ratio":   leverage_ratio,
            "leverage_breach":  leverage_breach,
            "coverage_ratio":   coverage_ratio,
            "coverage_breach":  coverage_breach,
            "any_breach":       leverage_breach or coverage_breach,
        })

    return results


def print_covenant_summary(results: list) -> None:
    """
    Print the annual covenant compliance table to the terminal.

    Breached covenants are flagged with a warning indicator.

    Args:
        results (list[dict]): Output of check_covenants().
    """
    sep = "─" * 62

    print(f"\n{'COVENANT COMPLIANCE':^62}")
    print(sep)
    print(f"  {'Year':>4}  {'Lev. Ratio':>10}  {'Threshold':>10}  "
          f"{'Cov. Ratio':>10}  {'Threshold':>10}")
    print(f"  {sep[2:]}")

    any_breach_overall = False
    for r in results:
        lev_status = "⚠ BREACH" if r["leverage_breach"] else ("N/A" if np.isnan(r["leverage_ratio"]) else "OK")
        cov_status = "⚠ BREACH" if r["coverage_breach"] else ("N/A" if np.isnan(r["coverage_ratio"]) else "OK")
        if r["any_breach"]:
            any_breach_overall = True
        lev_str = f"{r['leverage_ratio']:>10.2f}x" if not np.isnan(r['leverage_ratio']) else f"{'N/A':>11}"
        cov_str = f"{r['coverage_ratio']:>10.2f}x" if not np.isnan(r['coverage_ratio']) else f"{'N/A':>11}"
        print(
            f"  {r['year']:>4}  "
            f"{lev_str}  "
            f"{lev_status:>10}  "
            f"{cov_str}  "
            f"{cov_status:>10}"
        )

    print(f"  {sep[2:]}")
    overall = "⚠  One or more covenant breaches detected" if any_breach_overall else "✓  All covenants passed"
    print(f"  {overall}")
    print(f"\n{sep}\n")
