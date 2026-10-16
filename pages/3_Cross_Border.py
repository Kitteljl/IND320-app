"""
IND320 - Cross-border flows from MongoDB.
"""

from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from mongo_db import get_mongo_db

COLLECTION = "cross_border"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.set_page_config(page_title="Cross-border flows", layout="wide")
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


@st.cache_data(ttl=3600)
def yearly_totals(link, year):
    """Total energy (MWh) per direction for one link and year."""
    rows = collection().aggregate([
        {"$match": {"link": link,
                    "starttime": {"$gte": datetime(year, 1, 1),
                                  "$lt": datetime(year + 1, 1, 1)}}},
        {"$group": {"_id": "$direction", "total_mwh": {"$sum": "$flow_mw"}}},
    ])
    return {r["_id"]: r["total_mwh"] for r in rows}


@st.cache_data(ttl=3600)
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
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(values, labels=["Out of Norway", "Into Norway"],
               autopct="%1.1f%%", startangle=90)
        ax.set_title(f"{link}, {year} (total {sum(values) / 1e3:,.0f} GWh)")
        st.pyplot(fig)
        plt.close(fig)

# ---------------- Right: line plot ----------------
with right:
    st.subheader("Hourly flow in a month")
    month_name = st.selectbox("Month", MONTHS, index=0)
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
            fig, ax = plt.subplots(figsize=(7, 5))
            for name, g in df[df["series"].isin(chosen)].groupby("series"):
                g = g.sort_values("starttime")
                ax.plot(g["starttime"], g["flow_mw"], label=name, linewidth=1.2)
            ax.set_ylabel("Flow (MW)")
            ax.set_title(f"{month_name} {year}")
            ax.grid(alpha=0.3)
            ax.legend()
            fig.autofmt_xdate()
            st.pyplot(fig)
            plt.close(fig)

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