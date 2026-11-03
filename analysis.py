"""Analysis functions shared by the notebook and the Streamlit pages.

Each function takes a pandas Series (datetime index) and returns a matplotlib figure
(plus a summary dict for the outlier/anomaly functions).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL


def plot_spc_outliers(series, cutoff_freq=1/30, n_std=3.0, title="Precipitation"):
    """Outliers in hourly data via DCT high-pass filtering + Statistical Process Control.

    cutoff_freq : DCT cut-off in cycles per day (default 1/30 = periods longer than ~30 days
                  are treated as seasonal/slow variation and removed)
    n_std       : number of robust standard deviations for the SPC boundaries

    The high-pass filtered series (SATV) is only used to find the boundaries and outliers;
    it is not plotted. Returns the figure and a summary dict.
    """
    x = series.to_numpy(float)
    N = len(x)
    coef = dct(x, type=2, norm="ortho")
    k0 = int(np.ceil(cutoff_freq * 2 * N / 24))      # DCT index k <-> k*24/(2N) cycles/day (hourly data)
    low, high = coef.copy(), coef.copy()
    low[k0:] = 0                                     # keep slow variation
    high[:k0] = 0                                    # keep fast variation (SATV)
    slow = idct(low, type=2, norm="ortho")
    satv = idct(high, type=2, norm="ortho")

    # Robust statistics from the whole period: median and MAD (scaled to a standard deviation)
    center = np.median(satv)
    sigma = 1.4826 * np.median(np.abs(satv - center))
    is_out = np.abs(satv - center) > n_std * sigma

    # Boundaries drawn around the slow component, in the units of the original series
    upper = slow + center + n_std * sigma
    lower = slow + center - n_std * sigma

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, x, color="tab:blue", lw=0.6, label="Average precipitation")
    ax.plot(series.index, upper, color="black", lw=1, ls="--", label=f"SPC boundaries (±{n_std} robust SD)")
    ax.plot(series.index, lower, color="black", lw=1, ls="--")
    ax.scatter(series.index[is_out], x[is_out], color="tab:red", s=10, zorder=3, label="Outliers")
    ax.set_ylabel("Precipitation (mm/h)")
    ax.set_title(f"{title}: DCT cut-off {cutoff_freq:.3f} cycles/day, {n_std} SD")
    ax.legend(loc="upper right")
    fig.tight_layout()

    summary = {"n_outliers": int(is_out.sum()),
               "percent_outliers": round(float(100 * is_out.mean()), 2),
               "dct_coefficients_removed": k0,
               "robust_sigma": round(float(sigma), 4),
               "outliers": pd.DataFrame({"time": series.index[is_out], "precipitation": x[is_out]})}
    return fig, summary


def plot_lof_anomalies(series, contamination=0.01, n_neighbors=20, title="Temperature"):
    """Anomalies in hourly temperature with the Local Outlier Factor method.

    contamination : proportion of points flagged as anomalies (default 1 %)
    n_neighbors   : neighbourhood size used to estimate local density

    Features are the temperature and its hour-to-hour change (both standardised),
    so both unusual levels and unusually fast changes can be detected.
    Returns the figure and a summary dict.
    """
    x = series.to_numpy(float)
    feats = StandardScaler().fit_transform(np.column_stack([x, np.gradient(x)]))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_out = lof.fit_predict(feats) == -1             # -1 = anomaly
    score = -lof.negative_outlier_factor_             # larger = more anomalous

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, x, color="tab:blue", lw=0.6, label="Average temperature")
    ax.scatter(series.index[is_out], x[is_out], color="tab:red", s=12, zorder=3, label="LOF anomalies")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"{title}: LOF, contamination={contamination:.1%}, n_neighbors={n_neighbors}")
    ax.legend(loc="upper right")
    fig.tight_layout()

    out = pd.DataFrame({"time": series.index[is_out], "temperature": x[is_out], "lof_score": score[is_out]})
    summary = {"n_anomalies": int(is_out.sum()),
               "percent_anomalies": round(float(100 * is_out.mean()), 2),
               "anomalies": out.sort_values("lof_score", ascending=False).reset_index(drop=True)}
    return fig, summary


def plot_stl(series, period=52, seasonal=13, trend=105, robust=True, title="STL decomposition"):
    """STL decomposition of a weekly series. Returns the figure.

    period   : observations per seasonal cycle (52 weeks = 1 year)
    seasonal : seasonal smoother length (odd; larger = smoother seasonal pattern)
    trend    : trend smoother length (odd, larger than period; larger = smoother trend)
    robust   : True downweights outliers in the fit
    """
    # Make the series regular (weekly) and fill small gaps so STL can run
    s = series.sort_index().resample("W").mean().interpolate()
    res = STL(s, period=period, seasonal=seasonal, trend=trend, robust=robust).fit()
    fig = res.plot()
    fig.set_size_inches(10, 8)
    fig.suptitle(f"{title} (seasonal={seasonal}, trend={trend}, robust={robust})", y=1.0)
    fig.tight_layout()
    return fig


def plot_spectrogram(series, window_length=156, overlap=0.75, fmax=6, title="Spectrogram"):
    """Spectrogram of a weekly series. Returns the figure.

    window_length : window length in weeks (default 156 = 3 years)
    overlap       : fraction of the window shared by neighbouring windows (default 0.75)
    fmax          : highest frequency shown, in cycles per year
    """
    # Regular weekly series (fill small gaps), so 52 samples = 1 year
    s = series.sort_index().resample("W").mean().interpolate()
    x = s.to_numpy(float)

    nperseg = int(window_length)
    noverlap = int(overlap * nperseg)
    # fs = 52 samples/year -> frequencies come out in cycles per year
    f, t, Sxx = spectrogram(x, fs=52, window="hann", nperseg=nperseg,
                            noverlap=noverlap, detrend="constant", scaling="density")

    # Segment centres (in years) -> dates
    dates = s.index[0] + pd.to_timedelta(t * 365.25, unit="D")

    fig, ax = plt.subplots(figsize=(11, 4.5))
    mesh = ax.pcolormesh(dates, f, 10 * np.log10(Sxx + 1e-12), shading="auto", cmap="viridis")
    ax.set_ylim(0, fmax)
    ax.set_ylabel("Frequency (cycles per year)")
    ax.set_title(f"{title}: window={window_length} weeks, overlap={overlap:.0%}")
    fig.colorbar(mesh, ax=ax, label="Power (dB)")
    fig.tight_layout()
    return fig