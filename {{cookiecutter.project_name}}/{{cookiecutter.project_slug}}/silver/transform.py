"""Silver layer: cleansed and conformed NYC taxi trips.

Demo implementation
-------------------
This module reads from the bronze ``nyctaxi_trips`` table (populated by the
bronze job), applies cleaning rules, and writes to the silver layer.

Silver contract
---------------
- Rows with null fare, distance, or timestamps are dropped.
- Trip duration is derived (``trip_duration_minutes``).
- Passenger count is validated (must be 1–6).
- Result is written in **overwrite** mode — silver is a full refresh of clean data.

When adapting to a real project, replace the ``transform()`` logic with your
own cleansing rules and update the table name to match your source system.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from {{cookiecutter.project_slug}}.utils.catalog import CATALOG_PREFIX, CATALOG_SUFFIX, SCHEMA_PREFIX, get_table

DEMO_TABLE = "nyctaxi_trips"


def read_bronze(spark: SparkSession, env: str) -> DataFrame:
    """Read raw NYC taxi trips from the bronze layer.

    Args:
        spark: Active SparkSession.
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).

    Returns:
        Raw DataFrame from the bronze table.
    """
    source = get_table(CATALOG_PREFIX, env, SCHEMA_PREFIX, "bronze", DEMO_TABLE, CATALOG_SUFFIX)
    return spark.read.table(source)


def transform(df: DataFrame) -> DataFrame:
    """Cleanse and conform the raw NYC taxi trips.

    Rules applied:
    - Drop rows where fare, trip distance, pickup or dropoff time is null.
    - Keep only trips with 1–6 passengers (invalid entries removed).
    - Add ``trip_duration_minutes`` column (dropoff − pickup time).
    - Deduplicate on the full row (idempotent re-runs).

    Args:
        df: Raw DataFrame from the bronze layer.

    Returns:
        Cleansed and conformed DataFrame ready for the silver table.
    """
    return (
        df
        .dropna(subset=["fare_amount", "trip_distance", "tpep_pickup_datetime", "tpep_dropoff_datetime"])
        .filter(F.col("passenger_count").between(1, 6))
        .withColumn(
            "trip_duration_minutes",
            F.round(
                (F.unix_timestamp("tpep_dropoff_datetime") - F.unix_timestamp("tpep_pickup_datetime")) / 60,
                2,
            ),
        )
        .filter(F.col("trip_duration_minutes") > 0)
        .dropDuplicates()
    )


def write_silver(df: DataFrame, env: str) -> None:
    """Overwrite the silver Delta table with cleansed trip records.

    Args:
        df: Cleansed DataFrame.
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    target = get_table(CATALOG_PREFIX, env, SCHEMA_PREFIX, "silver", DEMO_TABLE, CATALOG_SUFFIX)
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target)
    )


def run(spark: SparkSession, env: str) -> None:
    """Entry point called from the silver notebook.

    Args:
        spark: Active SparkSession (injected by Databricks at runtime).
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    df = read_bronze(spark, env)
    df = transform(df)
    write_silver(df, env)
