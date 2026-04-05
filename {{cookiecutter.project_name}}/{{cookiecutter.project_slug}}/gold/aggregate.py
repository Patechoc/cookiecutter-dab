"""Gold layer: daily NYC taxi trip summary.

Demo implementation
-------------------
This module reads from the silver ``nyctaxi_trips`` table (populated by the
silver job) and produces a daily summary table in the gold layer.

Gold contract
-------------
The output table ``daily_trip_summary`` contains one row per calendar day:

| Column                   | Type    | Description                              |
|--------------------------|---------|------------------------------------------|
| pickup_date              | date    | Calendar date of the trip pickup         |
| total_trips              | long    | Number of completed trips                |
| avg_fare_usd             | double  | Average fare amount (USD)                |
| avg_trip_distance_miles  | double  | Average trip distance (miles)            |
| avg_duration_minutes     | double  | Average trip duration (minutes)          |
| total_passengers         | long    | Total passengers carried                 |

Result is written in **overwrite** mode — gold is always a full recomputation
from silver. This keeps gold tables simple to reason about and re-runnable.

When adapting to a real project, replace ``aggregate()`` with your own
business-level aggregations and rename the output table accordingly.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from {{cookiecutter.project_slug}}.utils.catalog import CATALOG_PREFIX, CATALOG_SUFFIX, SCHEMA_PREFIX, get_table

SOURCE_TABLE = "nyctaxi_trips"
TARGET_TABLE = "daily_trip_summary"


def read_silver(spark: SparkSession, env: str) -> DataFrame:
    """Read cleansed NYC taxi trips from the silver layer.

    Args:
        spark: Active SparkSession.
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).

    Returns:
        Cleansed DataFrame from the silver table.
    """
    source = get_table(CATALOG_PREFIX, env, SCHEMA_PREFIX, "silver", SOURCE_TABLE, CATALOG_SUFFIX)
    return spark.read.table(source)


def aggregate(df: DataFrame) -> DataFrame:
    """Compute a daily trip summary from silver trip records.

    Groups by pickup date and aggregates key metrics. The result is one row
    per calendar day and is suitable for dashboards and reports.

    Args:
        df: Cleansed DataFrame from the silver layer.

    Returns:
        Aggregated daily summary DataFrame.
    """
    return (
        df
        .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
        .groupBy("pickup_date")
        .agg(
            F.count("*").alias("total_trips"),
            F.round(F.avg("fare_amount"), 2).alias("avg_fare_usd"),
            F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance_miles"),
            F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration_minutes"),
            F.sum("passenger_count").cast("long").alias("total_passengers"),
        )
        .orderBy("pickup_date")
    )


def write_gold(df: DataFrame, env: str) -> None:
    """Overwrite the gold daily summary table.

    Args:
        df: Aggregated daily summary DataFrame.
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    target = get_table(CATALOG_PREFIX, env, SCHEMA_PREFIX, "gold", TARGET_TABLE, CATALOG_SUFFIX)
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target)
    )


def run(spark: SparkSession, env: str) -> None:
    """Entry point called from the gold notebook.

    Args:
        spark: Active SparkSession (injected by Databricks at runtime).
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    df = read_silver(spark, env)
    df = aggregate(df)
    write_gold(df, env)
