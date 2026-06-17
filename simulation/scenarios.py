"""
Scenario definitions and orchestration for ResistAI.

Scenarios:
  - Early Action:        intervention begins immediately (year 0)
  - Delayed Action:      full growth for delay_years, then intervention
  - No Additional Action: no intervention for the full horizon
  - Recovery Strategy:   simulate prior inaction, then compare recovery vs status quo

IMPORTANT: Policy simulation only — not for clinical decision-making.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from simulation.amr_model import (
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_START_YEAR,
    compute_intervention_strength,
    get_country_baseline,
    normalize_level,
    project_timeline,
)
from simulation.calculations import (
    build_comparison_table,
    build_recovery_comparison_summary,
    build_summary,
    compute_cumulative_deaths,
)


class ScenarioType(str, Enum):
    """Supported simulation scenario types."""

    EARLY_ACTION = "Early Action"
    DELAYED_ACTION = "Delayed Action"
    NO_ADDITIONAL_ACTION = "No Additional Action"
    RECOVERY_STRATEGY = "Recovery Strategy"


@dataclass
class SimulationInputs:
    """
    User-controlled inputs for the main three-scenario comparison.

    Attributes:
        country:            Country or region (Global, USA, India, Brazil, Peru).
        delay_years:        Years of policy delay before intervention (0–20).
        funding_level:      'Low', 'Medium', or 'High'.
        stewardship_rate:   Antibiotic stewardship adoption rate (0–100 %).
        rd_investment:      'Low', 'Medium', or 'High'.
        projection_years:   Simulation horizon (default 20 years).
        start_year:         Calendar year for year-0 (default 2025).
    """

    country: str
    delay_years: int
    funding_level: str
    stewardship_rate: float
    rd_investment: str
    projection_years: int = DEFAULT_PROJECTION_YEARS
    start_year: int = DEFAULT_START_YEAR


@dataclass
class RecoveryInputs:
    """
    Inputs for the What-If recovery strategy simulator.

    Workflow:
      1. Simulate damage from prior_delay_years of inaction.
      2. Project forward with chosen recovery levers.
      3. Compare against continuing with no action from the damaged state.
    """

    country: str
    prior_delay_years: int
    funding_level: str
    stewardship_rate: float
    rd_investment: str
    projection_years: int = 10
    start_year: int = DEFAULT_START_YEAR


@dataclass
class SimulationResult:
    """Output container for a single scenario run."""

    scenario: str
    country: str
    years: list[int]
    annual_deaths: list[int]
    resistance_burden: list[float]
    summary: dict[str, Any]


@dataclass
class ScenarioComparison:
    """Side-by-side results for Early, Delayed, and No Action scenarios."""

    early: SimulationResult
    delayed: SimulationResult
    no_action: SimulationResult
    comparison_summary: dict[str, Any]
    comparison_table: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RecoveryComparison:
    """Results for the What-If recovery strategy workflow."""

    damage_phase: dict[str, Any]
    recovery: SimulationResult
    continue_no_action: SimulationResult
    comparison_summary: dict[str, Any]


def _validate_simulation_inputs(inputs: SimulationInputs) -> SimulationInputs:
    """Clamp and normalize main simulation inputs."""
    return SimulationInputs(
        country=get_country_baseline(inputs.country)["country"],
        delay_years=max(0, min(20, int(inputs.delay_years))),
        funding_level=normalize_level(inputs.funding_level),
        stewardship_rate=max(0.0, min(100.0, float(inputs.stewardship_rate))),
        rd_investment=normalize_level(inputs.rd_investment),
        projection_years=max(1, int(inputs.projection_years)),
        start_year=int(inputs.start_year),
    )


def _validate_recovery_inputs(inputs: RecoveryInputs) -> RecoveryInputs:
    """Clamp and normalize recovery simulation inputs."""
    return RecoveryInputs(
        country=get_country_baseline(inputs.country)["country"],
        prior_delay_years=max(1, min(20, int(inputs.prior_delay_years))),
        funding_level=normalize_level(inputs.funding_level),
        stewardship_rate=max(0.0, min(100.0, float(inputs.stewardship_rate))),
        rd_investment=normalize_level(inputs.rd_investment),
        projection_years=max(1, int(inputs.projection_years)),
        start_year=int(inputs.start_year),
    )


def build_scenario_config(
    scenario_type: ScenarioType,
    inputs: SimulationInputs,
) -> dict[str, Any]:
    """
    Map a scenario type to intervention timing and strength parameters.

    Returns:
        Dict with intervention_start_year and intervention_strength.
    """
    strength = compute_intervention_strength(
        inputs.funding_level,
        inputs.stewardship_rate,
        inputs.rd_investment,
    )

    if scenario_type == ScenarioType.EARLY_ACTION:
        start = 0
    elif scenario_type == ScenarioType.DELAYED_ACTION:
        start = inputs.delay_years
    elif scenario_type == ScenarioType.NO_ADDITIONAL_ACTION:
        start = inputs.projection_years + 1  # never intervenes within horizon
        strength = 0.0
    else:
        raise ValueError(
            f"ScenarioType {scenario_type} is not supported by build_scenario_config."
        )

    return {
        "intervention_start_year": start,
        "intervention_strength": strength,
    }


def _timeline_to_result(
    scenario_name: str,
    timeline: dict[str, Any],
    intervention_strength: float,
    reference_deaths: list[int] | None = None,
    no_action_deaths: list[int] | None = None,
) -> SimulationResult:
    """Convert a raw timeline dict into a SimulationResult with summary."""
    summary = build_summary(
        scenario_name=scenario_name,
        country=timeline["country"],
        years=timeline["years"],
        annual_deaths=timeline["annual_deaths"],
        resistance_burden=timeline["resistance_burden"],
        intervention_strength=intervention_strength,
        assumptions=timeline["assumptions"],
        reference_deaths=reference_deaths,
        no_action_deaths=no_action_deaths,
    )
    return SimulationResult(
        scenario=scenario_name,
        country=timeline["country"],
        years=timeline["years"],
        annual_deaths=timeline["annual_deaths"],
        resistance_burden=timeline["resistance_burden"],
        summary=summary,
    )


def run_scenario(
    scenario_type: ScenarioType,
    inputs: SimulationInputs,
    reference_deaths: list[int] | None = None,
    no_action_deaths: list[int] | None = None,
) -> SimulationResult:
    """
    Run a single scenario projection.

    Args:
        scenario_type:    Which scenario to simulate.
        inputs:           User-controlled parameters.
        reference_deaths: Early Action deaths (for additional-death baseline).
        no_action_deaths: No Action deaths (for lives-saved metrics).

    Returns:
        SimulationResult with time series and summary dict.
    """
    validated = _validate_simulation_inputs(inputs)
    config = build_scenario_config(scenario_type, validated)

    timeline = project_timeline(
        country=validated.country,
        intervention_start_year=config["intervention_start_year"],
        intervention_strength=config["intervention_strength"],
        projection_years=validated.projection_years,
        start_year=validated.start_year,
    )

    return _timeline_to_result(
        scenario_name=scenario_type.value,
        timeline=timeline,
        intervention_strength=config["intervention_strength"],
        reference_deaths=reference_deaths,
        no_action_deaths=no_action_deaths,
    )


def compare_scenarios(inputs: SimulationInputs) -> ScenarioComparison:
    """
    Run Early Action, Delayed Action, and No Additional Action scenarios.

    Additional deaths are measured against Early Action (cost-of-delay narrative).
    """
    validated = _validate_simulation_inputs(inputs)

    early = run_scenario(ScenarioType.EARLY_ACTION, validated)
    no_action = run_scenario(ScenarioType.NO_ADDITIONAL_ACTION, validated)

    early = run_scenario(
        ScenarioType.EARLY_ACTION,
        validated,
        reference_deaths=early.annual_deaths,
        no_action_deaths=no_action.annual_deaths,
    )
    no_action = run_scenario(
        ScenarioType.NO_ADDITIONAL_ACTION,
        validated,
        reference_deaths=early.annual_deaths,
        no_action_deaths=no_action.annual_deaths,
    )
    delayed = run_scenario(
        ScenarioType.DELAYED_ACTION,
        validated,
        reference_deaths=early.annual_deaths,
        no_action_deaths=no_action.annual_deaths,
    )

    comparison_summary = {
        "country": validated.country,
        "delay_years": validated.delay_years,
        "additional_deaths_from_delay": delayed.summary["additional_deaths_from_delay"],
        "healthcare_cost_increase_usd_m": delayed.summary[
            "healthcare_cost_increase_usd_m"
        ],
        "gdp_loss_usd_m": delayed.summary["gdp_loss_usd_m"],
        "lives_saved_by_early_action": early.summary["lives_saved_vs_no_action"],
        "lives_lost_to_delay": delayed.summary["additional_deaths_from_delay"],
        "best_scenario": "Early Action",
        "worst_scenario": "No Additional Action",
        "critical_year_early": early.summary["critical_year"],
        "critical_year_delayed": delayed.summary["critical_year"],
        "critical_year_no_action": no_action.summary["critical_year"],
    }

    return ScenarioComparison(
        early=early,
        delayed=delayed,
        no_action=no_action,
        comparison_summary=comparison_summary,
        comparison_table=build_comparison_table(
            early.summary, delayed.summary, no_action.summary
        ),
    )


def run_recovery_comparison(inputs: RecoveryInputs) -> RecoveryComparison:
    """
    What-If recovery workflow (core innovation feature).

    Steps:
      1. Simulate prior_delay_years of inaction to establish damaged baseline.
      2. From that state, project recovery_years forward with user recovery levers.
      3. In parallel, project the same horizon with continued inaction.
      4. Compare outcomes (lives saved, cost savings, risk levels).
    """
    validated = _validate_recovery_inputs(inputs)

    # Phase 1 — damage from prior inaction.
    damage_timeline = project_timeline(
        country=validated.country,
        intervention_start_year=validated.prior_delay_years + 1,
        intervention_strength=0.0,
        projection_years=validated.prior_delay_years,
        start_year=validated.start_year,
    )

    rbi_at_end = damage_timeline["resistance_burden"][-1]
    deaths_at_end = damage_timeline["annual_deaths"][-1]
    recovery_start_year = damage_timeline["years"][-1]

    damage_info = {
        "prior_delay_years": validated.prior_delay_years,
        "rbi_at_delay_end": round(rbi_at_end, 2),
        "deaths_at_delay_end": deaths_at_end,
        "cumulative_deaths_during_delay": compute_cumulative_deaths(
            damage_timeline["annual_deaths"]
        ),
        "years": damage_timeline["years"],
        "resistance_burden": damage_timeline["resistance_burden"],
        "annual_deaths": damage_timeline["annual_deaths"],
    }

    recovery_strength = compute_intervention_strength(
        validated.funding_level,
        validated.stewardship_rate,
        validated.rd_investment,
    )

    # Phase 2a — recovery strategy from damaged state.
    recovery_timeline = project_timeline(
        country=validated.country,
        intervention_start_year=0,
        intervention_strength=recovery_strength,
        projection_years=validated.projection_years,
        start_year=recovery_start_year,
        initial_rbi=rbi_at_end,
        initial_deaths=deaths_at_end,
    )

    # Phase 2b — continue with no action from damaged state.
    continue_timeline = project_timeline(
        country=validated.country,
        intervention_start_year=validated.projection_years + 1,
        intervention_strength=0.0,
        projection_years=validated.projection_years,
        start_year=recovery_start_year,
        initial_rbi=rbi_at_end,
        initial_deaths=deaths_at_end,
    )

    recovery_result = _timeline_to_result(
        scenario_name=ScenarioType.RECOVERY_STRATEGY.value,
        timeline=recovery_timeline,
        intervention_strength=recovery_strength,
        reference_deaths=continue_timeline["annual_deaths"],
        no_action_deaths=continue_timeline["annual_deaths"],
    )

    continue_result = _timeline_to_result(
        scenario_name=ScenarioType.NO_ADDITIONAL_ACTION.value,
        timeline=continue_timeline,
        intervention_strength=0.0,
        reference_deaths=recovery_timeline["annual_deaths"],
        no_action_deaths=continue_timeline["annual_deaths"],
    )

    comparison_summary = build_recovery_comparison_summary(
        recovery_deaths=recovery_result.annual_deaths,
        continue_no_action_deaths=continue_result.annual_deaths,
        damage_info=damage_info,
        country=validated.country,
        recovery_summary=recovery_result.summary,
        continue_no_action_summary=continue_result.summary,
    )

    return RecoveryComparison(
        damage_phase=damage_info,
        recovery=recovery_result,
        continue_no_action=continue_result,
        comparison_summary=comparison_summary,
    )
