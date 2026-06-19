"""
Authoritative source registry for the ResistAI temporary data module.

Catharine's production data/ module should replace the numeric values in
country_baselines.py and economic_assumptions.py while keeping the same
public functions exported from data/__init__.py.

Data vintage: 2019 mortality year (Lancet) + 2022–2024 report vintages where noted.
Last reviewed for MVP integration: 2025.
"""

from __future__ import annotations

DATA_VINTAGE = "2025-MVP-temporary"

# ---------------------------------------------------------------------------
# Primary references (human-readable for judges and README citations)
# ---------------------------------------------------------------------------

SOURCES: dict[str, str] = {
    "lancet_2022_global_direct_deaths": (
        "Murray CJ et al. Global burden of bacterial antimicrobial resistance "
        "in 2019: a systematic analysis. The Lancet, 2022. "
        "Reports ~1.27 million deaths directly attributable to bacterial AMR "
        "worldwide in 2019 (95% UI 1.06–1.51 million)."
    ),
    "lancet_2022_associated_deaths": (
        "Murray CJ et al. The Lancet, 2022. "
        "Reports ~4.95 million deaths associated with bacterial AMR in 2019."
    ),
    "lancet_2022_country_estimates": (
        "Murray CJ et al. The Lancet, 2022 — country-level estimates in "
        "supplementary materials. Country death counts used here are drawn from "
        "published Lancet country rankings and rounded for the simulator."
    ),
    "who_amr_global_report": (
        "WHO. Antimicrobial resistance and its implications (global reports). "
        "Used for qualitative severity tiers and policy context."
    ),
    "who_glass": (
        "WHO Global Antimicrobial Resistance and Use Surveillance System (GLASS). "
        "Used to inform relative resistance-burden tiers (RBI calibration). "
        "https://www.who.int/initiatives/glass"
    ),
    "oecd_amr_economic_burden": (
        "OECD. The Economic Impact of Antimicrobial Resistance (2019) and related "
        "health expenditure analyses. Used for excess healthcare cost assumptions."
    ),
    "world_bank_gdp": (
        "World Bank. GDP per capita (current US$), approximate 2023 values. "
        "Used for productivity-loss scaling in economic impact estimates."
    ),
    "rbi_calibration": (
        "ResistAI policy index (estimate): RBI (Resistance Burden Index) is NOT a "
        "WHO metric. Values 0–100 are calibrated to GLASS/WHO resistance severity "
        "tiers for demonstration purposes only."
    ),
    "country_modifier_calibration": (
        "ResistAI growth modifier (estimate): relative AMR growth scaling derived "
        "from WHO/OECD regional trend narratives, not a measured annual rate."
    ),
    "peru_country_deaths_estimate": (
        "Estimate: Peru annual AMR deaths scaled from Lancet 2022 Latin America "
        "regional burden and population share. Marked is_estimate=True in metadata."
    ),
}

# Standard disclaimer shown in the UI and metadata payloads.
POLICY_DISCLAIMER = (
    "ResistAI uses published AMR statistics and transparent estimates for "
    "policy education and decision-support simulation. It is not a clinical "
    "forecast and does not diagnose patients."
)
