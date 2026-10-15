"""Lightweight data-quality gate (no Great Expectations) for the Airflow pipeline."""
import sys, duckdb
con = duckdb.connect("transforms/energy.duckdb")
n, nulls, mn, mx = con.sql("""
    select count(*),
           count(*) filter (where demand_mw is null),
           min(demand_mw), max(demand_mw)
    from mart_demand_hourly
""").fetchone()
ok = (n > 10000) and (nulls == 0) and (500 < mn) and (mx < 8000)
print(f"rows={n} nulls={nulls} min={mn} max={mx} -> {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
