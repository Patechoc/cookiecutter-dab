# resources/ — DAB Job Definitions

This directory contains the Databricks Asset Bundle **job definitions**.
Each `.yml` file is picked up automatically by `databricks.yml` via:

```yaml
include:
  - resources/**/*.yml
```

---

## Jobs

| File | Job name (in Databricks UI) | Purpose |
|---|---|---|
| `jobs/bronze_ingestion.yml` | `[<target>] {{cookiecutter.project_slug}} - Bronze Ingestion` | Ingests raw source data into the bronze layer |
| `jobs/silver_transform.yml` | `[<target>] {{cookiecutter.project_slug}} - Silver Transform` | Cleanses and conforms bronze data into silver |
| `jobs/gold_aggregate.yml` | `[<target>] {{cookiecutter.project_slug}} - Gold Aggregate` | Aggregates silver data into business-ready gold tables |
| `jobs/unit_tests.yml` | `[<target>] {{cookiecutter.project_slug}} - Unit Tests` | CI job: runs the pytest suite on a cluster |

The `[<target>]` prefix is added automatically by DAB (`${bundle.target}`),
so the same job definition produces distinct job names per deployment target —
e.g. `[dev_personal]`, `[release_{{cookiecutter.databricks_workspace_role}}_dev]`, `[release_{{cookiecutter.databricks_workspace_role}}_prod]`.

---

## Schedule and pause behaviour

| Target | Bronze / Silver / Gold | Unit tests |
|---|---|---|
| `dev_personal` | PAUSED (deploy, don't run on schedule) | PAUSED |
| `ci_{{cookiecutter.databricks_workspace_role}}_test` | PAUSED | PAUSED (triggered by CI pipeline) |
| `release_{{cookiecutter.databricks_workspace_role}}_dev` | PAUSED | PAUSED |
| `release_{{cookiecutter.databricks_workspace_role}}_test` | PAUSED | PAUSED |
| `release_{{cookiecutter.databricks_workspace_role}}_prod` | **ACTIVE** (scheduled) | PAUSED |

Pause status is controlled by `presets.trigger_pause_status` in `databricks.yml`.
The job definitions themselves declare `UNPAUSED` — the target presets override
this to `PAUSED` for everything except production.

---

## Cluster configuration

All jobs share the single-node cluster defined as a DAB variable in `databricks.yml`:

```yaml
variables:
  job_cluster_single_node:
    type: complex
    default:
      spark_version: ${var.spark_version}
      node_type_id: Standard_DS3_v2
      num_workers: 0
      data_security_mode: SINGLE_USER
      azure_attributes:
        availability: SPOT_WITH_FALLBACK_AZURE
```

To use a different cluster for a specific job, override `new_cluster` directly
in that job's task definition.

---

## How to scale: multiple tables and multiple data products

### Within this project — add tasks, not jobs

When this project ingests or transforms multiple source entities (tables, API
endpoints, files), add them as **tasks inside the existing job**, not as new
job files.

```yaml
# resources/jobs/bronze_ingestion.yml
tasks:
  - task_key: ingest_contacts       # first entity
    notebook_task: ...

  - task_key: ingest_accounts       # second entity — no dependency
    notebook_task: ...

  - task_key: ingest_activities     # third entity — depends on accounts
    depends_on:
      - task_key: ingest_accounts
    notebook_task: ...
```

**Why tasks, not separate job files?**

- All bronze entities in this project share the same schedule and cluster — no
  reason to fragment them.
- Task-level `depends_on` lets you express intra-project dependencies
  (e.g. activities reference accounts) cleanly.
- One job per layer gives a single view of all running/failed ingestions in the
  Databricks Jobs UI.
- Separate job files for each entity make schedule coordination hard and create
  unnecessary clutter.

### Across data products — one repo per product

Each data product (schema prefix) lives in its own repo with its own bundle.
The bundles are fully independent — separate deployments, separate schedules,
separate clusters.

```
crm-ingestion repo      →  bundle: crm_ingestion  →  schema: crm_dyn365_bronze/_silver/_gold
npb-analytics repo      →  bundle: npb_analytics  →  schema: npb_volunteering_bronze/_silver/_gold
ipb-pims repo           →  bundle: ipb_pims        →  schema: ipb_pims_bronze/_silver/_gold
```

Each repo is generated independently from this cookiecutter template with its
own `databricks_schema_prefix`. They all write to the same Unity Catalog
(`mdp_dev`, `mdp_test`, `mdp_prod`) but to distinct schemas — so there is no
collision and no need to coordinate their job definitions.

### Adding a new job type

If you genuinely need a new kind of job (e.g. a data quality check job, or a
one-off backfill job) that is separate from the bronze/silver/gold pipeline:

1. Create a new file `resources/jobs/my_job.yml`.
2. Run `databricks bundle validate --target dev_personal` to check for errors.
3. Run `databricks bundle deploy --target dev_personal` to deploy it.

No changes to `databricks.yml` are needed — the `include: resources/**/*.yml`
glob picks up new files automatically.
