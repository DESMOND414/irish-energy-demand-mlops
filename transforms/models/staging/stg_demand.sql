-- Raw 15-minute grid demand, read straight from the Azure lake
select
    EffectiveTime as ts_15min,
    demand_mw
from read_parquet('az://energy-lake/bronze/demand/**/*.parquet')
