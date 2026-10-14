-- Raw hourly weather, read straight from the Azure lake
select
    time as ts_hour,
    temperature_2m,
    wind_speed_10m,
    relative_humidity_2m
from read_parquet('az://energy-lake/bronze/weather/**/*.parquet')
