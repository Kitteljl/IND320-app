import io
import requests
import pandas as pd


def download_exchange_rates(start, end, currencies=("EUR", "USD")):
    """Download daily NOK exchange rates from Norges Bank (SDMX API).

    Returns a DataFrame indexed by date with one column per currency,
    in NOK per 1 unit of the foreign currency. Only business days exist.
    """
    # B = daily frequency, SP = spot rate, NOK = quote currency
    url = "https://data.norges-bank.no/api/data/EXR/B." + "+".join(currencies) + ".NOK.SP"
    params = {"format": "csv", "startPeriod": start, "endPeriod": end, "locale": "en"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    # Let pandas detect the separator (the API may use ; or ,)
    df = pd.read_csv(io.StringIO(r.text), sep=None, engine="python")
    df.columns = [c.strip().strip('"') for c in df.columns]

    # Find the needed columns regardless of exact naming
    def find(*names):
        for c in df.columns:
            if c.upper() in names:
                return c
        raise KeyError(f"None of {names} found. Columns were: {list(df.columns)}")

    time_col = find("TIME_PERIOD")
    cur_col = find("BASE_CUR")
    val_col = find("OBS_VALUE")

    df = df[[time_col, cur_col, val_col]].copy()
    df[val_col] = pd.to_numeric(df[val_col].astype(str).str.replace(",", "."), errors="coerce")
    wide = df.pivot(index=time_col, columns=cur_col, values=val_col)
    wide.index = pd.to_datetime(wide.index)
    wide.index.name = "date"
    return wide.rename(columns=lambda c: f"NOK_per_{c}")