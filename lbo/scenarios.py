"""
scenarios.py — Multi-scenario analysis for the LBO engine.

Runs the full pipeline (OperatingModel → DebtSchedule → Returns → covenants)
under Downside, Base, and Upside assumptions and returns a comparison summary.
"""

from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.covenants import check_covenants

# --- Scenario overrides (only these three parameters vary across scenarios) ---
SCENARIOS = {
    "Downside": {"revenue_growth": 0.03, "ebitda_margin": 0.22, "exit_multiple": 8.0},
    "Base":     {"revenue_growth": 0.06, "ebitda_margin": 0.25, "exit_multiple": 9.0},
    "Upside":   {"revenue_growth": 0.09, "ebitda_margin": 0.27, "exit_multiple": 10.0},
}


def run_scenarios(base_config: dict) -> dict:
    """
    Run the full LBO pipeline for each scenario and return a results summary.

    For each scenario, overrides revenue_growth, ebitda_margin, and exit_multiple
    from SCENARIOS while keeping all other parameters from base_config unchanged.

    Pipeline per scenario:
        OperatingModel → DebtSchedule → Returns → check_covenants

    Args:
        base_config (dict): Full config dict loaded from config.yaml.

    Returns:
        dict: Keys are scenario names ("Downside", "Base", "Upside").
              Each value is a dict with:
                  exit_ev, equity_at_exit, moic, irr,
                  ending_debt, any_covenant_breach.
    """
    # Sponsor equity is fixed at entry — same across all scenarios
    from lbo.deal_model import DealModel
    deal = DealModel(
        entry_ebitda=base_config["entry_ebitda"],
        purchase_multiple=base_config["purchase_multiple"],
        leverage_ratio=base_config["leverage_ratio"],
        fee_pct=base_config["fee_pct"],
    )

    results = {}

    for name, overrides in SCENARIOS.items():
        cfg = {**base_config, **overrides}

        op = OperatingModel(
            revenue_initial=cfg["revenue_initial"],
            revenue_growth=cfg["revenue_growth"],
            ebitda_margin=cfg["ebitda_margin"],
            capex_pct=cfg["capex_pct"],
            nwc_pct=cfg["nwc_pct"],
            tax_rate=cfg["tax_rate"],
            holding_period=cfg["holding_period"],
        )

        debt = DebtSchedule(
            debt_raised=deal.debt_raised,
            fcf_series=op.get_fcf_series(),
            interest_rate=cfg["interest_rate"],
            amortization_rate=cfg["amortization_rate"],
            cash_sweep=cfg["cash_sweep"],
        )

        ret = Returns(
            exit_ebitda=op.get_ebitda_by_year(cfg["holding_period"]),
            exit_multiple=cfg["exit_multiple"],
            ending_debt=debt.get_ending_debt(cfg["holding_period"]),
            sponsor_equity=deal.sponsor_equity,
            holding_period=cfg["holding_period"],
        )

        covenants = check_covenants(debt, op)
        any_breach = any(r["any_breach"] for r in covenants)

        results[name] = {
            "exit_ev":            ret.exit_ev,
            "equity_at_exit":     ret.equity_at_exit,
            "moic":               ret.moic,
            "irr":                ret.irr,
            "ending_debt":        ret.ending_debt,
            "any_covenant_breach": any_breach,
        }

    return results


def print_scenario_summary(results: dict) -> None:
    """
    Print a side-by-side comparison table for all three scenarios.

    Args:
        results (dict): Output of run_scenarios().
    """
    scenarios = ["Downside", "Base", "Upside"]
    sep = "─" * 62

    print(f"\n{'SCENARIO ANALYSIS':^62}")
    print(sep)
    print(f"  {'':22}  {'Downside':>10}  {'Base':>10}  {'Upside':>10}")
    print(f"  {sep[2:]}")

    rows = [
        ("Exit EV ($M)",        "exit_ev",          "{:>10.1f}"),
        ("Equity at Exit ($M)", "equity_at_exit",   "{:>10.1f}"),
        ("Ending Debt ($M)",    "ending_debt",       "{:>10.1f}"),
        ("MOIC (x)",            "moic",              "{:>10.2f}"),
        ("IRR (%)",             "irr",               "{:>10.1f}"),
    ]

    for label, key, fmt in rows:
        vals = []
        for s in scenarios:
            v = results[s][key]
            if key == "irr":
                v = v * 100
            vals.append(fmt.format(v))
        print(f"  {label:<22}  {'  '.join(vals)}")

    # Covenant breach row
    breach_vals = []
    for s in scenarios:
        breach_vals.append(f"{'⚠ YES':>10}" if results[s]["any_covenant_breach"] else f"{'NO':>10}")
    print(f"  {'Covenant Breach':<22}  {'  '.join(breach_vals)}")

    print(f"\n{sep}\n")
