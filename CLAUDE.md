# CLAUDE.md — LBO Engine Project Instructions

This file is auto-loaded by Claude Code. Read it fully before doing anything.

---

## What this project is

A professional LBO (Leveraged Buyout) simulation engine in Python.
Built by a CFA student as a GitHub portfolio project.
First Python project — code must be clean, well-documented, and beginner-friendly.

Core question the tool answers:
> "If a PE fund buys a company at a given multiple, with a given debt structure,
> and sells it in X years — how much does it make?"

---

## How we work

**Always show a plan before writing any code.**
Wait for the user to confirm the plan before executing.

---

## Repo structure

```
lbo-engine/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── main.py                  # Orchestrator only — no financial logic here
├── config.yaml              # All base case assumptions live here
│
├── lbo/
│   ├── __init__.py
│   ├── deal_model.py        # ✅ Done — Entry EV, Sources & Uses, sponsor equity
│   ├── operating_model.py   # ✅ Done — Revenue, EBITDA, FCF projection
│   ├── debt_schedule.py     # ✅ Done — Interest, amortization, cash sweep
│   ├── returns.py           # ✅ Done — Exit EV, MOIC, IRR
│   ├── covenants.py         # ✅ Done — Leverage & coverage breach detection
│   ├── scenarios.py         # ✅ Done — Downside / Base / Upside
│   ├── monte_carlo.py       # ⏳ Next — 1000+ simulations
│   ├── waterfall.py         # ⏳ Planned — Year-by-year cash flow waterfall
│   ├── valuation.py         # ⏳ Planned — Entry & exit multiple valuation
│   └── utils.py             # ⏳ Planned — Helpers, CSV export, formatting
│
├── data/
│   ├── base_case.json
│   ├── upside_case.json
│   └── downside_case.json
│
├── tests/
│   ├── test_deal_model.py
│   ├── test_debt_schedule.py
│   ├── test_returns.py
│   └── test_covenants.py
│
├── notebooks/
│   └── lbo_demo.ipynb
│
├── app/
│   └── streamlit_app.py     # ⏳ Planned — Interactive Streamlit UI
│
└── outputs/
    ├── base_case_results.csv
    ├── debt_schedule.csv
    ├── sensitivity_table.csv
    └── monte_carlo_summary.csv
```

---

## Build versions — what is done vs planned

| Version | Scope | Status |
|---------|-------|--------|
| V1 | Scaffold + DealModel (entry deal, Sources & Uses) | ✅ Done |
| V2 | OperatingModel + DebtSchedule + Returns (IRR/MOIC) | ✅ Done |
| V3 | Covenants + Scenarios + Sensitivity tables | ✅ Done |
| V4 | Monte Carlo + Streamlit app + Unit tests | ⏳ Next |

---

## Code style — always follow these rules

- Mix of classes and pure functions
- Classes for core objects: `DealModel`, `OperatingModel`, `DebtSchedule`
- Pure functions for utilities and helpers
- Docstring on every class and every method
- All simplifying assumptions documented in inline comments
- No file longer than ~150 lines — split if needed
- `main.py` is an orchestrator only — all logic lives in `lbo/` modules
- Never hardcode numbers — everything comes from `config.yaml`

---

## Financial logic reference

### deal_model.py ✅
```
entry_ev        = entry_ebitda × purchase_multiple
fees            = entry_ev × fee_pct
total_uses      = entry_ev + fees
debt_raised     = entry_ev × leverage_ratio
sponsor_equity  = total_uses - debt_raised
# Assumption: fees funded by equity (conservative)
```

### operating_model.py ⏳
```
Revenue(t)  = Revenue(t-1) × (1 + revenue_growth)
EBITDA(t)   = Revenue(t) × ebitda_margin
Capex(t)    = Revenue(t) × capex_pct
Taxes(t)    = EBITDA(t) × tax_rate        # Simplified: on EBITDA not EBT
ΔNWC(t)     = Revenue(t) × nwc_pct
FCF(t)      = EBITDA(t) - Capex(t) - Taxes(t) - ΔNWC(t)
```

### debt_schedule.py ⏳
```
Interest(t)             = Opening_Debt(t) × interest_rate
Mandatory_Repayment(t)  = Opening_Debt(t) × amortization_rate
Cash_after_debt(t)      = FCF(t) - Interest(t) - Mandatory_Repayment(t)
Optional_Repayment(t)   = max(0, Cash_after_debt(t)) × cash_sweep
Ending_Debt(t)          = Opening_Debt(t) - Mandatory_Repayment(t) - Optional_Repayment(t)
# Assumption: interest on opening balance (not average)
```

### returns.py ⏳
```
Exit_EV        = Exit_EBITDA × exit_multiple
Equity_at_Exit = Exit_EV - Ending_Debt(final year)
MOIC           = Equity_at_Exit / sponsor_equity
IRR            = numpy_financial.irr([-sponsor_equity, 0, 0, 0, 0, equity_at_exit])
```

### covenants.py ⏳
```
Leverage covenant : Total_Debt / EBITDA <= 6.0x
Coverage covenant : EBITDA / Interest   >= 2.0x
# Check every year, flag breach with year + actual value vs limit
```

---

## config.yaml parameters

```yaml
entry_ebitda: 50.0
purchase_multiple: 10.0
leverage_ratio: 0.60
fee_pct: 0.02
revenue_initial: 200.0
revenue_growth: 0.06
ebitda_margin: 0.25
capex_pct: 0.03
nwc_pct: 0.02
tax_rate: 0.25
holding_period: 5
interest_rate: 0.08
amortization_rate: 0.05
cash_sweep: 1.0
exit_multiple: 9.0
```

---

## Simplifying assumptions (acceptable — all documented in code)

- Taxes on EBITDA, not EBT
- Interest on opening debt balance, not average
- No minimum cash balance
- No working capital seasonality
- No refinancing at maturity
- Exit at end of fiscal year
- No management rollover
- No dividend recap
- Single debt tranche in V1/V2 (multi-tranche in V3+)
- Fees funded by equity

---

## Dependencies

```
pandas
numpy
numpy-financial
pyyaml
streamlit
plotly
pytest
```
