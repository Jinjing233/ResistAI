// WHO / Lancet (2019) global burden of disease estimate: ~1.27M deaths
// directly attributable to antimicrobial resistance per year.
const ANNUAL_AMR_DEATHS = 1270000;
const SECONDS_PER_YEAR = 365 * 24 * 60 * 60;
const DEATHS_PER_SECOND = ANNUAL_AMR_DEATHS / SECONDS_PER_YEAR;

function getSecondsSinceMidnight() {
  const now = new Date();
  const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return (now - midnight) / 1000;
}

const state = {
  counter: Math.round(DEATHS_PER_SECOND * getSecondsSinceMidnight()),
  country: "India",
  delay: 5,
  funding: 6,
  stewardship: 3,
  rd: 8,
  savedLives: 1847293,
};

const yearlyLabels = [2025, 2030, 2035, 2040, 2045, 2050];

const countryMultipliers = {
  India: 1,
  Nigeria: 0.72,
  Brazil: 0.78,
  "United Kingdom": 0.36,
  "United States": 0.52,
};

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
  fundingValue: document.getElementById("fundingValue"),
  stewardshipValue: document.getElementById("stewardshipValue"),
  rdValue: document.getElementById("rdValue"),
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
  delayedDeaths: document.getElementById("delayedDeaths"),
  delayedCost: document.getElementById("delayedCost"),
  delayedGdp: document.getElementById("delayedGdp"),
  noneDeaths: document.getElementById("noneDeaths"),
  noneCost: document.getElementById("noneCost"),
  noneGdp: document.getElementById("noneGdp"),
  lineChart: document.getElementById("lineChart"),
  barChart: document.getElementById("barChart"),
  applyRecommendations: document.getElementById("applyRecommendations"),
  successPanel: document.getElementById("successPanel"),
  savedLives: document.getElementById("savedLives"),
  headlineBox: document.getElementById("headlineBox"),
  downloadReport: document.getElementById("downloadReport"),
};

function formatCompactMillions(value) {
  return `${(value / 1000000).toFixed(1)}M`;
}

function formatCompactThousands(value) {
  if (value >= 1000000) return `${Math.round(value / 100000) / 10}M`;
  return `${Math.round(value / 1000)}K`;
}

function formatCurrencyBillions(value) {
  return `$${Math.round(value)}B`;
}

function formatNegativeCurrencyBillions(value) {
  return `-$${Math.round(value)}B`;
}

function formatMood(value) {
  if (value <= 3) return "Low";
  if (value <= 7) return "Medium";
  return "High";
}

function calculateScenario() {
  const factor = countryMultipliers[state.country] ?? 1;
  const delayPenalty = 1 + state.delay * 0.18;
  const protection = 1 + (state.funding + state.stewardship + state.rd) / 30;

  const liveDeaths = 650000 * factor * delayPenalty / (protection * 0.74);
  const liveCost = 44 * factor * delayPenalty / (protection * 0.63);
  const liveGdp = 68 * factor * delayPenalty / (protection * 0.58);

  const earlyDeaths = liveDeaths * 0.62;
  const delayedDeaths = liveDeaths * 1.92;
  const noActionDeaths = liveDeaths * 3.25;

  const earlyCost = liveCost * 0.78;
  const delayedCost = liveCost * 2.25;
  const noActionCost = liveCost * 5.05;

  const earlyGdp = liveGdp * 0.82;
  const delayedGdp = liveGdp * 2.75;
  const noActionGdp = liveGdp * 5.5;

  const preventedLives = Math.max(noActionDeaths - earlyDeaths, 50000);
  const immediate = preventedLives * 0.18;
  const shortTerm = preventedLives * 0.43;
  const longTerm = preventedLives * 0.81;

  return {
    liveDeaths,
    liveCost,
    liveGdp,
    earlyDeaths,
    delayedDeaths,
    noActionDeaths,
    earlyCost,
    delayedCost,
    noActionCost,
    earlyGdp,
    delayedGdp,
    noActionGdp,
    preventedLives,
    immediate,
    shortTerm,
    longTerm,
  };
}

function buildTrendSeries(base) {
  const early = yearlyLabels.map((_, index) => base.earlyDeaths * (0.48 + index * 0.11));
  const delayed = yearlyLabels.map((_, index) => base.delayedDeaths * (0.38 + index * 0.12));
  const none = yearlyLabels.map((_, index) => base.noActionDeaths * (0.28 + index * 0.15));
  return { early, delayed, none };
}

function updateLabels() {
  elements.delayValue.textContent = `${state.delay} years`;
  elements.fundingValue.textContent = formatMood(state.funding);
  elements.stewardshipValue.textContent = formatMood(state.stewardship);
  elements.rdValue.textContent = formatMood(state.rd);
}

function renderLineChart(series) {
  const svg = elements.lineChart;
  const width = 620;
  const height = 260;
  const pad = { top: 18, right: 18, bottom: 34, left: 54 };
  const max = Math.max(...series.early, ...series.delayed, ...series.none);
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;

  const x = (index) => pad.left + (index / (yearlyLabels.length - 1)) * plotWidth;
  const y = (value) => pad.top + plotHeight - (value / max) * plotHeight;

  const pathFor = (values) =>
    values.map((value, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(value)}`).join(" ");

  const ticks = [0.25, 0.5, 0.75, 1].map((ratio) => {
    const value = max * ratio;
    const pos = y(value);
    return `
      <line x1="${pad.left}" y1="${pos}" x2="${width - pad.right}" y2="${pos}" stroke="rgba(255,255,255,0.08)" />
      <text x="${pad.left - 10}" y="${pos + 4}" fill="rgba(255,255,255,0.58)" font-size="11" text-anchor="end">${formatCompactMillions(value)}</text>
    `;
  });

  const yearAxis = yearlyLabels
    .map(
      (label, index) => `
        <text x="${x(index)}" y="${height - 10}" fill="rgba(255,255,255,0.58)" font-size="11" text-anchor="middle">${label}</text>
      `,
    )
    .join("");

  svg.innerHTML = `
    <rect x="0" y="0" width="${width}" height="${height}" rx="18" fill="transparent" />
    ${ticks.join("")}
    <path d="${pathFor(series.early)}" fill="none" stroke="#39d98a" stroke-width="4" stroke-linecap="round" />
    <path d="${pathFor(series.delayed)}" fill="none" stroke="#ffb347" stroke-width="4" stroke-linecap="round" />
    <path d="${pathFor(series.none)}" fill="none" stroke="#ff3b30" stroke-width="4" stroke-linecap="round" />
    ${yearAxis}
    <g>
      <circle cx="${x(5)}" cy="${y(series.early[5])}" r="4.5" fill="#39d98a"></circle>
      <circle cx="${x(5)}" cy="${y(series.delayed[5])}" r="4.5" fill="#ffb347"></circle>
      <circle cx="${x(5)}" cy="${y(series.none[5])}" r="4.5" fill="#ff3b30"></circle>
    </g>
  `;
}

function renderBarChart(summary) {
  const svg = elements.barChart;
  const width = 620;
  const height = 260;
  const pad = { top: 18, right: 18, bottom: 42, left: 54 };
  const values = [summary.earlyCost, summary.delayedCost, summary.noActionCost];
  const labels = ["Early", "Delayed", "No action"];
  const colors = ["#39d98a", "#ffb347", "#ff3b30"];
  const max = Math.max(...values);
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
        <text x="${barX + barWidth / 2}" y="${barY - 10}" fill="#ffffff" font-size="12" text-anchor="middle">${formatCurrencyBillions(value)}</text>
        <text x="${barX + barWidth / 2}" y="${height - 12}" fill="rgba(255,255,255,0.62)" font-size="12" text-anchor="middle">${labels[index]}</text>
      `;
    })
    .join("");

  svg.innerHTML = `
    <line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="rgba(255,255,255,0.14)" />
    ${bars}
  `;
}

function render() {
  updateLabels();
  const summary = calculateScenario();

  elements.liveDeaths.textContent = formatCompactMillions(summary.liveDeaths);
  elements.liveCost.textContent = formatCurrencyBillions(summary.liveCost);
  elements.liveGdp.textContent = formatNegativeCurrencyBillions(summary.liveGdp);

  elements.earlyDeaths.textContent = formatCompactThousands(summary.earlyDeaths);
  elements.earlyCost.textContent = formatCurrencyBillions(summary.earlyCost);
  elements.earlyGdp.textContent = formatNegativeCurrencyBillions(summary.earlyGdp);

  elements.delayedDeaths.textContent = formatCompactMillions(summary.delayedDeaths);
  elements.delayedCost.textContent = formatCurrencyBillions(summary.delayedCost);
  elements.delayedGdp.textContent = formatNegativeCurrencyBillions(summary.delayedGdp);

  elements.noneDeaths.textContent = formatCompactMillions(summary.noActionDeaths);
  elements.noneCost.textContent = formatCurrencyBillions(summary.noActionCost);
  elements.noneGdp.textContent = formatNegativeCurrencyBillions(summary.noActionGdp);

  elements.explanation.textContent = `Based on your inputs, delaying AMR action in ${state.country} by ${state.delay} years raises mortality, treatment cost, and economic loss while weakening the health system's resilience.`;
  elements.aiSummary.textContent = `Based on your inputs, delaying action in ${state.country} by ${state.delay} years could lead to ${formatCompactMillions(summary.delayedDeaths)} deaths under a delayed pathway, compared with ${formatCompactThousands(summary.earlyDeaths)} if strong action begins now.`;

  elements.recImmediate.textContent = `Saves ${formatCompactThousands(summary.immediate)} lives`;
  elements.recShort.textContent = `Saves ${formatCompactThousands(summary.shortTerm)} lives`;
  elements.recLong.textContent = `Saves ${formatCompactMillions(summary.longTerm)} lives`;

  state.savedLives = Math.round(summary.preventedLives);
  elements.savedLives.textContent = `You just saved ${state.savedLives.toLocaleString()} lives`;
  elements.headlineBox.textContent = `${state.country} 2031: AMR Crisis Averted — Early Investment Saves ${formatCompactThousands(summary.preventedLives)} Lives`;

  const trendSeries = buildTrendSeries(summary);
  renderLineChart(trendSeries);
  renderBarChart(summary);
}

function handleInputChange() {
  state.country = elements.country.value;
  state.delay = Number(elements.delay.value);
  state.funding = Number(elements.funding.value);
  state.stewardship = Number(elements.stewardship.value);
  state.rd = Number(elements.rd.value);
  render();
}

function tickCounter() {
  // Recompute from the real per-second AMR death rate rather than a random jump,
  // so the number stays anchored to the WHO/Lancet annual estimate.
  state.counter = Math.round(DEATHS_PER_SECOND * getSecondsSinceMidnight());
  elements.dailyCounter.textContent = state.counter.toLocaleString();
}

elements.scenarioForm.addEventListener("input", handleInputChange);
elements.scenarioForm.addEventListener("submit", (event) => {
  event.preventDefault();
  render();
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

elements.dailyCounter.textContent = state.counter.toLocaleString();
setInterval(tickCounter, 2600);
render();