import math
import numpy as np
import pandas as pd
from river import time_series, linear_model, preprocessing, optim


def _fourier(date, k):
    """Yearly seasonal features: sin/cos of the day of year, k harmonics."""
    t = date.dayofyear / 365.25
    feats = {}
    for i in range(1, k + 1):
        feats[f"sin{i}"] = math.sin(2 * math.pi * i * t)
        feats[f"cos{i}"] = math.cos(2 * math.pi * i * t)
    return feats


def _climatology(exog):
    """Mean of each exogenous column per ISO week number (from past data only)."""
    weeks = exog.index.isocalendar().week.astype(int).to_numpy()
    return exog.groupby(weeks).mean()


def forecast_filling(y, horizon=12, history_weeks=104, p=1, d=1, q=1,
                     fourier_k=2, lr=0.01, exog=None):
    """Forecast weekly reservoir filling with River's SNARIMAX.

    y             : pandas Series, weekly Sunday dates as index (filling degree)
    horizon       : number of weeks ahead to predict
    history_weeks : how many of the most recent weeks the model learns from
    p, d, q       : AR order, differencing, MA order
    fourier_k     : yearly harmonics used as exogenous features (0 = none)
    lr            : SGD learning rate of the underlying linear regressor
    exog          : optional DataFrame of weekly features (e.g. temperature, precipitation),
                    indexed by the same Sunday dates. Only rows up to the last date of y are used.
                    For the forecast weeks the average value of that ISO week is used (unknown future).
    Returns a Series of forecasts indexed by the future weekly dates.
    """
    y = y.dropna().sort_index().iloc[-history_weeks:]
    last_date = y.index[-1]

    cols, clim = None, None
    if exog is not None and exog.shape[1] > 0:
        exog = exog.sort_index().loc[:last_date]      # never look past the forecast origin
        cols = list(exog.columns)
        clim = _climatology(exog)

    def features(date, known):
        x = _fourier(date, fourier_k) if fourier_k > 0 else {}
        if cols is not None:
            if known and date in exog.index and not exog.loc[date, cols].isna().any():
                x.update(exog.loc[date, cols].to_dict())
            else:
                wk = int(date.isocalendar().week)
                wk = wk if wk in clim.index else 52     # week 53 falls back to week 52
                x.update(clim.loc[wk, cols].to_dict())
        return x or None

    model = time_series.SNARIMAX(
        p=p, d=d, q=q,
        regressor=preprocessing.StandardScaler()
        | linear_model.LinearRegression(intercept_lr=0.1, optimizer=optim.SGD(lr)),
    )

    # Learn the history one observation at a time (online learning)
    for date, value in y.items():
        model.learn_one(value, features(date, known=True))

    future_dates = pd.date_range(last_date + pd.Timedelta(days=7), periods=horizon, freq="7D")
    xs = [features(fd, known=False) for fd in future_dates]
    if xs[0] is None:
        xs = None
    preds = model.forecast(horizon=horizon, xs=xs)
    return pd.Series(preds, index=future_dates, name="forecast")


def holdout_eval(y, horizon=12, **kwargs):
    """Hide the last `horizon` weeks, forecast them, and compare with a naive forecast
    (repeat the last known value). Returns forecast, actual values, MAE and naive MAE."""
    y = y.dropna().sort_index()
    train, test = y.iloc[:-horizon], y.iloc[-horizon:]
    fc = forecast_filling(train, horizon=horizon, **kwargs)
    mae = float(np.mean(np.abs(fc.values - test.values)))
    naive_mae = float(np.mean(np.abs(train.iloc[-1] - test.values)))
    return fc, test, mae, naive_mae


def rolling_eval(y, horizon=12, n_origins=6, step=26, **kwargs):
    """Average hold-out error over several forecast start dates, spaced `step` weeks apart.
    Returns (mean MAE of model, mean MAE of naive)."""
    y = y.dropna().sort_index()
    maes, naives = [], []
    for k in range(n_origins):
        cut = len(y) - horizon - k * step
        train, test = y.iloc[:cut], y.iloc[cut:cut + horizon]
        fc = forecast_filling(train, horizon=horizon, **kwargs)
        maes.append(float(np.mean(np.abs(fc.values - test.values))))
        naives.append(float(np.mean(np.abs(train.iloc[-1] - test.values))))
    return float(np.mean(maes)), float(np.mean(naives))