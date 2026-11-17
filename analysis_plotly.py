"""Plotly versions of the analysis plots used in the Streamlit app (blue theme).

The calculations are the same as in analysis.py (used in the part 3 notebook); only the
figures are interactive Plotly figures instead of static matplotlib ones.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL

from theme import COLORWAY, OUTLIER

# Hourly weather properties that can be selected: column name -> (label, unit)
WEATHER_PROPS = {
    "temperature_2m": ("Temperature", "°C"),
    "precipitation": ("Precipitation", "mm/h"),
    "snowfall": ("Snowfall", "cm/h"),
    "wind_speed_10m": ("Wind speed", "km/h"),
    "wind_gusts_10m": ("Wind gusts", "km/h"),
}


def plot_spc_outliers(series, cutoff_freq=1/30, n_std=3.0, title="", label="Temperature", unit="°C"):
    """Outliers in an hourly weather series via DCT high-pass filtering + SPC.

    cutoff_freq : DCT cut-off in cycles per day (periods longer than 1/cutoff_freq days are
                  treated as slow/seasonal variation)
    n_std       : number of robust standard deviations for the SPC boundaries
    The high-pass filtered series (SATV) is only used to find the boundaries and outliers.
    Returns a Plotly figure and a summary dict.
    """
    x = series.to_numpy(float)
    N = len(x)
    coef = dct(x, type=2, norm="ortho")
    k0 = int(np.ceil(cutoff_freq * 2 * N / 24))      # DCT index k <-> k*24/(2N) cycles/day
    low, high = coef.copy(), coef.copy()
    low[k0:] = 0                                     # keep slow variation
    high[:k0] = 0                                    # keep fast variation (SATV)
    slow = idct(low, type=2, norm="ortho")
    satv = idct(high, type=2, norm="ortho")

    # Robust statistics from the whole period: median and MAD (scaled to a standard deviation)
    center = np.median(satv)
    sigma = 1.4826 * np.median(np.abs(satv - center))
    is_out = np.abs(satv - center) > n_std * sigma
    upper = slow + center + n_std * sigma
    lower = slow + center - n_std * sigma

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=x, mode="lines", name=label,
                    line=dict(color=COLORWAY[0], width=1))
    fig.add_scatter(x=series.index, y=upper, mode="lines", name=f"SPC boundaries (±{n_std} robust SD)",
                    line=dict(color="black", width=1, dash="dash"), legendgroup="spc")
    fig.add_scatter(x=series.index, y=lower, mode="lines", showlegend=False,
                    line=dict(color="black", width=1, dash="dash"), legendgroup="spc")
    fig.add_scatter(x=series.index[is_out], y=x[is_out], mode="markers", name="Outliers",
                    marker=dict(color=OUTLIER, size=6))
    fig.update_layout(title=f"{title}: {label}, DCT cut-off {cutoff_freq:.3f} cycles/day, {n_std} SD",
                      yaxis_title=f"{label} ({unit})", hovermode="x unified", height=450,
                      legend=dict(orientation="h", y=-0.15))

    summary = {"n_outliers": int(is_out.sum()),
               "percent_outliers": round(float(100 * is_out.mean()), 2),
               "dct_coefficients_removed": k0,
               "robust_sigma": round(float(sigma), 4),
               "outliers": pd.DataFrame({"time": series.index[is_out], "value": x[is_out]})}
    return fig, summary


def plot_lof_anomalies(series, contamination=0.01, n_neighbors=20, title="", label="Temperature", unit="°C"):
    """Anomalies in an hourly weather series with the Local Outlier Factor method.

    Features are the value and its hour-to-hour change (both standardised).
    Returns a Plotly figure and a summary dict.
    """
    x = series.to_numpy(float)
    feats = StandardScaler().fit_transform(np.column_stack([x, np.gradient(x)]))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_out = lof.fit_predict(feats) == -1             # -1 = anomaly
    score = -lof.negative_outlier_factor_             # larger = more anomalous

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=x, mode="lines", name=label,
                    line=dict(color=COLORWAY[0], width=1))
    fig.add_scatter(x=series.index[is_out], y=x[is_out], mode="markers", name="LOF anomalies",
                    marker=dict(color=OUTLIER, size=6))
    fig.update_layout(title=f"{title}: {label}, LOF, contamination={contamination:.1%}, n_neighbors={n_neighbors}",
                      yaxis_title=f"{label} ({unit})", hovermode="x unified", height=450,
                      legend=dict(orientation="h", y=-0.15))

    out = pd.DataFrame({"time": series.index[is_out], "value": x[is_out], "lof_score": score[is_out]})
    summary = {"n_anomalies": int(is_out.sum()),
               "percent_anomalies": round(float(100 * is_out.mean()), 2),
               "anomalies": out.sort_values("lof_score", ascending=False).reset_index(drop=True)}
    return fig, summary


def plot_stl(series, period=52, seasonal=13, trend=105, robust=True, title="STL decomposition"):
    """STL decomposition of a weekly series as four stacked Plotly panels."""
    s = series.sort_index().resample("W").mean().interpolate()
    res = STL(s, period=period, seasonal=seasonal, trend=trend, robust=robust).fit()
    parts = [("Observed", res.observed), ("Trend", res.trend),
             ("Seasonal", res.seasonal), ("Residual", res.resid)]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=[p[0] for p in parts])
    for i, (_, values) in enumerate(parts, start=1):
        fig.add_scatter(x=s.index, y=values, mode="lines", showlegend=False,
                        line=dict(color=COLORWAY[0], width=1.2), row=i, col=1)
    fig.update_layout(height=720, hovermode="x unified",
                      title=f"{title} (seasonal={seasonal}, trend={trend}, robust={robust})")
    return fig


def plot_spectrogram(series, window_length=156, overlap=0.75, fmax=6, title="Spectrogram"):
    """Spectrogram of a weekly series as a Plotly heatmap (frequency in cycles per year)."""
    s = series.sort_index().resample("W").mean().interpolate()
    x = s.to_numpy(float)
    nperseg = int(window_length)
    noverlap = int(overlap * nperseg)
    # fs = 52 samples/year -> frequencies come out in cycles per year
    f, t, Sxx = spectrogram(x, fs=52, window="hann", nperseg=nperseg,
                            noverlap=noverlap, detrend="constant", scaling="density")
    dates = s.index[0] + pd.to_timedelta(t * 365.25, unit="D")
    keep = f <= fmax

    fig = go.Figure(go.Heatmap(x=dates, y=f[keep], z=10 * np.log10(Sxx[keep] + 1e-12),
                               colorscale="Blues", colorbar=dict(title="Power (dB)")))
    fig.update_layout(title=f"{title}: window={window_length} weeks, overlap={overlap:.0%}",
                      yaxis_title="Frequency (cycles per year)", height=450)
    return fig