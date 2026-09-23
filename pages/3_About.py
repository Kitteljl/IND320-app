"""
IND320 - About page.
"""

import streamlit as st

st.set_page_config(page_title="About", layout="wide")
st.title("About this project")

st.markdown(
    """
    This is the Streamlit app for the compulsory hand-in, Part 1, in IND320.

    **GitHub repository:** https://github.com/Kitteljl/IND320-app

    **Streamlit app:** https://ind320-app-kitteljl.streamlit.app/

    **Data:** weekly Norwegian hydropower reservoir statistics (`reservoirs.csv`),
    read locally and cached with `st.cache_data` for speed. In part 2 of the
    project, this local CSV file will be replaced with a MongoDB-backed data
    source.

    **Author:** Kittel Johannes Lande
    """
)