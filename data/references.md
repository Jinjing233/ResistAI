## COUNTRY SET USED IN THIS SIMULATION

The system supports the following seven countries/regions (single source of truth: `data/country_baselines.py`):

- **Global** — Lancet 2019 worldwide aggregate
- **USA**
- **India**
- **Brazil**
- **Peru**
- **Nigeria**
- **UK**

These were selected to represent:

- Global policy narrative (Global)
- High-income systems (USA, UK)
- Large middle-income burden (India, Brazil, Peru)
- Low-income high-burden region (Nigeria)

---

## DATA FILES

| File | Used for | Countries covered |
|------|----------|-------------------|
| `WHO_AMR_data.csv` | RBI derivation (resistance proxies) | India, Nigeria, Brazil, UK, USA |
| `OECD_economic_data.csv` | GDP, country_modifier, cost_per_death | India, Nigeria, Brazil, UK, USA |
| `country_baselines.py` | Runtime merge + Lancet death anchors + estimates | All seven |

**Note:** Global and Peru do not have rows in the CSV files. Global uses Lancet global mortality; Peru uses Lancet regional death estimates and documented economic proxies.

---

## ESTIMATES

Fields marked `is_estimate=True` in metadata include:

- Nigeria and UK **baseline AMR deaths** (scaled from Lancet regional anchors)
- Peru **baseline AMR deaths** (Latin America regional share)
- **RBI** for all countries (derived from WHO CSV proxies or documented calibration)
- Global **economic and RBI fields** (global proxies)

Lancet-sourced **Global direct deaths (1.27M)** and **associated deaths (4.95M)** are not marked as estimates.

---

## ALIASES

| Input | Canonical key |
|-------|---------------|
| US, United States, America | USA |
| UK, United Kingdom, Britain | UK |
| Nigeria | Nigeria |

Unknown countries fall back to **Global**.
