"""
Shared utilities for the IND320 Streamlit app.
"""

import pandas as pd
import streamlit as st

COLUMN_RENAME_MAP = {
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

NUMERIC_COLS = [
    "fill_level",
    "capacity_twh",
    "fill_twh",
    "fill_level_prev_week",
    "fill_level_change",
]

DATA_PATH = "data/reservoirs.csv"


@st.cache_data
def load_data(area_number: int = 4) -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["dato_Id"])
    df = df.rename(columns=COLUMN_RENAME_MAP)
    df = (
        df[df["area_number"] == area_number]
        .sort_values("date")
        .reset_index(drop=True)
    )
    return df