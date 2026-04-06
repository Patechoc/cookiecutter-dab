"""Unit tests for the bronze ingestion module.

Strategy
--------
``read_source`` reads from a live Unity Catalog table (``samples.nyctaxi.trips``),
which is not available in local test environments. Both ``read_source`` and
``write_bronze`` are therefore mocked; the tests verify call signatures and
integration wiring rather than Spark logic.

The meaningful Spark logic (filtering, transforms, aggregations) lives in the
silver and gold layers and is tested there with actual DataFrames.
"""
{% if cookiecutter.databricks_asset_bundle == 'y' -%}
from unittest.mock import MagicMock, patch

from {{cookiecutter.project_slug}}.bronze.ingest import DEMO_SOURCE_TABLE, DEMO_TABLE, run


class TestReadSource:
    def test_reads_from_demo_source_table(self):
        """read_source delegates to spark.read.table with the expected source path."""
        # Use a MagicMock as spark — avoids patching PySpark's read property,
        # which returns a new DataFrameReader instance on every access.
        from {{cookiecutter.project_slug}}.bronze.ingest import read_source
        mock_spark = MagicMock()
        result = read_source(mock_spark)

        mock_spark.read.table.assert_called_once_with(DEMO_SOURCE_TABLE)
        assert result is mock_spark.read.table.return_value

    def test_source_table_constant(self):
        """The demo source table is the Databricks built-in nyctaxi dataset."""
        assert DEMO_SOURCE_TABLE == "samples.nyctaxi.trips"


class TestWriteBronze:
    def test_writes_to_correct_table(self):
        """write_bronze calls saveAsTable with a correctly constructed 3-part name."""
        mock_df = MagicMock()
        # Chain the write builder mocks
        mock_df.write.format.return_value = mock_df.write.format.return_value
        mock_df.write.format().mode.return_value = mock_df.write.format().mode.return_value
        mock_df.write.format().mode().option.return_value = mock_df.write.format().mode().option.return_value

        from {{cookiecutter.project_slug}}.bronze.ingest import write_bronze
        write_bronze(mock_df, "dev")

        # Verify the chain ends in saveAsTable
        final = mock_df.write.format().mode().option()
        final.saveAsTable.assert_called_once()
        table_name = final.saveAsTable.call_args[0][0]
        # Must contain the env, the layer, and the demo table name
        assert "dev" in table_name
        assert "bronze" in table_name
        assert DEMO_TABLE in table_name

    def test_write_uses_append_mode(self):
        """Bronze writes are append — raw records are never overwritten."""
        mock_df = MagicMock()
        from {{cookiecutter.project_slug}}.bronze.ingest import write_bronze
        write_bronze(mock_df, "dev")
        mock_df.write.format().mode.assert_called_once_with("append")


class TestRun:
    def test_run_calls_read_and_write(self, spark):
        """run() wires read_source → write_bronze end-to-end."""
        mock_df = MagicMock()
        with (
            patch("{{cookiecutter.project_slug}}.bronze.ingest.read_source", return_value=mock_df) as mock_read,
            patch("{{cookiecutter.project_slug}}.bronze.ingest.write_bronze") as mock_write,
        ):
            run(spark, "dev")

        mock_read.assert_called_once_with(spark)
        mock_write.assert_called_once_with(mock_df, "dev")
{%- endif %}
