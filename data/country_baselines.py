"""
Country baseline dataset for ResistAI MVP — single runtime source of truth.

Builds records for seven supported countries/regions by merging:
  - Lancet 2019 mortality anchors (where documented)
  - Catharine's WHO_AMR_data.csv (RBI derivation)
  - Catharine's OECD_economic_data.csv (economic fields)
  - Transparent estimates for missing fields (always flagged in metadata)

Each record supplies fields required by simulation.get_country_baseline():
    country, baseline_deaths, rbi_0, gdp_per_capita, country_modifier, cost_per_death
"""

from __future__ import annotations

from typing import Any

from data.economic_assumptions import get_economic_assumptions
from data.loaders import (
    compute_rbi_from_who,
    load_oecd_economic_data,
    load_who_amr_data,
)
from data.sources import DATA_VINTAGE, POLICY_DISCLAIMER, SOURCES

# Canonical display and iteration order (single source of truth for the app).
SUPPORTED_COUNTRY_ORDER: list[str] = [
    "Global",
    "USA",
    "India",
    "Brazil",
    "Peru",
    "Nigeria",
    "UK",
]

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
    "nigeria": "Nigeria",
    "uk": "UK",
    "united kingdom": "UK",
    "britain": "UK",
    "great britain": "UK",
}


def _estimate_nigeria_deaths(who_row: dict[str, Any]) -> tuple[int, int]:
    """
    Estimate Nigeria AMR deaths when no authoritative country table is loaded.

    Method (documented estimate):
      1. Start from Lancet 2022 Sub-Saharan Africa high-burden anchor (~45,000 direct).
      2. Scale by WHO CSV infection_incidence relative to 0.50 baseline:
         adjusted = 45,000 × (1 + (infection_incidence − 0.50))
      3. Round to nearest 1,000.

    Associated deaths use a 3.2× multiplier consistent with Lancet global direct/associated ratio.
    """
    anchor = 45_000
    incidence = who_row["infection_incidence"]
    direct = int(round(anchor * (1 + (incidence - 0.50)) / 1000) * 1000)
    associated = int(round(direct * 3.2 / 1000) * 1000)
    return direct, associated


def _estimate_uk_deaths() -> tuple[int, int]:
    """
    Estimate UK AMR deaths when no authoritative country table is loaded.

    Method (documented estimate):
      - Lancet 2022 high-income European country allocation (~11,500 direct, rounded).
      - Associated deaths use ~3.3× multiplier (Lancet high-income pattern).
    """
    direct = 11_500
    associated = 38_000
    return direct, associated


def _build_country_records() -> dict[str, dict[str, Any]]:
    """Assemble all seven country records from anchors + CSV merges."""
    who_data = load_who_amr_data()
    oecd_data = load_oecd_economic_data()

    records: dict[str, dict[str, Any]] = {}

    # ── Global (no CSV rows — Lancet global anchors + documented proxies) ──
    records["Global"] = {
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
                "estimate (1.27M). Economic and RBI fields are global proxies, not CSV rows."
            ),
        },
    }

    # ── Lancet country death anchors (CSV does not supply baseline_deaths) ──
    lancet_death_anchors: dict[str, dict[str, Any]] = {
        "USA": {
            "baseline_deaths": 35_000,
            "associated_deaths_2019": 120_000,
            "population": 335_000_000,
            "notes": "USA deaths rounded from Lancet 2019 country-level estimates.",
        },
        "India": {
            "baseline_deaths": 191_000,
            "associated_deaths_2019": 590_000,
            "population": 1_400_000_000,
            "notes": "India among highest AMR-burden countries in Lancet 2019 estimates.",
        },
        "Brazil": {
            "baseline_deaths": 29_000,
            "associated_deaths_2019": 95_000,
            "population": 215_000_000,
            "notes": "Brazil rounded from Lancet 2019 Latin America regional allocation.",
        },
        "Peru": {
            "baseline_deaths": 6_800,
            "associated_deaths_2019": 22_000,
            "population": 34_000_000,
            "death_source": SOURCES["peru_country_deaths_estimate"],
            "notes": "Peru deaths scaled from Lancet Latin America regional share (estimate).",
        },
    }

    for country, anchor in lancet_death_anchors.items():
        who = who_data.get(country)
        oecd = oecd_data.get(country)

        if country == "Peru":
            rbi = 44.0
            rbi_source = SOURCES["rbi_calibration"]
            rbi_is_estimate = True
        else:
            rbi = compute_rbi_from_who(who) if who else 40.0
            rbi_source = SOURCES["rbi_from_who_csv"] if who else SOURCES["rbi_calibration"]
            rbi_is_estimate = True

        death_source = anchor.get("death_source", SOURCES["lancet_2022_country_estimates"])
        records[country] = {
            "baseline_deaths": anchor["baseline_deaths"],
            "rbi_0": rbi,
            "gdp_per_capita": oecd["gdp_per_capita"] if oecd else 7_500,
            "country_modifier": oecd["country_modifier"] if oecd else 1.10,
            "cost_per_death": int(oecd["cost_per_death"]) if oecd else 10_000,
            "population": anchor["population"],
            "associated_deaths_2019": anchor["associated_deaths_2019"],
            "metadata": {
                "baseline_deaths_source": death_source,
                "baseline_deaths_is_estimate": True,
                "associated_deaths_source": death_source,
                "associated_deaths_is_estimate": True,
                "rbi_source": rbi_source,
                "rbi_is_estimate": rbi_is_estimate,
                "gdp_per_capita_source": (
                    SOURCES["oecd_economic_csv"] if oecd else SOURCES["world_bank_gdp"]
                ),
                "gdp_per_capita_is_estimate": oecd is None,
                "country_modifier_source": (
                    SOURCES["oecd_economic_csv"] if oecd else SOURCES["country_modifier_calibration"]
                ),
                "country_modifier_is_estimate": oecd is None,
                "cost_per_death_source": (
                    SOURCES["oecd_economic_csv"] if oecd else SOURCES["oecd_amr_economic_burden"]
                ),
                "cost_per_death_is_estimate": oecd is None,
                "who_csv": who,
                "oecd_csv": oecd,
                "notes": anchor["notes"],
            },
        }

    # ── Nigeria (CSV-backed economics + WHO RBI; deaths estimated) ──
    who_ng = who_data["Nigeria"]
    oecd_ng = oecd_data["Nigeria"]
    ng_direct, ng_associated = _estimate_nigeria_deaths(who_ng)
    records["Nigeria"] = {
        "baseline_deaths": ng_direct,
        "rbi_0": compute_rbi_from_who(who_ng),
        "gdp_per_capita": oecd_ng["gdp_per_capita"],
        "country_modifier": oecd_ng["country_modifier"],
        "cost_per_death": int(oecd_ng["cost_per_death"]),
        "population": 223_000_000,
        "associated_deaths_2019": ng_associated,
        "metadata": {
            "baseline_deaths_source": SOURCES["nigeria_country_deaths_estimate"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["nigeria_country_deaths_estimate"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["rbi_from_who_csv"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["oecd_economic_csv"],
            "gdp_per_capita_is_estimate": False,
            "country_modifier_source": SOURCES["oecd_economic_csv"],
            "country_modifier_is_estimate": False,
            "cost_per_death_source": SOURCES["oecd_economic_csv"],
            "cost_per_death_is_estimate": False,
            "who_csv": who_ng,
            "oecd_csv": oecd_ng,
            "notes": (
                "Deaths estimated from Lancet Sub-Saharan Africa high-burden anchor scaled "
                "by WHO CSV infection_incidence (0.70). Economic fields and RBI from Catharine CSVs."
            ),
        },
    }

    # ── UK (CSV-backed economics + WHO RBI; deaths estimated) ──
    who_uk = who_data["UK"]
    oecd_uk = oecd_data["UK"]
    uk_direct, uk_associated = _estimate_uk_deaths()
    records["UK"] = {
        "baseline_deaths": uk_direct,
        "rbi_0": compute_rbi_from_who(who_uk),
        "gdp_per_capita": oecd_uk["gdp_per_capita"],
        "country_modifier": oecd_uk["country_modifier"],
        "cost_per_death": int(oecd_uk["cost_per_death"]),
        "population": 67_000_000,
        "associated_deaths_2019": uk_associated,
        "metadata": {
            "baseline_deaths_source": SOURCES["uk_country_deaths_estimate"],
            "baseline_deaths_is_estimate": True,
            "associated_deaths_source": SOURCES["uk_country_deaths_estimate"],
            "associated_deaths_is_estimate": True,
            "rbi_source": SOURCES["rbi_from_who_csv"],
            "rbi_is_estimate": True,
            "gdp_per_capita_source": SOURCES["oecd_economic_csv"],
            "gdp_per_capita_is_estimate": False,
            "country_modifier_source": SOURCES["oecd_economic_csv"],
            "country_modifier_is_estimate": False,
            "cost_per_death_source": SOURCES["oecd_economic_csv"],
            "cost_per_death_is_estimate": False,
            "who_csv": who_uk,
            "oecd_csv": oecd_uk,
            "notes": (
                "Deaths estimated from Lancet high-income European allocation. "
                "Economic fields and RBI from Catharine CSVs."
            ),
        },
    }

    return records


COUNTRY_RECORDS: dict[str, dict[str, Any]] = _build_country_records()


def list_supported_countries() -> list[str]:
    """Return the seven supported countries/regions in canonical display order."""
    return list(SUPPORTED_COUNTRY_ORDER)


def normalize_country(country: str, default: str = "Global") -> str:
    """Resolve a user-supplied country string to a canonical dataset key."""
    cleaned = country.strip()
    if not cleaned:
        return default

    for key in SUPPORTED_COUNTRY_ORDER:
        if key.lower() == cleaned.lower():
            return key

    alias = COUNTRY_ALIASES.get(cleaned.lower())
    if alias:
        return alias

    return default


def get_country_metadata(country: str) -> dict[str, Any]:
    """Return transparency metadata for a country (sources, estimate flags, notes)."""
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

    Returns:
        Dict with keys: country, baseline_deaths, rbi_0, gdp_per_capita,
        country_modifier, cost_per_death, plus metadata for UI transparency.
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
    """Return baselines for every supported country."""
    return {country: get_country_baseline(country) for country in SUPPORTED_COUNTRY_ORDER}
