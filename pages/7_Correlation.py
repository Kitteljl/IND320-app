"""
IND320 - Sliding window correlation between a weather property and reservoir filling.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analysis_plotly import WEATHER_PROPS
from theme import COLORWAY, OUTLIER
from utils import reservoir_controls, reservoir_series, shared_number, weekly_weather, WEEKLY_PROPS as PROPS
from weather import region_id

st.title("Sliding window correlation")

# ---------------- Shared area selection (sidebar) ----------------
area_type, _, _ = reservoir_controls(show_interval=False)
if area_type == "NO":
    st.info("Weather data is available for the EL (NO1-NO5) and VASS (VASS1-VASS3) areas. "
            "Select one of them in the sidebar.")
    st.stop()
with st.sidebar:
    st.header("Correlation")
    number = shared_number("Area number", list(range(1, 6 if area_type == "EL" else 4)),
                           "cor_area_number", area_type)
region = region_id(area_type, number)

# ---------------- Controls ----------------
c1, c2, c3, c4 = st.columns(4)
prop = c1.selectbox("Weather property", PROPS, format_func=lambda p: WEATHER_PROPS[p][0])
target = c2.radio("Reservoir variable", ["Filling (%)", "Weekly change (pp)"])
lag = c3.slider("Lag (weeks)", 0, 26, 0,
                help="The weather is shifted this many weeks before the filling: "
                     "lag 4 compares the filling with the weather 4 weeks earlier.")
window = c4.slider("Window (weeks)", 8, 156, 52)
this_year = pd.Timestamp.today().year
y0, y1 = st.slider("Weather years", 2005, this_year, (2015, this_year))
label, unit = WEATHER_PROPS[prop]

# ---------------- Data ----------------
try:
    weekly = weekly_weather(area_type, number, list(range(y0, y1 + 1)))
except Exception as e:
    st.error(f"Could not download weather data from Open-Meteo right now ({type(e).__name__}). "
             "Please try again in a few minutes.")
    st.stop()

fill = reservoir_series(area_type, number, y0, y1)            # weekly filling in %, Sunday dates
y = fill if target.startswith("Filling") else fill.diff()

data = pd.concat({"weather": weekly[prop].shift(lag), "reservoir": y}, axis=1).dropna()
if len(data) < window + 5:
    st.warning("Too little overlapping data for this window length. Choose a longer period "
               "or a shorter window.")
    st.stop()

roll = data["reservoir"].rolling(window).corr(data["weather"]).dropna()
overall = data["reservoir"].corr(data["weather"])

m1, m2, m3 = st.columns(3)
m1.metric("Overall correlation", f"{overall:.2f}")
m2.metric("Windows", len(roll))
m3.metric("Weeks of data", len(data))

tab_roll, tab_lag = st.tabs(["Sliding correlation", "Correlation by lag"])

# ---------------- Tab 1: sliding window ----------------
with tab_roll:
    left, right = st.columns([3, 1.6])
    with left:
        fig = go.Figure()
        fig.add_scatter(x=roll.index, y=roll.values, mode="lines", name="Correlation",
                        line=dict(color=COLORWAY[0], width=1.8))
        fig.add_hline(y=0, line=dict(color="black", width=1, dash="dot"))
        fig.update_layout(title=f"{region}: {label} vs {target.lower()}, window {window} weeks, lag {lag} weeks",
                          yaxis=dict(title="Correlation", range=[-1, 1]), hovermode="x unified", height=430)
        st.plotly_chart(fig, width="stretch", theme=None)
    with right:
        sc = px.scatter(data, x="weather", y="reservoir", opacity=0.45, trendline="ols",
                        labels={"weather": f"{label} ({unit})", "reservoir": f"{target}"},
                        title="All weeks")
        sc.update_layout(height=430)
        st.plotly_chart(sc, width="stretch", theme=None)

    with st.expander("Strongest windows"):
        best = pd.concat([roll.nlargest(5).rename("correlation").to_frame().assign(kind="most positive"),
                          roll.nsmallest(5).rename("correlation").to_frame().assign(kind="most negative")])
        best.index.name = "window ends"
        st.dataframe(best.round(3), width="stretch")

# ---------------- Tab 2: correlation by lag ----------------
with tab_lag:
    lags = list(range(0, 27))
    corr_by_lag = [y.corr(weekly[prop].shift(k)) for k in lags]
    best_lag = lags[int(pd.Series(corr_by_lag).abs().idxmax())]
    bar = go.Figure(go.Bar(x=lags, y=corr_by_lag,
                           marker_color=[OUTLIER if k == best_lag else COLORWAY[0] for k in lags]))
    bar.update_layout(title=f"{region}: overall correlation for each lag (strongest: {best_lag} weeks)",
                      xaxis_title="Lag (weeks)", yaxis=dict(title="Correlation", range=[-1, 1]), height=400)
    st.plotly_chart(bar, width="stretch", theme=None)

with st.expander("About the method"):
    st.markdown(
        f"""
        **Data:** hourly ERA5 weather from Open-Meteo for {region} (5 sampled locations averaged),
        converted to Oslo local time and aggregated to weeks ending on Sunday (temperature = mean,
        precipitation and snowfall = sum), so the weeks match NVE's Sunday dates.
        The reservoir variable is the weekly filling level of {region} from Magasinstatistikk.

        **Sliding window correlation:** the Pearson correlation between the two weekly series is computed
        in a window of the chosen length that moves one week at a time. The lag shifts the weather
        earlier in time, so a positive lag tests whether past weather helps explain the current filling.
        """
    )