import streamlit as st

st.set_page_config(page_title="IND320 - Reservoir Data", layout="wide")

st.title("IND320 - Reservoir Data Project")

st.sidebar.success("Select a page above to get started.")

st.markdown("""
Data are fetched live from the **NVE Magasinstatistikk API** (reservoir filling per area),
and cross-border power flows come from **ENTSO-E** via Cassandra/Spark, curated in **MongoDB Atlas**.
""")