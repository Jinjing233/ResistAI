"""
ResistAI — Streamlit integration controller (MVP).

Workflow:
  User inputs → simulation + data → AI recommendation → Full UI visualization
"""

from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

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
SECONDS_PER_YEAR = 365 * 24 * 60 * 60

SCENARIO_COLORS = {
    "Early Action": "#39d98a",
    "Delayed Action": "#ffb347",
    "No Additional Action": "#ff3b30",
    "Recovery Strategy": "#39d98a",
}

PLOTLY_CONFIG = {"responsive": True, "displayModeBar": False}


def inject_design_system() -> None:
    """Load Full UI fonts and CSS into the Streamlit page."""
    css = (FRONTEND_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700;800&family=Poppins:wght@600;700;800&display=swap"
          rel="stylesheet"
        />
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def compute_amr_deaths_today(global_annual_deaths: int) -> int:
    """Estimate global AMR deaths since local midnight (Python-only counter)."""
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    deaths_per_second = global_annual_deaths / SECONDS_PER_YEAR
    return int(deaths_per_second * seconds_since_midnight)


def fmt_count(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value)):,}"


def fmt_usd_m(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.1f}M"


def fmt_neg_usd_m(value: float | None) -> str:
    if value is None:
        return "—"
    return f"-{fmt_usd_m(value)}"


def cumulative_deaths(series: list[int]) -> int:
    return sum(series)


def _apply_plot_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        autosize=True,
        height=height,
        margin=dict(l=40, r=20, t=24, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plot_scenario_deaths(comparison) -> go.Figure:
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
    fig.update_layout(xaxis_title="Year", yaxis_title="Deaths per year")
    return _apply_plot_layout(fig)


def plot_scenario_costs(comparison) -> go.Figure:
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
    fig.update_layout(yaxis_title="USD millions", xaxis_title="")
    return _apply_plot_layout(fig)


def plot_recovery_deaths(recovery) -> go.Figure:
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
    fig.update_layout(xaxis_title="Year", yaxis_title="Deaths per year")
    return _apply_plot_layout(fig)


def plot_damage_phase(recovery) -> go.Figure:
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
        xaxis_title="Year",
        yaxis=dict(title="Annual deaths"),
        yaxis2=dict(title="RBI", overlaying="y", side="right"),
    )
    return _apply_plot_layout(fig)


def run_ai_recommendation(
    inputs: SimulationInputs,
    comparison,
) -> tuple[str, str]:
    """Generate policy brief via Claude or local demo fallback."""
    delayed = comparison.delayed.summary
    early = comparison.early.summary

    if not AI_AVAILABLE:
        from ai.demo_recommendation import generate_demo_recommendation

        return (
            generate_demo_recommendation(
                country=inputs.country,
                delay_years=inputs.delay_years,
                funding_level=inputs.funding_level,
                stewardship_rate=inputs.stewardship_rate,
                rd_investment=inputs.rd_investment,
                additional_deaths=delayed["additional_deaths_from_delay"],
                healthcare_cost=delayed["healthcare_cost_increase_usd_m"],
                gdp_loss=delayed["gdp_loss_usd_m"],
                risk_level=delayed["risk_level"],
                intervention_strength=delayed["intervention_strength"],
                lives_saved_vs_no_action=early["lives_saved_vs_no_action"],
                critical_year=delayed["critical_year"],
                projected_final_year_deaths=delayed["projected_annual_deaths_final_year"],
            ),
            "demo",
        )

    return generate_recommendation(
        country=inputs.country,
        delay_years=inputs.delay_years,
        funding_level=inputs.funding_level,
        stewardship_rate=inputs.stewardship_rate,
        rd_investment=inputs.rd_investment,
        deaths=delayed["additional_deaths_from_delay"],
        healthcare_cost=delayed["healthcare_cost_increase_usd_m"],
        gdp_loss=delayed["gdp_loss_usd_m"],
        risk_level=delayed["risk_level"],
        intervention_strength=delayed["intervention_strength"],
        lives_saved_vs_no_action=early["lives_saved_vs_no_action"],
        critical_year=delayed["critical_year"],
        projected_final_year_deaths=delayed["projected_annual_deaths_final_year"],
    )


def render_scenario_card(title: str, css_class: str, result) -> str:
    summary = result.summary
    deaths = cumulative_deaths(result.annual_deaths)
    return f"""
    <article class="result-card {css_class}">
      <p>{escape(title)}</p>
      <ul>
        <li>Deaths: <strong>{fmt_count(deaths)}</strong></li>
        <li>Cost: <strong>{fmt_usd_m(summary["healthcare_cost_increase_usd_m"])}</strong></li>
        <li>GDP: <strong>{fmt_neg_usd_m(summary["gdp_loss_usd_m"])}</strong></li>
        <li>Risk: <strong>{escape(summary["risk_level"])}</strong></li>
      </ul>
    </article>
    """


@st.fragment(run_every=timedelta(seconds=3))
def render_hero(global_annual_deaths: int) -> None:
    count = compute_amr_deaths_today(global_annual_deaths)
    st.markdown(
        f"""
        <section class="hero">
          <div class="hero__noise"></div>
          <div class="hero__content">
            <p class="eyebrow">People killed by AMR today:</p>
            <p class="hero__counter" aria-live="polite">{count:,}</p>
            <div class="hero__title-group">
              <h1>ResistAI: The Cost of Delay</h1>
              <p class="hero__subtitle">
                An AI simulator that shows policymakers the true cost of inaction on antibiotic resistance.
              </p>
            </div>
            <p class="hero__source">
              Use the sidebar to configure your scenario and run the simulation.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_live_panel(inputs: SimulationInputs, comparison) -> None:
    delayed = comparison.delayed.summary
    explanation = (
        f"In {inputs.country}, delaying AMR action by {inputs.delay_years} year(s) is projected "
        f"to cause {fmt_count(delayed['additional_deaths_from_delay'])} additional deaths versus "
        f"early action, with {fmt_usd_m(delayed['healthcare_cost_increase_usd_m'])} in excess "
        f"healthcare costs and {fmt_neg_usd_m(delayed['gdp_loss_usd_m'])} in productivity losses."
    )
    st.markdown(
        f"""
        <section class="simulation" id="simulation-results">
          <div class="section-heading">
            <span class="section-kicker">Results</span>
            <h2>Estimated Impact</h2>
          </div>
          <aside class="live-panel">
            <p class="live-panel__label">Estimated impact from simulation</p>
            <div class="metric-stack">
              <div class="metric">
                <span>Additional deaths (delay)</span>
                <strong>{fmt_count(delayed["additional_deaths_from_delay"])}</strong>
              </div>
              <div class="metric">
                <span>Healthcare cost increase</span>
                <strong>{fmt_usd_m(delayed["healthcare_cost_increase_usd_m"])}</strong>
              </div>
              <div class="metric">
                <span>GDP / productivity loss</span>
                <strong>{fmt_neg_usd_m(delayed["gdp_loss_usd_m"])}</strong>
              </div>
            </div>
            <p class="live-panel__note">{escape(explanation)}</p>
          </aside>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_results(comparison) -> None:
    cards_html = "".join(
        [
            render_scenario_card("Early Action", "result-card--positive", comparison.early),
            render_scenario_card("Delayed Action", "result-card--warning", comparison.delayed),
            render_scenario_card("No Action", "result-card--danger", comparison.no_action),
        ]
    )
    st.markdown(
        f"""
        <section class="results">
          <div class="cards">{cards_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    years = comparison.early.years
    year_span = f"{years[0]}–{years[-1]}" if years else "Projection"

    st.markdown('<div class="viz-grid">', unsafe_allow_html=True)
    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        st.markdown(
            f"""
            <div class="viz-card-head">
              <span>{escape(year_span)}</span>
              <h3>Deaths over time</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_scenario_deaths(comparison),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )
    with chart_cols[1]:
        st.markdown(
            """
            <div class="viz-card-head">
              <span>Scenario comparison</span>
              <h3>Healthcare cost increase (USD M)</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_scenario_costs(comparison),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )
    st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown(
        """
        <div class="scenario-table-shell">
          <div class="section-heading" style="margin-bottom: 16px;">
            <span class="section-kicker">Detail</span>
            <h2>Scenario comparison table</h2>
          </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_recovery_section(recovery, prior_delay_years: int) -> None:
    summary = recovery.comparison_summary
    damage = summary["damage_at_delay_end"]

    st.markdown(
        f"""
        <section class="recovery" id="recovery">
          <div class="section-heading">
            <span class="section-kicker">Recovery What-If</span>
            <h2>After {prior_delay_years} Year(s) of Inaction</h2>
          </div>
          <p class="live-panel__note" style="margin-bottom: 20px;">
            Compares a recovery strategy against continuing with no additional action
            after the prior delay period.
          </p>
          <div class="live-panel" style="margin-bottom: 24px;">
            <p class="live-panel__label">Damage caused by delay</p>
            <div class="metric-stack">
              <div class="metric">
                <span>RBI at delay end</span>
                <strong>{damage["rbi"]}</strong>
              </div>
              <div class="metric">
                <span>Annual deaths at delay end</span>
                <strong>{fmt_count(damage["annual_deaths"])}</strong>
              </div>
              <div class="metric">
                <span>Cumulative deaths during delay</span>
                <strong>{fmt_count(damage["cumulative_deaths"])}</strong>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col, = st.columns(1)
    with col:
        st.markdown(
            """
            <div class="viz-card-head">
              <span>Damage phase</span>
              <h3>Deaths and resistance burden during delay</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_damage_phase(recovery),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    st.markdown(
        f"""
        <div class="live-panel" style="margin: 24px auto;">
          <p class="live-panel__label">Recovery strategy vs continued no action</p>
          <div class="metric-stack">
            <div class="metric">
              <span>Lives saved by recovery</span>
              <strong>{fmt_count(summary["lives_saved_by_recovery"])}</strong>
            </div>
            <div class="metric">
              <span>Healthcare cost avoided</span>
              <strong>{fmt_usd_m(summary["recovery_healthcare_savings_usd_m"])}</strong>
            </div>
            <div class="metric">
              <span>GDP loss avoided</span>
              <strong>{fmt_usd_m(summary["recovery_gdp_savings_usd_m"])}</strong>
            </div>
            <div class="metric">
              <span>Risk: recovery → continue</span>
              <strong>{escape(summary["recovery_risk_level"])} → {escape(summary["continue_no_action_risk_level"])}</strong>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    recovery_cols = st.columns(2, gap="large")
    with recovery_cols[0]:
        st.markdown(
            """
            <div class="viz-card-head">
              <span>Recovery pathways</span>
              <h3>Annual deaths after prior delay</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_recovery_deaths(recovery),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    compare_rows = [
        {
            "Pathway": "Recovery Strategy",
            "Cumulative deaths": sum(recovery.recovery.annual_deaths),
            "Risk level": recovery.recovery.summary["risk_level"],
            "Final-year deaths": recovery.recovery.summary["projected_annual_deaths_final_year"],
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
    with recovery_cols[1]:
        st.markdown(
            """
            <div class="scenario-table-shell">
              <div class="section-heading" style="margin-bottom: 12px;">
                <span class="section-kicker">Outcomes</span>
                <h2>Side-by-side comparison</h2>
              </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(compare_rows, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_recovery_unavailable(note: str) -> None:
    st.markdown(
        f"""
        <section class="recovery" id="recovery">
          <div class="section-heading">
            <span class="section-kicker">Recovery What-If</span>
            <h2>Recovery Analysis</h2>
          </div>
          <div class="info-panel">{escape(note)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_ai_section(
    ai_text: str,
    ai_source: str,
    inputs: SimulationInputs,
    comparison,
) -> None:
    delayed = comparison.delayed.summary
    early = comparison.early.summary
    saved_lives = early["lives_saved_vs_no_action"]
    critical = (
        str(delayed["critical_year"])
        if delayed["critical_year"]
        else "Not reached in horizon"
    )

    badge_class = "ai-badge--claude" if ai_source == "claude" else "ai-badge--demo"
    badge_label = "Powered by Claude" if ai_source == "claude" else "Demo mode — local policy brief"

    st.markdown(
        f"""
        <section class="results" id="ai-recommendation">
          <div class="ai-box">
            <div>
              <span class="section-kicker">AI explanation</span>
              <span class="ai-badge {badge_class}">{escape(badge_label)}</span>
            </div>
            <div class="recommendations">
              <div>
                <span>Lives saved (early vs no action)</span>
                <strong>{fmt_count(saved_lives)} lives</strong>
              </div>
              <div>
                <span>Lives lost to delay</span>
                <strong>{fmt_count(delayed["additional_deaths_from_delay"])} lives</strong>
              </div>
              <div>
                <span>Critical year (delayed)</span>
                <strong>{escape(critical)}</strong>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ai-box ai-brief-body">', unsafe_allow_html=True)
    st.markdown(ai_text)
    st.markdown("</div>", unsafe_allow_html=True)

    headline = (
        f"{inputs.country}: {delayed['risk_level']} risk if action is delayed — "
        f"early investment saves {fmt_count(saved_lives)} lives"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="resistai-inline-btn">', unsafe_allow_html=True)
        if st.button("✓ Apply Recommendations", key="apply_recommendations"):
            st.session_state["show_success_panel"] = True
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="resistai-inline-btn resistai-inline-btn--primary">', unsafe_allow_html=True)
        st.caption("Use Ctrl+P (Cmd+P on Mac) to print or save this report as PDF.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("show_success_panel"):
        st.markdown(
            f"""
            <div class="success-panel">
              <p class="success-panel__count">
                Early action could save {fmt_count(saved_lives)} lives vs no action
              </p>
              <div class="headline-box">{escape(headline)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_about() -> None:
    st.markdown(
        f"""
        <section class="about">
          <div class="section-heading">
            <span class="section-kicker">About</span>
            <h2>About This Tool</h2>
          </div>
          <div class="about-grid">
            <article class="about-card">
              <h3>⚠️ What this tool does NOT do</h3>
              <ul>
                <li>Does not diagnose patients</li>
                <li>Does not replace doctors</li>
                <li>Does not predict exact outcomes</li>
              </ul>
            </article>
            <article class="about-card">
              <h3>📊 Our Data Sources</h3>
              <ul>
                <li>WHO Global AMR Report 2023</li>
                <li>OECD AMR Report</li>
                <li>Lancet 2022 global bacterial AMR burden study</li>
              </ul>
            </article>
            <article class="about-card">
              <h3>👤 Human in the Loop</h3>
              <p>
                All recommendations must be reviewed by qualified public health experts
                before any action is taken.
              </p>
            </article>
            <article class="about-card">
              <h3>📅 Data Last Updated</h3>
              <p>Data vintage: {escape(DATA_VINTAGE)}</p>
            </article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="ResistAI: The Cost of Delay",
        page_icon="🦠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_design_system()

    global_baseline = get_country_baseline("Global")
    global_deaths = global_baseline["baseline_deaths"]

    with st.sidebar:
        st.markdown(
            """
            <div class="section-heading" style="margin-bottom: 12px;">
              <span class="section-kicker">Simulator</span>
              <h2 style="font-size: 1.5rem;">Build Your Scenario</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        country = st.selectbox("Country", list_supported_countries(), index=4)
        delay_years = st.slider("Years of delay", min_value=0, max_value=20, value=5)
        funding_level = st.selectbox("Funding level", ["Low", "Medium", "High"], index=1)
        stewardship_rate = st.slider(
            "Stewardship adoption rate (%)", min_value=0, max_value=100, value=50
        )
        rd_investment = st.selectbox("R&D investment", ["Low", "Medium", "High"], index=1)

        st.divider()
        st.markdown(
            """
            <div class="section-heading" style="margin-bottom: 8px;">
              <span class="section-kicker">Recovery</span>
              <h2 style="font-size: 1.35rem;">What-If Levers</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
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

        run_clicked = st.button("Run Simulation →", type="primary", use_container_width=True)

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
            ai_text, ai_source = run_ai_recommendation(inputs, comparison)

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
                    "Increase 'Years of delay' in the sidebar to enable this section."
                )

            st.session_state["comparison"] = comparison
            st.session_state["inputs"] = inputs
            st.session_state["recovery"] = recovery
            st.session_state["recovery_note"] = recovery_note
            st.session_state["effective_prior_delay"] = effective_prior_delay
            st.session_state["ai_text"] = ai_text
            st.session_state["ai_source"] = ai_source

    comparison = st.session_state["comparison"]
    inputs = st.session_state["inputs"]
    recovery = st.session_state.get("recovery")
    recovery_note = st.session_state.get("recovery_note")

    st.markdown('<div class="resistai-page">', unsafe_allow_html=True)
    render_hero(global_deaths)
    render_live_panel(inputs, comparison)
    render_scenario_results(comparison)

    if recovery is not None:
        render_recovery_section(recovery, st.session_state["effective_prior_delay"])
    elif recovery_note:
        render_recovery_unavailable(recovery_note)

    render_ai_section(
        st.session_state["ai_text"],
        st.session_state.get("ai_source", "demo"),
        inputs,
        comparison,
    )
    render_about()
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
