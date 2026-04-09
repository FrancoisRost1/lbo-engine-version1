"""
tab_overview.py — Tab 1: Deal Summary, Sources & Uses, Returns, Exit Analysis.
"""

import streamlit as st


def render(r: dict) -> None:
    """
    Render the OVERVIEW tab content.

    Args:
        r (dict): Pipeline results from run_pipeline().
    """
    # Deal Summary
    st.subheader("Deal Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Entry EV",       f"${r['entry_ev']:.0f}M")
    c2.metric("Debt Raised",    f"${r['debt_raised']:.0f}M")
    c3.metric("Sponsor Equity", f"${r['sponsor_equity']:.0f}M")
    c4.metric("Debt / EV",      f"{r['debt_raised'] / r['entry_ev'] * 100:.0f}%")
    c5.metric("Debt / EBITDA",  f"{r['debt_raised'] / r['entry_ebitda']:.1f}x")

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Sources & Uses
    st.subheader("Sources & Uses")
    uses_col, sources_col = st.columns(2)
    with uses_col:
        st.markdown("**USES**")
        st.markdown(f"Purchase Price &nbsp;&nbsp;&nbsp;&nbsp; **${r['entry_ev']:.1f}M**")
        st.markdown(f"Transaction Fees &nbsp;&nbsp; **${r['fees']:.1f}M**")
        st.markdown("---")
        st.markdown(f"**Total Uses** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['total_uses']:.1f}M**")
    with sources_col:
        st.markdown("**SOURCES**")
        st.markdown(f"Debt Raised &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['debt_raised']:.1f}M**")
        st.markdown(f"Sponsor Equity &nbsp;&nbsp;&nbsp;&nbsp; **${r['sponsor_equity']:.1f}M**")
        st.markdown("---")
        st.markdown(f"**Total Sources** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **${r['total_uses']:.1f}M**")

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Investor Returns
    st.subheader("Investor Returns")
    irr = r["irr"]
    irr_color_sec = "#0a5c36" if irr > 0.20 else "#7a6000" if irr > 0.10 else "#8b0000"
    rc1, rc2 = st.columns(2)
    rc1.metric("MOIC", f"{r['moic']:.2f}x")
    with rc2:
        st.markdown("**IRR**")
        st.markdown(
            f"<h2 style='color:{irr_color_sec}; margin-top:0'>{irr*100:.1f}%</h2>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:0.3rem 0; border-color:#2a2a2a'>", unsafe_allow_html=True)

    # Exit Analysis
    st.subheader("Exit Analysis")
    e1, e2, e3, e4, e5 = st.columns(5)
    e1.metric("Exit EBITDA ($M)",      f"${r['exit_ebitda']:.1f}M")
    e2.metric("Exit Multiple (x)",     f"{r['exit_multiple']:.1f}x")
    e3.metric("Exit EV ($M)",          f"${r['exit_ev']:.1f}M")
    e4.metric("Net Debt at Exit ($M)", f"${r['ending_debt']:.1f}M")
    e5.metric("Equity at Exit ($M)",   f"${r['equity_at_exit']:.1f}M")
