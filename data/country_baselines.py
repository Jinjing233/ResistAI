"""
Temporary country baseline dataset for ResistAI MVP integration.

Each record supplies the fields required by simulation.get_country_baseline():
    country, baseline_deaths, rbi_0, gdp_per_capita, country_modifier, cost_per_death

Additional metadata (sources, is_estimate flags) is included for transparency
and can be shown in the Streamlit UI without affecting simulation math.

Catharine can replace COUNTRY_RECORDS with validated WHO/OECD tables while
keeping get_country_baseline() unchanged.
"""

from __future__ import annotations

from typing import Any

from data.economic_assumptions import get_economic_assumptions
from data.sources import DATA_VINTAGE, POLICY_DISCLAIMER, SOURCES

# ---------------------------------------------------------------------------
# Country records
# ---------------------------------------------------------------------------
# baseline_deaths: annual deaths directly attributable to bacterial AMR (2019 baseline year)
# rbi_0: Resistance Burden Index (0–100) — ResistAI policy index, NOT a WHO metric
# gdp_per_capita: World Bank approximate USD (2023)
# country_modifier: relative AMR growth scaling (estimate)
# cost_per_death: excess healthcare cost proxy per AMR death (USD, estimate)

COUNTRY_RECORDS: dict[str, dict[str, Any]] = {
    "Global": {
        "baseline_deaths": 1_270_000,
        "rbi_0": 35.0,
        "gdp_per_capita": 12_000,
        "country_modifier": 1.0,
        "cost_per_death": 20_000,
        "population": 8_000_000_000,
        "associated_deaths_2019": 4_950_000,
        "metadata": {
            "baseline_deaths_source": SOURCES["lancet_2022_global_direct_deaths"],
            "baseline_deaths_is_estimate": False,
            "associated_deaths_source": SOURCES["lancet_2022_associated_deaths"],
            "associated_deaths_is_estimate": False,
            "rbi_source": SOURCES["rbi_calibration"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["world_bank_gdp"],
            "gdp_per_capita_is_estimate": True,
            "country_modifier_source": SOURCES["country_modifier_calibration"],
            "country_modifier_is_estimate": True,
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "notes": (
                "Global aggregate aligned to Lancet 2019 direct AMR mortality central "
                "estimate (1.27M). GDP figure is a weighted global proxy."
            ),
        },
    },
    "USA": {
        "baseline_deaths": 35_000,
        "rbi_0": 38.0,
        "gdp_per_capita": 65_000,
        "country_modifier": 0.95,
        "cost_per_death": 45_000,
        "population": 335_000_000,
        "associated_deaths_2019": 120_000,
        "metadata": {
            "baseline_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["rbi_calibration"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["world_bank_gdp"],
            "gdp_per_capita_is_estimate": True,
            "country_modifier_source": SOURCES["country_modifier_calibration"],
            "country_modifier_is_estimate": True,
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "notes": (
                "USA deaths rounded from Lancet 2019 country-level estimates for "
                "high-income North America. Higher cost_per_death reflects OECD "
                "healthcare expenditure patterns."
            ),
        },
    },
    "India": {
        "baseline_deaths": 191_000,
        "rbi_0": 52.0,
        "gdp_per_capita": 2_500,
        "country_modifier": 1.12,
        "cost_per_death": 8_000,
        "population": 1_400_000_000,
        "associated_deaths_2019": 590_000,
        "metadata": {
            "baseline_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["who_glass"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["world_bank_gdp"],
            "gdp_per_capita_is_estimate": True,
            "country_modifier_source": SOURCES["country_modifier_calibration"],
            "country_modifier_is_estimate": True,
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "notes": (
                "India is among the highest AMR-burden countries in Lancet 2019 "
                "estimates. RBI set high per WHO GLASS regional resistance severity."
            ),
        },
    },
    "Brazil": {
        "baseline_deaths": 29_000,
        "rbi_0": 46.0,
        "gdp_per_capita": 9_000,
        "country_modifier": 1.08,
        "cost_per_death": 12_000,
        "population": 215_000_000,
        "associated_deaths_2019": 95_000,
        "metadata": {
            "baseline_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["lancet_2022_country_estimates"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["who_glass"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["world_bank_gdp"],
            "gdp_per_capita_is_estimate": True,
            "country_modifier_source": SOURCES["country_modifier_calibration"],
            "country_modifier_is_estimate": True,
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "notes": (
                "Brazil estimate rounded from Lancet 2019 Latin America regional "
                "burden allocation."
            ),
        },
    },
    "Peru": {
        "baseline_deaths": 6_800,
        "rbi_0": 44.0,
        "gdp_per_capita": 7_500,
        "country_modifier": 1.10,
        "cost_per_death": 10_000,
        "population": 34_000_000,
        "associated_deaths_2019": 22_000,
        "metadata": {
            "baseline_deaths_source": SOURCES["peru_country_deaths_estimate"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["peru_country_deaths_estimate"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["who_glass"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["world_bank_gdp"],
            "gdp_per_capita_is_estimate": True,
            "country_modifier_source": SOURCES["country_modifier_calibration"],
            "country_modifier_is_estimate": True,
            "cost_per_death_source": SOURCES["oecd_amr_economic_burden"],
            "cost_per_death_is_estimate": True,
            "notes": (
                "Peru country-level deaths are scaled estimates pending Catharine's "
                "validated national dataset."
            ),
        },
    },
}

# Aliases for frontend / free-text country inputs (integration Step 2).
COUNTRY_ALIASES: dict[str, str] = {
    "global": "Global",
    "world": "Global",
    "united states": "USA",
    "us": "USA",
    "u.s.": "USA",
    "u.s.a.": "USA",
    "america": "USA",
    "india": "India",
    "brazil": "Brazil",
    "peru": "Peru",
}


def list_supported_countries() -> list[str]:
    """Return canonical country keys available in the temporary dataset."""
    return list(COUNTRY_RECORDS.keys())


def normalize_country(country: str, default: str = "Global") -> str:
    """
    Resolve a user-supplied country string to a canonical dataset key.

    Unknown countries fall back to `default` (Global aggregate).
    """
    cleaned = country.strip()
    if not cleaned:
        return default

    for key in COUNTRY_RECORDS:
        if key.lower() == cleaned.lower():
            return key

    alias = COUNTRY_ALIASES.get(cleaned.lower())
    if alias:
        return alias

    return default


def get_country_metadata(country: str) -> dict[str, Any]:
    """
    Return transparency metadata for a country (sources, estimate flags, notes).

    Does not include simulation numeric fields beyond documentation context.
    """
    canonical = normalize_country(country)
    record = COUNTRY_RECORDS[canonical]
    return {
        "country": canonical,
        "data_vintage": DATA_VINTAGE,
        "disclaimer": POLICY_DISCLAIMER,
        "population": record.get("population"),
        "associated_deaths_2019": record.get("associated_deaths_2019"),
        **record.get("metadata", {}),
    }


def get_country_baseline(country: str) -> dict[str, Any]:
    """
    Return simulation-compatible baseline parameters for a country or region.

    This is the primary integration function. simulation.amr_model.get_country_baseline()
    should delegate here in Step 2 without changing its public signature.

    Returns:
        Dict with keys required by the simulation engine:
            country, baseline_deaths, rbi_0, gdp_per_capita,
            country_modifier, cost_per_death
        Plus optional metadata block for UI transparency.
    """
    canonical = normalize_country(country)
    record = COUNTRY_RECORDS[canonical]
    return {
        "country": canonical,
        "baseline_deaths": record["baseline_deaths"],
        "rbi_0": record["rbi_0"],
        "gdp_per_capita": record["gdp_per_capita"],
        "country_modifier": record["country_modifier"],
        "cost_per_death": record["cost_per_death"],
        "metadata": {
            "data_vintage": DATA_VINTAGE,
            "disclaimer": POLICY_DISCLAIMER,
            "population": record.get("population"),
            "associated_deaths_2019": record.get("associated_deaths_2019"),
            **record.get("metadata", {}),
            "economic_defaults": get_economic_assumptions(),
        },
    }


def get_all_baselines() -> dict[str, dict[str, Any]]:
    """Return baselines for every supported country (useful for data validation UI)."""
    return {country: get_country_baseline(country) for country in COUNTRY_RECORDS}
