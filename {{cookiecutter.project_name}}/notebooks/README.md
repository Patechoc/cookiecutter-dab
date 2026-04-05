# Notebooks and dbt — Demo Pipeline

This directory contains the **Databricks notebook entrypoints** for the
`{{cookiecutter.project_slug}}` bundle.

The project also includes a **dbt project** (`dbt/`) that implements the same
silver and gold transformations in SQL. Both approaches are shown side-by-side
so you can understand their trade-offs and choose what fits your team.

---

## Notebooks vs dbt — when to use which

| Situation                              | Use notebooks (Python)                          | Use dbt (SQL)                                              |
|----------------------------------------|-------------------------------------------------|------------------------------------------------------------|
| **Raw ingestion** (bronze)             | Yes — reading files, APIs, JDBC                 | Not applicable — dbt reads from existing tables            |
| **Complex transformations**            | Yes — ML models, UDFs, pandas, custom libraries | No                                                         |
| **Schema-on-read, nested JSON, binary**| Yes — Python handles this naturally             | Hard to do cleanly in SQL                                  |
| **Simple cleansing and filtering**     | Works, but verbose                              | Yes — SQL is concise and readable                          |
| **Aggregations and business metrics**  | Works, but SQL is more natural                  | Yes — GROUP BY is what SQL is built for                    |
| **Data lineage and documentation**     | Manual                                          | Built-in — `dbt docs generate` produces a full catalogue   |
| **Column-level data tests**            | Write them in pytest                            | Built-in — `not_null`, `unique`, `accepted_values`         |
| **Your team speaks SQL**               | Extra translation layer                         | Yes — analysts can read and contribute to dbt models       |
| **Your team speaks Python**            | Yes — no context switching                      | Needs SQL knowledge                                        |

### The rule of thumb

> **Notebooks for ingestion and Python-heavy work. dbt for SQL transformations.**

A common pattern is:

- Bronze layer → **notebook** (Python: raw ingestion from source systems)
- Silver layer → **dbt** (SQL: cleansing, filtering, type-casting)
- Gold layer → **dbt** (SQL: aggregations, business metrics)

Or for projects with complex transformations:

- Bronze → **notebook**
- Silver → **notebook** (Python UDFs, complex logic)
- Gold → **dbt** (final aggregations for reporting)

They are not mutually exclusive: a job can have a notebook task followed by a
dbt task in the same DAB job definition.

---

## Demo pipeline: NYC Taxi Trips

The bundled example uses `samples.nyctaxi.trips`, available in **every
Databricks workspace** without any setup.

### Data flow — two parallel paths

```text
samples.nyctaxi.trips   (built-in Databricks dataset)
        |
        v  [bronze notebook job — Python only, no dbt alternative]
{catalog}.{{cookiecutter.databricks_schema_prefix}}_bronze.nyctaxi_trips
        |
        +------- Python path (notebook jobs) -------+------- dbt path (SQL) --------+
        |                                           |                               |
        v  [silver notebook]                        v  [dbt run]                    |
  _silver.nyctaxi_trips (Python)            _silver.nyctaxi_trips_clean (dbt)      |
        |                                           |                               |
        v  [gold notebook]                          v  [dbt run]                    |
  _gold.daily_trip_summary (Python)         _gold.daily_trip_summary (dbt)  <------+
```

Both paths produce the same `daily_trip_summary` output. The demo keeps both
so you can compare them directly. In a real project you would pick one.

`{catalog}` resolves from the DAB `catalog_name` variable, e.g.:

- `{{cookiecutter.databricks_catalog_prefix}}_dev_{{cookiecutter.databricks_catalog_suffix}}` (current infrastructure)
- `{{cookiecutter.databricks_catalog_prefix}}_dev` (future per-env catalogs)

### What each step does

| Step            | Tool     | File                                                                          | What it does                                                          |
|-----------------|----------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Bronze          | Notebook | `bronze/{{cookiecutter.databricks_schema_prefix}}_to_bronze.py`               | Reads `samples.nyctaxi.trips`, appends raw records unchanged          |
| Silver (Python) | Notebook | `silver/{{cookiecutter.databricks_schema_prefix}}_bronze_to_silver.py`        | Drops nulls, validates passengers, derives `trip_duration_minutes`    |
| Silver (SQL)    | dbt      | `dbt/models/silver/nyctaxi_trips_clean.sql`                                   | Same logic in pure SQL, with built-in dbt column tests                |
| Gold (Python)   | Notebook | `gold/{{cookiecutter.databricks_schema_prefix}}_silver_to_gold.py`            | Groups by date, computes trip metrics                                 |
| Gold (SQL)      | dbt      | `dbt/models/gold/daily_trip_summary.sql`                                      | Same aggregation in SQL, reads silver via `ref()`                     |

### Gold output schema

The final `daily_trip_summary` table (produced by either path):

| Column                    | Type   | Description                              |
|---------------------------|--------|------------------------------------------|
| `pickup_date`             | date   | Calendar date of pickup                  |
| `total_trips`             | long   | Number of completed trips that day       |
| `avg_fare_usd`            | double | Average fare amount (USD)                |
| `avg_trip_distance_miles` | double | Average trip distance (miles)            |
| `avg_duration_minutes`    | double | Average trip duration (minutes)          |
| `total_passengers`        | long   | Total passengers carried                 |

---

## Running the demo

### Notebook path (Python)

```bash
# 1. Fill in workspace URL in databricks.yml (replace the TODO comment)
# 2. Authenticate
databricks auth login

# 3. Deploy
databricks bundle deploy --target dev_personal

# 4. Run in order: bronze first, then silver, then gold
databricks bundle run bronze_ingestion --target dev_personal
databricks bundle run silver_transform --target dev_personal
databricks bundle run gold_aggregate   --target dev_personal
```

### dbt path (SQL)

**One-time setup:**

```bash
# 1. Install dbt-databricks
uv add --dev dbt-databricks

# 2. Set up credentials — copy the example file and fill in your values.
#    dbt/.env is gitignored and will never be committed.
cp dbt/.env.example dbt/.env
# Edit dbt/.env: paste your workspace URL, SQL warehouse HTTP path, and access token.

# 3. Load the environment (or use direnv to do this automatically)
source dbt/.env
#    DBT_PROFILES_DIR=./dbt is set in .env, so dbt uses dbt/profiles.yml
#    instead of the default ~/.dbt/profiles.yml.
```

> **Security reminder:** `dbt/profiles.yml` is safe to commit because it contains
> only `env_var()` references, never actual credentials. Keep all secrets in
> `dbt/.env` (gitignored). Never hardcode tokens or passwords in `profiles.yml`.

**Run the demo:**

```bash
# Run bronze notebook first — dbt cannot ingest from external sources
databricks bundle run bronze_ingestion --target dev_personal

# Run dbt models — dbt resolves silver-before-gold order automatically
dbt run --target dev

# Run built-in column tests (not_null, unique, accepted_values)
dbt test --target dev

# Generate and browse the data catalogue (lineage + column docs)
dbt docs generate --target dev
dbt docs serve
```

### Unit tests locally (no cluster needed)

```bash
uv run pytest tests/ -v
```

The Python `transform()` and `aggregate()` functions are tested with a local
SparkSession. dbt models are tested via `dbt test` against the real workspace.

---

## dbt project layout

```text
dbt/
├── dbt_project.yml              # Project config: name, profile, materialisations
├── profiles.yml                 # Connection config using env_var() — safe to commit
├── .env.example                 # Template showing which env vars to set — safe to commit
├── .env                         # Your actual credentials — gitignored, never committed
└── models/
    ├── sources.yml              # Declares the bronze layer as a dbt source
    ├── silver/
    │   ├── schema.yml           # Column descriptions + built-in data tests
    │   └── nyctaxi_trips_clean.sql
    └── gold/
        ├── schema.yml
        └── daily_trip_summary.sql
```

**`profiles.yml` is safe to commit** because it only contains `env_var()` calls —
no credentials. The actual secrets live in `dbt/.env` which is listed in `.gitignore`.

Why project-local `profiles.yml` instead of `~/.dbt/profiles.yml`?

- Every developer gets the correct connection config immediately after cloning.
- No manual copy-paste of a sample file.
- The profile is version-controlled alongside the code it connects to.
- `DBT_PROFILES_DIR=./dbt` in `.env.example` tells dbt where to find it.

---

## Adapting to your project

1. **Bronze always stays as a notebook** — dbt cannot connect to external sources
   directly; it needs data to already be in a Delta table.

2. **Replace the silver dbt model** with your own cleansing SQL. The
   `{% raw %}{{ source('bronze', 'nyctaxi_trips') }}{% endraw %}` reference points at your bronze
   table as declared in `models/sources.yml`.

3. **Replace the gold dbt model** with your own business aggregations. Use
   `{% raw %}{{ ref('your_silver_model') }}{% endraw %}` to reference the silver model — dbt resolves
   the execution order automatically.

4. **Add dbt tests** in `models/silver/schema.yml` and `models/gold/schema.yml`
   to validate your data at each layer. Tests run with `dbt test`.

5. **Remove the Python silver/gold jobs** if you commit to the dbt path (or
   vice versa). Running both is fine for comparison but redundant in production.
