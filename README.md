# ResistAI: The Cost of Delay

Antimicrobial resistance (AMR) is one of the most urgent global health threats of our time. As resistant infections spread, common treatments fail, hospital stays lengthen, and preventable deaths rise. When policymakers delay action, the human and economic costs do not stay flat—they compound year after year.

**ResistAI** is an AI-powered **policy decision-support simulator** that helps policymakers and public health stakeholders **visualize the consequences of inaction** and **compare different intervention strategies**. Users can explore early action, delayed action, and no additional action across seven countries and regions, review data-driven impact metrics, and export a shareable policy brief.

> **Disclaimer:** ResistAI is a **policy decision-support and educational tool**. It is **not** a clinical diagnostic system and **not** a strict epidemiological prediction model. All outputs are intended to support discussion and planning and should be reviewed by qualified public health experts before any real-world decision.

## Workflow

```
User Input → Simulation Model → Data-Driven Impact Analysis → AI Policy Brief → Visualization & Report Export
```

## Supported countries / regions

ResistAI currently supports seven selectable countries and regions:

- Global
- USA
- India
- Brazil
- Peru
- Nigeria
- UK

## Data sources

Impact estimates combine published global health data with documented assumptions where country-level figures are incomplete. Primary references include:

- **WHO** — AMR resistance proxies and global AMR reporting context
- **OECD** — economic indicators including GDP, cost-per-death estimates, and country modifiers
- **Lancet 2019/2022** — AMR mortality anchors

For transparency and documentation, see [`data/references.md`](data/references.md) and [`data/sources.py`](data/sources.py). Some values are documented estimates and are clearly identified in the application.

## Try it online

You can explore ResistAI without installing anything locally:

**[https://resist-ai.streamlit.app/](https://resist-ai.streamlit.app/)**

Open the link in your browser, select a country and scenario in the sidebar, and run a simulation. The online demo provides the same core workflow as the local version: impact analysis, recovery what-if, AI policy brief, and HTML report download.

## Installation & local usage

### Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Run the application

```bash
streamlit run app.py
```

Streamlit will start a local server and open the app in your browser, usually at **http://localhost:8501**. Use the sidebar to configure country and scenario settings, then scroll through results, recovery analysis, and the AI policy brief.

## HTML report export

After running a simulation, scroll to the **AI Policy Brief** section and click **Download HTML Report**.

The downloaded file is a self-contained HTML document (inline CSS, light print-friendly layout) that includes:

- Selected scenario settings
- Impact metrics
- Comparison tables
- Recovery analysis (when available)
- AI policy brief
- Data sources and disclaimer

Open the downloaded HTML file in any browser. To save a PDF, use **Ctrl+P** (Windows/Linux) or **Cmd+P** (macOS) and choose **Save as PDF**.

## Smoke tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

These smoke tests validate country baselines, simulation output, AI demo fallback, and HTML report export. **No external API key is required.**

## Project structure

| Path | Role |
|------|------|
| `app.py` | Streamlit UI controller |
| `simulation/` | AMR model and scenario engine |
| `data/` | Country baselines, CSV loaders, references |
| `ai/` | AI recommendation system and demo fallback |
| `report_export.py` | HTML report generation |
| `frontend/style.css` | Full UI styling |
| `archive/frontend/` | Legacy frontend design reference |
| `tests/` | Smoke tests |

## Team roles

- **Frontend & UI Design:** Roshni
- **Simulation Model & System Integration:** Jinjing
- **Data Collection & Validation:** Catharine
- **AI Recommendation System:** Ximena
