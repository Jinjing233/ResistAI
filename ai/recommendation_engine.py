"""
AI-powered recommendation engine for the ResistAI project.

Uses Claude when ANTHROPIC_API_KEY is available; falls back to the local demo
generator so hackathon demos never fail due to missing credentials.
"""

from __future__ import annotations

import os

from ai.claude_client import ask_claude
from ai.demo_recommendation import generate_demo_recommendation


def _build_claude_prompt(
    country: str,
    delay_years: int,
    funding_level: str,
    stewardship_rate: float,
    rd_investment: str,
    deaths: int,
    healthcare_cost: float,
    gdp_loss: float,
) -> str:
    deaths_formatted = f"{deaths:,}"
    healthcare_cost_fmt = f"${healthcare_cost:,.1f}M"
    gdp_loss_fmt = f"${gdp_loss:,.1f}M"
    stewardship_pct = f"{stewardship_rate:.0f}%"

    return f"""
You are a public health policy advisor specializing in antimicrobial resistance (AMR).
Your audience is a government policymaker with no technical background.
Use clear, simple, and empathetic language. Avoid jargon.

## SIMULATION CONTEXT

- **Country:** {country}
- **Policy Delay:** {delay_years} year(s) without implementing AMR policies
- **Funding Level:** {funding_level}
- **Stewardship Adoption Rate:** {stewardship_pct}
- **R&D Investment Level:** {rd_investment}

## PROJECTED IMPACT OF THIS DELAY

- **Additional Deaths:** {deaths_formatted} people
- **Healthcare Cost Increase:** {healthcare_cost_fmt} USD
- **GDP Loss:** {gdp_loss_fmt} USD

---

Based on this simulation, please provide a structured policy brief with the following sections.
Use plain language as if explaining to someone making urgent national decisions.

### 1. SITUATION SUMMARY
Write 2-3 sentences explaining what this delay means in simple terms for {country}.

### 2. HUMAN IMPACT
Explain in human terms what {deaths_formatted} additional deaths means.
Use relatable comparisons (e.g., equivalent to filling X stadiums, X families affected).

### 3. ECONOMIC IMPACT
Explain what a loss of {gdp_loss_fmt} USD means for {country}'s economy in practical terms.
Mention what could have been funded instead (hospitals, schools, salaries).

### 4. IMMEDIATE ACTIONS (Next 30 days)
List 3 specific actions the government can take RIGHT NOW.
Each action should include an estimated number of lives that could be saved.

### 5. SHORT-TERM ACTIONS (3-12 months)
List 3 policy measures to implement within the year.
Each should include estimated lives saved and brief implementation notes.

### 6. LONG-TERM ACTIONS (1-5 years)
List 3 structural investments or reforms.
Each should include projected lives saved and economic benefit.

### 7. FINAL MESSAGE TO THE POLICYMAKER
End with a 2-3 sentence direct, compelling message that conveys the urgency
without being alarmist. Make it clear that action today saves lives tomorrow.

---
Format the response clearly with the section headers shown above.
Keep each section concise but impactful. Do NOT use overly technical terminology.
"""


def generate_recommendation(
    country: str,
    delay_years: int,
    funding_level: str,
    stewardship_rate: float,
    rd_investment: str,
    deaths: int,
    healthcare_cost: float,
    gdp_loss: float,
    risk_level: str = "Medium",
    intervention_strength: float = 0.5,
    lives_saved_vs_no_action: int = 0,
    critical_year: int | None = None,
    projected_final_year_deaths: int | None = None,
) -> tuple[str, str]:
    """
    Generate a policy recommendation using Claude or the local demo fallback.

    Returns:
        (recommendation_text, source) where source is "claude" or "demo".
    """
    demo_kwargs = dict(
        country=country,
        delay_years=delay_years,
        funding_level=funding_level,
        stewardship_rate=stewardship_rate,
        rd_investment=rd_investment,
        additional_deaths=deaths,
        healthcare_cost=healthcare_cost,
        gdp_loss=gdp_loss,
        risk_level=risk_level,
        intervention_strength=intervention_strength,
        lives_saved_vs_no_action=lives_saved_vs_no_action,
        critical_year=critical_year,
        projected_final_year_deaths=projected_final_year_deaths,
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return generate_demo_recommendation(**demo_kwargs), "demo"

    try:
        prompt = _build_claude_prompt(
            country,
            delay_years,
            funding_level,
            stewardship_rate,
            rd_investment,
            deaths,
            healthcare_cost,
            gdp_loss,
        )
        return ask_claude(prompt), "claude"
    except EnvironmentError:
        return generate_demo_recommendation(**demo_kwargs), "demo"
    except Exception:
        return generate_demo_recommendation(**demo_kwargs), "demo"
