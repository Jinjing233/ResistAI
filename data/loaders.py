"""
CSV loaders for Catharine's WHO and OECD datasets.

Maps CSV country codes to canonical keys used by country_baselines.py:
    US  → USA
    UK  → UK
    others match directly (India, Brazil, Nigeria)
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent

# CSV row labels → canonical simulation keys
CSV_TO_CANONICAL: dict[str, str] = {
    "US": "USA",
    "UK": "UK",
    "India": "India",
    "Brazil": "Brazil",
    "Nigeria": "Nigeria",
}


def _canonical_csv_country(raw: str) -> str:
    return CSV_TO_CANONICAL.get(raw.strip(), raw.strip())


@lru_cache(maxsize=1)
def load_who_amr_data() -> dict[str, dict[str, Any]]:
    """
    Load WHO_AMR_data.csv keyed by canonical country name.

    Columns:
        ecoli_resistance_pct, mrsa_resistance_pct, infection_incidence (0–1 proxies)
    """
    path = DATA_DIR / "WHO_AMR_data.csv"
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            country = _canonical_csv_country(row["country"])
            rows[country] = {
                "ecoli_resistance_pct": float(row["ecoli_resistance_pct"]),
                "mrsa_resistance_pct": float(row["mrsa_resistance_pct"]),
                "infection_incidence": float(row["infection_incidence"]),
            }
    return rows


@lru_cache(maxsize=1)
def load_oecd_economic_data() -> dict[str, dict[str, Any]]:
    """
    Load OECD_economic_data.csv keyed by canonical country name.

    Columns used by the simulator:
        gdp_per_capita, country_modifier, cost_per_death
    Additional columns retained in metadata for transparency.
    """
    path = DATA_DIR / "OECD_economic_data.csv"
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            country = _canonical_csv_country(row["country"])
            rows[country] = {
                "gdp_per_capita": float(row["gdp_per_capita"]),
                "health_expenditure_pct": float(row["health_expenditure_pct"]),
                "physicians_per_1000": float(row["physicians_per_1000"]),
                "country_modifier": float(row["country_modifier"]),
                "cost_per_death": float(row["cost_per_death"]),
            }
    return rows


def compute_rbi_from_who(who_row: dict[str, Any]) -> float:
    """
    Derive ResistAI RBI (0–100) from WHO CSV resistance proxies.

    Formula (documented estimate, NOT a WHO official index):
        RBI = mean(ecoli_resistance_pct, mrsa_resistance_pct, infection_incidence) × 100
    """
    mean_resistance = (
        who_row["ecoli_resistance_pct"]
        + who_row["mrsa_resistance_pct"]
        + who_row["infection_incidence"]
    ) / 3
    return round(mean_resistance * 100, 1)
