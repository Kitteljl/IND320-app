"""
IND320 - Reservoir overview: one row per area number with a trend line.
"""

import pandas as pd
import streamlit as st

from utils import reservoir_controls, download_reservoir_interval

st.set_page_config(page_title="Reservoir overview", layout="wide")
st.title("Reservoir overview")
st.markdown(
    "Weekly fill level from NVE Magasinstatistikk. Choose the area type and the "
    "download interval in the sidebar; each row below is one area number."
)

area_type, start_year, end_year = reservoir_controls()
df = download_reservoir_interval(start_year, end_year)
data = df[df["area_type"] == area_type].sort_values("date").copy()
data["fill_pct"] = data["fill_level"] * 100

# First month in the selected interval (used for the mini charts)
first_date = data["date"].min()
first_month = data[(data["date"].dt.year == first_date.year) &
                   (data["date"].dt.month == first_date.month)]
FIRST_COL = f"First month ({first_date:%b %Y})"

rows = []
for number, g in data.groupby("area_number"):
    fm = first_month[first_month["area_number"] == number]
    rows.append({
        "Area": f"{area_type}{number}",
        FIRST_COL: fm["fill_pct"].tolist(),          # mini chart: first month only
        "Latest (%)": g["fill_pct"].iloc[-1],         # stats: whole selected interval
        "Min (%)": g["fill_pct"].min(),
        "Max (%)": g["fill_pct"].max(),
        "Capacity (TWh)": g["capacity_twh"].iloc[-1],
    })
summary = pd.DataFrame(rows)

if summary.empty:
    st.info("No data for this selection.")
else:
    st.dataframe(
        summary,
        column_config={
            FIRST_COL: st.column_config.LineChartColumn(
            f"First month ({first_date:%b %Y}, %)",
            y_min=0, y_max=100, width="large",),
            "Latest (%)": st.column_config.NumberColumn(format="%.1f"),
            "Min (%)": st.column_config.NumberColumn(format="%.1f"),
            "Max (%)": st.column_config.NumberColumn(format="%.1f"),
            "Capacity (TWh)": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True,
        use_container_width=True,
    )

with st.expander("Show raw data"):
    st.dataframe(data.drop(columns="fill_pct"), use_container_width=True)