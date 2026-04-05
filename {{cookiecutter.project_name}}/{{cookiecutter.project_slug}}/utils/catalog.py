"""Unity Catalog naming utilities.

Catalog naming patterns
-----------------------
  Per-environment (recommended long-term):
    {prefix}_{env}          → mdp_dev, mdp_test, mdp_prod

  Per-layer (current infrastructure):
    {prefix}_{env}_{suffix}  → mdp_dev_bronze, mdp_test_bronze, mdp_prod_bronze

The constants below are baked in at project creation from cookiecutter variables.
They can be overridden at call time, or changed here when the infrastructure evolves.

Migration path: once catalogs are renamed from mdp_dev_bronze → mdp_dev,
set CATALOG_SUFFIX = "" here (or re-generate the project with databricks_catalog_suffix="").
"""
from __future__ import annotations

# Baked-in defaults — set once at project creation, rarely changed.
CATALOG_PREFIX: str = "{{cookiecutter.databricks_catalog_prefix}}"
CATALOG_SUFFIX: str = "{{cookiecutter.databricks_catalog_suffix}}"
SCHEMA_PREFIX: str = "{{cookiecutter.databricks_schema_prefix}}"


def get_catalog(catalog_prefix: str, env: str, catalog_suffix: str = CATALOG_SUFFIX) -> str:
    """Return the Unity Catalog name for a given environment.

    Args:
        catalog_prefix: Org-level prefix, e.g. "mdp".
        env: Deployment environment: "dev", "test", or "prod".
        catalog_suffix: Optional layer suffix for per-layer catalog layouts.
                        Defaults to the project-level CATALOG_SUFFIX constant.
                        Pass "" to use the recommended per-environment pattern.

    Returns:
        "mdp_dev_bronze" when catalog_suffix="bronze" (current infra),
        "mdp_dev"        when catalog_suffix=""        (target pattern).
    """
    if catalog_suffix:
        return f"{catalog_prefix}_{env}_{catalog_suffix}"
    return f"{catalog_prefix}_{env}"


def get_schema(schema_prefix: str, layer: str) -> str:
    """Return the schema name for a given medallion layer.

    Args:
        schema_prefix: Domain/system identifier set at project creation,
                       e.g. "crm_dyn365", "npb_volunteering", "ipb_pims".
        layer: Medallion layer: "bronze", "silver", or "gold".

    Returns:
        Schema name, e.g. "crm_dyn365_bronze".
    """
    return f"{schema_prefix}_{layer}"


def get_table(
    catalog_prefix: str,
    env: str,
    schema_prefix: str,
    layer: str,
    table: str,
    catalog_suffix: str = CATALOG_SUFFIX,
) -> str:
    """Return the fully-qualified 3-level table path: {catalog}.{schema}.{table}.

    Args:
        catalog_prefix: Org-level prefix, e.g. "mdp".
        env: Deployment environment: "dev", "test", or "prod".
        schema_prefix: Domain/system identifier, e.g. "crm_dyn365".
        layer: Medallion layer: "bronze", "silver", or "gold".
        table: Table name, e.g. "contacts".
        catalog_suffix: Optional layer suffix (see get_catalog).

    Returns:
        Full table path, e.g.:
        "mdp_dev_bronze.crm_dyn365_bronze.contacts"  (current infra, suffix="bronze")
        "mdp_dev.crm_dyn365_bronze.contacts"         (target pattern, suffix="")

    Example:
        >>> get_table("mdp", "dev", "crm_dyn365", "bronze", "contacts")
        'mdp_dev_bronze.crm_dyn365_bronze.contacts'
    """
    catalog = get_catalog(catalog_prefix, env, catalog_suffix)
    schema = get_schema(schema_prefix, layer)
    return f"{catalog}.{schema}.{table}"
