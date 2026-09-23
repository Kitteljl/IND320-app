"""
IND320 - Interactive Plot page.
"""

import streamlit as st
import matplotlib.pyplot as plt

from utils import load_data, NUMERIC_COLS

st.set_page_config(page_title="Plots", layout="wide")
st.title("Interactive Plot")

st.markdown(
    """
    Choose a single column (or all columns together) below, and use the slider
    to select which months to display. The default view shows the first month
    of data.

    When "All columns" is selected, columns are grouped by their natural unit
    (fraction vs. TWh) and shown on two separate y-axes, so every column's
    variation stays clearly visible.
    """
)

df = load_data()

df["month_period"] = df["date"].dt.to_period("M")
months = sorted(df["month_period"].unique())
month_labels = [str(m) for m in months]

col1, col2 = st.columns([1, 2])

with col1:
    selected_col = st.selectbox(
        "Choose a column",
        ["All columns"] + NUMERIC_COLS,
    )

with col2:
    selected_range = st.select_slider(
        "Select month range",
        options=month_labels,
        value=(month_labels[0], month_labels[0]),
    )

start_label, end_label = selected_range
month_str = df["month_period"].astype(str)
mask = (month_str >= start_label) & (month_str <= end_label)
filtered = df[mask]

fig, ax1 = plt.subplots(figsize=(11, 5))

if selected_col == "All columns":
    color_fill = "#1f77b4"
    ax1.plot(filtered["date"], filtered["fill_level"], color=color_fill,
              linewidth=1.8, label="fill_level")
    ax1.plot(filtered["date"], filtered["fill_level_prev_week"], color="#17becf",
              linewidth=1.4, linestyle="--", alpha=0.7, label="fill_level_prev_week")
    ax1.plot(filtered["date"], filtered["fill_level_change"], color="#d62728",
              linewidth=1.2, alpha=0.8, label="fill_level_change")
    ax1.axhline(0, color="gray", linewidth=0.8, linestyle=":")
    ax1.set_ylabel("Fill level / change (fraction)", color=color_fill)
    ax1.tick_params(axis="y", labelcolor=color_fill)

    ax2 = ax1.twinx()
    color_twh = "#2ca02c"
    ax2.plot(filtered["date"], filtered["capacity_twh"], color=color_twh,
              linewidth=1.8, label="capacity_twh")
    ax2.plot(filtered["date"], filtered["fill_twh"], color="#ff7f0e",
              linewidth=1.8, label="fill_twh")
    ax2.set_ylabel("Capacity / fill (TWh)", color=color_twh)
    ax2.tick_params(axis="y", labelcolor=color_twh)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc="upper left", bbox_to_anchor=(1.15, 1), frameon=False)

    ax1.set_title(f"All reservoir columns, {start_label} to {end_label}")
else:
    ax1.plot(filtered["date"], filtered[selected_col], color="#1f77b4", linewidth=2)
    ax1.set_ylabel(selected_col)
    ax1.set_title(f"{selected_col}, {start_label} to {end_label}")

ax1.set_xlabel("Date")
ax1.grid(alpha=0.3)
fig.autofmt_xdate()

st.pyplot(fig)