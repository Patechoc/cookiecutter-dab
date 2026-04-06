# Data Contracts

Data contracts are YAML documents that describe the **schema**, **quality rules**,
and **SLA** for each table produced by this project. They serve as a shared
specification between data producers (this repo) and data consumers (dashboards,
downstream jobs, other teams).

## File layout

```
data-contracts/
├── bronze/
│   └── nyctaxi_trips.yml       # Raw ingestion table
├── silver/
│   └── nyctaxi_trips.yml       # Cleansed trips (nulls removed, duration derived)
└── gold/
    └── daily_trip_summary.yml  # Daily aggregation (one row per pickup date)
```

One contract file per table, organised by medallion layer.
When you add a new source entity, add a contract file alongside it.

## Contract structure

Each file follows a consistent structure:

```yaml
apiVersion: "datacontract/v1"
kind: DataContract

metadata:
  name: ...         # Unique identifier
  version: ...      # Semantic version — bump when schema changes
  status: ...       # draft | active | deprecated
  layer: ...        # bronze | silver | gold
  domain: ...       # Schema prefix (e.g. crm_dyn365)
  owner: ...        # Team or person responsible
  contact: ...      # Email

servers:
  dev:              # One entry per environment if they differ
    catalog_prefix: ...
    catalog_suffix: ...
    schema: ...
    table: ...
    write_mode: ...
    format: delta

schema:
  - name: column_name
    type: string | integer | long | double | date | timestamp | boolean
    nullable: true | false
    description: ...

quality:
  - rule: not_null | unique | value_between | value_above | row_count_above | ...
    columns: [...]   # or column: single_col
    severity: critical | warning

sla:
  freshness_hours: 25
  availability_percent: 99

tags: [...]
```

## Enforcing contracts

These YAML files are documentation by default.
To enforce them at runtime, plug them into a data quality framework:

| Tool | How to integrate |
|---|---|
| [Great Expectations](https://docs.greatexpectations.io/) | Generate an Expectation Suite from `quality` rules; run as a DAB notebook task |
| [Soda Core](https://docs.soda.io/) | Map `quality` rules to Soda checks in `checks.yml` |
| [dbt tests](https://docs.getdbt.com/docs/build/data-tests) | Translate `quality` rules into dbt schema tests in `_schema.yml` |

The `quality.rule` names in this project intentionally map to Great Expectations
expectation names (e.g. `not_null` → `expect_column_values_to_not_be_null`).

## Versioning

- Bump `metadata.version` whenever the schema changes (new columns, type changes).
- Set `status: deprecated` before removing a table — give consumers time to adapt.
- Breaking changes (column removals, type narrowing) should be coordinated with
  consumers before merging.

## Adding a contract for a new table

1. Create `data-contracts/<layer>/<table_name>.yml` following the structure above.
2. Fill in all columns from your Python/dbt model output.
3. Add quality rules for each nullable: false column.
4. Set a realistic `sla.freshness_hours` based on the job schedule in `resources/jobs/`.
5. Bump the contract `version` when the schema evolves.
