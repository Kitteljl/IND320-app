"""
IND320 - Data Table page.
"""

import streamlit as st
import pandas as pd

from utils import get_reservoir_area

st.set_page_config(page_title="Data Table", layout="wide")
st.title("Data Table")

st.markdown(
    """
    This page shows an overview of the reservoir data fetched from the NVE
    Magasinstatistikk API. Each row below corresponds to **one column** in the
    dataset, with a small line chart previewing the **first month** (first
    4 weeks) of that column's values.
    """
)

NUMERIC_COLS = [
    "fill_level",
    "capacity_twh",
    "fill_twh",
    "fill_level_prev_week",
    "fill_level_change",
]
FIRST_MONTH_WEEKS = 4

col1, col2 = st.columns(2)
area_type = col1.selectbox("Area type", ["EL", "NO", "VASS"], index=0)
numbers = sorted(
    get_reservoir_area(area_type)["area_number"].unique().tolist()
)
default = numbers.index(4) if 4 in numbers else 0
area_number = col2.selectbox("Area number", numbers, index=default)

df = get_reservoir_area(area_type, area_number)
first_month = df.iloc[:FIRST_MONTH_WEEKS]

summary = pd.DataFrame(
    {
        "column": NUMERIC_COLS,
        "first_month_trend": [first_month[col].tolist() for col in NUMERIC_COLS],
        "min": [df[col].min() for col in NUMERIC_COLS],
        "max": [df[col].max() for col in NUMERIC_COLS],
    }
)

st.dataframe(
    summary,
    column_config={
        "column": st.column_config.TextColumn("Column"),
        "first_month_trend": st.column_config.LineChartColumn(
            "First month trend (4 weeks)", width="medium"
        ),
        "min": st.column_config.NumberColumn("Min", format="%.3f"),
        "max": st.column_config.NumberColumn("Max", format="%.3f"),
    },
    hide_index=True,
    use_container_width=True,
)

with st.expander("Show full raw data"):
    st.dataframe(df, use_container_width=True)