"""
tab_ic_memo.py — Tab 5: Investment Committee memo auto-generation.

Produces a one-page IC summary with verdict (STRONG BUY / BUY /
CONDITIONAL BUY / PASS) based on base-case IRR and MOIC.
"""

import streamlit as st


def render(r: dict) -> None:
    """
    Render the IC MEMO tab content.

    Args:
        r (dict): Pipeline results from run_pipeline().
    """
    st.subheader("Investment Committee Summary")

    if st.button("Generate IC Memo", type="primary"):
        irr_pct = r["irr"] * 100
        moic    = r["moic"]

        if irr_pct > 25:
            verdict       = "STRONG BUY"
            verdict_color = "#1a5c36"
        elif irr_pct > 20:
            verdict       = "BUY"
            verdict_color = "#2d6a4f"
        elif irr_pct > 15:
            verdict       = "CONDITIONAL BUY"
            verdict_color = "#7a6000"
        else:
            verdict       = "PASS"
            verdict_color = "#8b0000"

        st.markdown(f"""
        <div style='background:#111;border:1px solid #333;padding:20px;border-radius:2px'>
        <h3 style='color:#fff;margin-bottom:4px'>INVESTMENT COMMITTEE MEMO</h3>
        <p style='color:#888;font-size:11px'>Generated — Base Case Analysis</p>

        <div style='background:{verdict_color};padding:8px 12px;margin:12px 0;border-radius:2px'>
        <strong style='color:#fff'>RECOMMENDATION: {verdict}</strong>
        </div>

        <h4 style='color:#bbb'>DEAL OVERVIEW</h4>
        <p style='color:#ccc'>
        Entry EV of <strong>${r['entry_ev']:.0f}M</strong> at <strong>{r['purchase_multiple']:.1f}x EBITDA</strong>,
        financed with <strong>{r['debt_raised']/r['entry_ev']*100:.0f}% debt</strong>
        ({r['debt_raised']/r['entry_ebitda']:.1f}x Debt/EBITDA at entry).
        Sponsor equity invested: <strong>${r['sponsor_equity']:.0f}M</strong>.
        </p>

        <h4 style='color:#bbb'>RETURN PROFILE</h4>
        <p style='color:#ccc'>
        Base case:<br>
        • IRR: <strong style='color:#00c97a'>{irr_pct:.1f}%</strong> | MOIC: <strong>{moic:.2f}x</strong><br>
        • Exit EV: <strong>${r['exit_ev']:.0f}M</strong> ({r['exit_multiple']:.1f}x exit multiple)<br>
        • Net Debt at Exit: <strong>${r['ending_debt']:.0f}M</strong><br>
        • Equity at Exit: <strong>${r['equity_at_exit']:.0f}M</strong>
        </p>

        <h4 style='color:#bbb'>VALUE CREATION DRIVERS</h4>
        <p style='color:#ccc'>
        EBITDA growth: <strong>${r['vc_ebitda_growth']:.0f}M</strong> |
        Multiple effect: <strong>${r['vc_multiple_effect']:.0f}M</strong> |
        Debt paydown: <strong>${r['vc_debt_paydown']:.0f}M</strong>
        </p>

        <h4 style='color:#bbb'>SCENARIO ANALYSIS</h4>
        <p style='color:#ccc'>
        Downside IRR: <strong style='color:#e03c31'>{r['scenarios']['Downside']['irr']*100:.1f}%</strong> |
        Base IRR: <strong style='color:#f0a500'>{r['scenarios']['Base']['irr']*100:.1f}%</strong> |
        Upside IRR: <strong style='color:#00c97a'>{r['scenarios']['Upside']['irr']*100:.1f}%</strong>
        </p>

        <h4 style='color:#bbb'>RISK FACTORS</h4>
        <p style='color:#ccc'>
        • Covenant breach probability (Monte Carlo): <strong>{r['mc_stats']['prob_covenant_breach']*100:.1f}%</strong><br>
        • P(IRR &lt; 20% hurdle): <strong>{(1-r['mc_stats']['prob_irr_above_20'])*100:.1f}%</strong><br>
        • Downside case equity: <strong>${r['scenarios']['Downside']['equity_at_exit']:.0f}M</strong>
          ({r['scenarios']['Downside']['moic']:.2f}x MOIC)
        </p>

        <h4 style='color:#bbb'>KEY RISK</h4>
        <p style='color:#ccc'>
        {"• Return heavily dependent on multiple expansion" if r['vc_multiple_effect'] > r['vc_ebitda_growth'] else "• Return driven primarily by debt paydown, limited operational improvement" if r['vc_debt_paydown'] > r['vc_ebitda_growth'] else "• Return driven by EBITDA growth — execution risk on operational targets"}
        </p>
        </div>
        """, unsafe_allow_html=True)
