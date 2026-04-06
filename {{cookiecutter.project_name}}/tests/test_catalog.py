"""Unit tests for Unity Catalog naming utilities.

These tests are pure Python — no SparkSession required.
They verify that catalog, schema, and table names are assembled correctly
for both the current per-layer layout (suffix set) and the target
per-environment layout (empty suffix).
"""
{% if cookiecutter.databricks_asset_bundle == 'y' -%}
import pytest

from {{cookiecutter.project_slug}}.utils.catalog import get_catalog, get_schema, get_table


# ── get_catalog ────────────────────────────────────────────────────────────────

class TestGetCatalog:
    def test_with_suffix_returns_prefix_env_suffix(self):
        assert get_catalog("mdp", "dev", "bronze") == "mdp_dev_bronze"

    def test_with_suffix_test_env(self):
        assert get_catalog("mdp", "test", "gold") == "mdp_test_gold"

    def test_empty_suffix_returns_prefix_env(self):
        assert get_catalog("mdp", "dev", "") == "mdp_dev"

    def test_empty_suffix_prod(self):
        assert get_catalog("mdp", "prod", "") == "mdp_prod"

    def test_default_suffix_uses_project_constant(self):
        # The default comes from CATALOG_SUFFIX baked at project creation.
        # We just verify the function signature accepts two args (no suffix arg).
        result = get_catalog("mdp", "dev")
        assert result.startswith("mdp_dev")


# ── get_schema ─────────────────────────────────────────────────────────────────

class TestGetSchema:
    def test_bronze_layer(self):
        assert get_schema("crm_dyn365", "bronze") == "crm_dyn365_bronze"

    def test_silver_layer(self):
        assert get_schema("npb_volunteering", "silver") == "npb_volunteering_silver"

    def test_gold_layer(self):
        assert get_schema("ipb_pims", "gold") == "ipb_pims_gold"


# ── get_table ──────────────────────────────────────────────────────────────────

class TestGetTable:
    def test_full_path_with_suffix(self):
        result = get_table("mdp", "dev", "crm_dyn365", "bronze", "contacts", "bronze")
        assert result == "mdp_dev_bronze.crm_dyn365_bronze.contacts"

    def test_full_path_without_suffix(self):
        result = get_table("mdp", "prod", "crm_dyn365", "gold", "daily_summary", "")
        assert result == "mdp_prod.crm_dyn365_gold.daily_summary"

    def test_three_part_format(self):
        result = get_table("mdp", "test", "npb", "silver", "volunteers", "silver")
        parts = result.split(".")
        assert len(parts) == 3, f"Expected catalog.schema.table, got: {result}"

    def test_env_propagates_to_catalog(self):
        dev = get_table("mdp", "dev", "npb", "bronze", "trips", "bronze")
        prod = get_table("mdp", "prod", "npb", "bronze", "trips", "bronze")
        assert "dev" in dev
        assert "prod" in prod
        assert dev != prod

    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    def test_all_environments(self, env):
        result = get_table("mdp", env, "crm", "silver", "accounts", "silver")
        assert env in result
{%- endif %}
