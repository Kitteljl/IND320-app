"""
IND320 - Cross-border flows from MongoDB.
"""

from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mongo_db import get_mongo_db

COLLECTION = "cross_border"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.title("Cross-border flows (MongoDB)")


def collection():
    return get_mongo_db()[COLLECTION]


@st.cache_data(ttl=3600, show_spinner="Reading from MongoDB ...")
def get_options():
    """All links (one per physical connection) and the years stored."""
    col = collection()
    links = sorted(col.distinct("link"))
    bounds = list(col.aggregate([
        {"$group": {"_id": None,
                    "min": {"$min": "$starttime"},
                    "max": {"$max": "$starttime"}}}
    ]))[0]
    years = list(range(bounds["min"].year, bounds["max"].year + 1))
    return links, years


@st.cache_data(ttl=3600, show_spinner="Reading from MongoDB ...")
def yearly_totals(link, year):
    """Total energy (MWh) per direction for one link and year."""
    rows = collection().aggregate([
        {"$match": {"link": link,
                    "starttime": {"$gte": datetime(year, 1, 1),
                                  "$lt": datetime(year + 1, 1, 1)}}},
        {"$group": {"_id": "$direction", "total_mwh": {"$sum": "$flow_mw"}}},
    ])
    return {r["_id"]: r["total_mwh"] for r in rows}


@st.cache_data(ttl=3600, show_spinner="Reading from MongoDB ...")
def month_data(year, month):
    """Hourly flows for all links and directions in one month."""
    start = datetime(year, month, 1)
    end = datetime(year + (month == 12), month % 12 + 1, 1)
    docs = collection().find(
        {"starttime": {"$gte": start, "$lt": end}}, {"_id": 0}
    )
    df = pd.DataFrame(docs)
    if not df.empty:
        df["series"] = df["link"] + " " + df["direction"]
    return df


links, years = get_options()
left, right = st.columns(2)

# ---------------- Left: pie chart ----------------
with left:
    st.subheader("Total flow in a year")
    link = st.radio("Connection", links, horizontal=True)
    year = st.selectbox("Year", years, index=len(years) - 1)

    totals = yearly_totals(link, year)
    values = [totals.get("out", 0), totals.get("in", 0)]
    if sum(values) <= 0:
        st.info("No data for this selection.")
    else:
        fig = px.pie(names=["Out of Norway", "Into Norway"], values=values, hole=0.35,
                    title=f"{link}, {year} (total {sum(values) / 1e3:,.0f} GWh)")
        fig.update_traces(textinfo="percent+label", rotation=90, sort=False, showlegend=False)
        st.plotly_chart(fig, width="stretch", theme=None)

# ---------------- Right: line plot ----------------
with right:
    st.subheader("Hourly flow in a month")
    month_name = st.pills("Month", MONTHS, selection_mode="single", default="Jan")

    if month_name is None:
        st.info("Select a month.")
    else:
        month = MONTHS.index(month_name) + 1
        df = month_data(year, month)
        

        if df.empty:
            st.info("No data for this month.")
        else:
            options = sorted(df["series"].unique())
            default = [s for s in options if s.startswith(link + " ")]
            chosen = st.pills("Connections and directions", options,
                              selection_mode="multi", default=default)
            if not chosen:
                st.info("Select at least one series.")
            else:
                fig = go.Figure()
                for name, g in df[df["series"].isin(chosen)].groupby("series"):
                    g = g.sort_values("starttime")
                    fig.add_scatter(x=g["starttime"], y=g["flow_mw"], mode="lines",
                                    name=name, line=dict(width=1.5))
                fig.update_layout(title=f"{month_name} {year}", yaxis_title="Flow (MW)",
                                  hovermode="x unified", height=450,
                                  legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig, width="stretch", theme=None)

# ---------------- Source documentation ----------------
with st.expander("About the data"):
    st.markdown(
        """
        **Source:** ENTSO-E Transparency Platform, physical cross-border flows
        between Norwegian bidding zones and neighbouring zones, 2024-2025.
        Fetched with the `entsoe-py` client, converted to hourly mean values,
        stored in Cassandra with Spark, then extracted with Spark and loaded into
        MongoDB Atlas (database `ind320`, collection `cross_border`), which this
        page reads.

        **Columns:** link (for example `NO2-DK1`, the same for both directions),
        direction (`out` is flow from Norway, `in` is flow into Norway), start
        time (UTC) and flow in MW. Hourly MW values are summed to MWh for the
        yearly totals.
        """
    )