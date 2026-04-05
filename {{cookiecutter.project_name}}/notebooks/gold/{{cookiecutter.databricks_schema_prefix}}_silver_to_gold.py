# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # Gold: `{{cookiecutter.databricks_schema_prefix}}_silver` -> `{{cookiecutter.databricks_schema_prefix}}_gold`
# MAGIC
# MAGIC **Source table:** `${var.catalog_name}.{{cookiecutter.databricks_schema_prefix}}_silver.nyctaxi_trips`
# MAGIC
# MAGIC **Target table:** `${var.catalog_name}.{{cookiecutter.databricks_schema_prefix}}_gold.daily_trip_summary`
# MAGIC
# MAGIC Aggregation applied (see `{{cookiecutter.project_slug}}/gold/aggregate.py`):
# MAGIC - Group by pickup date
# MAGIC - Compute: total trips, avg fare, avg distance, avg duration, total passengers
# MAGIC - Result is one row per calendar day — ready for dashboards and reports
# MAGIC
# MAGIC This notebook is a **thin wrapper** — all logic lives in the Python wheel and is
# MAGIC unit-testable locally without a cluster.
# MAGIC
# MAGIC See `notebooks/README.md` for a full walkthrough of the demo pipeline.

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Environment (dev / test / prod)")
env = dbutils.widgets.get("env")

# COMMAND ----------

from {{cookiecutter.project_slug}}.gold.aggregate import run

run(spark, env)
