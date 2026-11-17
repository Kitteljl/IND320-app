import streamlit as st

# Replace with the address of Kristian Hovde Liland's LinkedIn page (or the post with the fish)
NOFIMA = "https://nofimadatamodeling.wordpress.com/2016/10/25/nofima-at-cost-meeting-foodmc/"

st.title("IND320 - Reservoir Data Project")

st.markdown("""
Data are fetched live from the **NVE Magasinstatistikk API** (reservoir filling per area),
hourly weather comes from **Open-Meteo** (ERA5 reanalysis), and cross-border power flows
come from **ENTSO-E** via Cassandra/Spark, curated in **MongoDB Atlas**.

### Pages
**Explore**
- **Map**: GeoJSON map of price areas, water areas and Norway, coloured by reservoir filling or a weather
  property for a chosen week. Click an area to select it for the other pages.
- **Reservoir overview**: table with a mini chart per area
- **Reservoir plots**: filling level over time
- **Cross-border flows**: yearly totals and hourly flows per connection

**Analyse**
- **Seasonal analysis**: STL decomposition and spectrogram of the filling level
- **Weather outliers**: outliers (DCT + SPC) and anomalies (LOF) for a selectable weather property

**Predict**
- **Sliding window correlation**: correlation between a weather property and the filling, with selectable
  lag and window length
- **Forecast**: River SNARIMAX forecast of the filling, animated with Plotly. It starts from the week
  chosen on the map

The area type (price areas, water areas or Norway) in the sidebar is shared by all pages, and the area
and week you choose on the map are used as the starting point on the other pages.
""")

# Opened directly when the logo in the sidebar is clicked (link ?about=logo)
open_logo = st.query_params.get("about") == "logo"

with st.expander("About the data"):
    st.markdown(
        """
        **Reservoir filling:** NVE Magasinstatistikk API, weekly values (Sundays) per price area (EL),
        water area (VASS) and Norway (NO).

        **Weather:** hourly ERA5 reanalysis from the Open-Meteo archive API, averaged over random locations
        sampled inside each area (1000 per area were sampled; the weather and outlier pages use 25 of them,
        the map, correlation and forecast pages use 5 for speed and API limits). All hourly data is in UTC.

        **Power flows:** physical cross-border flows from ENTSO-E (2024-2025), stored in Cassandra, curated
        in MongoDB Atlas.

        **Areas:** price areas and NVE regions from NVE shapefiles, converted to GeoJSON.
        Water areas are built from the NVE regions: VASS1 = RS + RØ, VASS2 = RV, VASS3 = RM + RN.
        """
    )

with st.expander("About the logo", expanded=open_logo):
    st.markdown(
        f"""
        The fish in the sidebar is a drawing by **Kristian Hovde Liland**. I got this logo from NOFIMA DATA modelling
        ({NOFIMA}). He was my lecturer in IND320, and I appreciate his work in
        the course. He did good work on his fish too.
        """
    )
    st.image("images/fish_original.png",
             caption="The original picture where the fish comes from (source: Kristian Hovde Liland's LinkedIn page)")