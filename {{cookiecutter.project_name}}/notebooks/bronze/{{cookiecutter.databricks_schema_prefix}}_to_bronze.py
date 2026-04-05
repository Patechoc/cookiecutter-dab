# Databricks notebook source
# COMMAND ----------

# MAGIC %md
# MAGIC # Bronze: ingest NYC taxi trips → `{{cookiecutter.databricks_schema_prefix}}_bronze`
# MAGIC
# MAGIC **Demo source:** `samples.nyctaxi.trips` (built-in Databricks dataset, no setup needed)
# MAGIC
# MAGIC **Target table:** `${var.catalog_name}.{{cookiecutter.databricks_schema_prefix}}_bronze.nyctaxi_trips`
# MAGIC
# MAGIC This notebook is a **thin wrapper** — it only sets the `env` parameter and calls
# MAGIC the `run()` function from the Python wheel. All business logic lives in:
# MAGIC ```
# MAGIC {{cookiecutter.project_slug}}/bronze/ingest.py
# MAGIC ```
# MAGIC which is fully unit-testable locally without a cluster.
# MAGIC
# MAGIC See `notebooks/README.md` for a full walkthrough of the demo pipeline.

# COMMAND ----------

dbutils.widgets.text("env", "dev", "Environment (dev / test / prod)")
env = dbutils.widgets.get("env")

# COMMAND ----------

from {{cookiecutter.project_slug}}.bronze.ingest import run

run(spark, env)
