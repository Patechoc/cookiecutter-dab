# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # Silver: `{{cookiecutter.databricks_schema_prefix}}_bronze` → `{{cookiecutter.databricks_schema_prefix}}_silver`
# MAGIC
# MAGIC **Source table:** `${var.catalog_name}.{{cookiecutter.databricks_schema_prefix}}_bronze.nyctaxi_trips`
# MAGIC
# MAGIC **Target table:** `${var.catalog_name}.{{cookiecutter.databricks_schema_prefix}}_silver.nyctaxi_trips`
# MAGIC
# MAGIC Transformations applied (see `{{cookiecutter.project_slug}}/silver/transform.py`):
# MAGIC - Drop rows with null fare, distance, or timestamps
# MAGIC - Keep only trips with 1–6 passengers
# MAGIC - Derive `trip_duration_minutes` from pickup/dropoff timestamps (dropoff - pickup)
# MAGIC - Deduplicate on full row
# MAGIC
# MAGIC This notebook is a **thin wrapper** — all logic lives in the Python wheel and is
# MAGIC unit-testable locally without a cluster.
# MAGIC
# MAGIC See `notebooks/README.md` for a full walkthrough of the demo pipeline.

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Environment (dev / test / prod)")
env = dbutils.widgets.get("env")

# COMMAND ----------

from {{cookiecutter.project_slug}}.silver.transform import run

run(spark, env)
