-- Gold model: daily NYC taxi trip summary
--
-- Reads from the silver model (nyctaxi_trips_clean) via ref(),
-- which lets dbt build the correct execution order automatically.
--
-- Produces one row per calendar day with key trip metrics.
-- This table is ready for dashboards, Power BI, or downstream SQL queries.
--
-- This is a natural fit for dbt: pure aggregation SQL with no Python needed.
-- The equivalent Python implementation is in gold/aggregate.py, kept for
-- comparison — in a real project you would choose one approach, not both.
--
-- Materialized as: Delta table (set in dbt_project.yml)
-- Target schema:   <catalog>.<schema_prefix>_gold  (schema_prefix set in dbt_project.yml)

{{ config(
    materialized = 'table',
    file_format  = 'delta'
) }}

with trips as (

    select * from {{ ref('nyctaxi_trips_clean') }}

),

daily as (

    select
        cast(tpep_pickup_datetime as date)       as pickup_date,
        count(*)                                  as total_trips,
        round(avg(fare_amount), 2)                as avg_fare_usd,
        round(avg(trip_distance), 2)              as avg_trip_distance_miles,
        round(avg(trip_duration_minutes), 2)      as avg_duration_minutes,
        cast(sum(passenger_count) as bigint)      as total_passengers

    from trips
    group by cast(tpep_pickup_datetime as date)

)

select * from daily
order by pickup_date
