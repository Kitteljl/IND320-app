# IND320 - Reservoir, weather and power-flow dashboard

Streamlit app and notebooks for the IND320 project work (NMBU). The app combines Norwegian reservoir
filling, hourly weather and cross-border power flows, and adds anomaly detection, correlation analysis
and a short-term forecast of reservoir filling.

- **Streamlit app:** https://YOUR-APP.streamlit.app/
- **Notebooks:** `notebooks/IND320_part1.ipynb` to `IND320_part4.ipynb` (development, documentation, log)

## Data sources

| Source | Used for | Access |
|---|---|---|
| NVE Magasinstatistikk API | weekly reservoir filling for price areas (EL), water areas (VASS) and Norway (NO) | downloaded live, cached |
| Open-Meteo (ERA5 archive) | hourly temperature, precipitation, snowfall and wind, averaged over sampled locations per area | downloaded live, cached |
| Norges Bank (SDMX API) | daily EUR and USD exchange rates | `exchange_rates.py`, used in the notebook |
| ENTSO-E | physical cross-border power flows, 2024-2025 | stored in Cassandra, curated in MongoDB Atlas |
| NVE area polygons | price areas and NVE regions, converted to GeoJSON for the map | files in `data/` |

Water areas are built from the NVE regions: VASS1 = RS + RO, VASS2 = RV, VASS3 = RM + RN.
All hourly sources are handled in UTC; daily and weekly sources are matched through the Oslo calendar date
(see section 3 of the Part 4 notebook).

## App pages

| Group | Page | What it shows |
|---|---|---|
| | Home | overview of the project and the pages |
| Explore | Map | GeoJSON map of the areas, coloured by filling or a weather property for a chosen week; a click selects an area for the other pages |
| Explore | Reservoir overview | table with a mini chart per area |
| Explore | Reservoir plots | filling level over time |
| Explore | Cross-border flows | yearly totals and hourly flows per connection |
| Analyse | Seasonal analysis | STL decomposition and spectrogram of the filling level |
| Analyse | Weather outliers | outliers (DCT + SPC) and anomalies (LOF) for a selectable weather property |
| Predict | Sliding window correlation | correlation between a weather property and the filling, with selectable lag and window |
| Predict | Forecast | River SNARIMAX forecast of the filling, animated with Plotly |

## Project structure

```
app.py                    entry point: theme, page groups and navigation
home.py                   home page
pages/                    one script per page (see the table above)
utils.py                  shared selectors, cached data loading (NVE, weather)
weather.py                Open-Meteo download for sampled locations per area
analysis.py               matplotlib analysis functions used in the part 3 notebook
analysis_plotly.py        Plotly versions of the plots used in the app
forecasting.py            River SNARIMAX forecast and evaluation functions
exchange_rates.py         Norges Bank currency download
theme.py                  shared colours and Plotly template (blue theme)
config.py, mongo_db.py,
local_db.py               database access for the power-flow data
data/                     area polygons (shapefiles, GeoJSON), sampled points, cached weather
notebooks/                notebooks for each part of the project work
images/                   sketches of the app structure and page layouts
.streamlit/config.toml    app theme
requirements.txt          Python packages
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The power-flow page reads from MongoDB Atlas. Put the connection details in `.streamlit/secrets.toml`
(see `config.py` for the key names). This file is listed in `.gitignore` and is never committed.

## Branches

`main` holds the finished and reviewed parts. New work for each part is done on a separate branch
(for example `part4`) and merged after peer review and feedback.