"""
IND320 - Outliers (DCT + SPC) and anomalies (LOF) for a selectable weather property.
"""
import streamlit as st

from analysis_plotly import WEATHER_PROPS, plot_lof_anomalies, plot_spc_outliers
from utils import load_weather, weather_controls
from weather import region_id

@st.cache_data(show_spinner="Computing outliers ...")
def spc(series, *args, **kwargs):
    return plot_spc_outliers(series, *args, **kwargs)


@st.cache_data(show_spinner="Computing anomalies ...")
def lof(series, *args, **kwargs):
    return plot_lof_anomalies(series, *args, **kwargs)

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

# Only offer the properties that exist in the downloaded data (temperature first = default)
props = [p for p in WEATHER_PROPS if p in weather.columns]

tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# ---------------- Tab 1: DCT + SPC ----------------
with tab_spc:
    c0, c1, c2 = st.columns(3)
    prop = c0.selectbox("Weather property", props, key="spc_prop",
                        format_func=lambda p: WEATHER_PROPS[p][0])
    cutoff_days = c1.slider("DCT cut-off period (days)", 5, 90, 30,
                            help="Variation slower than this is treated as seasonal and removed "
                                 "before the SPC limits are estimated.")
    n_std = c2.slider("Number of standard deviations", 1.0, 6.0, 3.0, step=0.5,
                      help="Width of the SPC boundaries (robust standard deviation).")
    label, unit = WEATHER_PROPS[prop]
    fig, summary = spc(weather[prop], cutoff_freq=1 / cutoff_days, n_std=n_std,
                                     title=f"{region} {year}", label=label, unit=unit)
    st.plotly_chart(fig, width="stretch", theme=None)

    m1, m2, m3 = st.columns(3)
    m1.metric("Outliers", summary["n_outliers"])
    m2.metric("Share of hours", f"{summary['percent_outliers']} %")
    m3.metric(f"Robust SD ({unit})", summary["robust_sigma"])
    with st.expander("List of outliers"):
        st.dataframe(summary["outliers"], hide_index=True, width="stretch")

# ---------------- Tab 2: LOF ----------------
with tab_lof:
    c0, c1, c2 = st.columns(3)
    prop = c0.selectbox("Weather property", props, key="lof_prop",
                        format_func=lambda p: WEATHER_PROPS[p][0])
    contamination = c1.slider("Proportion of outliers (%)", 0.1, 5.0, 1.0, step=0.1,
                              help="Share of hours flagged as anomalies.") / 100
    n_neighbors = c2.slider("Number of neighbours", 5, 100, 20,
                            help="Neighbourhood size used to estimate local density.")
    label, unit = WEATHER_PROPS[prop]
    fig, summary = lof(weather[prop], contamination=contamination,
                                      n_neighbors=n_neighbors, title=f"{region} {year}",
                                      label=label, unit=unit)
    st.plotly_chart(fig, width="stretch", theme=None)

    m1, m2 = st.columns(2)
    m1.metric("Anomalies", summary["n_anomalies"])
    m2.metric("Share of hours", f"{summary['percent_anomalies']} %")
    with st.expander("List of anomalies (most anomalous first)"):
        st.dataframe(summary["anomalies"], hide_index=True, width="stretch")

# ---------------- Documentation ----------------
with st.expander("About the data and methods"):
    st.markdown(
        f"""
        **Data:** hourly ERA5 reanalysis from the Open-Meteo archive API for {region}, {year}.
        1000 random locations were sampled inside each area (NVE shapefiles); the app downloads
        a subset of 25 of them (API limits) and averages them hour by hour.
        VASS areas are built from NVE regions: VASS1 = RS + RØ, VASS2 = RV, VASS3 = RM + RN.

        **Outliers (SPC):** the selected weather property is high-pass filtered with the Discrete
        Cosine Transform (cut-off set above). The filtered series is only used to estimate
        a robust centre and spread (median and MAD) over the whole year. Hours outside
        the boundaries (shown around the slow variation) are outliers.

        **Anomalies (LOF):** the Local Outlier Factor compares the density around each hour
        (the value and its hour-to-hour change) with that of its neighbours and flags
        the chosen share of most isolated hours.
        """
    )