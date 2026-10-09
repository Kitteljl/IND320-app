"""
Shared utilities for the IND320 Streamlit app.
"""

import pandas as pd
import streamlit as st
import requests



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