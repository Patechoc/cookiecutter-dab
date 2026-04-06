"""Shared pytest fixtures.

The SparkSession fixture is only used by DAB tests (tests/bronze/, tests/silver/).
It runs in local mode — no cluster or Databricks workspace required.

Configuration choices:
  master="local[1]"               — single thread, deterministic and fast for unit tests
  shuffle.partitions=1            — avoid unnecessary shuffle overhead on tiny test data
  ui.enabled=false                — suppress the Spark web UI in test output
"""
{% if cookiecutter.databricks_asset_bundle == 'y' -%}
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Local SparkSession shared across all tests in the session.

    Session scope keeps startup cost (≈5–10 s) to a single hit per test run.
    The session is stopped automatically after all tests complete.
    """
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("{{cookiecutter.project_slug}}-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
{%- endif %}
