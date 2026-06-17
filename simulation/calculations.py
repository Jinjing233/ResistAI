"""
Economic impact, risk scoring, and summary builders for ResistAI simulations.

All formulas use simple linear scaling from excess deaths so that judges can
follow the arithmetic without specialist knowledge.
"""

from __future__ import annotations

from typing import Any

from simulation.amr_model import (
    CRITICAL_DEATHS_MULTIPLIER,
    CRITICAL_RBI_THRESHOLD,
    DEFAULT_LABOR_PARTICIPATION,
    DEFAULT_PRODUCTIVITY_YEARS_LOST,
    get_country_baseline,
)


def compute_cumulative_deaths(deaths_series: list[int]) -> int:
    """Sum annual deaths across the projection horizon."""
    return int(sum(deaths_series))


def compute_additional_deaths(
    scenario_deaths: list[int],
    baseline_deaths: list[int],
) -> int:
    """
    Compute excess cumulative deaths of one scenario vs a baseline scenario.

    Used for "Cost of Delay": Delayed Action cumulative − Early Action cumulative.
    """
    return max(
        0,
        compute_cumulative_deaths(scenario_deaths)
        - compute_cumulative_deaths(baseline_deaths),
    )


def compute_healthcare_cost(
    additional_deaths: int,
    cost_per_death: float,
) -> float:
    """
    Estimate healthcare cost increase in USD millions.

    Formula:
        cost (USD M) = additional_deaths × cost_per_death / 1,000,000
    """
    return additional_deaths * cost_per_death / 1_000_000


def compute_gdp_loss(
    additional_deaths: int,
    gdp_per_capita: float,
    productivity_years: float = DEFAULT_PRODUCTIVITY_YEARS_LOST,
    labor_participation: float = DEFAULT_LABOR_PARTICIPATION,
) -> float:
    """
    Estimate GDP / productivity loss in USD millions.

    Formula:
        gdp_loss (USD M) = additional_deaths
                         × productivity_years
                         × gdp_per_capita
                         × labor_participation
                         / 1,000,000

    Each excess death represents lost economic output over remaining working years.
    """
    return (
        additional_deaths
        * productivity_years
        * gdp_per_capita
        * labor_participation
        / 1_000_000
    )


def compute_lives_saved(
    reference_deaths: list[int],
    intervention_deaths: list[int],
) -> int:
    """
    Lives saved = cumulative deaths(reference) − cumulative deaths(intervention).

    Example: lives saved by Early Action vs No Action.
    """
    return max(
        0,
        compute_cumulative_deaths(reference_deaths)
        - compute_cumulative_deaths(intervention_deaths),
    )


def estimate_critical_year(
    years: list[int],
    rbi_series: list[float],
    deaths_series: list[int],
    baseline_deaths: float,
) -> int | None:
    """
    Return the first calendar year when risk becomes critical.

    Primary trigger:  RBI(t) >= CRITICAL_RBI_THRESHOLD (default 75)
    Fallback trigger: deaths(t) >= baseline_deaths × CRITICAL_DEATHS_MULTIPLIER
    """
    threshold_deaths = baseline_deaths * CRITICAL_DEATHS_MULTIPLIER
    for year, rbi, deaths in zip(years, rbi_series, deaths_series):
        if rbi >= CRITICAL_RBI_THRESHOLD or deaths >= threshold_deaths:
            return year
    return None


def compute_risk_level(rbi_series: list[float]) -> str:
    """
    Map the peak RBI in the series to a categorical risk level.

    | RBI peak | Risk level |
    |----------|------------|
    | < 40     | Low        |
    | 40–59    | Medium     |
    | 60–79    | High       |
    | ≥ 80     | Critical   |
    """
    peak = max(rbi_series) if rbi_series else 0.0
    if peak >= 80:
        return "Critical"
    if peak >= 60:
        return "High"
    if peak >= 40:
        return "Medium"
    return "Low"


def build_summary(
    scenario_name: str,
    country: str,
    years: list[int],
    annual_deaths: list[int],
    resistance_burden: list[float],
    intervention_strength: float,
    assumptions: dict[str, Any],
    reference_deaths: list[int] | None = None,
    no_action_deaths: list[int] | None = None,
) -> dict[str, Any]:
    """
    Build the flat summary dict consumed by the frontend and AI modules.

    Args:
        scenario_name:         Human-readable scenario label.
        country:               Resolved country name.
        years:                 Calendar years.
        annual_deaths:         Scenario death series.
        resistance_burden:     Scenario RBI series.
        intervention_strength: Combined lever score.
        assumptions:           Model assumptions metadata.
        reference_deaths:      Baseline for additional-death calc (Early Action).
        no_action_deaths:      No-action series for lives-saved metrics.
    """
    baseline = get_country_baseline(country)
    final_year_deaths = annual_deaths[-1] if annual_deaths else 0
    baseline_deaths_value = assumptions.get(
        "baseline_deaths", baseline["baseline_deaths"]
    )

    additional_deaths = (
        compute_additional_deaths(annual_deaths, reference_deaths)
        if reference_deaths is not None
        else 0
    )
    healthcare_cost = compute_healthcare_cost(
        additional_deaths, baseline["cost_per_death"]
    )
    gdp_loss = compute_gdp_loss(additional_deaths, baseline["gdp_per_capita"])

    lives_saved_vs_no_action = (
        compute_lives_saved(no_action_deaths, annual_deaths)
        if no_action_deaths is not None
        else 0
    )
    lives_saved_vs_reference = (
        compute_lives_saved(reference_deaths, annual_deaths)
        if reference_deaths is not None
        else 0
    )

    return {
        "scenario": scenario_name,
        "country": country,
        "projected_annual_deaths_final_year": final_year_deaths,
        "additional_deaths_from_delay": additional_deaths,
        "healthcare_cost_increase_usd_m": round(healthcare_cost, 2),
        "gdp_loss_usd_m": round(gdp_loss, 2),
        "critical_year": estimate_critical_year(
            years, resistance_burden, annual_deaths, baseline_deaths_value
        ),
        "lives_saved_early_vs_delayed": lives_saved_vs_reference,
        "lives_saved_vs_no_action": lives_saved_vs_no_action,
        "risk_level": compute_risk_level(resistance_burden),
        "intervention_strength": round(intervention_strength, 3),
        "assumptions_used": assumptions,
    }


def build_comparison_table(
    early_summary: dict[str, Any],
    delayed_summary: dict[str, Any],
    no_action_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build row-oriented data for frontend comparison tables / charts.

    Returns one dict per scenario with key metrics aligned for side-by-side display.
    """
    rows = []
    for summary in (early_summary, delayed_summary, no_action_summary):
        rows.append(
            {
                "scenario": summary["scenario"],
                "final_year_deaths": summary["projected_annual_deaths_final_year"],
                "additional_deaths_from_delay": summary["additional_deaths_from_delay"],
                "healthcare_cost_usd_m": summary["healthcare_cost_increase_usd_m"],
                "gdp_loss_usd_m": summary["gdp_loss_usd_m"],
                "critical_year": summary["critical_year"],
                "lives_saved_vs_no_action": summary["lives_saved_vs_no_action"],
                "risk_level": summary["risk_level"],
            }
        )
    return rows


def build_recovery_comparison_summary(
    recovery_deaths: list[int],
    continue_no_action_deaths: list[int],
    damage_info: dict[str, Any],
    country: str,
    recovery_summary: dict[str, Any],
    continue_no_action_summary: dict[str, Any],
) -> dict[str, Any]:
    """
    Summarize the What-If recovery comparison for the frontend.

    Compares recovery strategy against continuing inaction from the post-delay state.
    """
    lives_saved_by_recovery = compute_lives_saved(
        continue_no_action_deaths, recovery_deaths
    )
    baseline = get_country_baseline(country)

    return {
        "prior_delay_years": damage_info["prior_delay_years"],
        "damage_at_delay_end": {
            "rbi": damage_info["rbi_at_delay_end"],
            "annual_deaths": damage_info["deaths_at_delay_end"],
            "cumulative_deaths": damage_info["cumulative_deaths_during_delay"],
        },
        "lives_saved_by_recovery": lives_saved_by_recovery,
        "additional_deaths_avoided_vs_continue": lives_saved_by_recovery,
        "recovery_risk_level": recovery_summary["risk_level"],
        "continue_no_action_risk_level": continue_no_action_summary["risk_level"],
        "recovery_healthcare_savings_usd_m": round(
            compute_healthcare_cost(
                lives_saved_by_recovery, baseline["cost_per_death"]
            ),
            2,
        ),
        "recovery_gdp_savings_usd_m": round(
            compute_gdp_loss(lives_saved_by_recovery, baseline["gdp_per_capita"]),
            2,
        ),
    }
