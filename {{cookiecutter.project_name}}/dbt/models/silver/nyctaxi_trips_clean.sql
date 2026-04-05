-- Silver model: cleansed NYC taxi trips
--
-- Reads from the bronze source declared in models/sources.yml.
-- Applies the same cleaning rules as the Python silver job (silver/transform.py),
-- expressed here in pure SQL — no Spark session or Python runtime required.
--
-- Choose between this SQL model and the Python job depending on your context:
--   - Use this model when transformations are expressible as SQL and your team
--     prefers dbt's lineage, testing, and documentation features.
--   - Use the Python job (silver/transform.py) for transformations that need
--     Python libraries, ML models, or complex UDFs.
--
-- Materialized as: Delta table (set in dbt_project.yml)
-- Target schema:   <catalog>.<schema_prefix>_silver  (schema_prefix set in dbt_project.yml)

{{ config(
    materialized = 'table',
    file_format  = 'delta'
) }}

with raw as (

    select * from {{ source('bronze', 'nyctaxi_trips') }}

),

cleaned as (

    select
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        passenger_count,
        trip_distance,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        total_amount,
        payment_type,
        -- Derived column: trip duration in minutes
        round(
            (unix_timestamp(tpep_dropoff_datetime) - unix_timestamp(tpep_pickup_datetime)) / 60,
            2
        ) as trip_duration_minutes

    from raw

    where
        -- Drop rows with critical nulls
        fare_amount            is not null
        and trip_distance      is not null
        and tpep_pickup_datetime  is not null
        and tpep_dropoff_datetime is not null
        -- Validate passenger count
        and passenger_count between 1 and 6
        -- Remove zero-duration or negative-duration trips
        and tpep_dropoff_datetime > tpep_pickup_datetime

),

deduplicated as (

    -- Remove exact duplicate rows (idempotent re-runs)
    select distinct * from cleaned

)

select * from deduplicated
