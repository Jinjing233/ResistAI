"""Self-contained HTML report export for ResistAI (light theme, inline CSS)."""

from __future__ import annotations

import re
from datetime import datetime
from html import escape

from data import DATA_VINTAGE, POLICY_DISCLAIMER, get_country_metadata

REPORT_CSS = """
body {
  font-family: Georgia, "Times New Roman", serif;
  color: #1a1a1a;
  background: #ffffff;
  margin: 0;
  padding: 32px 40px 48px;
  line-height: 1.6;
}
.report {
  max-width: 900px;
  margin: 0 auto;
}
.report__header {
  border-bottom: 3px solid #c0392b;
  padding-bottom: 18px;
  margin-bottom: 28px;
}
.report__header h1 {
  margin: 0 0 8px;
  font-size: 2rem;
  color: #111111;
}
.report__meta {
  color: #555555;
  font-size: 0.95rem;
  margin: 0;
}
.section {
  margin-bottom: 32px;
}
.section h2 {
  font-size: 1.35rem;
  color: #111111;
  border-bottom: 1px solid #dddddd;
  padding-bottom: 8px;
  margin: 0 0 16px;
}
.section h3 {
  font-size: 1.05rem;
  color: #222222;
  margin: 1.25rem 0 0.5rem;
}
.kicker {
  display: block;
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #777777;
  margin-bottom: 6px;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 8px;
}
.metric-card {
  border: 1px solid #dddddd;
  border-radius: 8px;
  padding: 14px 16px;
  background: #fafafa;
}
.metric-card span {
  display: block;
  font-size: 0.82rem;
  color: #666666;
  margin-bottom: 6px;
}
.metric-card strong {
  font-size: 1.15rem;
  color: #111111;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
  margin-top: 8px;
}
th, td {
  border: 1px solid #dddddd;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}
th {
  background: #f3f3f3;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.brief p {
  margin: 0 0 1rem;
}
.brief ol {
  margin: 0 0 1rem;
  padding-left: 1.4rem;
}
.brief li {
  margin-bottom: 0.5rem;
}
.brief strong {
  color: #111111;
}
.note {
  background: #fff8e6;
  border: 1px solid #f0d080;
  border-radius: 8px;
  padding: 14px 16px;
  color: #5c4a00;
  font-size: 0.92rem;
}
.disclaimer {
  border-top: 1px solid #dddddd;
  padding-top: 20px;
  color: #555555;
  font-size: 0.88rem;
}
.disclaimer ul {
  padding-left: 1.2rem;
}
.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: #eef6ff;
  border: 1px solid #b8d4f0;
  color: #1a5276;
  margin-bottom: 12px;
}
@media print {
  body { padding: 16px; }
}
"""


def _inline_markdown_html(text: str) -> str:
    parts = re.split(r"(\*\*.+?\*\*)", text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            rendered.append(f"<strong>{escape(part[2:-2])}</strong>")
        else:
            rendered.append(escape(part))
    return "".join(rendered)


def format_ai_brief_html(markdown_text: str) -> str:
    blocks = re.split(r"\n(?=### )", markdown_text.strip())
    html_parts: list[str] = []

    for block in blocks:
        lines = [line.rstrip() for line in block.split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        if not lines:
            continue

        body_start = 0
        if lines[0].startswith("### "):
            html_parts.append(f"<h3>{_inline_markdown_html(lines[0][4:].strip())}</h3>")
            body_start = 1

        i = body_start
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            if re.match(r"^\d+\.\s", line):
                html_parts.append("<ol>")
                while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                    item = re.sub(r"^\d+\.\s*", "", lines[i].strip(), count=1)
                    html_parts.append(f"<li>{_inline_markdown_html(item)}</li>")
                    i += 1
                html_parts.append("</ol>")
                continue

            paragraph_lines: list[str] = []
            while i < len(lines):
                current = lines[i].strip()
                if not current or re.match(r"^\d+\.\s", current) or current.startswith("### "):
                    break
                paragraph_lines.append(current)
                i += 1

            if paragraph_lines:
                html_parts.append(f"<p>{_inline_markdown_html(' '.join(paragraph_lines))}</p>")

    return "\n".join(html_parts)


def _fmt_count(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value)):,}"


def _fmt_usd_m(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.1f}M"


def _format_table_cell(column: str, value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and ("USD" in column or "cost" in column.lower() or "GDP" in column):
        return _fmt_usd_m(value)
    if isinstance(value, int) and ("death" in column.lower() or "Death" in column):
        return _fmt_count(value)
    return str(value)


def _render_table(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "<p>No data available.</p>"

    headers = list(rows[0].keys())
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = "".join(
            f"<td>{escape(_format_table_cell(col, row[col]))}</td>" for col in headers
        )
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _build_scenario_comparison_rows(comparison) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in (comparison.early, comparison.delayed, comparison.no_action):
        summary = result.summary
        rows.append(
            {
                "Scenario": result.scenario,
                "Cumulative deaths": sum(result.annual_deaths),
                "Additional deaths vs early": summary["additional_deaths_from_delay"],
                "Healthcare cost (USD M)": summary["healthcare_cost_increase_usd_m"],
                "GDP loss (USD M)": summary["gdp_loss_usd_m"],
                "Lives saved vs no action": summary["lives_saved_vs_no_action"],
                "Risk level": summary["risk_level"],
                "Critical year": summary["critical_year"],
            }
        )
    return rows


def _build_side_by_side_rows(comparison, recovery=None) -> list[dict[str, object]]:
    if recovery is not None:
        return [
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

    rows: list[dict[str, object]] = []
    for result in (comparison.early, comparison.delayed, comparison.no_action):
        summary = result.summary
        rows.append(
            {
                "Scenario": result.scenario,
                "Cumulative deaths": sum(result.annual_deaths),
                "Additional deaths vs early": summary["additional_deaths_from_delay"],
                "Healthcare cost (USD M)": summary["healthcare_cost_increase_usd_m"],
                "GDP loss (USD M)": summary["gdp_loss_usd_m"],
                "Risk level": summary["risk_level"],
            }
        )
    return rows


def build_downloadable_html_report(
    *,
    inputs,
    comparison,
    ai_text: str,
    ai_source: str,
    recovery=None,
    recovery_settings: dict | None = None,
    recovery_note: str | None = None,
    effective_prior_delay: int | None = None,
) -> str:
    """Build a complete standalone HTML document for download."""
    delayed = comparison.delayed.summary
    early = comparison.early.summary
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    ai_label = "Claude API" if ai_source == "claude" else "Local demo generator"

    scenario_settings_rows = [
        {"Setting": "Country / region", "Value": inputs.country},
        {"Setting": "Years of delay", "Value": inputs.delay_years},
        {"Setting": "Funding level", "Value": inputs.funding_level},
        {"Setting": "Stewardship adoption (%)", "Value": f"{inputs.stewardship_rate:.0f}"},
        {"Setting": "R&D investment", "Value": inputs.rd_investment},
    ]

    recovery_html = ""
    if recovery is not None and recovery_settings:
        damage = recovery.comparison_summary["damage_at_delay_end"]
        summary = recovery.comparison_summary
        recovery_settings_rows = [
            {"Setting": "Prior delay (years)", "Value": effective_prior_delay},
            {"Setting": "Recovery funding", "Value": recovery_settings.get("funding_level")},
            {
                "Setting": "Recovery stewardship (%)",
                "Value": recovery_settings.get("stewardship_rate"),
            },
            {"Setting": "Recovery R&D", "Value": recovery_settings.get("rd_investment")},
            {
                "Setting": "Recovery projection (years)",
                "Value": recovery_settings.get("projection_years"),
            },
        ]
        damage_rows = [
            {"Metric": "RBI at delay end", "Value": damage["rbi"]},
            {"Metric": "Annual deaths at delay end", "Value": _fmt_count(damage["annual_deaths"])},
            {
                "Metric": "Cumulative deaths during delay",
                "Value": _fmt_count(damage["cumulative_deaths"]),
            },
            {
                "Metric": "Lives saved by recovery",
                "Value": _fmt_count(summary["lives_saved_by_recovery"]),
            },
            {
                "Metric": "Healthcare cost avoided (USD M)",
                "Value": _fmt_usd_m(summary["recovery_healthcare_savings_usd_m"]),
            },
            {
                "Metric": "GDP loss avoided (USD M)",
                "Value": _fmt_usd_m(summary["recovery_gdp_savings_usd_m"]),
            },
        ]
        recovery_html = f"""
        <section class="section">
          <span class="kicker">Recovery What-If</span>
          <h2>Recovery Analysis</h2>
          <h3>Recovery policy settings</h3>
          {_render_table(recovery_settings_rows)}
          <h3>Damage after prior inaction</h3>
          {_render_table(damage_rows)}
          <h3>Recovery pathway comparison</h3>
          {_render_table(_build_side_by_side_rows(comparison, recovery))}
        </section>
        """
    elif recovery_note:
        recovery_html = f"""
        <section class="section">
          <span class="kicker">Recovery What-If</span>
          <h2>Recovery Analysis</h2>
          <div class="note">{escape(recovery_note)}</div>
        </section>
        """

    brief_html = format_ai_brief_html(ai_text)
    side_by_side = _render_table(_build_side_by_side_rows(comparison, recovery))
    metadata = get_country_metadata(inputs.country)
    estimate_notes: list[str] = []
    if metadata.get("baseline_deaths_is_estimate"):
        if inputs.country in ("Peru", "Nigeria", "UK"):
            estimate_notes.append("Baseline AMR mortality uses documented regional scaling.")
        else:
            estimate_notes.append("Baseline AMR mortality is a documented estimate.")
    if any(metadata.get(k) for k in metadata if k.endswith("_is_estimate")):
        estimate_notes.append("Some economic or RBI fields are transparent estimates — see data/references.md.")
    estimate_html = ""
    if estimate_notes:
        estimate_html = (
            '<div class="note"><strong>Data transparency:</strong> '
            + " ".join(escape(note) for note in estimate_notes)
            + "</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ResistAI Report — {escape(inputs.country)}</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
  <div class="report">
    <header class="report__header">
      <h1>ResistAI: The Cost of Delay</h1>
      <p class="report__meta">
        Policy simulation report · {escape(inputs.country)} · Generated {escape(generated)} ·
        Data vintage {escape(DATA_VINTAGE)}
      </p>
    </header>

    <section class="section">
      <span class="kicker">Scenario</span>
      <h2>Scenario Settings</h2>
      {_render_table(scenario_settings_rows)}
      {estimate_html}
    </section>

    <section class="section">
      <span class="kicker">Impact</span>
      <h2>Key Metrics (Delayed Action vs Early Action)</h2>
      <div class="metrics">
        <div class="metric-card">
          <span>Additional deaths from delay</span>
          <strong>{_fmt_count(delayed["additional_deaths_from_delay"])}</strong>
        </div>
        <div class="metric-card">
          <span>Healthcare cost increase</span>
          <strong>{_fmt_usd_m(delayed["healthcare_cost_increase_usd_m"])}</strong>
        </div>
        <div class="metric-card">
          <span>GDP / productivity loss</span>
          <strong>{_fmt_usd_m(delayed["gdp_loss_usd_m"])}</strong>
        </div>
        <div class="metric-card">
          <span>Lives saved (early vs no action)</span>
          <strong>{_fmt_count(early["lives_saved_vs_no_action"])}</strong>
        </div>
        <div class="metric-card">
          <span>Risk level (delayed)</span>
          <strong>{escape(delayed["risk_level"])}</strong>
        </div>
        <div class="metric-card">
          <span>Critical year (delayed)</span>
          <strong>{escape(str(delayed["critical_year"]) if delayed["critical_year"] else "Not reached")}</strong>
        </div>
      </div>
    </section>

    <section class="section">
      <span class="kicker">Comparison</span>
      <h2>Scenario Comparison</h2>
      {_render_table(_build_scenario_comparison_rows(comparison))}
    </section>

    {recovery_html}

    <section class="section">
      <span class="kicker">AI Policy Brief</span>
      <h2>AI Recommendation</h2>
      <span class="badge">Source: {escape(ai_label)}</span>
      <div class="brief">
        {brief_html}
      </div>
    </section>

    <section class="section">
      <span class="kicker">Outcomes</span>
      <h2>Side-by-side Comparison</h2>
      {side_by_side}
    </section>

    <section class="section disclaimer">
      <h2>Data Sources &amp; Disclaimer</h2>
      <p>{escape(POLICY_DISCLAIMER)}</p>
      <ul>
        <li>WHO Global AMR Report 2023</li>
        <li>OECD AMR economic burden analyses</li>
        <li>Lancet 2022 global bacterial AMR burden study</li>
      </ul>
      <p><strong>What this tool does NOT do:</strong> It does not diagnose patients, replace doctors,
      or predict exact clinical outcomes. All recommendations require review by qualified public
      health experts before action is taken.</p>
    </section>
  </div>
</body>
</html>"""
