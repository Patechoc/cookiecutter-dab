# cookiecutter-dab

A [cookiecutter](https://github.com/cookiecutter/cookiecutter) template for creating
**Databricks Asset Bundle (DAB)** Python projects at NRX / Norwegian Red Cross.

Generates a production-ready repository with a medallion pipeline (Bronze → Silver → Gold),
dbt models, Azure DevOps CI/CD pipelines, data contracts, and a full test suite — all
wired together with `databricks.yml` and ready to deploy in minutes.

---

## What gets generated

```text
<project-name>/
├── databricks.yml              # Bundle definition: targets, variables, job cluster
├── <project_slug>/
│   ├── bronze/ingest.py        # Raw ingestion (demo: samples.nyctaxi.trips)
│   ├── silver/transform.py     # Cleansing and conforming
│   ├── gold/aggregate.py       # Business-level aggregations
│   └── utils/catalog.py        # Unity Catalog naming helpers
├── notebooks/                  # Thin wrappers calling the Python package
├── dbt/
│   ├── models/silver/          # dbt SQL models (alternative to Python silver/gold)
│   ├── models/gold/
│   ├── profiles.yml            # Safe to commit — uses env_var() for secrets
│   └── .env.example            # Copy to .env, fill in credentials, never commit
├── resources/jobs/
│   ├── bronze_ingestion.yml    # Daily notebook job
│   ├── silver_transform.yml
│   ├── gold_aggregate.yml
│   ├── dbt_transformations.yml # Native dbt_task with serverless environment
│   └── unit_tests.yml          # CI unit test job (always paused)
├── azuredevops/
│   ├── ci.yml                  # PR: lint + pytest + bundle validate
│   ├── cd_deploy.yml           # Merge: DEV → TEST → PROD (manual gate on PROD)
│   ├── cd_destroy.yml          # Manual: destroy resources in one environment
│   └── templates/              # Reusable deploy/destroy steps
├── data-contracts/             # YAML contracts: schema, quality rules, SLA
├── tests/
│   ├── conftest.py             # Local SparkSession fixture (no cluster needed)
│   ├── test_catalog.py         # Pure Python catalog naming tests
│   ├── bronze/test_ingest.py   # Mocked I/O tests
│   └── silver/test_transform.py # Real Spark DataFrame transform tests
├── pyproject.toml              # databricks-sdk runtime + pyspark/pytest-mock dev
└── Makefile                    # bundle-validate / bundle-deploy-* / bundle-run-*
```

---

## Quickstart

The repository is hosted in Azure DevOps and requires authentication.
Before running the template, [create a Personal Access Token (PAT)](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate), [here
in Azure DevOps](https://dev.azure.com/RedCrossNorway/_usersSettings/tokens) with **Code (Read)** scope, then store it as an environment variable:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export ADO_TOKEN=<your-PAT>
```

Then run the template:

```bash
uvx cookiecutter "https://RedCrossNorway:${ADO_TOKEN}@dev.azure.com/RedCrossNorway/Data%20Warehouse/_git/cookiecutter-dab"
```

Or from a local clone:

```bash
uvx cookiecutter /path/to/cookiecutter-dab
```

Follow the prompts. Once generation completes:

```bash
cd <project-name>
make install          # uv sync + pre-commit hooks
make bundle-validate  # confirm the bundle parses cleanly
make bundle-deploy-dev
```

---

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `author` | `Firstname Lastname` | Your full name |
| `email` | `foo.bar@redcross.no` | Your email address |
| `author_github_handle` | `foobar` | GitHub username (used for doc links) |
| `project_name` | `npb-analytics` | Kebab-case repo name, e.g. `npb-analytics`, `ipb-pims` |
| `project_slug` | *(auto)* | Python package name — dashes replaced by underscores |
| `project_description` | *(auto)* | One-line description pre-filled from project_name |
| `layout` | `flat` | `flat` (package at root) or `src` (under `src/`) |
| `cicd_github_actions` | `n` | Add `.github/workflows/` |
| `cicd_azure_pipelines` | `y` | Add `azuredevops/` DAB CI/CD pipelines |
| `publish_to_pypi` | `n` | Add PyPI publish step |
| `deptry` | `y` | Unused/missing dependency checker |
| `mkdocs` | `y` | MkDocs documentation site |
| `codecov` | `y` | Codecov coverage reporting |
| `dockerfile` | `n` | Add a Dockerfile |
| `devcontainer` | `y` | VS Code Dev Container |
| `type_checker` | `ty` | `ty` (Astral, fast) or `mypy` (classic) |
| `open_source_license` | `Not open source` | License file; choose "Not open source" for internal projects |
| `databricks_asset_bundle` | `y` | Add DAB support — all Databricks files, pipelines, tests |
| `databricks_catalog_prefix` | `mdp` | Unity Catalog prefix, e.g. `mdp`, `nrx` |
| `databricks_catalog_suffix` | `bronze` | Layer suffix for per-layer catalogs (`mdp_dev_bronze`). Leave empty for per-environment catalogs (`mdp_dev`). |
| `databricks_schema_prefix` | `crm_dyn365` | Schema prefix for this project, e.g. `npb_volunteering`, `ipb_pims` |
| `databricks_workspace_role` | `in` | Suffix in DAB target names. `in` → `release_in_dev` (generic), `ip` → Ingestion Process, `da` → Data Applications |
| `databricks_default_spark_version` | `13.3.x-scala2.12` | Databricks Runtime version for job clusters |
| `databricks_workspace_host_dev` | *(NRX IP DEV URL)* | Databricks workspace URL for DEV — safe to commit |
| `databricks_workspace_host_test` | *(NRX IP TEST URL)* | Databricks workspace URL for TEST |
| `databricks_workspace_host_prod` | *(NRX IP PROD URL)* | Databricks workspace URL for PROD |
| `ado_service_connection_prefix` | `SC` | ADO service connection prefix — generates `SC-dev`, `SC-test`, `SC-prod` |
| `ado_keyvault_name_dev` | `kv-nrx-dev-dlz-di-euw` | Azure Key Vault for DEV credentials |
| `ado_keyvault_name_test` | `kv-nrx-test-dlz-di-euw` | Azure Key Vault for TEST credentials |
| `ado_keyvault_name_prod` | `kv-nrx-prod-dlz-di-euw` | Azure Key Vault for PROD credentials |
| `ado_agent_pool_dev` | `MDP-MPDAAS-SELFHOSTED-DEV` | Azure Pipelines self-hosted agent pool for DEV |
| `ado_agent_pool_test` | `MDP-MPDAAS-SELFHOSTED-TEST` | Azure Pipelines self-hosted agent pool for TEST |
| `ado_agent_pool_prod` | `MDP-MPDAAS-SELFHOSTED-PROD` | Azure Pipelines self-hosted agent pool for PROD |
| `ado_environment_dev` | `dev` | ADO Environment name for DEV |
| `ado_environment_test` | `test` | ADO Environment name for TEST |
| `ado_environment_prod` | `prod` | ADO Environment name for PROD (add approval check here) |
| `data_contracts` | `y` | Add `data-contracts/` YAML schema and quality contracts |

### Catalog naming

| `catalog_suffix` | Naming pattern | Example (dev) |
| --- | --- | --- |
| `bronze` (current default) | `{prefix}_{env}_{suffix}` | `mdp_dev_bronze` |
| *(empty)* | `{prefix}_{env}` | `mdp_dev` |

The per-layer suffix (`mdp_dev_bronze`) is a transitional pattern matching today's
infrastructure. Set `catalog_suffix=""` when catalogs are renamed to the per-environment
pattern (`mdp_dev`). The migration path is documented in `utils/catalog.py`.

---

## Architecture

Two transformation paths are included side-by-side so you can choose per entity:

```text
Source System
     │
     ▼  (bronze_ingestion job — notebook task + cluster)
 Bronze Delta table
     │
     ├──▶  (silver_transform job — notebook task)  ──▶  Silver Delta table
     │                                                        │
     │                                                        ▼  (gold_aggregate job)
     │                                                   Gold Delta table
     │
     └──▶  (dbt_transformations job — dbt_task + serverless warehouse)
               silver model  ──▶  gold model
```

| Path | Tool | When to use |
| --- | --- | --- |
| Python modules + notebooks | PySpark | Ingestion, Python-heavy logic, ML features |
| dbt SQL models | `dbt_task` (serverless) | Pure SQL transforms, lineage tracking, dbt tests |

See `notebooks/README.md` for the full comparison and decision guide.

---

## CI/CD

```text
Pull Request  ──▶  azuredevops/ci.yml
                     ├── Lint + pytest (local Spark, no cluster)
                     └── databricks bundle validate

Merge to main ──▶  azuredevops/cd_deploy.yml
                     ├── DEV  (automatic)
                     ├── TEST (automatic, depends on DEV)
                     └── PROD (manual approval gate)

Manual trigger ──▶  azuredevops/cd_destroy.yml
                     └── Destroy resources in chosen environment
```

### One-time ADO setup (per project)

These already exist in the NRX MDPaaS project — no new infrastructure required:

1. **Service connections** — `SC-dev`, `SC-test`, `SC-prod` (one per environment).
2. **ADO Environments** — `dev`, `test`, `prod`.
   The `prod` environment has an approval check already configured.
3. **Key Vault secrets** per environment (`databricks-sp-client-id`, `databricks-sp-secret`).
   Key Vaults: `kv-nrx-dev-dlz-di-euw` / `kv-nrx-test-dlz-di-euw` / `kv-nrx-prod-dlz-di-euw`.
4. **Agent pools** — `MDP-MPDAAS-SELFHOSTED-DEV` / `-TEST` / `-PROD`.

---

## Makefile reference

```bash
make install              # uv sync + pre-commit hooks
make check                # ruff + type checker + deptry
make test                 # pytest (local Spark, no cluster needed)

make bundle-validate      # validate bundle structure (no deployment)
make bundle-deploy-dev    # build wheel + deploy to DEV
make bundle-deploy-test   # build wheel + deploy to TEST
make bundle-deploy-prod   # build wheel + deploy to PROD
make bundle-destroy-dev   # destroy DEV resources (tables are NOT affected)

make bundle-run-bronze    # trigger bronze ingestion job in DEV immediately
make bundle-run-silver    # trigger silver transform job in DEV immediately
make bundle-run-gold      # trigger gold aggregation job in DEV immediately
make bundle-run-dbt       # trigger dbt transformations job in DEV immediately
```

---

## dbt credentials

`dbt/profiles.yml` is version-controlled because it only contains `env_var()` references.
Actual secrets live in `.env` (gitignored).

```bash
cp dbt/.env.example dbt/.env
# Fill in DBT_DATABRICKS_HOST_DEV, DBT_DATABRICKS_HTTP_PATH_DEV, DBT_DATABRICKS_TOKEN_DEV
source dbt/.env
dbt run --profiles-dir dbt --target dev
```

---

## Template development

```bash
# Run the template test suite (fast — no cluster, no installs)
uv run pytest tests/ -m "not slow"

# Run all tests including install + test runs of generated projects (slow)
uv run pytest tests/ --slow
```

---

## Acknowledgements

Based on [osprey-oss/cookiecutter-uv](https://github.com/osprey-oss/cookiecutter-uv),
extended with Databricks Asset Bundle support for the NRX Data Platform.
