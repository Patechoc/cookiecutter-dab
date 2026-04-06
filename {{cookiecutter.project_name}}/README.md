# {{cookiecutter.project_name}}

{{cookiecutter.project_description}}
{% if cookiecutter.databricks_asset_bundle == 'y' %}
This repository contains a **Databricks Asset Bundle (DAB)** implementing a medallion
pipeline (Bronze → Silver → Gold) in Unity Catalog, with both Python notebook tasks
and native `dbt_task` transformations.
{% endif %}

## Getting started

### 1. Create the repository in Azure DevOps

```bash
git init -b main
git add .
git commit -m "init: generated from cookiecutter-dab"
git remote add origin <your-azure-devops-repo-url>
git push -u origin main
```

### 2. Install the development environment

```bash
make install
```

Runs `uv sync` and installs pre-commit hooks.

{% if cookiecutter.databricks_asset_bundle == 'y' %}

### 3. Configure local Databricks credentials

For local `databricks bundle` commands, set in your shell
(or use a `[DEFAULT]` profile in `~/.databrickscfg`):

```bash
export DATABRICKS_HOST=https://<your-workspace>.azuredatabricks.net
export DATABRICKS_TOKEN=<your-pat-or-service-principal-token>
```

Validate the bundle:

```bash
make bundle-validate
```

### 4. Configure dbt credentials

```bash
cp dbt/.env.example dbt/.env
# Fill in DBT_DATABRICKS_HOST_DEV, DBT_DATABRICKS_HTTP_PATH_DEV, DBT_DATABRICKS_TOKEN_DEV
source dbt/.env
```

`dbt/profiles.yml` is version-controlled (uses `env_var()` only — no secrets).
Never commit `.env`.

### 5. Deploy to DEV

```bash
make bundle-deploy-dev
```

Builds the Python wheel and deploys all jobs to your DEV Databricks workspace.

---

## Project structure

```text
{{cookiecutter.project_slug}}/
├── bronze/ingest.py        # Raw ingestion — reads source, writes bronze Delta table
├── silver/transform.py     # Cleansing — drops nulls, validates, derives columns
├── gold/aggregate.py       # Aggregation — daily summaries for dashboards
└── utils/catalog.py        # Unity Catalog naming helpers

notebooks/                  # Thin Databricks notebooks — call the Python package
dbt/models/                 # dbt SQL equivalents of silver and gold transforms
resources/jobs/             # Job YAML files (bronze, silver, gold, dbt, unit_tests)
azuredevops/                # CI/CD pipelines (ci.yml, cd_deploy.yml, cd_destroy.yml)
```

## Catalog and schema names

| Layer | Table path |
| --- | --- |
| Bronze | `{{cookiecutter.databricks_catalog_prefix}}_<env>{% if cookiecutter.databricks_catalog_suffix %}_{{cookiecutter.databricks_catalog_suffix}}{% endif %}.{{cookiecutter.databricks_schema_prefix}}_bronze.<table>` |
| Silver | `{{cookiecutter.databricks_catalog_prefix}}_<env>{% if cookiecutter.databricks_catalog_suffix %}_{{cookiecutter.databricks_catalog_suffix}}{% endif %}.{{cookiecutter.databricks_schema_prefix}}_silver.<table>` |
| Gold | `{{cookiecutter.databricks_catalog_prefix}}_<env>{% if cookiecutter.databricks_catalog_suffix %}_{{cookiecutter.databricks_catalog_suffix}}{% endif %}.{{cookiecutter.databricks_schema_prefix}}_gold.<table>` |

When the infrastructure migrates to per-environment catalogs, set `CATALOG_SUFFIX = ""`
in `{{cookiecutter.project_slug}}/utils/catalog.py`.

## Running jobs in DEV

```bash
make bundle-run-bronze    # run bronze ingestion immediately (bypasses schedule)
make bundle-run-silver    # run silver transform immediately
make bundle-run-gold      # run gold aggregation immediately
make bundle-run-dbt       # run dbt silver + gold immediately
```

## CI/CD pipelines

| Pipeline | File | Trigger |
| --- | --- | --- |
| CI | `azuredevops/ci.yml` | Every pull request targeting `main` |
| CD deploy | `azuredevops/cd_deploy.yml` | Every merge to `main` |
| CD destroy | `azuredevops/cd_destroy.yml` | Manual only |

CD deploy runs DEV and TEST automatically, then waits for manual approval before PROD.

**One-time ADO setup:**

1. Service connection `nrx-azure-service-connection` with Key Vault access.
2. ADO Environments: `databricks-dev`, `databricks-test`, `databricks-prod`.
   Add an approval check on `databricks-prod`.
3. Key Vaults must expose: `DATABRICKS-HOST`, `DATABRICKS-CLIENT-ID`, `DATABRICKS-CLIENT-SECRET`.

{% if cookiecutter.data_contracts == 'y' %}

## Data contracts

Schema, quality rules, and SLA definitions for each table:

```text
data-contracts/
├── bronze/nyctaxi_trips.yml
├── silver/nyctaxi_trips.yml
└── gold/daily_trip_summary.yml
```

Quality rules map to Great Expectations expectations — see `data-contracts/README.md`.

{% endif %}

{% else %}

### 3. Run the tests

```bash
make test
```

{% endif %}

---

## Running tests

```bash
make test
```

{% if cookiecutter.databricks_asset_bundle == 'y' %}
Tests run locally with a PySpark `local[1]` session — no Databricks cluster required.

| Test file | What it tests |
| --- | --- |
| `tests/test_catalog.py` | Catalog/schema/table name assembly — pure Python |
| `tests/bronze/test_ingest.py` | Bronze I/O with mocked SparkSession |
| `tests/silver/test_transform.py` | Silver logic with real DataFrames (nulls, filters, dedup) |

{% endif %}

## Releasing a new version

```bash
make release VERSION=X.Y.Z
```

Bumps `pyproject.toml`, updates `CHANGELOG.md` via `git-cliff`, commits, tags, and pushes.
{% if cookiecutter.databricks_asset_bundle == 'y' %}
After tagging, the CD pipeline deploys to PROD on the next merge, or run manually:

```bash
make bundle-deploy-prod
```

{% endif %}
