"""
IND320 - Reservoir plots: one line per area number.
"""

import streamlit as st

from utils import reservoir_controls, download_reservoir_interval

st.set_page_config(page_title="Reservoir plots", layout="wide")
st.title("Reservoir plots")

area_type, start_year, end_year = reservoir_controls()
df = download_reservoir_interval(start_year, end_year)
data = df[df["area_type"] == area_type].copy()
data["fill_pct"] = data["fill_level"] * 100
data["change_pct"] = data["fill_level_change"] * 100

VARIABLES = {
    "Fill level (%)": "fill_pct",
    "Fill (TWh)": "fill_twh",
    "Capacity (TWh)": "capacity_twh",
    "Weekly change (percentage points)": "change_pct",
}
label = st.selectbox("Variable", list(VARIABLES))
column = VARIABLES[label]

# One line per area number within the chosen area type
wide = data.pivot_table(index="date", columns="area_number", values=column).sort_index()
wide.columns = [f"{area_type}{n}" for n in wide.columns]

if wide.empty:
    st.info("No data for this selection.")
else:
    st.subheader(f"{label}, {area_type} areas, {start_year}-{end_year}")
    st.line_chart(wide, x_label="Date", y_label=label)

with st.expander("About the data and the interval"):
    st.write(
        "Data comes from the NVE Magasinstatistikk API (`HentOffentligData`). "
        "The API has no date parameters, so the full series is downloaded once and "
        "cached for one hour. The interval slider decides which years are passed on "
        "to this page. Fill level is given as a fraction by NVE and shown as a percentage."
    )