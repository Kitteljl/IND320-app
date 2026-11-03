import streamlit as st

st.set_page_config(page_title="IND320 - Reservoir Data", layout="wide")

st.title("IND320 - Reservoir Data Project")

st.sidebar.success("Select a page above to get started.")

st.markdown("""
Data are fetched live from the **NVE Magasinstatistikk API** (reservoir filling per area),
hourly weather comes from **Open-Meteo** (ERA5 reanalysis), and cross-border power flows
come from **ENTSO-E** via Cassandra/Spark, curated in **MongoDB Atlas**.

### Pages
**Reservoirs** (NVE Magasinstatistikk API)
1. **Reservoir Overview**: table with a mini chart per area
2. **Reservoir Plots**: filling level over time
3. **Seasonal Analysis**: STL decomposition and spectrogram of the filling level

**Weather** (Open-Meteo ERA5)
4. **Weather Outliers**: outliers in precipitation (DCT + SPC) and anomalies in temperature (LOF)

**Power flows** (ENTSO-E, Cassandra/Spark, MongoDB Atlas)
5. **Cross Border**: yearly totals and hourly flows per connection

The area type (EL / NO / VASS) and the download interval in the sidebar are shared by the
reservoir and weather pages. The weather pages download data for the selected area on demand
(cached), using 25 of the 1000 sampled locations in each area.
""")