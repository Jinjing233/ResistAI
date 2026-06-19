"""
ResistAI — Streamlit integration controller (MVP).

Workflow:
  User inputs → simulation + data → AI recommendation → Streamlit charts + frontend display
"""

from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from data import DATA_VINTAGE, get_country_baseline, list_supported_countries
from simulation import (
    RecoveryInputs,
    SimulationInputs,
    compare_scenarios,
    run_recovery_comparison,
)

try:
    from ai.recommendation_engine import generate_recommendation

    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

FRONTEND_DIR = Path(__file__).parent / "frontend"

SCENARIO_COLORS = {
    "Early Action": "#39d98a",
    "Delayed Action": "#ffb347",
    "No Additional Action": "#ff3b30",
    "Recovery Strategy": "#39d98a",
}


def _serialize_scenario(result) -> dict:
    """Convert a SimulationResult into JSON-safe dict for the frontend."""
    return {
        "scenario": result.scenario,
        "country": result.country,
        "years": result.years,
        "annual_deaths": result.annual_deaths,
        "resistance_burden": result.resistance_burden,
        "summary": result.summary,
    }


def build_display_payload(
    comparison,
    inputs: SimulationInputs,
    recovery=None,
    ai_recommendation: str | None = None,
    ai_fallback: str | None = None,
) -> dict:
    """Build the JSON payload consumed by frontend/script.js."""
    global_baseline = get_country_baseline("Global")
    payload = {
        "embedded": True,
        "supported_countries": list_supported_countries(),
        "global_direct_deaths": global_baseline["baseline_deaths"],
        "data_vintage": DATA_VINTAGE,
        "inputs": {
            "country": inputs.country,
            "delay_years": inputs.delay_years,
            "funding_level": inputs.funding_level,
            "stewardship_rate": inputs.stewardship_rate,
            "rd_investment": inputs.rd_investment,
        },
        "comparison": {
            "early": _serialize_scenario(comparison.early),
            "delayed": _serialize_scenario(comparison.delayed),
            "no_action": _serialize_scenario(comparison.no_action),
            "summary": comparison.comparison_summary,
        },
        "ai_recommendation": ai_recommendation or "",
        "ai_fallback": ai_fallback or "",
    }
    if recovery is not None:
        payload["recovery"] = {
            "damage_phase": recovery.damage_phase,
            "recovery": _serialize_scenario(recovery.recovery),
            "continue_no_action": _serialize_scenario(recovery.continue_no_action),
            "comparison_summary": recovery.comparison_summary,
        }
    return payload


def plot_scenario_deaths(comparison) -> go.Figure:
    """Line chart: annual deaths for Early, Delayed, and No Action."""
    fig = go.Figure()
    for result in (comparison.early, comparison.delayed, comparison.no_action):
        fig.add_trace(
            go.Scatter(
                x=result.years,
                y=result.annual_deaths,
                mode="lines",
                name=result.scenario,
                line=dict(color=SCENARIO_COLORS.get(result.scenario, "#ffffff"), width=3),
            )
        )
    fig.update_layout(
        title="Annual AMR deaths by scenario",
        xaxis_title="Year",
        yaxis_title="Deaths per year",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig


def plot_scenario_costs(comparison) -> go.Figure:
    """Bar chart: healthcare cost increase vs Early Action baseline."""
    scenarios = ["Early Action", "Delayed Action", "No Additional Action"]
    results = [comparison.early, comparison.delayed, comparison.no_action]
    values = [r.summary["healthcare_cost_increase_usd_m"] for r in results]
    colors = [SCENARIO_COLORS[s] for s in scenarios]

    fig = go.Figure(
        data=[
            go.Bar(
                x=scenarios,
                y=values,
                marker_color=colors,
                text=[f"${v:,.1f}M" for v in values],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title="Healthcare cost increase vs Early Action (USD millions)",
        yaxis_title="USD millions",
        template="plotly_dark",
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig


def plot_recovery_deaths(recovery) -> go.Figure:
    """Line chart: recovery strategy vs continued no action after delay damage."""
    fig = go.Figure()
    for result in (recovery.recovery, recovery.continue_no_action):
        fig.add_trace(
            go.Scatter(
                x=result.years,
                y=result.annual_deaths,
                mode="lines",
                name=result.scenario,
                line=dict(color=SCENARIO_COLORS.get(result.scenario, "#ffb347"), width=3),
            )
        )
    fig.update_layout(
        title="Recovery What-If: annual deaths after prior delay",
        xaxis_title="Year",
        yaxis_title="Deaths per year",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
    )
    return fig


def plot_damage_phase(recovery) -> go.Figure:
    """Line chart: AMR damage accumulated during the prior delay period."""
    damage = recovery.damage_phase
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=damage["years"],
            y=damage["annual_deaths"],
            mode="lines+markers",
            name="Deaths during delay",
            line=dict(color="#ff3b30", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=damage["years"],
            y=damage["resistance_burden"],
            mode="lines",
            name="Resistance burden (RBI)",
            yaxis="y2",
            line=dict(color="#ffb347", width=2, dash="dot"),
        )
    )
    fig.update_layout(
        title=f"Damage phase: {damage['prior_delay_years']} year(s) of inaction",
        xaxis_title="Year",
        yaxis=dict(title="Annual deaths"),
        yaxis2=dict(title="RBI", overlaying="y", side="right"),
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=420,
    )
    return fig


def render_frontend_display(payload: dict, height: int = 3600) -> None:
    """Embed the static frontend with injected simulation payload."""
    css = (FRONTEND_DIR / "style.css").read_text(encoding="utf-8")
    js = (FRONTEND_DIR / "script.js").read_text(encoding="utf-8")
    body_html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    main_start = body_html.find("<main")
    main_end = body_html.rfind("</main>") + len("</main>")
    main_content = body_html[main_start:main_end]

    payload_json = json.dumps(payload).replace("</", "<\\/")

    html_doc = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet" />
        <style>{css}</style>
      </head>
      <body>
        {main_content}
        <script>
          window.RESISTAI_PAYLOAD = {payload_json};
        </script>
        <script>{js}</script>
      </body>
    </html>
    """
    components.html(html_doc, height=height, scrolling=True)


def run_ai_recommendation(inputs: SimulationInputs, delayed_summary: dict) -> tuple[str | None, str | None]:
    """Call the AI module or return a fallback message if unavailable."""
    if not AI_AVAILABLE:
        return None, "AI module could not be imported. Check ai/ package syntax and dependencies."

    try:
        text = generate_recommendation(
            country=inputs.country,
            delay_years=inputs.delay_years,
            funding_level=inputs.funding_level,
            stewardship_rate=inputs.stewardship_rate,
            rd_investment=inputs.rd_investment,
            deaths=delayed_summary["additional_deaths_from_delay"],
            healthcare_cost=delayed_summary["healthcare_cost_increase_usd_m"],
            gdp_loss=delayed_summary["gdp_loss_usd_m"],
        )
        return text, None
    except EnvironmentError:
        return None, (
            "AI recommendations require ANTHROPIC_API_KEY. "
            "Simulation results below are still fully functional."
        )
    except Exception as exc:
        return None, f"AI recommendation unavailable: {exc}"


def render_delay_section(comparison) -> None:
    """Streamlit section: Cost of Delay scenario comparison."""
    delayed = comparison.delayed.summary

    st.subheader("Cost of Delay — scenario comparison")
    cols = st.columns(4)
    cols[0].metric("Additional deaths from delay", f"{delayed['additional_deaths_from_delay']:,}")
    cols[1].metric(
        "Healthcare cost increase (USD M)",
        f"${delayed['healthcare_cost_increase_usd_m']:,.1f}",
    )
    cols[2].metric("GDP loss (USD M)", f"${delayed['gdp_loss_usd_m']:,.1f}")
    cols[3].metric("Risk level (delayed)", delayed["risk_level"])

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.plotly_chart(plot_scenario_deaths(comparison), use_container_width=True)
    with chart_cols[1]:
        st.plotly_chart(plot_scenario_costs(comparison), use_container_width=True)

    with st.expander("Scenario comparison table"):
        rows = []
        for result in (comparison.early, comparison.delayed, comparison.no_action):
            s = result.summary
            rows.append(
                {
                    "Scenario": result.scenario,
                    "Cumulative deaths": sum(result.annual_deaths),
                    "Additional deaths vs early": s["additional_deaths_from_delay"],
                    "Healthcare cost (USD M)": s["healthcare_cost_increase_usd_m"],
                    "GDP loss (USD M)": s["gdp_loss_usd_m"],
                    "Lives saved vs no action": s["lives_saved_vs_no_action"],
                    "Risk level": s["risk_level"],
                    "Critical year": s["critical_year"],
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)


def render_recovery_section(recovery, prior_delay_years: int) -> None:
    """Streamlit section: Recovery What-If comparison."""
    summary = recovery.comparison_summary
    damage = summary["damage_at_delay_end"]

    st.subheader("Recovery What-If — after a period of inaction")
    st.caption(
        f"Assumes {prior_delay_years} year(s) of prior inaction, then compares a "
        "recovery strategy against continuing with no additional action."
    )

    st.markdown("**1. Damage caused by delay**")
    damage_cols = st.columns(3)
    damage_cols[0].metric("RBI at delay end", f"{damage['rbi']}")
    damage_cols[1].metric("Annual deaths at delay end", f"{damage['annual_deaths']:,}")
    damage_cols[2].metric(
        "Cumulative deaths during delay",
        f"{damage['cumulative_deaths']:,}",
    )
    st.plotly_chart(plot_damage_phase(recovery), use_container_width=True)

    st.markdown("**2. Recovery strategy vs continued no action**")
    benefit_cols = st.columns(4)
    benefit_cols[0].metric(
        "Lives saved by recovery",
        f"{summary['lives_saved_by_recovery']:,}",
    )
    benefit_cols[1].metric(
        "Healthcare cost avoided (USD M)",
        f"${summary['recovery_healthcare_savings_usd_m']:,.1f}",
    )
    benefit_cols[2].metric(
        "GDP loss avoided (USD M)",
        f"${summary['recovery_gdp_savings_usd_m']:,.1f}",
    )
    benefit_cols[3].metric(
        "Risk: recovery → continue",
        f"{summary['recovery_risk_level']} → {summary['continue_no_action_risk_level']}",
    )

    recovery_cols = st.columns(2)
    with recovery_cols[0]:
        st.plotly_chart(plot_recovery_deaths(recovery), use_container_width=True)
    with recovery_cols[1]:
        compare_rows = [
            {
                "Pathway": "Recovery Strategy",
                "Cumulative deaths": sum(recovery.recovery.annual_deaths),
                "Risk level": recovery.recovery.summary["risk_level"],
                "Final-year deaths": recovery.recovery.summary[
                    "projected_annual_deaths_final_year"
                ],
            },
            {
                "Pathway": "Continued no action",
                "Cumulative deaths": sum(recovery.continue_no_action.annual_deaths),
                "Risk level": recovery.continue_no_action.summary["risk_level"],
                "Final-year deaths": recovery.continue_no_action.summary[
                    "projected_annual_deaths_final_year"
                ],
            },
        ]
        st.markdown("**3. Side-by-side outcomes**")
        st.dataframe(compare_rows, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="ResistAI: The Cost of Delay",
        page_icon="🦠",
        layout="wide",
    )

    st.title("ResistAI: The Cost of Delay")
    st.caption(
        "Policy decision-support simulator — not for clinical use. "
        f"Data vintage: {DATA_VINTAGE}"
    )

    with st.sidebar:
        st.header("Scenario inputs")
        country = st.selectbox("Country / region", list_supported_countries(), index=4)
        delay_years = st.slider("Years of delay", min_value=0, max_value=20, value=5)
        funding_level = st.selectbox("Funding level", ["Low", "Medium", "High"], index=1)
        stewardship_rate = st.slider(
            "Stewardship adoption rate (%)", min_value=0, max_value=100, value=50
        )
        rd_investment = st.selectbox("R&D investment", ["Low", "Medium", "High"], index=1)

        st.divider()
        st.header("Recovery What-If")
        st.caption("Policy levers applied after the delay period ends.")
        recovery_funding = st.selectbox(
            "Recovery funding level", ["Low", "Medium", "High"], index=2, key="recovery_funding"
        )
        recovery_stewardship = st.slider(
            "Recovery stewardship (%)", 0, 100, 75, key="recovery_stewardship"
        )
        recovery_rd = st.selectbox(
            "Recovery R&D investment", ["Low", "Medium", "High"], index=2, key="recovery_rd"
        )
        recovery_horizon = st.slider(
            "Recovery projection (years)", min_value=5, max_value=20, value=10, key="recovery_horizon"
        )

        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)

    inputs = SimulationInputs(
        country=country,
        delay_years=delay_years,
        funding_level=funding_level,
        stewardship_rate=float(stewardship_rate),
        rd_investment=rd_investment,
    )

    if run_clicked or "comparison" not in st.session_state:
        with st.spinner("Running AMR simulation..."):
            comparison = compare_scenarios(inputs)
            ai_text, ai_fallback = run_ai_recommendation(inputs, comparison.delayed.summary)

            recovery = None
            recovery_note = None
            effective_prior_delay = max(delay_years, 1)
            if delay_years >= 1:
                recovery_inputs = RecoveryInputs(
                    country=country,
                    prior_delay_years=effective_prior_delay,
                    funding_level=recovery_funding,
                    stewardship_rate=float(recovery_stewardship),
                    rd_investment=recovery_rd,
                    projection_years=recovery_horizon,
                )
                recovery = run_recovery_comparison(recovery_inputs)
            else:
                recovery_note = (
                    "Recovery What-If requires at least 1 year of prior delay. "
                    "Increase 'Years of delay' to enable this section."
                )

            st.session_state["comparison"] = comparison
            st.session_state["inputs"] = inputs
            st.session_state["recovery"] = recovery
            st.session_state["recovery_note"] = recovery_note
            st.session_state["effective_prior_delay"] = effective_prior_delay
            st.session_state["ai_text"] = ai_text
            st.session_state["ai_fallback"] = ai_fallback

    comparison = st.session_state["comparison"]
    inputs = st.session_state["inputs"]
    recovery = st.session_state.get("recovery")
    recovery_note = st.session_state.get("recovery_note")

    tab_delay, tab_recovery, tab_ai, tab_ui = st.tabs(
        ["Cost of Delay", "Recovery What-If", "AI Recommendation", "Full UI"]
    )

    with tab_delay:
        render_delay_section(comparison)

    with tab_recovery:
        if recovery is not None:
            render_recovery_section(recovery, st.session_state["effective_prior_delay"])
        else:
            st.info(recovery_note or "Run the simulation to view recovery outcomes.")

    with tab_ai:
        if st.session_state.get("ai_text"):
            st.markdown(st.session_state["ai_text"])
        elif st.session_state.get("ai_fallback"):
            st.info(st.session_state["ai_fallback"])
        else:
            st.caption("Run the simulation to generate an AI policy brief.")

    with tab_ui:
        st.caption("Embedded frontend display layer (visual report).")
        payload = build_display_payload(
            comparison=comparison,
            inputs=inputs,
            recovery=recovery,
            ai_recommendation=st.session_state.get("ai_text"),
            ai_fallback=st.session_state.get("ai_fallback"),
        )
        render_frontend_display(payload)


if __name__ == "__main__":
    main()
