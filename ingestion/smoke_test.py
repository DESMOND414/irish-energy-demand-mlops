"""Day-1 smoke test: confirm EirGrid + Open-Meteo return usable data. No keys needed."""
import requests, pandas as pd

def eirgrid_demand(date_from="01-Sep-2025", date_to="07-Sep-2025", region="ROI"):
    url = "https://www.smartgriddashboard.com/api/chart/"
    params = {"region": region, "chartType": "default", "dateRange": "month",
              "dateFrom": date_from, "dateTo": date_to, "areas": "demandactual"}
    rows = requests.get(url, params=params, timeout=30).json()["Rows"]
    df = pd.DataFrame(rows)
    df["EffectiveTime"] = pd.to_datetime(df["EffectiveTime"], format="%d-%b-%Y %H:%M:%S")
    return df

def open_meteo(lat=53.43, lon=-6.25, start="2025-09-01", end="2025-09-07"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
              "hourly": "temperature_2m,wind_speed_10m", "timezone": "Europe/Dublin"}
    h = requests.get(url, params=params, timeout=30).json()["hourly"]
    return pd.DataFrame(h)

if __name__ == "__main__":
    d = eirgrid_demand()
    print(f"EirGrid demand: {len(d)} rows | {d.EffectiveTime.min()} → {d.EffectiveTime.max()} "
          f"| MW range {d.Value.min()}–{d.Value.max()}")
    w = open_meteo()
    print(f"Open-Meteo weather: {len(w)} rows | temp {w.temperature_2m.min()}–{w.temperature_2m.max()}°C")
    d.head(200).to_csv("data/sample/eirgrid_demand_sample.csv", index=False)
    w.head(200).to_csv("data/sample/weather_sample.csv", index=False)
    print("Wrote samples to data/sample/ ✅")