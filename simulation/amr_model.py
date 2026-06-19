"""
Core AMR growth and mortality projection for ResistAI.

This module models antimicrobial resistance (AMR) as a Resistance Burden Index
(RBI) that grows exponentially when unchecked. Policy interventions reduce the
effective growth rate — they do not eliminate resistance entirely.

IMPORTANT: This is a policy decision-support illustration, NOT a clinical
forecast or medical diagnostic tool. All constants are transparent placeholders
that Catharine's data/ module can replace later without changing the public API.
"""

from __future__ import annotations

import math
from typing import Any

# ---------------------------------------------------------------------------
# Global model constants (documented assumptions for judges)
# ---------------------------------------------------------------------------

DEFAULT_PROJECTION_YEARS = 20
DEFAULT_START_YEAR = 2025

# Annual exponential growth rate applied to RBI when no intervention is active.
# 0.035 ≈ 3.5 % compound growth per year — illustrative, not epidemiological fact.
BASE_GROWTH_RATE = 0.035

# Even a "perfect" intervention only removes up to 70 % of baseline growth.
# The remaining 30 % reflects that AMR cannot be fully reversed overnight.
MAX_REDUCTION_FACTOR = 0.70

# Deaths scale with RBI raised to this elasticity (>1 means deaths accelerate
# faster than resistance burden once critical thresholds are crossed).
MORTALITY_ELASTICITY = 1.2

# RBI is capped at 100 (abstract index, not a percentage of population).
RBI_MAX = 100.0

# Threshold above which the simulation marks the situation as "critical".
CRITICAL_RBI_THRESHOLD = 75.0

# Fallback: critical year when annual deaths exceed this multiple of baseline.
CRITICAL_DEATHS_MULTIPLIER = 3.0

# Intervention input mappings (Low / Medium / High → effectiveness factor 0–1).
FUNDING_FACTORS: dict[str, float] = {"Low": 0.25, "Medium": 0.55, "High": 0.85}
RD_FACTORS: dict[str, float] = {"Low": 0.20, "Medium": 0.50, "High": 0.80}

# Weights when combining the three intervention levers into one strength score.
WEIGHT_FUNDING = 0.40
WEIGHT_STEWARDSHIP = 0.35
WEIGHT_RD = 0.25

# Economic defaults used when country-specific values are absent.
DEFAULT_COST_PER_DEATH_USD = 20_000
DEFAULT_PRODUCTIVITY_YEARS_LOST = 15
DEFAULT_LABOR_PARTICIPATION = 0.65

# Placeholder country baselines — replace internals of get_country_baseline()
# with WHO/OECD data from data/ without changing function signatures.
COUNTRY_DEFAULTS: dict[str, dict[str, Any]] = {
    "Global": {
        "baseline_deaths": 1_000_000,
        "rbi_0": 35.0,
        "gdp_per_capita": 12_000,
        "country_modifier": 1.0,
        "cost_per_death": 20_000,
    },
    "USA": {
        "baseline_deaths": 35_000,
        "rbi_0": 38.0,
        "gdp_per_capita": 65_000,
        "country_modifier": 0.95,
        "cost_per_death": 45_000,
    },
    "India": {
        "baseline_deaths": 58_000,
        "rbi_0": 50.0,
        "gdp_per_capita": 2_500,
        "country_modifier": 1.15,
        "cost_per_death": 8_000,
    },
    "Brazil": {
        "baseline_deaths": 25_000,
        "rbi_0": 45.0,
        "gdp_per_capita": 9_000,
        "country_modifier": 1.08,
        "cost_per_death": 12_000,
    },
    "Peru": {
        "baseline_deaths": 8_000,
        "rbi_0": 42.0,
        "gdp_per_capita": 7_500,
        "country_modifier": 1.10,
        "cost_per_death": 10_000,
    },
}


def normalize_level(level: str) -> str:
    """
    Normalize a categorical level string to 'Low', 'Medium', or 'High'.

    Args:
        level: Raw user input (case-insensitive).

    Returns:
        Canonical level string.

    Raises:
        ValueError: If the level is not recognized.
    """
    normalized = level.strip().capitalize()
    if normalized not in FUNDING_FACTORS:
        raise ValueError(
            f"Invalid level '{level}'. Expected one of: Low, Medium, High."
        )
    return normalized


def normalize_country(country: str) -> str:
    """
    Resolve a country name to a supported baseline key.

    Delegates to data.normalize_country() so the country list has a single source.
    """
    from data import normalize_country as data_normalize_country

    return data_normalize_country(country)


def get_country_baseline(country: str) -> dict[str, Any]:
    """
    Return baseline parameters for a country or region.

    Delegates to data.get_country_baseline(). Metadata from the data module is
    preserved for UI transparency; simulation formulas use the numeric fields only.

    Returns:
        Dict with keys: country, baseline_deaths, rbi_0, gdp_per_capita,
        country_modifier, cost_per_death.
    """
    from data import get_country_baseline as data_get_country_baseline

    return data_get_country_baseline(country)


def compute_intervention_strength(
    funding_level: str,
    stewardship_rate: float,
    rd_investment: str,
) -> float:
    """
    Combine three policy levers into a single intervention strength score.

    Formula:
        strength = clamp(
            w_funding  × funding_factor
          + w_steward  × (stewardship_rate / 100)
          + w_rd       × rd_factor,
            0, 1
        )

    Args:
        funding_level:    'Low', 'Medium', or 'High'.
        stewardship_rate: Antibiotic stewardship adoption, 0–100 %.
        rd_investment:    'Low', 'Medium', or 'High'.

    Returns:
        Float in [0, 1] representing overall intervention effectiveness.
    """
    funding = normalize_level(funding_level)
    rd = normalize_level(rd_investment)
    stewardship = max(0.0, min(100.0, stewardship_rate)) / 100.0

    strength = (
        WEIGHT_FUNDING * FUNDING_FACTORS[funding]
        + WEIGHT_STEWARDSHIP * stewardship
        + WEIGHT_RD * RD_FACTORS[rd]
    )
    return max(0.0, min(1.0, strength))


def _effective_growth_rate(
    base_rate: float,
    country_modifier: float,
    intervention_strength: float,
    intervening: bool,
) -> float:
    """
    Compute the annual RBI growth rate for one time step.

    When intervening:
        r_eff = base_rate × country_modifier × (1 − strength × max_reduction)
    Otherwise:
        r_eff = base_rate × country_modifier
    """
    rate = base_rate * country_modifier
    if intervening:
        rate *= 1.0 - intervention_strength * MAX_REDUCTION_FACTOR
    return rate


def project_resistance_burden(
    rbi_0: float,
    base_growth_rate: float,
    country_modifier: float,
    intervention_start_year: int,
    intervention_strength: float,
    projection_years: int,
) -> list[float]:
    """
    Project RBI year-by-year using piecewise exponential growth.

    Formula per step:
        RBI(t+1) = min(RBI(t) × exp(r_eff), RBI_MAX)

    Args:
        rbi_0:                   Starting resistance burden index.
        base_growth_rate:        Unmitigated annual growth rate.
        country_modifier:        Country-specific multiplier on growth.
        intervention_start_year: Year index (0-based) when intervention begins.
                                   Use a value > projection_years for no intervention.
        intervention_strength:   Combined lever score in [0, 1].
        projection_years:        Number of years to project (returns projection_years + 1 values).

    Returns:
        List of RBI values indexed 0 … projection_years.
    """
    rbi_series = [float(rbi_0)]
    for year in range(1, projection_years + 1):
        intervening = year >= intervention_start_year and intervention_strength > 0
        r_eff = _effective_growth_rate(
            base_growth_rate,
            country_modifier,
            intervention_strength,
            intervening,
        )
        next_rbi = rbi_series[-1] * math.exp(r_eff)
        rbi_series.append(min(next_rbi, RBI_MAX))
    return rbi_series


def project_deaths_from_burden(
    baseline_deaths: float,
    rbi_0: float,
    rbi_series: list[float],
) -> list[int]:
    """
    Derive annual AMR deaths from the RBI trajectory.

    Formula:
        deaths(t) = baseline_deaths × (RBI(t) / RBI_0) ^ mortality_elasticity

    Args:
        baseline_deaths: Annual AMR deaths at the starting RBI level.
        rbi_0:           Starting RBI (must match rbi_series[0]).
        rbi_series:      RBI values over time.

    Returns:
        List of integer annual death counts (same length as rbi_series).
    """
    if rbi_0 <= 0:
        raise ValueError("rbi_0 must be positive.")

    deaths: list[int] = []
    for rbi in rbi_series:
        ratio = rbi / rbi_0
        raw = baseline_deaths * (ratio ** MORTALITY_ELASTICITY)
        deaths.append(max(0, int(round(raw))))
    return deaths


def project_timeline(
    country: str,
    intervention_start_year: int,
    intervention_strength: float,
    projection_years: int = DEFAULT_PROJECTION_YEARS,
    start_year: int = DEFAULT_START_YEAR,
    initial_rbi: float | None = None,
    initial_deaths: float | None = None,
) -> dict[str, Any]:
    """
    Build a full AMR projection timeline (years, RBI, deaths).

    Args:
        country:                 Country or region name.
        intervention_start_year: 0-based year when intervention starts.
        intervention_strength:   Combined intervention score [0, 1].
        projection_years:        Horizon length in years.
        start_year:              Calendar year for index 0 (for chart labels).
        initial_rbi:             Optional override for starting RBI (recovery mode).
        initial_deaths:          Optional override for starting deaths (recovery mode).

    Returns:
        Dict with calendar years, rbi_series, deaths_series, and assumptions metadata.
    """
    baseline = get_country_baseline(country)
    rbi_0 = initial_rbi if initial_rbi is not None else baseline["rbi_0"]
    deaths_0 = initial_deaths if initial_deaths is not None else baseline["baseline_deaths"]

    rbi_series = project_resistance_burden(
        rbi_0=rbi_0,
        base_growth_rate=BASE_GROWTH_RATE,
        country_modifier=baseline["country_modifier"],
        intervention_start_year=intervention_start_year,
        intervention_strength=intervention_strength,
        projection_years=projection_years,
    )
    deaths_series = project_deaths_from_burden(deaths_0, rbi_0, rbi_series)
    calendar_years = [start_year + i for i in range(projection_years + 1)]

    return {
        "country": baseline["country"],
        "years": calendar_years,
        "resistance_burden": rbi_series,
        "annual_deaths": deaths_series,
        "assumptions": {
            "rbi_0": rbi_0,
            "baseline_deaths": deaths_0,
            "base_growth_rate": BASE_GROWTH_RATE,
            "country_modifier": baseline["country_modifier"],
            "intervention_start_year": intervention_start_year,
            "intervention_strength": intervention_strength,
            "mortality_elasticity": MORTALITY_ELASTICITY,
            "max_reduction_factor": MAX_REDUCTION_FACTOR,
            "projection_years": projection_years,
        },
    }
