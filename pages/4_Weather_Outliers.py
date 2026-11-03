"""
IND320 - Outliers (DCT + SPC on precipitation) and anomalies (LOF on temperature).
"""
import matplotlib.pyplot as plt
import streamlit as st

from analysis import plot_lof_anomalies, plot_spc_outliers
from utils import load_weather, weather_controls
from weather import region_id

st.set_page_config(page_title="Weather outliers", layout="wide")
st.title("Weather: outliers and anomalies")

# Area type (EL/VASS) comes from the shared sidebar selector; number and year are local
area_type, number, year, _, _ = weather_controls()
region = region_id(area_type, number)

try:
    weather = load_weather(area_type, number, year)       # cached, downloads from Open-Meteo (ERA5)
except Exception as e:
    st.error(f"Could not download weather data from Open-Meteo right now ({type(e).__name__}). "
             "Please try again in a few minutes.")
    st.stop()

tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# ---------------- Tab 1: DCT + SPC on precipitation ----------------
with tab_spc:
    c1, c2 = st.columns(2)
    cutoff_days = c1.slider("DCT cut-off period (days)", 5, 90, 30,
                            help="Variation slower than this is treated as seasonal and removed "
                                 "before the SPC limits are estimated.")
    n_std = c2.slider("Number of standard deviations", 1.0, 6.0, 3.0, step=0.5,
                      help="Width of the SPC boundaries (robust standard deviation).")
    fig, summary = plot_spc_outliers(weather["precipitation"], cutoff_freq=1 / cutoff_days,
                                     n_std=n_std, title=f"{region} {year}")
    st.pyplot(fig)
    plt.close(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Outliers", summary["n_outliers"])
    m2.metric("Share of hours", f"{summary['percent_outliers']} %")
    m3.metric("Robust SD (mm/h)", summary["robust_sigma"])
    with st.expander("List of outliers"):
        st.dataframe(summary["outliers"], hide_index=True, use_container_width=True)

# ---------------- Tab 2: LOF on temperature ----------------
with tab_lof:
    c1, c2 = st.columns(2)
    contamination = c1.slider("Proportion of outliers (%)", 0.1, 5.0, 1.0, step=0.1,
                              help="Share of hours flagged as anomalies.") / 100
    n_neighbors = c2.slider("Number of neighbours", 5, 100, 20,
                            help="Neighbourhood size used to estimate local density.")
    fig, summary = plot_lof_anomalies(weather["temperature_2m"], contamination=contamination,
                                      n_neighbors=n_neighbors, title=f"{region} {year}")
    st.pyplot(fig)
    plt.close(fig)

    m1, m2 = st.columns(2)
    m1.metric("Anomalies", summary["n_anomalies"])
    m2.metric("Share of hours", f"{summary['percent_anomalies']} %")
    with st.expander("List of anomalies (most anomalous first)"):
        st.dataframe(summary["anomalies"], hide_index=True, use_container_width=True)

# ---------------- Documentation ----------------
with st.expander("About the data and methods"):
    st.markdown(
        f"""
        **Data:** hourly ERA5 reanalysis from the Open-Meteo archive API for {region}, {year}.
        1000 random locations were sampled inside each area (NVE shapefiles); the app downloads
        a subset of 25 of them (API limits) and averages them hour by hour.
        VASS areas are built from NVE regions: VASS1 = RS + RØ, VASS2 = RV, VASS3 = RM + RN.

        **Outliers (SPC):** precipitation is high-pass filtered with the Discrete Cosine
        Transform (cut-off set above). The filtered series is only used to estimate
        a robust centre and spread (median and MAD) over the whole year. Hours outside
        the boundaries (shown around the slow variation) are outliers.

        **Anomalies (LOF):** the Local Outlier Factor compares the density around each hour
        (temperature and hour-to-hour change) with that of its neighbours and flags
        the chosen share of most isolated hours.
        """
    )