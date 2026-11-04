"""
Shared utilities for the IND320 Streamlit app.
"""

import pandas as pd
import streamlit as st
import requests
import os



NVE_URL = (
    "https://biapi.nve.no/magasinstatistikk/api/"
    "Magasinstatistikk/HentOffentligData"
)

NVE_RENAME = {
    "dato_Id": "date",
    "omrType": "area_type",
    "omrnr": "area_number",
    "iso_aar": "iso_year",
    "iso_uke": "iso_week",
    "fyllingsgrad": "fill_level",
    "kapasitet_TWh": "capacity_twh",
    "fylling_TWh": "fill_twh",
    "neste_Publiseringsdato": "next_publish_date",
    "fyllingsgrad_forrige_uke": "fill_level_prev_week",
    "endring_fyllingsgrad": "fill_level_change",
}


@st.cache_data(ttl=3600, show_spinner="Henter data fra NVE ...")
def load_reservoir_data() -> pd.DataFrame:
    """Alle områder (EL, NO, VASS) fra NVE Magasinstatistikk, med engelske kolonnenavn."""
    r = requests.get(NVE_URL, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json()).rename(columns=NVE_RENAME)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    # 0001-01-01 er en plassholder, ikke en ekte dato -> NaT
    df["next_publish_date"] = pd.to_datetime(df["next_publish_date"], errors="coerce")
    return df.sort_values(["area_type", "area_number", "date"]).reset_index(drop=True)



def get_reservoir_area(area_type: str, area_number: int | None = None) -> pd.DataFrame:
    """Filtrer ut ett område, f.eks. ('NO', 4) eller ('EL', 4)."""
    df = load_reservoir_data()
    df = df[df["area_type"] == area_type]
    if area_number is not None:
        df = df[df["area_number"] == area_number]
    return df.reset_index(drop=True)

def reservoir_controls(show_interval=True):
    df = load_reservoir_data()
    first_year = int(df["date"].dt.year.min())
    last_year = int(df["date"].dt.year.max())
    with st.sidebar:
        st.header("Reservoir data")
        area_type = st.radio("Area type", ["EL", "NO", "VASS"], key="res_area_type")
        if show_interval:
            start_year, end_year = st.slider("Download interval (years)",
                                             min_value=first_year, max_value=last_year,
                                             value=(max(first_year, last_year - 9), last_year),
                                             key="res_interval")
        else:
            start_year, end_year = first_year, last_year   # not used on the weather pages
    return area_type, start_year, end_year


@st.cache_data(ttl=3600, show_spinner="Loading the selected interval ...")
def download_reservoir_interval(start_year: int, end_year: int) -> pd.DataFrame:
    """The NVE API has no date parameters, so the full series is downloaded once
    (cached) and only the chosen interval is passed on to the pages."""
    df = load_reservoir_data()
    return df[df["date"].dt.year.between(start_year, end_year)].reset_index(drop=True)

from weather import download_weather, region_id


@st.cache_data(ttl=86400, show_spinner="Downloading weather data from Open-Meteo ...")
@st.cache_data(ttl=86400, show_spinner="Downloading weather data from Open-Meteo ...")
def load_weather(area_type, area_number, year):
    """Hourly ERA5 weather averaged over the sampled locations of the selected area.

    Uses a pre-downloaded file in data/weather_cache/ when it exists (fast), otherwise
    downloads from Open-Meteo (a few minutes). Cached for 24 hours per area and year.
    """
    region = region_id(area_type, area_number)          # e.g. EL + 3 -> NO3, VASS + 1 -> VASS1
    path = f"data/weather_cache/{region}_{year}.csv"
    if os.path.exists(path):
        return pd.read_csv(path, index_col="time", parse_dates=True)

    # ERA5 is ~5 days behind, so cut the end date for the current year
    end = min(pd.Timestamp(f"{year}-12-31"), pd.Timestamp.today().normalize() - pd.Timedelta(days=7))
    # The pages only need temperature and precipitation, which also makes the download faster
    return download_weather(region, f"{year}-01-01", end.strftime("%Y-%m-%d"),
                            hourly=["temperature_2m", "precipitation"])


def weather_controls():
    
    area_type, start_year, end_year = reservoir_controls(show_interval=False)
    if area_type == "NO":
        st.info("Weather data is available for the EL (NO1-NO5) and VASS (VASS1-VASS3) areas. "
                "Select one of them in the sidebar.")
        st.stop()
    with st.sidebar:
        st.header("Weather data")
        number = st.selectbox("Area number", list(range(1, 6 if area_type == "EL" else 4)),
                              key="wx_area_number")
               
        years = list(range(pd.Timestamp.today().year - 1, 1999, -1))   # complete years
        year = st.selectbox("Year", years, index=years.index(2024), key="wx_year",
                            help="Weather is downloaded one year at a time (hourly ERA5 data).")
    return area_type, number, year, start_year, end_year


def reservoir_series(area_type, number, start_year, end_year):
    """Weekly filling level (%) of one reservoir area in the selected interval, indexed by date."""
    df = download_reservoir_interval(start_year, end_year)
    one = df[(df["area_type"] == area_type) & (df["area_number"] == number)].set_index("date")
    return (one["fill_level"] * 100).sort_index()