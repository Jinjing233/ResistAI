"""
Authoritative source registry for the ResistAI data module.

Data vintage: 2019 mortality year (Lancet) + Catharine CSV datasets + 2022–2024 reports.
Last reviewed for MVP seven-country integration: 2025.
"""

from __future__ import annotations

DATA_VINTAGE = "2025-MVP-seven-country"

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
    "who_amr_csv": (
        "data/WHO_AMR_data.csv (Catharine). Resistance and infection-incidence "
        "proxies used to derive RBI where a CSV row exists."
    ),
    "oecd_economic_csv": (
        "data/OECD_economic_data.csv (Catharine). GDP per capita, country_modifier, "
        "and cost_per_death used where a CSV row exists."
    ),
    "who_amr_global_report": (
        "WHO. Antimicrobial resistance and its implications (global reports). "
        "Used for qualitative severity tiers and policy context."
    ),
    "who_glass": (
        "WHO Global Antimicrobial Resistance and Use Surveillance System (GLASS). "
        "Context for resistance-burden calibration. "
        "https://www.who.int/initiatives/glass"
    ),
    "oecd_amr_economic_burden": (
        "OECD. The Economic Impact of Antimicrobial Resistance (2019) and related "
        "health expenditure analyses. Used for excess healthcare cost assumptions."
    ),
    "world_bank_gdp": (
        "World Bank. GDP per capita (current US$), approximate 2023 values. "
        "Used for productivity-loss scaling where not supplied by OECD CSV."
    ),
    "rbi_from_who_csv": (
        "ResistAI policy index (estimate): RBI = mean(WHO CSV resistance proxies) × 100. "
        "NOT a WHO official metric."
    ),
    "rbi_calibration": (
        "ResistAI policy index (estimate): RBI (Resistance Burden Index) is NOT a "
        "WHO metric. Used for Global and Peru where no WHO CSV row exists."
    ),
    "country_modifier_calibration": (
        "ResistAI growth modifier (estimate): relative AMR growth scaling derived "
        "from WHO/OECD regional trend narratives when not supplied by OECD CSV."
    ),
    "peru_country_deaths_estimate": (
        "Estimate: Peru annual AMR deaths scaled from Lancet 2022 Latin America "
        "regional burden and population share. Marked is_estimate=True in metadata."
    ),
    "nigeria_country_deaths_estimate": (
        "Estimate: Nigeria direct AMR deaths scaled from Lancet 2022 Sub-Saharan "
        "Africa high-burden country ranking, adjusted upward by WHO CSV "
        "infection_incidence (0.70). Marked is_estimate=True."
    ),
    "uk_country_deaths_estimate": (
        "Estimate: UK direct AMR deaths scaled from Lancet 2022 high-income "
        "European country-level allocation, consistent with lower WHO CSV "
        "resistance proxies. Marked is_estimate=True."
    ),
}

POLICY_DISCLAIMER = (
    "ResistAI uses published AMR statistics and transparent estimates for "
    "policy education and decision-support simulation. It is not a clinical "
    "forecast and does not diagnose patients."
)
