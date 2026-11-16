import streamlit as st

st.title("IND320 - Reservoir Data Project")

st.markdown("""
   Data are fetched live from the **NVE Magasinstatistikk API** (reservoir filling per area),
   hourly weather comes from **Open-Meteo** (ERA5 reanalysis), and cross-border power flows
   come from **ENTSO-E** via Cassandra/Spark, curated in **MongoDB Atlas**.

   ### Pages
   **Explore**
   - **Reservoir overview**: table with a mini chart per area
   - **Reservoir plots**: filling level over time
   - **Cross-border flows**: yearly totals and hourly flows per connection

   **Analyse**
   - **Seasonal analysis**: STL decomposition and spectrogram of the filling level
   - **Weather outliers**: outliers in precipitation (DCT + SPC) and anomalies in temperature (LOF)

   The area type (EL / NO / VASS) and the download interval in the sidebar are shared by the
   reservoir and weather pages. The weather pages download data for the selected area on demand
   (cached), using 25 of the 1000 sampled locations in each area.
   """)