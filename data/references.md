## COUNTRY SET USED IN THIS SIMULATION

The system supports the following seven countries/regions as the current MVP country set:

- **Global** — Lancet 2019 worldwide aggregate
- **USA / United States**
- **India**
- **Brazil**
- **Peru**
- **Nigeria**
- **UK / United Kingdom**

These countries were selected to represent:

- Global policy narrative (**Global**)
- High-income healthcare systems (**USA, UK**)
- Large middle-income or transition regions (**India, Brazil, Peru**)
- Low-income high-burden region (**Nigeria**)

The single runtime source of truth is `data/country_baselines.py`.

---

## DATA FILES

| File | Used for | Countries covered |
|------|----------|-------------------|
| `WHO_AMR_data.csv` | RBI derivation / resistance proxy values | India, Nigeria, Brazil, UK, USA |
| `OECD_economic_data.csv` | GDP, country modifier, cost per death | India, Nigeria, Brazil, UK, USA |
| `country_baselines.py` | Runtime merge, Lancet death anchors, and documented estimates | All seven |

**Note:** Global and Peru do not have rows in the CSV files. Global uses Lancet global mortality values. Peru uses Lancet regional estimates and documented economic proxies.

---

## ESTIMATES

Fields marked `is_estimate=True` in metadata include:

- Nigeria and UK baseline AMR deaths, scaled from Lancet regional anchors
- Peru baseline AMR deaths, based on Latin America regional share
- RBI values, derived from WHO CSV proxies or documented calibration
- Global economic and RBI proxy fields

Lancet-sourced **Global direct deaths (1.27M)** and **associated deaths (4.95M)** are not marked as estimates.

---

## ALIASES

| Input | Canonical key |
|-------|---------------|
| US, United States, America | USA |
| UK, United Kingdom, Britain | UK |
| Nigeria | Nigeria |

Unknown countries fall back to **Global**.