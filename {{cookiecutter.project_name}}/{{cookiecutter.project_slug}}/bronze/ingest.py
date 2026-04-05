"""Bronze layer: raw ingestion from source systems.

Demo implementation
-------------------
This module uses the built-in Databricks sample dataset ``samples.nyctaxi.trips``
as its source. That table is available in every Databricks workspace without any
setup, so the example runs end-to-end immediately after deploying the bundle.

When adapting this to your own project, replace ``read_source()`` with your
actual connector (ADLS files, JDBC, REST API, etc.) and update the table name
to match your source system.

Bronze contract
---------------
- Raw data is written **as received**, without transformations.
- Mode is **append** — every run adds new records.
- ``mergeSchema`` is enabled so source schema evolution does not break the job.
"""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from {{cookiecutter.project_slug}}.utils.catalog import CATALOG_PREFIX, CATALOG_SUFFIX, SCHEMA_PREFIX, get_table

# Name of the demo table written to the bronze layer.
DEMO_TABLE = "nyctaxi_trips"

# Source: built-in Databricks sample dataset, available in every workspace.
DEMO_SOURCE_TABLE = "samples.nyctaxi.trips"


def read_source(spark: SparkSession) -> DataFrame:
    """Read raw records from the source system.

    This demo reads from the Databricks built-in ``samples.nyctaxi.trips`` table.
    Replace with your actual source connector when adapting to a real project.

    Args:
        spark: Active SparkSession.

    Returns:
        Raw DataFrame as received from the source — no transformations applied.
    """
    return spark.read.table(DEMO_SOURCE_TABLE)


def write_bronze(df: DataFrame, env: str) -> None:
    """Append raw records to the bronze Delta table.

    Args:
        df: Raw DataFrame to persist.
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    target = get_table(CATALOG_PREFIX, env, SCHEMA_PREFIX, "bronze", DEMO_TABLE, CATALOG_SUFFIX)
    (
        df.write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(target)
    )


def run(spark: SparkSession, env: str) -> None:
    """Entry point called from the bronze notebook.

    Args:
        spark: Active SparkSession (injected by Databricks at runtime).
        env: Deployment environment (``"dev"``, ``"test"``, ``"prod"``).
    """
    df = read_source(spark)
    write_bronze(df, env)
