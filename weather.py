"""Hourly ERA5 weather from Open-Meteo for the sampled locations of a region."""
import time
import numpy as np
import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
POINTS_CSV = "data/sample_points.csv"      # layer, region, lon, lat (made in the notebook)

# Magasinstatistikk VASS areas are built from the NVE regions:
#   VASS1 = RS + RØ,  VASS2 = RV,  VASS3 = RM + RN
# NO1..NO5 (price areas) and single NVE region codes (RV, RM, RN, RØ, RS) work directly as ids.
REGION_MAP = {"VASS1": ["RS", "RØ"],
              "VASS2": ["RV"],
              "VASS3": ["RM", "RN"]}

# Hourly variables: precipitation and temperature plus other relevant properties
HOURLY = ["temperature_2m", "precipitation", "rain", "snowfall",
          "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]


def region_id(area_type, number):
    """Map the Magasinstatistikk selector (EL/VASS + area number) to a weather region id."""
    if area_type == "EL":
        return f"NO{number}"          # electricity price areas NO1..NO5
    if area_type == "VASS":
        return f"VASS{number}"        # VASS1..VASS3
    raise ValueError(f"No weather region defined for area type '{area_type}'")


def get_points(region, n_points=25):
    """Return the first n_points sampled (lon, lat) pairs of each region/area in `region`."""
    pts = pd.read_csv(POINTS_CSV)
    codes = REGION_MAP.get(region, [region])
    sel = pts[pts["region"].isin(codes)]
    if sel.empty:
        raise ValueError(f"No sampled points for '{region}'. Known: {sorted(pts['region'].unique())}")
    return sel.groupby("region").head(n_points).reset_index(drop=True)[["lon", "lat"]]


def download_weather(region, start, end, n_points=25, batch=5, hourly=HOURLY, timeout=180):
    """Download hourly ERA5 data for a region and time interval ('YYYY-MM-DD').

    Locations are fetched in small batches (large requests time out), then averaged
    over all locations for each hour. Returns a DataFrame indexed by UTC time.
    """
    pts = get_points(region, n_points)
    frames = []
    for i in range(0, len(pts), batch):
        chunk = pts.iloc[i:i + batch]
        params = {"latitude": ",".join(f"{v:.4f}" for v in chunk["lat"]),
                  "longitude": ",".join(f"{v:.4f}" for v in chunk["lon"]),
                  "start_date": start, "end_date": end,
                  "hourly": ",".join(hourly), "models": "era5", "timezone": "UTC"}
        for attempt in range(5):                        # retry on rate limit or timeout
            try:
                r = requests.get(ARCHIVE_URL, params=params, timeout=timeout)
            except requests.exceptions.Timeout:
                print(f"  timeout on batch {i // batch + 1}, retrying ({attempt + 1}/5) ...")
                time.sleep(5)
                continue
            if r.status_code == 429:                    # too many requests: wait and retry
                print(f"  rate limited, waiting {20 * (attempt + 1)} s ...")
                time.sleep(20 * (attempt + 1))
                continue
            r.raise_for_status()
            break
        else:
            raise RuntimeError("Open-Meteo did not respond: try again later or use fewer points.")
        data = r.json()
        data = [data] if isinstance(data, dict) else data   # one dict per location
        frames += [pd.DataFrame(loc["hourly"]) for loc in data]
        print(f"  downloaded {min(i + batch, len(pts))}/{len(pts)} locations")

    df = pd.concat(frames)
    df["time"] = pd.to_datetime(df["time"])
    # Wind direction is an angle, so average it as a vector (circular mean)
    rad = np.deg2rad(df["wind_direction_10m"])
    df["_s"], df["_c"] = np.sin(rad), np.cos(rad)
    out = df.drop(columns="wind_direction_10m").groupby("time").mean()
    out["wind_direction_10m"] = np.rad2deg(np.arctan2(out["_s"], out["_c"])) % 360
    return out.drop(columns=["_s", "_c"])