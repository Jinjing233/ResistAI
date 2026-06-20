/**
 * ResistAI frontend display layer.
 *
 * This file does NOT run mock epidemiological models. It renders results injected
 * by app.py via window.RESISTAI_PAYLOAD (countries from data.list_supported_countries,
 * metrics from simulation.compare_scenarios).
 */

const SECONDS_PER_YEAR = 365 * 24 * 60 * 60;

const elements = {
  dailyCounter: document.getElementById("dailyCounter"),
  startSimBtn: document.getElementById("startSimBtn"),
  scenarioForm: document.getElementById("scenarioForm"),
  country: document.getElementById("country"),
  delay: document.getElementById("delay"),
  funding: document.getElementById("funding"),
  stewardship: document.getElementById("stewardship"),
  rd: document.getElementById("rd"),
  delayValue: document.getElementById("delayValue"),
  stewardshipValue: document.getElementById("stewardshipValue"),
  liveDeaths: document.getElementById("liveDeaths"),
  liveCost: document.getElementById("liveCost"),
  liveGdp: document.getElementById("liveGdp"),
  explanation: document.getElementById("explanation"),
  aiSummary: document.getElementById("aiSummary"),
  recImmediate: document.getElementById("recImmediate"),
  recShort: document.getElementById("recShort"),
  recLong: document.getElementById("recLong"),
  earlyDeaths: document.getElementById("earlyDeaths"),
  earlyCost: document.getElementById("earlyCost"),
  earlyGdp: document.getElementById("earlyGdp"),
  earlyRisk: document.getElementById("earlyRisk"),
  delayedDeaths: document.getElementById("delayedDeaths"),
  delayedCost: document.getElementById("delayedCost"),
  delayedGdp: document.getElementById("delayedGdp"),
  delayedRisk: document.getElementById("delayedRisk"),
  noneDeaths: document.getElementById("noneDeaths"),
  noneCost: document.getElementById("noneCost"),
  noneGdp: document.getElementById("noneGdp"),
  noneRisk: document.getElementById("noneRisk"),
  lineChart: document.getElementById("lineChart"),
  barChart: document.getElementById("barChart"),
  chartYearSpan: document.getElementById("chartYearSpan"),
  applyRecommendations: document.getElementById("applyRecommendations"),
  successPanel: document.getElementById("successPanel"),
  savedLives: document.getElementById("savedLives"),
  headlineBox: document.getElementById("headlineBox"),
  downloadReport: document.getElementById("downloadReport"),
  dataVintage: document.getElementById("dataVintage"),
};

function getPayload() {
  return window.RESISTAI_PAYLOAD || null;
}

function getSecondsSinceMidnight() {
  const now = new Date();
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return (now - midnight) / 1000;
}

function formatCount(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return Math.round(value).toLocaleString();
}

function formatMillions(value) {
  if (value == null || Number.isNaN(value)) return "—";
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}K`;
  return formatCount(value);
}

function formatUsdMillions(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
}

function formatNegativeUsdMillions(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `-${formatUsdMillions(value)}`;
}

function cumulativeDeaths(series) {
  return (series || []).reduce((sum, value) => sum + value, 0);
}

function populateCountryOptions(countries, selected) {
  elements.country.innerHTML = "";
  countries.forEach((country) => {
    const option = document.createElement("option");
    option.value = country;
    option.textContent = country;
    if (country === selected) option.selected = true;
    elements.country.appendChild(option);
  });
}

function applyInputsToForm(inputs, readOnly) {
  if (!inputs) return;

  populateCountryOptions(
    getPayload()?.supported_countries || [inputs.country],
    inputs.country,
  );
  elements.delay.value = inputs.delay_years;
  elements.delayValue.textContent = `${inputs.delay_years} years`;
  elements.funding.value = inputs.funding_level;
  elements.stewardship.value = inputs.stewardship_rate;
  elements.stewardshipValue.textContent = `${Math.round(inputs.stewardship_rate)}%`;
  elements.rd.value = inputs.rd_investment;

  if (readOnly) {
    elements.country.disabled = true;
    elements.delay.disabled = true;
    elements.funding.disabled = true;
    elements.stewardship.disabled = true;
    elements.rd.disabled = true;
    elements.scenarioForm.querySelector('button[type="submit"]').hidden = true;
  }
}

function downsampleSeries(years, values, targetPoints = 6) {
  if (!years?.length) return { years: [], values: [] };
  if (years.length <= targetPoints) return { years, values };

  const step = Math.max(1, Math.floor((years.length - 1) / (targetPoints - 1)));
  const sampledYears = [];
  const sampledValues = [];
  for (let i = 0; i < years.length; i += step) {
    sampledYears.push(years[i]);
    sampledValues.push(values[i]);
  }
  const lastIndex = years.length - 1;
  if (sampledYears[sampledYears.length - 1] !== years[lastIndex]) {
    sampledYears.push(years[lastIndex]);
    sampledValues.push(values[lastIndex]);
  }
  return { years: sampledYears, values: sampledValues };
}

function renderLineChart(payload) {
  const svg = elements.lineChart;
  const early = downsampleSeries(payload.comparison.early.years, payload.comparison.early.annual_deaths);
  const delayed = downsampleSeries(payload.comparison.delayed.years, payload.comparison.delayed.annual_deaths);
  const none = downsampleSeries(payload.comparison.no_action.years, payload.comparison.no_action.annual_deaths);
  const yearlyLabels = early.years;
  const width = 620;
  const height = 260;
  const pad = { top: 18, right: 18, bottom: 34, left: 54 };
  const max = Math.max(...early.values, ...delayed.values, ...none.values, 1);
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;

  const x = (index) => pad.left + (index / Math.max(yearlyLabels.length - 1, 1)) * plotWidth;
  const y = (value) => pad.top + plotHeight - (value / max) * plotHeight;
  const pathFor = (values) =>
    values.map((value, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(value)}`).join(" ");

  const ticks = [0.25, 0.5, 0.75, 1]
    .map((ratio) => {
      const value = max * ratio;
      const pos = y(value);
      return `
        <line x1="${pad.left}" y1="${pos}" x2="${width - pad.right}" y2="${pos}" stroke="rgba(255,255,255,0.08)" />
        <text x="${pad.left - 10}" y="${pos + 4}" fill="rgba(255,255,255,0.58)" font-size="11" text-anchor="end">${formatMillions(value)}</text>
      `;
    })
    .join("");

  const yearAxis = yearlyLabels
    .map(
      (label, index) => `
        <text x="${x(index)}" y="${height - 10}" fill="rgba(255,255,255,0.58)" font-size="11" text-anchor="middle">${label}</text>
      `,
    )
    .join("");

  svg.innerHTML = `
    <rect x="0" y="0" width="${width}" height="${height}" rx="18" fill="transparent" />
    ${ticks}
    <path d="${pathFor(early.values)}" fill="none" stroke="#39d98a" stroke-width="4" stroke-linecap="round" />
    <path d="${pathFor(delayed.values)}" fill="none" stroke="#ffb347" stroke-width="4" stroke-linecap="round" />
    <path d="${pathFor(none.values)}" fill="none" stroke="#ff3b30" stroke-width="4" stroke-linecap="round" />
    ${yearAxis}
  `;

  if (yearlyLabels.length >= 2) {
    elements.chartYearSpan.textContent = `${yearlyLabels[0]}–${yearlyLabels[yearlyLabels.length - 1]}`;
  }
}

function renderBarChart(payload) {
  const svg = elements.barChart;
  const width = 620;
  const height = 260;
  const pad = { top: 18, right: 18, bottom: 42, left: 54 };
  const values = [
    payload.comparison.early.summary.healthcare_cost_increase_usd_m,
    payload.comparison.delayed.summary.healthcare_cost_increase_usd_m,
    payload.comparison.no_action.summary.healthcare_cost_increase_usd_m,
  ];
  const labels = ["Early", "Delayed", "No action"];
  const colors = ["#39d98a", "#ffb347", "#ff3b30"];
  const max = Math.max(...values, 1);
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const barWidth = 98;
  const gap = (plotWidth - values.length * barWidth) / (values.length + 1);

  const bars = values
    .map((value, index) => {
      const barHeight = (value / max) * plotHeight;
      const barX = pad.left + gap + index * (barWidth + gap);
      const barY = pad.top + plotHeight - barHeight;
      return `
        <rect x="${barX}" y="${barY}" width="${barWidth}" height="${barHeight}" rx="18" fill="${colors[index]}" opacity="0.88"></rect>
        <text x="${barX + barWidth / 2}" y="${barY - 10}" fill="#ffffff" font-size="12" text-anchor="middle">${formatUsdMillions(value)}</text>
        <text x="${barX + barWidth / 2}" y="${height - 12}" fill="rgba(255,255,255,0.62)" font-size="12" text-anchor="middle">${labels[index]}</text>
      `;
    })
    .join("");

  svg.innerHTML = `
    <line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="rgba(255,255,255,0.14)" />
    ${bars}
  `;
}

function renderScenarioCard(prefix, scenario) {
  const cumulative = cumulativeDeaths(scenario.annual_deaths);
  const summary = scenario.summary;

  document.getElementById(`${prefix}Deaths`).textContent = formatCount(cumulative);
  document.getElementById(`${prefix}Cost`).textContent = formatUsdMillions(
    summary.healthcare_cost_increase_usd_m,
  );
  document.getElementById(`${prefix}Gdp`).textContent = formatNegativeUsdMillions(
    summary.gdp_loss_usd_m,
  );
  document.getElementById(`${prefix}Risk`).textContent = summary.risk_level || "—";
}

function renderFromPayload(payload) {
  if (!payload?.comparison) return;

  const { inputs, comparison } = payload;
  const delayed = comparison.delayed.summary;
  const early = comparison.early.summary;

  applyInputsToForm(inputs, Boolean(payload.embedded));

  elements.liveDeaths.textContent = formatCount(delayed.additional_deaths_from_delay);
  elements.liveCost.textContent = formatUsdMillions(delayed.healthcare_cost_increase_usd_m);
  elements.liveGdp.textContent = formatNegativeUsdMillions(delayed.gdp_loss_usd_m);

  elements.explanation.textContent = `In ${inputs.country}, delaying AMR action by ${inputs.delay_years} year(s) is projected to cause ${formatCount(delayed.additional_deaths_from_delay)} additional deaths versus early action, with ${formatUsdMillions(delayed.healthcare_cost_increase_usd_m)} in excess healthcare costs and ${formatNegativeUsdMillions(delayed.gdp_loss_usd_m)} in productivity losses (simulation output).`;

  renderScenarioCard("early", comparison.early);
  renderScenarioCard("delayed", comparison.delayed);
  renderScenarioCard("none", comparison.no_action);

  renderLineChart(payload);
  renderBarChart(payload);

  elements.recImmediate.textContent = `${formatCount(early.lives_saved_vs_no_action)} lives`;
  elements.recShort.textContent = `${formatCount(delayed.additional_deaths_from_delay)} lives`;
  elements.recLong.textContent = delayed.critical_year
    ? String(delayed.critical_year)
    : "Not reached in horizon";

  const savedLives = early.lives_saved_vs_no_action || 0;
  elements.savedLives.textContent = `Early action could save ${formatCount(savedLives)} lives vs no action`;
  elements.headlineBox.textContent = `${inputs.country}: ${delayed.risk_level} risk if action is delayed — early investment saves ${formatCount(savedLives)} lives`;

  if (payload.ai_recommendation) {
    elements.aiSummary.textContent = payload.ai_recommendation;
  } else if (payload.ai_fallback) {
    elements.aiSummary.textContent = payload.ai_fallback;
  }

  if (payload.data_vintage) {
    elements.dataVintage.textContent = `Data vintage: ${payload.data_vintage}`;
  }
}

function initCounter(globalDirectDeaths) {
  const annualDeaths = globalDirectDeaths || 1_270_000;
  const deathsPerSecond = annualDeaths / SECONDS_PER_YEAR;

  function tickCounter() {
    const counter = Math.round(deathsPerSecond * getSecondsSinceMidnight());
    elements.dailyCounter.textContent = counter.toLocaleString();
  }

  tickCounter();
  setInterval(tickCounter, 2600);
}

function initEmptyState() {
  const payload = getPayload();
  const countries = payload?.supported_countries || ["Global", "USA", "India", "Brazil", "Peru"];
  populateCountryOptions(countries, payload?.inputs?.country || countries[0]);
  initCounter(payload?.global_direct_deaths);
  if (payload?.comparison) {
    renderFromPayload(payload);
  }
}

elements.scenarioForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (getPayload()?.embedded) return;
  elements.explanation.textContent =
    "Adjust inputs in the Streamlit app and click Run Simulation to refresh results from the Python simulation engine.";
  document.getElementById("scenarioCards").scrollIntoView({ behavior: "smooth", block: "start" });
});

elements.startSimBtn.addEventListener("click", () => {
  document.getElementById("simulation").scrollIntoView({ behavior: "smooth", block: "start" });
});

elements.applyRecommendations.addEventListener("click", () => {
  elements.successPanel.hidden = false;
  elements.successPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

elements.downloadReport.addEventListener("click", () => {
  window.print();
});

initEmptyState();
