"""
deal_model.py — Entry-side LBO deal structure (Sources & Uses).

This module computes how a PE fund structures the acquisition:
  - How much total capital is needed (Uses)
  - How it is funded between debt and equity (Sources)
"""


class DealModel:
    """
    Represents the Sources & Uses table for an LBO transaction.

    Computes the capital structure at entry based on four inputs:
    entry EBITDA, purchase multiple, leverage ratio, and transaction fees.

    Simplifying assumptions:
    - Fees are calculated on Entry EV (not Total Uses) — standard market practice.
    - Fees are entirely funded by sponsor equity (conservative assumption).
    - A single tranche of debt is used (no senior/mezzanine split in V1).
    - No rollover equity from management or sellers is modelled.
    - Debt raised = leverage_ratio × Entry EV (not × Total Uses).
    """

    def __init__(
        self,
        entry_ebitda: float,
        purchase_multiple: float,
        leverage_ratio: float,
        fee_pct: float,
    ):
        """
        Initialise and compute the deal structure.

        Args:
            entry_ebitda (float): LTM EBITDA of the target at acquisition ($M).
            purchase_multiple (float): Entry EV / EBITDA multiple (e.g. 10.0).
            leverage_ratio (float): Debt as a fraction of Entry EV (e.g. 0.60 = 60%).
            fee_pct (float): Transaction fees as a fraction of Entry EV (e.g. 0.02 = 2%).
        """
        self.entry_ebitda = entry_ebitda
        self.purchase_multiple = purchase_multiple
        self.leverage_ratio = leverage_ratio
        self.fee_pct = fee_pct

        # --- Uses of Funds ---
        self.entry_ev = entry_ebitda * purchase_multiple
        self.fees = self.entry_ev * fee_pct
        self.total_uses = self.entry_ev + self.fees

        # --- Sources of Funds ---
        # Debt is sized on EV, not total uses (fees are an equity cost)
        self.debt_raised = self.entry_ev * leverage_ratio
        self.sponsor_equity = self.total_uses - self.debt_raised

        # Derived ratio for reference
        self.equity_ratio = self.sponsor_equity / self.total_uses

    def summary(self) -> dict:
        """
        Return the full deal structure as a dictionary.

        Returns:
            dict: Keys are descriptive labels, values are floats in $M.
        """
        return {
            # Inputs
            "Entry EBITDA ($M)":        self.entry_ebitda,
            "Purchase Multiple (x)":    self.purchase_multiple,
            "Leverage Ratio (%)":       self.leverage_ratio * 100,
            "Fee % of EV (%)":          self.fee_pct * 100,
            # Uses
            "Entry EV ($M)":            self.entry_ev,
            "Transaction Fees ($M)":    self.fees,
            "Total Uses ($M)":          self.total_uses,
            # Sources
            "Debt Raised ($M)":         self.debt_raised,
            "Sponsor Equity ($M)":      self.sponsor_equity,
            "Equity % of Uses (%)":     self.equity_ratio * 100,
        }

    def print_summary(self) -> None:
        """
        Print a formatted Sources & Uses table to the terminal.

        Layout:
            USES section  (purchase price + fees)
            SOURCES section  (debt + equity)
        """
        sep = "─" * 44

        print(f"\n{'LBO DEAL MODEL — SOURCES & USES':^44}")
        print(sep)

        print(f"\n  {'USES OF FUNDS'}")
        print(f"  {'Purchase Price (Entry EV)':<30} ${self.entry_ev:>8.1f}M")
        print(f"  {'Transaction Fees':<30} ${self.fees:>8.1f}M")
        print(f"  {sep[2:]}")
        print(f"  {'Total Uses':<30} ${self.total_uses:>8.1f}M")

        print(f"\n  {'SOURCES OF FUNDS'}")
        print(f"  {'Debt Raised':<30} ${self.debt_raised:>8.1f}M"
              f"  ({self.leverage_ratio*100:.0f}% of EV)")
        print(f"  {'Sponsor Equity':<30} ${self.sponsor_equity:>8.1f}M"
              f"  ({self.equity_ratio*100:.0f}% of Uses)")
        print(f"  {sep[2:]}")
        print(f"  {'Total Sources':<30} ${self.total_uses:>8.1f}M")

        print(f"\n  Entry Multiple : {self.purchase_multiple:.1f}x EBITDA")
        print(f"  Debt / EBITDA  : {self.debt_raised / self.entry_ebitda:.1f}x")
        print(f"\n{sep}\n")
