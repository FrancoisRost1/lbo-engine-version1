"""
covenants.py — Annual covenant compliance checks for an LBO.

Tests leverage and interest coverage covenants each year of the holding period.
A breach signals potential lender intervention or default risk.
"""

from lbo.debt_schedule import DebtSchedule
from lbo.operating_model import OperatingModel

# --- Covenant thresholds (lender-defined limits) ---
LEVERAGE_THRESHOLD = 6.0   # Maximum Debt / EBITDA allowed
COVERAGE_THRESHOLD = 2.0   # Minimum EBITDA / Interest required


def check_covenants(debt_schedule: DebtSchedule, operating_model: OperatingModel) -> list:
    """
    Test leverage and coverage covenants for every year of the holding period.

    Leverage covenant : Opening_Debt / EBITDA  <= LEVERAGE_THRESHOLD
    Coverage covenant : EBITDA / Interest      >= COVERAGE_THRESHOLD

    Args:
        debt_schedule (DebtSchedule): Built debt schedule object (provides Opening_Debt, Interest).
        operating_model (OperatingModel): Built operating model object (provides EBITDA).

    Returns:
        list[dict]: One dict per year with keys:
            year, leverage_ratio, leverage_breach,
            coverage_ratio, coverage_breach, any_breach.
    """
    results = []

    for _, debt_row in debt_schedule.schedule.iterrows():
        year = int(debt_row["Year"])
        ebitda = operating_model.get_ebitda_by_year(year)
        opening_debt = debt_row["Opening_Debt"]
        interest = debt_row["Interest"]

        leverage_ratio = opening_debt / ebitda
        coverage_ratio = ebitda / interest

        leverage_breach = leverage_ratio > LEVERAGE_THRESHOLD
        coverage_breach = coverage_ratio < COVERAGE_THRESHOLD

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
    print(f"  {'Year':>4}  {'Lev. Ratio':>10}  {'(<=6.0x)':>10}  "
          f"{'Cov. Ratio':>10}  {'(>=2.0x)':>10}")
    print(f"  {sep[2:]}")

    any_breach_overall = False
    for r in results:
        lev_status = "⚠ BREACH" if r["leverage_breach"] else "OK"
        cov_status = "⚠ BREACH" if r["coverage_breach"] else "OK"
        if r["any_breach"]:
            any_breach_overall = True
        print(
            f"  {r['year']:>4}  "
            f"{r['leverage_ratio']:>10.2f}x  "
            f"{lev_status:>10}  "
            f"{r['coverage_ratio']:>10.2f}x  "
            f"{cov_status:>10}"
        )

    print(f"  {sep[2:]}")
    overall = "⚠  One or more covenant breaches detected" if any_breach_overall else "✓  All covenants passed"
    print(f"  {overall}")
    print(f"\n{sep}\n")
