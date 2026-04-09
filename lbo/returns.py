"""
returns.py — Exit valuation and investor returns for an LBO.

Computes Exit EV, equity value at exit, MOIC, and IRR from the
perspective of the sponsor (PE fund).
"""

import logging

import numpy as np
import numpy_financial as npf

logger = logging.getLogger(__name__)


class Returns:
    """
    Computes LBO exit returns for the sponsor equity investor.

    Takes the exit EBITDA, exit multiple, residual debt at exit,
    sponsor equity invested at entry, and holding period to derive:
    - Exit Enterprise Value
    - Equity value at exit (after debt repayment)
    - MOIC (Multiple on Invested Capital)
    - IRR (Internal Rate of Return)

    Simplifying assumptions:
    - Exit occurs at the end of the final holding period year (no mid-year convention).
    - No transaction fees or taxes at exit.
    - No management equity or option pool dilution at exit.
    - IRR cash flows: equity outflow at Year 0, no interim dividends, equity inflow at exit.
    - Equity at exit cannot go below zero (distressed scenario floor).
    """

    def __init__(
        self,
        exit_ebitda: float,
        exit_multiple: float,
        ending_debt: float,
        sponsor_equity: float,
        holding_period: int,
    ):
        """
        Initialise and compute exit returns.

        Args:
            exit_ebitda (float): EBITDA in the final projection year ($M).
            exit_multiple (float): EV / EBITDA multiple at exit (e.g. 9.0).
            ending_debt (float): Residual debt at end of holding period ($M).
            sponsor_equity (float): Equity invested by sponsor at entry ($M).
            holding_period (int): Number of years from entry to exit.
        """
        self.exit_ebitda = exit_ebitda
        self.exit_multiple = exit_multiple
        self.ending_debt = ending_debt
        self.sponsor_equity = sponsor_equity
        self.holding_period = holding_period

        # --- Exit valuation ---
        self.exit_ev = exit_ebitda * exit_multiple
        # Equity at exit: residual EV after repaying all remaining debt
        self.equity_at_exit = max(0.0, self.exit_ev - ending_debt)

        # --- Returns ---
        if sponsor_equity == 0:
            self.moic = np.nan
            logger.warning("Sponsor equity is zero — MOIC undefined")
        else:
            self.moic = self.equity_at_exit / sponsor_equity

        # IRR cash flow vector: [-equity_in, 0, 0, ..., equity_out]
        # No interim dividends assumed
        cf = [-sponsor_equity] + [0.0] * (holding_period - 1) + [self.equity_at_exit]
        self.irr = npf.irr(cf)

        if self.irr is None or (isinstance(self.irr, float) and np.isnan(self.irr)):
            self.irr = np.nan
            logger.warning("IRR solver did not converge — set to NaN")

    def summary(self) -> dict:
        """
        Return all exit metrics as a labeled dictionary.

        Returns:
            dict: Keys are descriptive labels, values are floats.
        """
        return {
            "Exit EBITDA ($M)":       self.exit_ebitda,
            "Exit Multiple (x)":      self.exit_multiple,
            "Exit EV ($M)":           self.exit_ev,
            "Ending Debt ($M)":       self.ending_debt,
            "Equity at Exit ($M)":    self.equity_at_exit,
            "Sponsor Equity In ($M)": self.sponsor_equity,
            "MOIC (x)":               self.moic,
            "IRR (%)":                self.irr * 100 if not np.isnan(self.irr) else np.nan,
        }

    def print_summary(self) -> None:
        """
        Print the exit valuation and investor returns to the terminal.
        """
        sep = "─" * 44

        print(f"\n{'LBO RETURNS — EXIT ANALYSIS':^44}")
        print(sep)

        print(f"\n  {'EXIT VALUATION'}")
        print(f"  {'Exit EBITDA':<28} ${self.exit_ebitda:>8.1f}M")
        print(f"  {'Exit Multiple':<28} {self.exit_multiple:>9.1f}x")
        print(f"  {'Exit EV':<28} ${self.exit_ev:>8.1f}M")
        print(f"  {'(-) Ending Debt':<28} ${self.ending_debt:>8.1f}M")
        print(f"  {sep[2:]}")
        print(f"  {'Equity at Exit':<28} ${self.equity_at_exit:>8.1f}M")

        print(f"\n  {'INVESTOR RETURNS'}")
        print(f"  {'Sponsor Equity Invested':<28} ${self.sponsor_equity:>8.1f}M")
        print(f"  {'Holding Period':<28} {self.holding_period:>9d} yrs")
        print(f"  {sep[2:]}")
        moic_str = f"{self.moic:>9.2f}x" if not np.isnan(self.moic) else f"{'N/A':>10}"
        irr_str = f"{self.irr*100:>8.1f}%" if not np.isnan(self.irr) else f"{'N/A':>9}"
        print(f"  {'MOIC':<28} {moic_str}")
        print(f"  {'IRR':<28} {irr_str}")

        print(f"\n{sep}\n")
