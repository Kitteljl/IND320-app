"""
IND320 - Map of price areas (EL), water areas (VASS) and Norway (NO) with a GeoJSON overlay.
Colours show reservoir filling or a weather property for the chosen week; a click selects an area.
"""
import json
from datetime import timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from theme import COLORWAY, SEQUENTIAL
from utils import load_reservoir_data, reservoir_controls
from weather import download_weather, region_id

st.title("Map of areas")

GEOJSON_FILES = {"EL": "data/geojson/el.geojson",
                 "VASS": "data/geojson/vass.geojson",
                 "NO": "data/geojson/no.geojson"}


@st.cache_data
def load_geojson(area_type):
    with open(GEOJSON_FILES[area_type], encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=86400)
def area_weather_one(area_type, number, start, end):
    """Mean temperature and total precipitation for one area and period (5 sampled points keeps
    the download fast; days are UTC days from ERA5). Cached per area and period."""
    w = download_weather(region_id(area_type, number), start, end, n_points=5,
                         hourly=["temperature_2m", "precipitation"])
    return {"omrnr": number,
            "temperature_2m": float(w["temperature_2m"].mean()),
            "precipitation": float(w["precipitation"].sum())}


def area_weather(area_type, start, end):
    """All areas of one type, with a progress bar while downloading."""
    n_areas = 5 if area_type == "EL" else 3
    bar = st.progress(0.0, text="Downloading weather ...")
    rows = []
    for i in range(n_areas):
        bar.progress(i / n_areas, text=f"Downloading weather for {area_type}{i + 1} ({i + 1}/{n_areas}) ...")
        rows.append(area_weather_one(area_type, i + 1, start, end))
    bar.empty()
    return pd.DataFrame(rows)

# ---------------- Shared area type (sidebar) and data ----------------
area_type, _, _ = reservoir_controls(show_interval=False)
df = load_reservoir_data()
sub = df[df["area_type"] == area_type]
numbers = sorted(int(n) for n in sub["area_number"].unique())
gj = load_geojson(area_type)
names = {f["properties"]["key"]: f["properties"]["name"] for f in gj["features"]}

# ---------------- Controls ----------------
weather_ok = area_type != "NO"
options = ["Reservoir filling (%)"]
if weather_ok:
    options += ["Temperature (mean, °C)", "Precipitation (sum, mm)"]

c1, c2, c3, c4 = st.columns([2.2, 2.2, 1.4, 1.8])
colour_by = c1.radio("Colour by", options, key="map_colour")

last_date = sub["date"].max()
first_date = sub["date"].min()
sel_date = pd.Timestamp(c2.slider(
    "Week (Sunday date)", min_value=first_date.to_pydatetime(), max_value=last_date.to_pydatetime(),
    value=min(max(st.session_state.get("sel_date", last_date), first_date), last_date).to_pydatetime(),
    step=timedelta(days=7), format="YYYY-MM-DD", key="map_date"))

weeks = 1
if colour_by != options[0]:
    weeks = c3.select_slider("Weather period (weeks)", options=[1, 4, 12], key="map_weeks")

# ---------------- Values per area for the chosen week ----------------
if colour_by == options[0]:
    snap = sub[sub["date"] == sel_date]
    vals = pd.DataFrame({"omrnr": snap["area_number"].astype(int), "value": snap["fill_level"] * 100})
    unit = "%"
else:
    start = sel_date - timedelta(days=7 * weeks - 1)
    if sel_date > pd.Timestamp.today().normalize() - timedelta(days=7):
        st.warning("ERA5 weather is about a week behind. Choose an earlier week.")
        st.stop()
    try:
        wx = area_weather(area_type, start.strftime("%Y-%m-%d"), sel_date.strftime("%Y-%m-%d"))
    except Exception as e:
        st.error(f"Could not download the weather data ({e}). Try again later or choose reservoir filling.")
        st.stop()
    col = "temperature_2m" if colour_by.startswith("Temperature") else "precipitation"
    vals = wx[["omrnr", col]].rename(columns={col: "value"})
    unit = "°C" if col == "temperature_2m" else "mm"

if vals.empty or vals["value"].isna().all():
    st.warning("No data for this week and area type.")
    st.stop()

vals["key"] = area_type + vals["omrnr"].astype(str)
vals["name"] = vals["key"].map(names)
vals = vals.reset_index(drop=True)

# ---------------- Selected area: click or selectbox, stored for other pages ----------------
def clicked_key():
    """Key (e.g. 'EL3') of the area clicked on the map, or None."""
    ev = st.session_state.get("map_chart")
    pts = ((ev or {}).get("selection") or {}).get("points") or []
    if not pts or pts[0].get("curve_number", 0) != 0:
        return None
    p = pts[0]
    loc = p.get("location")
    if loc is None:
        idx = p.get("point_index", p.get("point_number"))
        if idx is not None and idx < len(vals):
            loc = vals.iloc[idx]["key"]
    return loc if loc in set(vals["key"]) else None


if st.session_state.get("map_area_select") not in numbers:      # e.g. after changing the area type
    st.session_state["map_area_select"] = numbers[0]

clk = clicked_key()
cur, prev = st.session_state.get("map_area_select"), st.session_state.get("_prev_sel")
if prev is not None and cur != prev:
    st.session_state["_last_click"] = clk            # the user used the selectbox: ignore the old click
elif clk != st.session_state.get("_last_click"):
    st.session_state["_last_click"] = clk
    if clk is not None:
        st.session_state["map_area_select"] = int(vals.loc[vals["key"] == clk, "omrnr"].iloc[0])

sel_number = c4.selectbox("Selected area", numbers, key="map_area_select",
                          format_func=lambda n: names.get(f"{area_type}{n}", str(n)))
st.session_state["_prev_sel"] = sel_number
sel_key = f"{area_type}{sel_number}"

# Shared selection for the other pages
st.session_state["sel_type"] = area_type
st.session_state["sel_number"] = sel_number
st.session_state["sel_date"] = sel_date

# ---------------- Map ----------------
fig = px.choropleth_map(
    vals, geojson=gj, locations="key", featureidkey="properties.key", color="value",
    color_continuous_scale=SEQUENTIAL, range_color=(vals["value"].min(), vals["value"].max()),
    opacity=0.65, hover_name="name", hover_data={"key": False, "value": ":.1f"},
    map_style="carto-positron", center={"lat": 65.0, "lon": 14.0}, zoom=3.2,
    labels={"value": unit},
)
fig.update_traces(marker_line_width=1.2, marker_line_color="#0b3c6d", selector=dict(type="choroplethmap"))
# Thick contrast outline for the selected area (transparent fill)
fig.add_trace(go.Choroplethmap(
    geojson=gj, locations=[sel_key], featureidkey="properties.key", z=[0], showscale=False,
    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
    marker=dict(line=dict(width=4, color=COLORWAY[1])), hoverinfo="skip"))
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=560, clickmode="event+select")

left, right = st.columns([3, 1.4])
with left:
    st.plotly_chart(fig, key="map_chart", on_select="rerun", selection_mode="points",
                    width="stretch", theme=None)
    st.caption("Click an area to select it (thick outline), or use the selector above the map.")

with right:
    row = vals[vals["key"] == sel_key].iloc[0]
    st.metric(names.get(sel_key, sel_key), f"{row['value']:.1f} {unit}")
    hist = sub[(sub["area_number"] == sel_number) & (sub["date"] >= sel_date - pd.DateOffset(years=10))
               & (sub["date"] <= sel_date)]
    line = px.line(hist, x="date", y=hist["fill_level"] * 100, title="Filling, last 10 years",
                   labels={"y": "%", "date": ""})
    line.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(line, width="stretch", theme=None)

# ---------------- Table ----------------
st.subheader(f"{colour_by} · week ending {sel_date.date()}")
st.dataframe(vals[["name", "value"]].rename(columns={"name": "Area", "value": unit}).sort_values(unit, ascending=False),
             hide_index=True, width="stretch")