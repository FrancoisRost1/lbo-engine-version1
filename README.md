# LBO Simulation Engine

A professional Leveraged Buyout (LBO) simulation engine built in Python — models a full PE deal from entry to exit, with scenario analysis, Monte Carlo simulation, and an interactive Streamlit dashboard.

![App Screenshot](screenshot.png)

---

## Features

**Financial Engine (`lbo/`)**
- `deal_model.py` — Entry EV, Sources & Uses, sponsor equity calculation
- `operating_model.py` — Revenue, EBITDA, Capex, tax, and FCF projection
- `debt_schedule.py` — Interest, mandatory amortization, and cash sweep
- `returns.py` — Exit EV, MOIC, and IRR computation
- `covenants.py` — Leverage and coverage covenant breach detection
- `scenarios.py` — Downside / Base / Upside scenario runner
- `monte_carlo.py` — 500-simulation IRR distribution with P5/P95 and breach probability

**Streamlit App (`app/streamlit_app.py`)**
- KPI banner — IRR and MOIC always visible
- Deal Summary and Sources & Uses
- Value Creation Bridge — waterfall chart (EBITDA growth, multiple effect, debt paydown)
- Debt Paydown chart and Cash Flow Waterfall table
- Scenario Analysis — Downside / Base / Upside comparison
- Sensitivity Table — IRR grid across exit multiples and leverage ratios
- Monte Carlo histogram
- IC Memo generator — one-click Investment Committee summary with verdict

---

## Installation

```bash
git clone https://github.com/FrancoisRost1/lbo-engine-version1.git
cd lbo-engine
pip install -r requirements.txt
```

---

## How to Run

**CLI — full pipeline output:**
```bash
python3 main.py
```

**Interactive dashboard:**
```bash
streamlit run app/streamlit_app.py
```

---

## Project Structure

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
│   ├── deal_model.py        # Entry EV, Sources & Uses, sponsor equity
│   ├── operating_model.py   # Revenue, EBITDA, FCF projection
│   ├── debt_schedule.py     # Interest, amortization, cash sweep
│   ├── returns.py           # Exit EV, MOIC, IRR
│   ├── covenants.py         # Leverage & coverage breach detection
│   ├── scenarios.py         # Downside / Base / Upside
│   ├── monte_carlo.py       # 500+ simulations, IRR distribution
│   ├── waterfall.py
│   └── valuation.py
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
├── app/
│   └── streamlit_app.py     # Interactive UI, dark mode, Bloomberg style
│
└── outputs/
    ├── base_case_results.csv
    ├── debt_schedule.csv
    ├── sensitivity_table.csv
    └── monte_carlo_summary.csv
```

---

## Financial Model

### Deal Model
```
Entry EV        = Entry EBITDA × Purchase Multiple
Fees            = Entry EV × Fee %
Total Uses      = Entry EV + Fees
Debt Raised     = Entry EV × Leverage Ratio
Sponsor Equity  = Total Uses − Debt Raised
```

### Operating Model
```
Revenue(t)  = Revenue(t-1) × (1 + Revenue Growth)
EBITDA(t)   = Revenue(t) × EBITDA Margin
Capex(t)    = Revenue(t) × Capex %
Taxes(t)    = EBITDA(t) × Tax Rate
ΔNWC(t)     = Revenue(t) × NWC %
FCF(t)      = EBITDA(t) − Capex(t) − Taxes(t) − ΔNWC(t)
```

### Debt Schedule
```
Interest(t)            = Opening Debt(t) × Interest Rate
Mandatory Repayment(t) = Opening Debt(t) × Amortization Rate
Cash after Debt(t)     = FCF(t) − Interest(t) − Mandatory Repayment(t)
Optional Repayment(t)  = max(0, Cash after Debt(t)) × Cash Sweep
Ending Debt(t)         = Opening Debt(t) − Mandatory − Optional Repayment(t)
```

### Returns
```
Exit EV        = Exit EBITDA × Exit Multiple
Equity at Exit = Exit EV − Ending Debt (final year)
MOIC           = Equity at Exit / Sponsor Equity
IRR            = numpy_financial.irr([−Sponsor Equity, 0, …, Equity at Exit])
```

### Simplifying Assumptions
- Taxes calculated on EBITDA (not EBT)
- Interest on opening debt balance (not average)
- No minimum cash balance
- No working capital seasonality
- No refinancing at maturity
- Exit at end of fiscal year
- Single debt tranche
- Transaction fees funded by equity

---

## Tech Stack

| Library | Purpose |
|---|---|
| Python 3 | Core engine |
| Streamlit | Interactive web dashboard |
| Plotly | Charts (waterfall, histogram, bar) |
| Pandas | DataFrames, scenario tables |
| numpy-financial | IRR calculation |
| PyYAML | Config file parsing |
| pytest | Unit tests |

---

*Built as a CFA portfolio project demonstrating PE financial modelling in Python.*
