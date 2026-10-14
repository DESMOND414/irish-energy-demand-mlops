-- Gold mart: demand aggregated to hourly, joined to weather + calendar features
with demand_hourly as (
    select
        date_trunc('hour', ts_15min) as ts_hour,   -- collapse 4x15min -> 1 hour
        avg(demand_mw) as demand_mw                 -- mean demand that hour
    from {{ ref('stg_demand') }}
    where demand_mw is not null                     -- drop EirGrid gaps (empty readings)
    group by 1
)
select
    d.ts_hour,
    d.demand_mw,
    w.temperature_2m,
    w.wind_speed_10m,
    w.relative_humidity_2m,
    extract('hour'  from d.ts_hour) as hour_of_day,
    extract('dow'   from d.ts_hour) as day_of_week,
    extract('month' from d.ts_hour) as month
from demand_hourly d
left join {{ ref('stg_weather') }} w using (ts_hour)
order by d.ts_hour
