"""
config_loader.py — Load config.yaml for the Streamlit app.

Single source of truth: all fixed parameters, scenario presets, and
sensitivity axes come from config.yaml. Nothing is hardcoded here.
"""

from pathlib import Path

import yaml


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"


def load_config() -> dict:
    """
    Load config.yaml from the project root.

    Returns:
        dict: Full config dictionary.
    """
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def get_fixed_params(cfg: dict) -> dict:
    """
    Extract parameters not exposed as sliders from config.

    These are the operating/debt assumptions that stay constant while the
    user adjusts deal-level inputs via the sidebar.

    Args:
        cfg (dict): Full config dictionary.

    Returns:
        dict: Keys matching the pipeline's expected parameter names.
    """
    return {
        "fee_pct":          cfg["fee_pct"],
        "capex_pct":        cfg["capex_pct"],
        "nwc_pct":          cfg["nwc_pct"],
        "tax_rate":         cfg["tax_rate"],
        "interest_rate":    cfg["interest_rate"],
        "amortization_rate": cfg["amortization_rate"],
        "cash_sweep":       cfg["cash_sweep"],
    }


def get_scenario_presets(cfg: dict) -> dict:
    """
    Build slider-default presets from config scenarios.

    Converts decimal fractions (0.06) to percentage integers (6) for slider
    display. Exit multiple stays as float.

    Args:
        cfg (dict): Full config dictionary.

    Returns:
        dict: {"Base": {"revenue_growth": 6, "ebitda_margin": 25, "exit_multiple": 9.0}, ...}
    """
    raw = cfg.get("scenarios", {})
    presets = {}
    for name, vals in raw.items():
        presets[name] = {
            "revenue_growth": int(round(vals["revenue_growth"] * 100)),
            "ebitda_margin":  int(round(vals["ebitda_margin"] * 100)),
            "exit_multiple":  vals["exit_multiple"],
        }
    return presets
