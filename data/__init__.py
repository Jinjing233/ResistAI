"""
ResistAI temporary data module (MVP).

Provides authoritative AMR baseline statistics and economic assumptions for the
simulation engine. Catharine can replace the internal records in
country_baselines.py without changing these exported functions.

Primary integration point:
    from data import get_country_baseline
    baseline = get_country_baseline("Peru")
"""

from data.country_baselines import (
    get_all_baselines,
    get_country_baseline,
    get_country_metadata,
    list_supported_countries,
    normalize_country,
)
from data.economic_assumptions import get_economic_assumptions
from data.sources import DATA_VINTAGE, POLICY_DISCLAIMER, SOURCES

__all__ = [
    "get_country_baseline",
    "get_country_metadata",
    "get_all_baselines",
    "list_supported_countries",
    "normalize_country",
    "get_economic_assumptions",
    "SOURCES",
    "DATA_VINTAGE",
    "POLICY_DISCLAIMER",
]
