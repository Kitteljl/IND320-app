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

# One row per area number, with the whole fill-level series as a mini line chart
rows = []
for number, g in data.groupby("area_number"):
    rows.append({
        "Area": f"{area_type}{number}",
        "Fill level trend": g["fill_pct"].tolist(),
        "Latest (%)": g["fill_pct"].iloc[-1],
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
            "Fill level trend": st.column_config.LineChartColumn(
                f"Fill level {start_year}-{end_year} (%)",
                y_min=0, y_max=100, width="large",
            ),
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