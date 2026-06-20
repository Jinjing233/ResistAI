# ResistAI: The Cost of Delay

An AI-powered **policy decision-support simulator** that models the human and economic cost of delaying action on antimicrobial resistance (AMR). ResistAI helps policymakers compare early action, delayed action, and no additional action across seven countries/regions.

> **Disclaimer:** This tool supports policy exploration and education. It is **not** a clinical diagnostic tool and **not** a strict epidemiological forecasting model. All outputs should be reviewed by qualified public health experts before any real-world decision.

## Workflow

```
User inputs → Simulation → Data-driven impact → AI recommendation → Visualization & export
```

## Supported countries / regions

`Global`, `USA`, `India`, `Brazil`, `Peru`, `Nigeria`, `UK`

## Data sources

- **WHO** — AMR resistance proxies (CSV) and global AMR reporting context  
- **OECD** — economic fields (GDP, cost per death, country modifiers)  
- **Lancet 2019/2022** — global and country-level AMR mortality anchors  

See `data/references.md` and `data/sources.py` for transparency notes. Some fields are documented estimates and are labeled in the UI.

## Installation

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the application

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`).

## Optional: Claude AI recommendations

By default, ResistAI uses a **local demo policy brief** when no API key is set (ideal for hackathon demos).

To enable Claude-generated recommendations:

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key-here"

# macOS / Linux
export ANTHROPIC_API_KEY="your-key-here"
```

Or add the key to a `.env` file in the project root (loaded if you use `python-dotenv` in your environment).

## Download HTML report

After running a simulation, scroll to the **AI Policy Brief** section and click **Download HTML Report**. The file is self-contained (inline CSS, light print-friendly layout) and includes scenario settings, metrics, tables, recovery results, the AI brief, and disclaimers.

## Smoke tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

No Anthropic API key is required.

## Project structure

| Path | Role |
|------|------|
| `app.py` | Streamlit UI controller |
| `simulation/` | AMR model and scenario engine |
| `data/` | Country baselines, CSV loaders, references |
| `ai/` | Claude client + demo fallback recommendations |
| `report_export.py` | Downloadable HTML report builder |
| `frontend/style.css` | Dark-theme styles injected into Streamlit |
| `archive/frontend/` | Legacy HTML/JS design reference (not used at runtime) |
| `tests/` | Smoke tests |

## Team roles

- Frontend: Roshni  
- Simulation model: Jinjing  
- Data & validation: Catharine  
- Claude API & AI recommendations: Ximena  
