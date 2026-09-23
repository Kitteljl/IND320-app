import streamlit as st

st.set_page_config(page_title="IND320 - Reservoir Data", layout="wide")

st.title("IND320 - Reservoir Data Project")

st.sidebar.success("Select a page above to get started.")

st.markdown(
    """
    Welcome to my IND320 compulsory project app.

    Use the sidebar to navigate between pages:

    - **Data Table** — an overview table of the imported reservoir data, with a
      small line-chart preview of the first month for each column.
    - **Plots** — an interactive plot of the reservoir data, where you can choose
      a column (or all columns) and a range of months to display.
    - **About** — project info and links to the GitHub repository and this app.

    **Data source:** weekly Norwegian hydropower reservoir statistics
    (`reservoirs.csv`), currently filtered to price area 4.
    """
)