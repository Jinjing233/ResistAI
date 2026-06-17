"""
ResistAI simulation module — public API.

Policy decision-support simulator for antimicrobial resistance (AMR).
NOT for clinical use.

Quick start:
    from simulation import SimulationInputs, compare_scenarios

    result = compare_scenarios(SimulationInputs(
        country="Peru",
        delay_years=5,
        funding_level="Medium",
        stewardship_rate=50.0,
        rd_investment="Medium",
    ))
    print(result.delayed.summary["additional_deaths_from_delay"])
"""

from simulation.amr_model import (
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_START_YEAR,
    compute_intervention_strength,
    get_country_baseline,
    project_timeline,
)
from simulation.calculations import (
    build_comparison_table,
    build_summary,
    compute_additional_deaths,
    compute_gdp_loss,
    compute_healthcare_cost,
    compute_lives_saved,
    compute_risk_level,
    estimate_critical_year,
)
from simulation.scenarios import (
    RecoveryComparison,
    RecoveryInputs,
    ScenarioComparison,
    ScenarioType,
    SimulationInputs,
    SimulationResult,
    build_scenario_config,
    compare_scenarios,
    run_recovery_comparison,
    run_scenario,
)

__all__ = [
    # Types
    "ScenarioType",
    "SimulationInputs",
    "RecoveryInputs",
    "SimulationResult",
    "ScenarioComparison",
    "RecoveryComparison",
    # Scenario runners
    "run_scenario",
    "compare_scenarios",
    "run_recovery_comparison",
    "build_scenario_config",
    # Core model
    "get_country_baseline",
    "compute_intervention_strength",
    "project_timeline",
    # Calculations
    "build_summary",
    "build_comparison_table",
    "compute_additional_deaths",
    "compute_healthcare_cost",
    "compute_gdp_loss",
    "compute_lives_saved",
    "estimate_critical_year",
    "compute_risk_level",
    # Constants
    "DEFAULT_PROJECTION_YEARS",
    "DEFAULT_START_YEAR",
]

# Convenience alias used in architecture docs.
run_simulation = compare_scenarios
