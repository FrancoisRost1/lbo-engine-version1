"""
operating_model.py — Multi-year operating projection for the LBO target.

Projects revenue, EBITDA, and Free Cash Flow over the holding period.
FCF is the cash available each year for debt repayment (feeds DebtSchedule).
"""

import pandas as pd


class OperatingModel:
    """
    Projects the operating performance of the LBO target over the holding period.

    Builds a year-by-year DataFrame of revenue, EBITDA, capex, taxes,
    NWC changes, and Free Cash Flow.

    Simplifying assumptions:
    - Revenue grows at a constant annual rate (no cyclicality).
    - EBITDA margin is stable throughout the holding period.
    - Taxes are applied directly to EBITDA (ignores interest deductibility
      and D&A shield) — this overstates taxes and produces conservative FCF.
    - Delta NWC is the incremental working capital investment: nwc_pct × (Revenue(t) − Revenue(t−1)).
      Year 1 uses entry revenue as the base. Only the change in NWC drains cash.
    - No D&A schedule; capex is treated as a pure cash outflow.
    """

    def __init__(
        self,
        revenue_initial: float,
        revenue_growth: float,
        ebitda_margin: float,
        capex_pct: float,
        nwc_pct: float,
        tax_rate: float,
        holding_period: int,
    ):
        """
        Initialise and run the operating projection.

        Args:
            revenue_initial (float): Year 0 (entry) revenue ($M).
            revenue_growth (float): Annual revenue growth rate (e.g. 0.06 = 6%).
            ebitda_margin (float): EBITDA as a fraction of revenue (e.g. 0.25 = 25%).
            capex_pct (float): Capex as a fraction of revenue (e.g. 0.03 = 3%).
            nwc_pct (float): NWC investment as a fraction of revenue (e.g. 0.02 = 2%).
            tax_rate (float): Effective tax rate applied to EBITDA (e.g. 0.25 = 25%).
            holding_period (int): Number of projection years (typically 5).
        """
        self.revenue_initial = revenue_initial
        self.revenue_growth = revenue_growth
        self.ebitda_margin = ebitda_margin
        self.capex_pct = capex_pct
        self.nwc_pct = nwc_pct
        self.tax_rate = tax_rate
        self.holding_period = holding_period

        self.projection: pd.DataFrame = self.build()

    def build(self) -> pd.DataFrame:
        """
        Run the year-by-year operating projection and store as self.projection.

        Returns:
            pd.DataFrame: Columns = [Year, Revenue, EBITDA, Capex, Taxes, Delta_NWC, FCF].
                          One row per year from Year 1 to holding_period.
        """
        rows = []
        prev_revenue = self.revenue_initial
        revenue = self.revenue_initial

        for t in range(1, self.holding_period + 1):
            revenue = revenue * (1 + self.revenue_growth)
            ebitda = revenue * self.ebitda_margin
            capex = revenue * self.capex_pct
            # Simplified tax: applied to EBITDA (ignores interest shield and D&A)
            taxes = ebitda * self.tax_rate
            # ΔNWC = incremental working capital tied up as revenue grows
            delta_nwc = (revenue - prev_revenue) * self.nwc_pct
            fcf = ebitda - capex - taxes - delta_nwc
            prev_revenue = revenue

            rows.append({
                "Year":      t,
                "Revenue":   revenue,
                "EBITDA":    ebitda,
                "Capex":     capex,
                "Taxes":     taxes,
                "Delta_NWC": delta_nwc,
                "FCF":       fcf,
            })

        self.projection = pd.DataFrame(rows)
        return self.projection

    def get_fcf_series(self) -> list:
        """
        Return the FCF values for all projected years as a plain list.

        Returns:
            list[float]: FCF in $M for Year 1 through holding_period.
        """
        return self.projection["FCF"].tolist()

    def get_ebitda_by_year(self, year: int) -> float:
        """
        Return EBITDA for a specific projection year.

        Args:
            year (int): Year number (1-indexed, e.g. 5 for exit year).

        Returns:
            float: EBITDA in $M for the requested year.

        Raises:
            ValueError: If year is outside the projection range.
        """
        row = self.projection[self.projection["Year"] == year]
        if row.empty:
            raise ValueError(f"Year {year} is outside the projection range (1–{self.holding_period}).")
        return float(row["EBITDA"].iloc[0])

    def print_summary(self) -> None:
        """Print the operating projection as a formatted table to the terminal."""
        sep = "─" * 66
        print(f"\n{f'OPERATING MODEL — {self.holding_period}-YEAR PROJECTION':^66}")
        print(sep)
        print(f"  {'Year':>4}  {'Revenue':>10}  {'EBITDA':>10}  {'Capex':>8}  "
              f"{'Taxes':>8}  {'ΔNWC':>8}  {'FCF':>8}")
        print(f"  {'':>4}  {'($M)':>10}  {'($M)':>10}  {'($M)':>8}  "
              f"{'($M)':>8}  {'($M)':>8}  {'($M)':>8}")
        print(f"  {sep[2:]}")

        for _, row in self.projection.iterrows():
            print(
                f"  {int(row['Year']):>4}  "
                f"{row['Revenue']:>10.1f}  "
                f"{row['EBITDA']:>10.1f}  "
                f"{row['Capex']:>8.1f}  "
                f"{row['Taxes']:>8.1f}  "
                f"{row['Delta_NWC']:>8.1f}  "
                f"{row['FCF']:>8.1f}"
            )

        print(f"  {sep[2:]}")
        print(f"  Note: Taxes applied to EBITDA (simplified — no interest/D&A shield)")
        print(f"\n{sep}\n")
