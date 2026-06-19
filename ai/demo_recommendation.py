"""Local policy brief generator for hackathon demos when Claude is unavailable."""

from __future__ import annotations


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def _fmt_usd_m(value: float) -> str:
    return f"${value:,.1f}M"


def generate_demo_recommendation(
    *,
    country: str,
    delay_years: int,
    funding_level: str,
    stewardship_rate: float,
    rd_investment: str,
    additional_deaths: int,
    healthcare_cost: float,
    gdp_loss: float,
    risk_level: str,
    intervention_strength: float,
    lives_saved_vs_no_action: int = 0,
    critical_year: int | None = None,
    projected_final_year_deaths: int | None = None,
) -> str:
    """Build a structured policy brief from simulation metrics."""
    stewardship_pct = f"{stewardship_rate:.0f}%"
    critical = str(critical_year) if critical_year else "not reached within the projection horizon"
    final_deaths = (
        _fmt_int(projected_final_year_deaths)
        if projected_final_year_deaths is not None
        else "rising steadily"
    )
    strength_pct = f"{intervention_strength * 100:.0f}%"

    immediate_lives = max(int(additional_deaths * 0.08), 1)
    short_lives = max(int(additional_deaths * 0.25), 1)
    long_lives = max(int(lives_saved_vs_no_action * 0.4), 1)

    return f"""### 1. SITUATION SUMMARY

Delaying AMR action in **{country}** by **{delay_years} year(s)** under **{funding_level}** funding, **{stewardship_pct}** stewardship adoption, and **{rd_investment}** R&D investment allows resistance to deepen. The simulation classifies the delayed pathway as **{risk_level}** risk, with intervention strength estimated at **{strength_pct}** of what early action would achieve.

### 2. HUMAN IMPACT

**{_fmt_int(additional_deaths)} additional deaths** are projected versus early action — lives that could be protected with timely policy. Early intervention could save **{_fmt_int(lives_saved_vs_no_action)} lives** compared with no additional action. Without course correction, annual deaths could reach **{final_deaths}** by the final projection year, with a critical inflection around **{critical}**.

### 3. ECONOMIC IMPACT

The delay adds **{_fmt_usd_m(healthcare_cost)}** in healthcare costs and **{_fmt_usd_m(gdp_loss)}** in GDP/productivity losses. These resources could otherwise fund hospitals, workforce training, surveillance systems, and school infrastructure — investments that both save lives and strengthen the economy.

### 4. IMMEDIATE ACTIONS (Next 30 days)

1. **Declare AMR a national priority** and convene a cross-ministry task force — estimated **{_fmt_int(immediate_lives)}** lives protected through rapid coordination.
2. **Fund antibiotic stewardship in the highest-burden facilities** — estimated **{_fmt_int(immediate_lives)}** lives protected by reducing inappropriate prescribing.
3. **Launch a public awareness campaign on responsible antibiotic use** — estimated **{_fmt_int(immediate_lives)}** lives protected by slowing community resistance spread.

### 5. SHORT-TERM STRATEGIES (3–12 months)

1. **Scale stewardship programs to {_fmt_int(int(stewardship_rate))}%+ facility coverage** — projected **{_fmt_int(short_lives)}** lives saved; align with current **{funding_level}** funding envelope.
2. **Expand AMR surveillance and reporting** — projected **{_fmt_int(short_lives)}** lives saved through earlier detection of resistance hotspots.
3. **Incentivize appropriate prescribing and diagnostics** — projected **{_fmt_int(short_lives)}** lives saved by replacing empiric broad-spectrum use.

### 6. LONG-TERM STRATEGIES (1–5 years)

1. **Increase R&D investment from {rd_investment} toward sustained high-tier funding** — projected **{_fmt_int(long_lives)}** lives saved via new treatments and diagnostics.
2. **Integrate AMR into national health and economic planning** — projected economic benefit of avoiding further **{_fmt_usd_m(gdp_loss)}**-scale losses.
3. **Build regional collaboration on resistance containment** — projected **{_fmt_int(long_lives)}** lives saved by preventing cross-border spread.

### 7. FINAL RECOMMENDATION FOR POLICYMAKERS

Every year of delay in **{country}** converts a preventable crisis into permanent loss. The simulation shows that early action saves **{_fmt_int(lives_saved_vs_no_action)} lives** and avoids **{_fmt_usd_m(gdp_loss)}** in economic damage. Policymakers should treat AMR funding and stewardship not as optional health spending, but as urgent national security for public health and the economy — action today determines how many lives **{country}** can still protect tomorrow.
"""
