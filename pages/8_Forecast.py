"""
IND320 - Forecast of reservoir filling with River (SNARIMAX), animated with Plotly.
"""
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis_plotly import WEATHER_PROPS
from forecasting import forecast_filling
from theme import COLORWAY
from utils import (WEEKLY_PROPS, load_reservoir_data, reservoir_controls, reservoir_series,
                   shared_number, weekly_weather)

st.title("Forecast of reservoir filling")


@st.cache_data(show_spinner=False)
def run_forecast(y, exog, horizon, history_weeks, p, d, q, fourier_k, lr):
    """Cached forecast: the same settings are never computed twice."""
    return forecast_filling(y, horizon=horizon, history_weeks=history_weeks, p=p, d=d, q=q,
                            fourier_k=fourier_k, lr=lr, exog=exog)


# ---------------- Shared area selection (sidebar) ----------------
area_type, y_start, y_end = reservoir_controls(show_interval=False)
df = load_reservoir_data()
numbers = sorted(int(n) for n in df.loc[df["area_type"] == area_type, "area_number"].unique())
with st.sidebar:
    st.header("Forecast")
    number = shared_number("Area number", numbers, "fc_area_number", area_type)
region = f"{area_type}{number}"

# Model on the 0-1 scale (as in the notebook tests), displayed in %
fill = reservoir_series(area_type, number, y_start, y_end)
y = fill / 100
if len(y) < 100:
    st.warning("Too little data for this area.")
    st.stop()

# ---------------- Controls ----------------
c1, c2, c3 = st.columns([2.4, 1.4, 1.4])
last = y.index[-1]
default_end = min(max(st.session_state.get("sel_date", last), y.index[52]), last)
train_end = pd.Timestamp(c1.slider(
    "Training data ends (synced with the map week)", min_value=y.index[52].to_pydatetime(),
    max_value=last.to_pydatetime(), value=default_end.to_pydatetime(), step=timedelta(days=7),
    format="YYYY-MM-DD", key="fc_train_end"))
st.session_state["sel_date"] = train_end
horizon = c2.slider("Forecast horizon (weeks)", 4, 26, 12)
history_weeks = c3.slider("History used (weeks)", 26, 520, 104)

if area_type == "NO":
    exog_props = []
    st.caption("Weather inputs are available for the EL and VASS areas.")
else:
    exog_props = st.multiselect("Weather inputs (exogenous variables)", WEEKLY_PROPS, default=["temperature_2m"],
                                format_func=lambda p_: WEATHER_PROPS[p_][0])

with st.expander("Model settings (SNARIMAX)"):
    m1, m2, m3, m4, m5 = st.columns(5)
    p = m1.slider("AR order p", 0, 6, 1)
    d = m2.slider("Differencing d", 0, 2, 1)
    q = m3.slider("MA order q", 0, 3, 1)
    fourier_k = m4.slider("Yearly Fourier terms", 0, 4, 2)
    lr = m5.select_slider("Learning rate", options=[0.001, 0.005, 0.01], value=0.01,
                          help="Higher rates make the online learning unstable.")

# ---------------- Run the forecast with visible progress ----------------
y_train = y.loc[:train_end]
try:
    with st.status("Running the forecast ...", expanded=True) as status:
        exog = None
        if exog_props:
            st.write("Getting weather data ...")
            years = list(range(train_end.year - 8, train_end.year + 1))   # 8 years for the weekly averages
            exog = weekly_weather(area_type, number, years)[exog_props]
        st.write("Training the model and forecasting ...")
        fc_raw = run_forecast(y_train, exog, horizon, history_weeks, p, d, q, fourier_k, lr)
        status.update(label="Forecast ready", state="complete", expanded=False)
except Exception as e:
    st.error(f"The forecast could not be computed ({type(e).__name__}: {e}). "
             "Try other settings or try again in a few minutes.")
    st.stop()
# A filling degree must stay between 0 and 100 %. Values far outside mean the model became unstable.
unstable = bool(((fc_raw < -0.05) | (fc_raw > 1.05)).any())
fc = fc_raw.clip(0, 1)
if unstable:
    st.warning("The forecast left the possible range of 0-100 %, so the model became unstable "
               "(often a learning rate that is too high). The values are clipped to 0-100 % here. "
               "Try a lower learning rate or other model settings.")
actual = y.reindex(fc.index)                     # NaN where the future is not observed yet
has_actual = actual.notna().all()

# ---------------- Metrics ----------------
k1, k2, k3 = st.columns(3)
k1.metric("Last observed filling", f"{y_train.iloc[-1] * 100:.1f} %")
k2.metric(f"Forecast, week {horizon}", f"{fc.iloc[-1] * 100:.1f} %")
if has_actual:
    mae = (fc - actual).abs().mean() * 100
    naive = (y_train.iloc[-1] - actual).abs().mean() * 100
    k3.metric("MAE vs naive (pp)", f"{mae:.1f} vs {naive:.1f}")
else:
    k3.metric("Observed weeks in horizon", f"{int(actual.notna().sum())} of {horizon}")

# ---------------- Animated plot ----------------
hist = y_train.iloc[-156:] * 100
x_line = [hist.index[-1]] + list(fc.index)       # forecast line starts at the last observed point
y_line = [hist.iloc[-1]] + list(fc.values * 100)

fig = go.Figure()
fig.add_scatter(x=hist.index, y=hist.values, name="Observed (training)", line=dict(color=COLORWAY[0], width=2))
fig.add_scatter(x=actual.dropna().index, y=actual.dropna().values * 100, name="Observed (after start)",
                line=dict(color="gray", dash="dot", width=2))
fig.add_scatter(x=x_line[:2], y=y_line[:2], name="Forecast", mode="lines+markers",
                line=dict(color=COLORWAY[1], width=3))
fig.frames = [go.Frame(data=[go.Scatter(x=x_line[:k + 2], y=y_line[:k + 2])], traces=[2], name=str(k))
              for k in range(len(fc))]
fig.update_layout(
    title=f"{region}: {horizon}-week forecast from {train_end.date()}", yaxis_title="Filling (%)",
    height=520, hovermode="x unified", legend=dict(orientation="h", y=-0.15),
    updatemenus=[dict(type="buttons", showactive=False, x=0.0, y=1.15, xanchor="left", buttons=[
        dict(label="Play", method="animate",
             args=[None, dict(frame=dict(duration=350, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
        dict(label="Pause", method="animate",
             args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]),
    ])],
)
st.plotly_chart(fig, width="stretch", theme=None)
st.caption("Press Play to see the forecast build up week by week.")

# ---------------- Table ----------------
table = pd.DataFrame({"Week ending": fc.index.date, "Forecast (%)": (fc.values * 100).round(1),
                      "Observed (%)": (actual.values * 100).round(1)})
st.dataframe(table, hide_index=True, width="stretch")

with st.expander("About the model"):
    st.markdown(
        """
        The forecast uses River's `SNARIMAX`, which learns online, one week at a time, from the chosen
        history. The yearly cycle is given as sine/cosine terms (Fourier terms). The selected weather
        properties are weekly values for the area; for the forecast weeks, where the weather is unknown,
        the average of that week of the year (calculated from past data only) is used. The forecast is
        dynamic: each predicted week is used as input for the next. If observed values exist after the
        chosen start week, they are shown and the error (MAE) is compared with a naive forecast that repeats
        the last observed value.
        """
    )