import streamlit as st
import pandas as pd

from utils import load_reservoir_data

st.title("Reservoir areas")
st.write(
    "Weekly reservoir fill level from NVE Magasinstatistikk, "
    "by area type (EL = electricity price areas, NO = Norway, VASS = watercourse areas)."
)

df = load_reservoir_data()

area_type = st.radio(
    "Area type",
    options=["EL", "NO", "VASS"],
    horizontal=True,
)

data = df[df["area_type"] == area_type].copy()
data["fill_pct"] = data["fill_level"] * 100

# One line per area number within the chosen type
wide = data.pivot_table(
    index="date", columns="area_number", values="fill_pct"
).sort_index()
wide.columns = [f"{area_type}{n}" for n in wide.columns]

st.subheader(f"Fill level for {area_type} areas")
st.line_chart(wide, y_label="Fill level (%)", x_label="Date")

with st.expander("Data source"):
    st.write(
        "Data is fetched live from the NVE Magasinstatistikk API "
        "(`HentOffentligData`) and cached for one hour. "
        "Fill level is given as a fraction by NVE and shown here as a percentage."
    )