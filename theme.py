import plotly.graph_objects as go
import plotly.io as pio

# Rain-blue palette: blues first, one warm accent and a teal for contrast between series
COLORWAY = ["#1e6fb8", "#e07b39", "#2a9d8f", "#0b3c6d", "#5fb3e6"]
OUTLIER = "#d1495b"          # outliers and anomalies
SEQUENTIAL = "Blues"         # colour scale for the map and heatmaps


def apply_plotly_theme():
    """Register and activate the shared Plotly template (same colours as .streamlit/config.toml)."""
    pio.templates["ind320"] = go.layout.Template(
        layout=dict(
            font=dict(family="sans-serif", size=13, color="#10243a"),
            colorway=COLORWAY,
            paper_bgcolor="#f4f8fc",
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#dbe9f6"),
            yaxis=dict(gridcolor="#dbe9f6"),
        )
    )
    pio.templates.default = "plotly+ind320"