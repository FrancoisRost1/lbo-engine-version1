"""
main.py — LBO Engine CLI entry point.

Loads base-case assumptions from config.yaml, builds the deal model,
and prints the Sources & Uses summary to the terminal.
"""

import yaml
from lbo.deal_model import DealModel
from lbo.operating_model import OperatingModel
from lbo.debt_schedule import DebtSchedule
from lbo.returns import Returns
from lbo.covenants import check_covenants, print_covenant_summary
from lbo.scenarios import run_scenarios, print_scenario_summary
from lbo.monte_carlo import run_monte_carlo, compute_mc_statistics, print_mc_summary


def load_config(path: str = "config.yaml") -> dict:
    """Load YAML configuration file and return as a dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    deal = DealModel(
        entry_ebitda=config["entry_ebitda"],
        purchase_multiple=config["purchase_multiple"],
        leverage_ratio=config["leverage_ratio"],
        fee_pct=config["fee_pct"],
    )

    deal.print_summary()

    op = OperatingModel(
        revenue_initial=config["revenue_initial"],
        revenue_growth=config["revenue_growth"],
        ebitda_margin=config["ebitda_margin"],
        capex_pct=config["capex_pct"],
        nwc_pct=config["nwc_pct"],
        tax_rate=config["tax_rate"],
        holding_period=config["holding_period"],
    )
    op.print_summary()

    debt = DebtSchedule(
        debt_raised=deal.debt_raised,
        fcf_series=op.get_fcf_series(),
        interest_rate=config["interest_rate"],
        amortization_rate=config["amortization_rate"],
        cash_sweep=config["cash_sweep"],
    )
    debt.print_summary()

    ret = Returns(
        exit_ebitda=op.get_ebitda_by_year(config["holding_period"]),
        exit_multiple=config["exit_multiple"],
        ending_debt=debt.get_ending_debt(config["holding_period"]),
        sponsor_equity=deal.sponsor_equity,
        holding_period=config["holding_period"],
    )
    ret.print_summary()

    covenant_results = check_covenants(debt, op)
    print_covenant_summary(covenant_results)

    scenario_results = run_scenarios(config)
    print_scenario_summary(scenario_results)

    mc_results = run_monte_carlo(config, n_simulations=1000)
    mc_stats = compute_mc_statistics(mc_results)
    print_mc_summary(mc_stats)


if __name__ == "__main__":
    main()
