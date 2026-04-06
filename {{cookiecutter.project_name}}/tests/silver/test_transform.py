"""Unit tests for the silver transformation logic.

Strategy
--------
``transform()`` is pure Spark logic with no I/O — it takes a DataFrame and
returns a DataFrame. These tests create in-memory DataFrames with controlled
data and assert on the output.

``read_bronze`` and ``write_silver`` perform Unity Catalog I/O and are mocked
in the ``run()`` integration test.

NYC taxi columns used by transform():
  tpep_pickup_datetime   — timestamp
  tpep_dropoff_datetime  — timestamp
  fare_amount            — double (nullable)
  trip_distance          — double (nullable)
  passenger_count        — integer
"""
{% if cookiecutter.databricks_asset_bundle == 'y' -%}
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from pyspark.sql import Row, SparkSession
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from {{cookiecutter.project_slug}}.silver.transform import transform


# ── Helpers ────────────────────────────────────────────────────────────────────

# Minimal schema matching the columns transform() actually touches.
TRIP_SCHEMA = StructType([
    StructField("tpep_pickup_datetime", TimestampType(), nullable=True),
    StructField("tpep_dropoff_datetime", TimestampType(), nullable=True),
    StructField("fare_amount", DoubleType(), nullable=True),
    StructField("trip_distance", DoubleType(), nullable=True),
    StructField("passenger_count", IntegerType(), nullable=True),
    # Extra columns that transform() must pass through unchanged.
    StructField("vendor_name", StringType(), nullable=True),
])

# A valid baseline trip: 15 min, 2 miles, $12.50, 2 passengers.
VALID_TRIP = Row(
    tpep_pickup_datetime=datetime(2023, 1, 15, 8, 0, 0),
    tpep_dropoff_datetime=datetime(2023, 1, 15, 8, 15, 0),
    fare_amount=12.50,
    trip_distance=2.0,
    passenger_count=2,
    vendor_name="CMT",
)


def make_df(spark: SparkSession, rows: list[Row]):
    return spark.createDataFrame(rows, TRIP_SCHEMA)


# ── Null filtering ─────────────────────────────────────────────────────────────

class TestNullFiltering:
    def test_drops_null_fare(self, spark):
        rows = [
            Row(**{**VALID_TRIP.asDict(), "fare_amount": None}),
            VALID_TRIP,
        ]
        result = transform(make_df(spark, rows))
        assert result.count() == 1
        assert result.first()["fare_amount"] == 12.50

    def test_drops_null_trip_distance(self, spark):
        rows = [
            Row(**{**VALID_TRIP.asDict(), "trip_distance": None}),
            VALID_TRIP,
        ]
        result = transform(make_df(spark, rows))
        assert result.count() == 1

    def test_drops_null_pickup_datetime(self, spark):
        rows = [
            Row(**{**VALID_TRIP.asDict(), "tpep_pickup_datetime": None}),
            VALID_TRIP,
        ]
        result = transform(make_df(spark, rows))
        assert result.count() == 1

    def test_drops_null_dropoff_datetime(self, spark):
        rows = [
            Row(**{**VALID_TRIP.asDict(), "tpep_dropoff_datetime": None}),
            VALID_TRIP,
        ]
        result = transform(make_df(spark, rows))
        assert result.count() == 1

    def test_keeps_row_with_all_fields_present(self, spark):
        result = transform(make_df(spark, [VALID_TRIP]))
        assert result.count() == 1


# ── Passenger count filter ─────────────────────────────────────────────────────

class TestPassengerFilter:
    @pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 6])
    def test_keeps_valid_passenger_counts(self, spark, count):
        row = Row(**{**VALID_TRIP.asDict(), "passenger_count": count})
        result = transform(make_df(spark, [row]))
        assert result.count() == 1

    @pytest.mark.parametrize("count", [0, 7, 8, -1])
    def test_drops_invalid_passenger_counts(self, spark, count):
        row = Row(**{**VALID_TRIP.asDict(), "passenger_count": count})
        result = transform(make_df(spark, [row]))
        assert result.count() == 0


# ── Trip duration derivation ───────────────────────────────────────────────────

class TestTripDurationDerivation:
    def test_duration_added_as_column(self, spark):
        result = transform(make_df(spark, [VALID_TRIP]))
        assert "trip_duration_minutes" in result.columns

    def test_duration_is_correct(self, spark):
        # VALID_TRIP: 08:00 → 08:15 = 15 minutes exactly.
        result = transform(make_df(spark, [VALID_TRIP]))
        assert result.first()["trip_duration_minutes"] == pytest.approx(15.0, abs=0.1)

    def test_duration_rounded_to_two_decimals(self, spark):
        # 08:00 → 08:17:23 = 17 min 23 s = 17.383... min, should round to 17.38
        row = Row(**{
            **VALID_TRIP.asDict(),
            "tpep_pickup_datetime": datetime(2023, 1, 15, 8, 0, 0),
            "tpep_dropoff_datetime": datetime(2023, 1, 15, 8, 17, 23),
        })
        result = transform(make_df(spark, [row]))
        duration = result.first()["trip_duration_minutes"]
        # Should be rounded to 2 decimal places
        assert duration == round(duration, 2)

    def test_zero_or_negative_duration_dropped(self, spark):
        # Pickup == dropoff → 0 minutes → should be filtered out.
        row = Row(**{
            **VALID_TRIP.asDict(),
            "tpep_pickup_datetime": datetime(2023, 1, 15, 8, 0, 0),
            "tpep_dropoff_datetime": datetime(2023, 1, 15, 8, 0, 0),
        })
        result = transform(make_df(spark, [row]))
        assert result.count() == 0


# ── Deduplication ──────────────────────────────────────────────────────────────

class TestDeduplication:
    def test_exact_duplicates_are_removed(self, spark):
        result = transform(make_df(spark, [VALID_TRIP, VALID_TRIP, VALID_TRIP]))
        assert result.count() == 1

    def test_distinct_rows_all_kept(self, spark):
        row2 = Row(**{
            **VALID_TRIP.asDict(),
            "fare_amount": 20.0,
            "tpep_pickup_datetime": datetime(2023, 1, 15, 9, 0, 0),
            "tpep_dropoff_datetime": datetime(2023, 1, 15, 9, 30, 0),
        })
        result = transform(make_df(spark, [VALID_TRIP, row2]))
        assert result.count() == 2


# ── run() integration (I/O mocked) ────────────────────────────────────────────

class TestRun:
    def test_run_wires_read_transform_write(self, spark):
        """run() calls read_bronze → transform → write_silver in order."""
        mock_df = MagicMock()
        mock_transformed = MagicMock()

        with (
            patch("{{cookiecutter.project_slug}}.silver.transform.read_bronze", return_value=mock_df) as mock_read,
            patch("{{cookiecutter.project_slug}}.silver.transform.transform", return_value=mock_transformed) as mock_tx,
            patch("{{cookiecutter.project_slug}}.silver.transform.write_silver") as mock_write,
        ):
            from {{cookiecutter.project_slug}}.silver.transform import run
            run(spark, "dev")

        mock_read.assert_called_once_with(spark, "dev")
        mock_tx.assert_called_once_with(mock_df)
        mock_write.assert_called_once_with(mock_transformed, "dev")
{%- endif %}
