"""Backfill EirGrid demand + Open-Meteo weather into Azure Blob as partitioned Parquet.
Resilient: retries with backoff, polite delay, and skips months already uploaded (resumable)."""
import os, io, time, requests, pandas as pd                # +time for sleep/backoff
from datetime import date
from dateutil.relativedelta import relativedelta
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
load_dotenv()

CONN = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "energy-lake")
svc = BlobServiceClient.from_connection_string(CONN)

def fetch_json(url, params, tries=4):                      # GET with retries + exponential backoff
    for attempt in range(tries):                           # try up to `tries` times
        try:
            r = requests.get(url, params=params, timeout=60)   # the actual request
            r.raise_for_status()                           # raise on 4xx/5xx HTTP errors
            return r.json()                                # success -> return parsed JSON
        except requests.exceptions.RequestException as e:  # any network/HTTP failure
            wait = 5 * (attempt + 1)                       # 5s, 10s, 15s, 20s backoff
            if attempt == tries - 1:                       # last attempt -> give up
                raise
            print(f"    retry {attempt+1}/{tries-1} after error ({e.__class__.__name__}); waiting {wait}s")
            time.sleep(wait)                               # wait before retrying

def eirgrid_month(d0, d1):
    p = {"region": "ROI", "chartType": "default", "dateRange": "month",
         "dateFrom": d0.strftime("%d-%b-%Y"), "dateTo": d1.strftime("%d-%b-%Y"), "areas": "demandactual"}
    rows = fetch_json("https://www.smartgriddashboard.com/api/chart/", p)["Rows"]  # now via retry helper
    df = pd.DataFrame(rows)
    df["EffectiveTime"] = pd.to_datetime(df["EffectiveTime"], format="%d-%b-%Y %H:%M:%S")
    return df[["EffectiveTime", "Value"]].rename(columns={"Value": "demand_mw"})

def weather_range(start, end, lat=53.43, lon=-6.25):
    p = {"latitude": lat, "longitude": lon, "start_date": start.isoformat(), "end_date": end.isoformat(),
         "hourly": "temperature_2m,wind_speed_10m,relative_humidity_2m", "timezone": "Europe/Dublin"}
    h = fetch_json("https://archive-api.open-meteo.com/v1/archive", p)["hourly"]   # now via retry helper
    w = pd.DataFrame(h)
    w["time"] = pd.to_datetime(w["time"])
    return w

def exists(path):                                          # is this blob already uploaded?
    return svc.get_blob_client(CONTAINER, path).exists()   # True/False

def upload(df, path):
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)
    svc.get_blob_client(CONTAINER, path).upload_blob(buf, overwrite=True)
    print(f"  uploaded {path}  ({len(df)} rows)")

def run(months_back=24):
    end = date.today().replace(day=1) - relativedelta(days=1)
    start = (end.replace(day=1) - relativedelta(months=months_back - 1))
    cur = start.replace(day=1)
    while cur <= end:
        nxt = cur + relativedelta(months=1) - relativedelta(days=1)
        dpath = f"bronze/demand/year={cur:%Y}/month={cur:%m}/demand.parquet"
        wpath = f"bronze/weather/year={cur:%Y}/month={cur:%m}/weather.parquet"
        if exists(dpath) and exists(wpath):                # already done -> skip (resumable)
            print(f"{cur:%Y-%m}: skip (already in lake)")
            cur += relativedelta(months=1)
            continue
        print(f"{cur:%Y-%m}:")
        upload(eirgrid_month(cur, nxt), dpath)
        upload(weather_range(cur, nxt), wpath)
        time.sleep(2)                                      # polite pause so EirGrid doesn't rate-limit us
        cur += relativedelta(months=1)

if __name__ == "__main__":
    run(24)
    print("Backfill complete \u2705")