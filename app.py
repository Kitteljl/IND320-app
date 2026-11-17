import streamlit as st
from theme import apply_plotly_theme

st.set_page_config(page_title="IND320 - Reservoir Data", layout="wide",
                   page_icon="images/fish_transparent.png")
apply_plotly_theme()   # shared blue Plotly template for every page
st.logo("images/fish_transparent.png")

pages = {
    "": [
        st.Page("home.py", title="Home", icon=":material/home:", default=True),
    ],
    "Explore": [
        st.Page("pages/6_Map.py", title="Map", icon=":material/map:"),
        st.Page("pages/1_Reservoir_Overview.py", title="Reservoir overview", icon=":material/table_chart:"),
        st.Page("pages/2_Reservoir_Plots.py", title="Reservoir plots", icon=":material/show_chart:"),
        st.Page("pages/5_Cross_Border.py", title="Cross-border flows", icon=":material/swap_horiz:"),
    ],
    "Analyse": [
        st.Page("pages/3_Seasonal_Analysis.py", title="Seasonal analysis", icon=":material/waves:"),
        st.Page("pages/4_Weather_Outliers.py", title="Weather outliers", icon=":material/thunderstorm:"),
    ],
    "Predict": [
        st.Page("pages/7_Correlation.py", title="Sliding window correlation", icon=":material/insights:"),
        st.Page("pages/8_Forecast.py", title="Forecast", icon=":material/trending_up:"),
    ],
}

pg = st.navigation(pages)
pg.run()