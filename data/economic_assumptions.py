"""
Economic impact assumptions for the ResistAI temporary data module.

These constants feed simulation/calculations.py via country baseline records
(cost_per_death) and documented metadata. Global defaults align with OECD
narratives on excess treatment costs and productivity loss from premature mortality.
"""

from __future__ import annotations

from typing import Any

from data.sources import SOURCES

# OECD and health-economics literature often cite substantially higher treatment
# costs for resistant infections vs susceptible infections. We use a conservative
# per-death excess cost proxy for the simulator (USD, estimate).
DEFAULT_COST_PER_DEATH_USD = 20_000

# Working years lost per AMR-related premature death (policy proxy, estimate).
DEFAULT_PRODUCTIVITY_YEARS_LOST = 15

# Share of population in the labour force (ILO-style global average, estimate).
DEFAULT_LABOR_PARTICIPATION = 0.65


def get_economic_assumptions() -> dict[str, Any]:
    """
    Return global economic assumptions with source documentation.

    Returns:
        Dict with numeric defaults and metadata for transparency panels.
    """
    return {
        "cost_per_death_usd": DEFAULT_COST_PER_DEATH_USD,
        "productivity_years_lost": DEFAULT_PRODUCTIVITY_YEARS_LOST,
        "labor_participation": DEFAULT_LABOR_PARTICIPATION,
        "metadata": {
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "productivity_years_source": (
                "Estimate: standard health-economics proxy for working-age "
                "mortality (15 years)."
            ),
            "labor_participation_source": (
                "Estimate: global labour-force participation proxy (~65%)."
            ),
        },
    }
