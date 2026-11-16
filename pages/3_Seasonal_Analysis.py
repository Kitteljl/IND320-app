"""
IND320 - STL decomposition and spectrogram of the reservoir filling level.
"""
import matplotlib.pyplot as plt
import streamlit as st

from analysis import plot_spectrogram, plot_stl
from utils import load_reservoir_data, reservoir_controls, reservoir_series

st.title("Reservoir filling: STL and spectrogram")

# Shared sidebar controls (area type EL/NO/VASS and download interval) + local area number
area_type, start_year, end_year = reservoir_controls()
df = load_reservoir_data()
numbers = sorted(df.loc[df["area_type"] == area_type, "area_number"].unique())
with st.sidebar:
    number = st.selectbox("Area number", numbers, key="seas_area_number")

series = reservoir_series(area_type, number, start_year, end_year)
label = f"{area_type}{number}"

# STL needs at least two full years of weekly data
if len(series) < 120:
    st.warning("The selected interval is too short for this analysis. "
               "Choose an interval of at least three years in the sidebar.")
    st.stop()

tab_stl, tab_spec = st.tabs(["STL decomposition", "Spectrogram"])

# ---------------- Tab 1: STL ----------------
with tab_stl:
    c1, c2, c3 = st.columns(3)
    seasonal = c1.slider("Seasonal smoother", 7, 53, 13, step=2,
                         help="Odd number. Larger = smoother seasonal pattern.")
    trend = c2.slider("Trend smoother", 55, 201, 105, step=2,
                      help="Odd number, larger than 52. Larger = smoother trend.")
    robust = c3.checkbox("Robust fitting", value=True,
                         help="Reduces the influence of outliers on the fit.")
    fig = plot_stl(series, seasonal=seasonal, trend=trend, robust=robust,
                   title=f"{label} filling level (%)")
    st.pyplot(fig)
    plt.close(fig)

# ---------------- Tab 2: Spectrogram ----------------
with tab_spec:
    max_window = min(260, len(series) - 1)
    c1, c2, c3 = st.columns(3)
    window = c1.slider("Window length (weeks)", 26, max_window, min(156, max_window),
                       help="Longer window = sharper frequencies, poorer time resolution.")
    overlap = c2.slider("Window overlap (%)", 0, 90, 75, step=5) / 100
    fmax = c3.slider("Highest frequency shown (cycles per year)", 2, 26, 6)
    fig = plot_spectrogram(series, window_length=window, overlap=overlap, fmax=fmax,
                           title=f"{label} filling level")
    st.pyplot(fig)
    plt.close(fig)

# ---------------- Documentation ----------------
with st.expander("About the analysis"):
    st.markdown(
        f"""
        **Data:** weekly reservoir filling level (%) for {label} from the NVE
        Magasinstatistikk API, limited to {start_year}-{end_year} (the interval slider
        in the sidebar). The series is made regular (weekly) and small gaps are interpolated.

        **STL** (Seasonal-Trend decomposition using LOESS) splits the series into trend,
        seasonal pattern (period 52 weeks) and residual. The seasonal and trend smoothers
        and robust fitting are set above.

        **Spectrogram:** shows how strong each frequency is over time. A bright band at one
        cycle per year is the annual filling and emptying of the reservoirs.
        """
    )