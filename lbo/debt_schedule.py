"""
debt_schedule.py — Annual debt repayment schedule for an LBO.

Models how the LBO debt is paid down each year via mandatory amortization
and optional cash sweep from Free Cash Flow.
"""

import pandas as pd


class DebtSchedule:
    """
    Builds the year-by-year debt repayment schedule for an LBO transaction.

    Each year, FCF is used to cover interest expense and mandatory amortization.
    Any remaining cash is swept against the debt balance (optional repayment).

    Simplifying assumptions:
    - Interest is computed on the opening debt balance (not the average balance).
    - A single blended interest rate applies to the full debt stack.
    - Debt cannot go below zero (floor at 0).
    - No minimum cash balance is maintained.
    - No refinancing or PIK toggle is modelled.
    - cash_after_debt can be negative (FCF < interest + mandatory) — signals a
      cash shortfall; optional repayment is simply zero in that case.
    """

    def __init__(
        self,
        debt_raised: float,
        fcf_series: list,
        interest_rate: float,
        amortization_rate: float,
        cash_sweep: float,
    ):
        """
        Initialise and build the debt schedule.

        Args:
            debt_raised (float): Initial LBO debt at close ($M).
            fcf_series (list[float]): FCF for each year of the holding period ($M).
            interest_rate (float): Annual interest rate on outstanding debt (e.g. 0.08).
            amortization_rate (float): Mandatory annual repayment as % of opening debt (e.g. 0.05).
            cash_sweep (float): Fraction of excess cash applied to optional repayment (e.g. 1.0).
        """
        self.debt_raised = debt_raised
        self.fcf_series = fcf_series
        self.interest_rate = interest_rate
        self.amortization_rate = amortization_rate
        self.cash_sweep = cash_sweep

        self.schedule: pd.DataFrame = self.build()

    def build(self) -> pd.DataFrame:
        """
        Run the year-by-year debt repayment projection.

        Returns:
            pd.DataFrame: Columns = [Year, Opening_Debt, Interest, Mandatory_Repayment,
                          Cash_after_debt, Optional_Repayment, Ending_Debt].
        """
        rows = []
        opening_debt = self.debt_raised

        for t, fcf in enumerate(self.fcf_series, start=1):
            interest = opening_debt * self.interest_rate
            mandatory = opening_debt * self.amortization_rate
            cash_after = fcf - interest - mandatory
            # cash_after can be negative (cash shortfall) — optional repayment floored at 0
            optional = max(0.0, cash_after) * self.cash_sweep

            # Debt cannot go negative
            ending_debt = max(0.0, opening_debt - mandatory - optional)

            rows.append({
                "Year":                 t,
                "Opening_Debt":         opening_debt,
                "Interest":             interest,
                "Mandatory_Repayment":  mandatory,
                "Cash_after_debt":      cash_after,
                "Optional_Repayment":   optional,
                "Ending_Debt":          ending_debt,
            })

            opening_debt = ending_debt

        self.schedule = pd.DataFrame(rows)
        return self.schedule

    def get_ending_debt(self, year: int) -> float:
        """
        Return the ending debt balance for a given year.

        Args:
            year (int): Year number (1-indexed).

        Returns:
            float: Ending debt balance in $M.

        Raises:
            ValueError: If year is outside the schedule range.
        """
        row = self.schedule[self.schedule["Year"] == year]
        if row.empty:
            raise ValueError(f"Year {year} is outside the schedule range (1–{len(self.fcf_series)}).")
        return float(row["Ending_Debt"].iloc[0])

    def print_summary(self) -> None:
        """
        Print the debt schedule as a formatted table to the terminal.
        """
        sep = "─" * 74

        print(f"\n{'DEBT SCHEDULE':^74}")
        print(sep)
        print(f"  {'Year':>4}  {'Open Debt':>10}  {'Interest':>9}  {'Mandatory':>9}  "
              f"{'Cash Left':>9}  {'Optional':>9}  {'End Debt':>9}")
        print(f"  {'':>4}  {'($M)':>10}  {'($M)':>9}  {'($M)':>9}  "
              f"{'($M)':>9}  {'($M)':>9}  {'($M)':>9}")
        print(f"  {sep[2:]}")

        for _, row in self.schedule.iterrows():
            print(
                f"  {int(row['Year']):>4}  "
                f"{row['Opening_Debt']:>10.1f}  "
                f"{row['Interest']:>9.1f}  "
                f"{row['Mandatory_Repayment']:>9.1f}  "
                f"{row['Cash_after_debt']:>9.1f}  "
                f"{row['Optional_Repayment']:>9.1f}  "
                f"{row['Ending_Debt']:>9.1f}"
            )

        final_debt = self.schedule["Ending_Debt"].iloc[-1]
        total_repaid = self.debt_raised - final_debt
        print(f"  {sep[2:]}")
        print(f"  Initial Debt : ${self.debt_raised:.1f}M  →  "
              f"Ending Debt : ${final_debt:.1f}M  "
              f"(${total_repaid:.1f}M repaid)")
        print(f"  Note: Interest on opening balance; debt floored at $0M")
        print(f"\n{sep}\n")
