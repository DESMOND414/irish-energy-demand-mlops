"""Data-drift monitoring via PSI: reference window vs recent data. Flags retrain."""
import sys, json
import numpy as np, pandas as pd

df = pd.read_parquet("data/features/feature_matrix.parquet").sort_values("ts_hour")

# Reference = everything older than 60 days; Current = last 30 days
ref_end   = df["ts_hour"].max() - pd.Timedelta(days=60)
cur_start = df["ts_hour"].max() - pd.Timedelta(days=30)
reference = df[df.ts_hour <= ref_end]
current   = df[df.ts_hour >= cur_start]

def psi(ref, cur, bins=10):
    """Population Stability Index: how much a distribution shifted."""
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    r = np.clip(np.histogram(ref, bins=edges)[0] / len(ref), 1e-6, None)
    c = np.clip(np.histogram(cur, bins=edges)[0] / len(cur), 1e-6, None)
    return float(np.sum((c - r) * np.log(c / r)))

FEATURES = ["demand_mw", "temperature_2m", "wind_speed_10m", "demand_lag_24h", "demand_roll_168h"]
report  = {f: round(psi(reference[f].values, current[f].values), 4) for f in FEATURES}
drifted = [f for f, v in report.items() if v > 0.2]   # >0.2 = significant shift

print(f"PSI drift report  (reference n={len(reference)} vs recent n={len(current)}):")
for f, v in report.items():
    tag = "DRIFT" if v > 0.2 else ("watch" if v > 0.1 else "ok")
    print(f"  {f:18s} PSI={v:.3f}  [{tag}]")

json.dump({"psi": report, "drifted": drifted}, open("monitoring/drift_report.json", "w"), indent=2)

if drifted:
    print(f"\n⚠️  Significant drift in {drifted} -> retrain recommended")
    sys.exit(1)
print("\n✅ No significant drift — model still valid")
