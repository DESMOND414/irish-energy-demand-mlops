"""Build the ML training matrix from the hourly mart: lags, rolling means, calendar, holidays."""
import duckdb, pandas as pd, holidays

# Load the clean mart, ordered in time
df = duckdb.connect("transforms/energy.duckdb").sql(
    "select * from mart_demand_hourly order by ts_hour").df()
df["ts_hour"] = pd.to_datetime(df["ts_hour"])
df = df.set_index("ts_hour")

# --- Lag features: demand at the same hour 1h, 1 day, and 1 week ago ---
for lag in [1, 24, 168]:
    df[f"demand_lag_{lag}h"] = df["demand_mw"].shift(lag)

# --- Rolling means (shift(1) first so the current hour is NOT in its own average = no leakage) ---
df["demand_roll_24h"]  = df["demand_mw"].shift(1).rolling(24).mean()   # last-day trend
df["demand_roll_168h"] = df["demand_mw"].shift(1).rolling(168).mean()  # last-week trend

# --- Calendar / holiday flags (demand behaves differently on days off) ---
df["is_weekend"] = (df.index.dayofweek >= 5).astype(int)
ie = holidays.Ireland()
df["is_holiday"] = df.index.to_series().dt.date.map(lambda d: int(d in ie))

# Lagging/rolling create NaNs in the first week -> drop them
df = df.dropna().reset_index()

# Save full matrix (gitignored) + a small committed sample
df.to_parquet("data/features/feature_matrix.parquet", index=False)
df.head(200).to_csv("data/sample/features_sample.csv", index=False)

print(f"feature matrix: {df.shape[0]} rows x {df.shape[1]} cols")
print(f"range: {df.ts_hour.min()} -> {df.ts_hour.max()}")
print("columns:", list(df.columns))
