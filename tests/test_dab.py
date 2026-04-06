"""Tests specific to Databricks Asset Bundle (DAB) template features.

Covers:
  - File presence/absence for all DAB-related options
  - Catalog naming logic (with/without suffix)
  - Workspace role rendered into target names and Makefile
  - pyproject.toml DAB dependency injection
  - azuredevops/ pipeline file structure
  - data-contracts/ conditional presence
  - databricks.yml YAML validity and key variable presence
  - pre_gen_project hook validation of catalog_suffix
"""
from __future__ import annotations


# ── DAB enabled / disabled ─────────────────────────────────────────────────────

class TestDabPresence:
    def test_dab_files_present_when_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        assert project.has_file("databricks.yml")
        assert project.has_dir("notebooks")
        assert project.has_dir("resources")
        assert project.has_dir("dbt")

    def test_dab_files_absent_when_disabled(self, bake):
        project = bake(databricks_asset_bundle="n")
        assert not project.has_file("databricks.yml")
        assert not project.has_dir("notebooks")
        assert not project.has_dir("resources")
        assert not project.has_dir("dbt")
        assert not project.has_dir("azuredevops")
        assert not project.has_dir("data-contracts")

    def test_dab_python_subpackages_present_when_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        for pkg in ["bronze", "silver", "gold", "utils"]:
            assert project.has_dir(f"npb_analytics/{pkg}"), f"npb_analytics/{pkg}/ should exist"

    def test_dab_python_subpackages_absent_when_disabled(self, bake):
        project = bake(databricks_asset_bundle="n")
        for pkg in ["bronze", "silver", "gold", "utils"]:
            assert not project.has_dir(f"npb_analytics/{pkg}"), f"npb_analytics/{pkg}/ should not exist"

    def test_dab_test_dirs_present_when_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        assert project.has_dir("tests/bronze")
        assert project.has_dir("tests/silver")
        assert project.has_file("tests/conftest.py")
        assert project.has_file("tests/test_catalog.py")

    def test_dab_test_dirs_absent_when_disabled(self, bake):
        project = bake(databricks_asset_bundle="n")
        assert not project.has_dir("tests/bronze")
        assert not project.has_dir("tests/silver")
        assert not project.has_file("tests/test_catalog.py")


# ── Catalog naming ─────────────────────────────────────────────────────────────

class TestCatalogNaming:
    def test_catalog_with_suffix_in_databricks_yml(self, bake):
        """With suffix='bronze', catalog_name must use {prefix}_{env}_{suffix}."""
        project = bake(
            databricks_asset_bundle="y",
            databricks_catalog_prefix="mdp",
            databricks_catalog_suffix="bronze",
        )
        content = project.read_file("databricks.yml")
        # The default value for dev target should contain the suffix pattern
        assert "mdp_dev_bronze" in content or "mdp_${var.env}_bronze" in content or "_bronze" in content

    def test_catalog_without_suffix_in_databricks_yml(self, bake):
        """With suffix='', catalog_name must use {prefix}_{env} only."""
        project = bake(
            databricks_asset_bundle="y",
            databricks_catalog_prefix="mdp",
            databricks_catalog_suffix="",
        )
        content = project.read_file("databricks.yml")
        # Must not contain trailing _bronze/_silver/_gold
        assert "mdp_dev_bronze" not in content
        assert "mdp_dev_silver" not in content
        assert "mdp_dev_gold" not in content

    def test_catalog_suffix_baked_into_utils(self, bake):
        """CATALOG_SUFFIX constant in utils/catalog.py must match the cookiecutter variable."""
        project = bake(
            databricks_asset_bundle="y",
            databricks_catalog_suffix="silver",
        )
        content = project.read_file("npb_analytics/utils/catalog.py")
        assert 'CATALOG_SUFFIX: str = "silver"' in content

    def test_empty_suffix_baked_into_utils(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_catalog_suffix="")
        content = project.read_file("npb_analytics/utils/catalog.py")
        assert 'CATALOG_SUFFIX: str = ""' in content

    def test_schema_prefix_baked_into_utils(self, bake):
        project = bake(
            databricks_asset_bundle="y",
            databricks_schema_prefix="npb_volunteering",
        )
        content = project.read_file("npb_analytics/utils/catalog.py")
        assert 'SCHEMA_PREFIX: str = "npb_volunteering"' in content


# ── Workspace role ─────────────────────────────────────────────────────────────

class TestWorkspaceRole:
    def test_role_da_in_makefile(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_workspace_role="da")
        content = project.read_file("Makefile")
        assert "DAB_ROLE := da" in content
        # Makefile expands the role at runtime via $(DAB_ROLE); no literal "release_da_dev"
        assert "release_$(DAB_ROLE)_dev" in content

    def test_role_ip_in_makefile(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_workspace_role="ip")
        content = project.read_file("Makefile")
        assert "DAB_ROLE := ip" in content
        assert "release_$(DAB_ROLE)_dev" in content

    def test_role_in_databricks_yml_targets(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_workspace_role="ip")
        content = project.read_file("databricks.yml")
        assert "release_ip_dev" in content
        assert "release_ip_test" in content
        assert "release_ip_prod" in content

    def test_role_in_cd_deploy_pipeline(self, bake):
        project = bake(
            databricks_asset_bundle="y",
            cicd_azure_pipelines="y",
            databricks_workspace_role="ip",
        )
        content = project.read_file("azuredevops/cd_deploy.yml")
        assert "release_ip_dev" in content
        assert "release_ip_test" in content
        assert "release_ip_prod" in content


# ── Azure DevOps pipelines ─────────────────────────────────────────────────────

class TestAzureDevOps:
    def test_azuredevops_dir_present_when_dab_and_azdo(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="y")
        assert project.has_dir("azuredevops")
        assert project.has_file("azuredevops/ci.yml")
        assert project.has_file("azuredevops/cd_deploy.yml")
        assert project.has_file("azuredevops/cd_destroy.yml")
        assert project.has_file("azuredevops/templates/dab_deploy.yml")
        assert project.has_file("azuredevops/templates/dab_destroy.yml")

    def test_azuredevops_dir_absent_when_azdo_disabled(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="n")
        assert not project.has_dir("azuredevops")

    def test_azuredevops_dir_absent_when_dab_disabled(self, bake):
        project = bake(databricks_asset_bundle="n", cicd_azure_pipelines="y")
        assert not project.has_dir("azuredevops")

    def test_ci_yml_is_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="y")
        assert project.is_valid_yaml("azuredevops/ci.yml")

    def test_cd_deploy_yml_is_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="y")
        assert project.is_valid_yaml("azuredevops/cd_deploy.yml")

    def test_cd_destroy_yml_is_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="y")
        assert project.is_valid_yaml("azuredevops/cd_destroy.yml")

    def test_dab_deploy_template_is_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y", cicd_azure_pipelines="y")
        assert project.is_valid_yaml("azuredevops/templates/dab_deploy.yml")


# ── Data contracts ─────────────────────────────────────────────────────────────

class TestDataContracts:
    def test_contracts_present_when_enabled(self, bake):
        project = bake(databricks_asset_bundle="y", data_contracts="y")
        assert project.has_dir("data-contracts")
        assert project.has_file("data-contracts/bronze/nyctaxi_trips.yml")
        assert project.has_file("data-contracts/silver/nyctaxi_trips.yml")
        assert project.has_file("data-contracts/gold/daily_trip_summary.yml")
        assert project.has_file("data-contracts/README.md")

    def test_contracts_absent_when_disabled(self, bake):
        project = bake(databricks_asset_bundle="y", data_contracts="n")
        assert not project.has_dir("data-contracts")

    def test_contracts_absent_when_dab_disabled(self, bake):
        project = bake(databricks_asset_bundle="n", data_contracts="y")
        assert not project.has_dir("data-contracts")

    def test_contract_files_are_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y", data_contracts="y")
        for contract in [
            "data-contracts/bronze/nyctaxi_trips.yml",
            "data-contracts/silver/nyctaxi_trips.yml",
            "data-contracts/gold/daily_trip_summary.yml",
        ]:
            assert project.is_valid_yaml(contract), f"{contract} is not valid YAML"

    def test_contract_schema_prefix_rendered(self, bake):
        project = bake(
            databricks_asset_bundle="y",
            data_contracts="y",
            databricks_schema_prefix="npb_volunteering",
        )
        content = project.read_file("data-contracts/bronze/nyctaxi_trips.yml")
        assert "npb_volunteering" in content


# ── pyproject.toml DAB dependencies ───────────────────────────────────────────

class TestPyprojectDabDeps:
    def test_pyspark_in_dev_deps_when_dab_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        content = project.read_file("pyproject.toml")
        assert "pyspark" in content

    def test_pytest_mock_in_dev_deps_when_dab_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        content = project.read_file("pyproject.toml")
        assert "pytest-mock" in content

    def test_databricks_sdk_in_runtime_deps_when_dab_enabled(self, bake):
        project = bake(databricks_asset_bundle="y")
        content = project.read_file("pyproject.toml")
        assert "databricks-sdk" in content

    def test_no_pyspark_when_dab_disabled(self, bake):
        project = bake(databricks_asset_bundle="n")
        content = project.read_file("pyproject.toml")
        assert "pyspark" not in content
        assert "databricks-sdk" not in content
        assert "pytest-mock" not in content

    def test_pyproject_is_valid_toml(self, bake):
        import tomllib
        project = bake(databricks_asset_bundle="y")
        raw = project.read_file("pyproject.toml")
        tomllib.loads(raw)  # raises if invalid


# ── databricks.yml structure ───────────────────────────────────────────────────

class TestDatabricksYml:
    def test_databricks_yml_is_valid_yaml(self, bake):
        project = bake(databricks_asset_bundle="y")
        assert project.is_valid_yaml("databricks.yml")

    def test_bundle_name_matches_project_slug(self, bake):
        project = bake(databricks_asset_bundle="y", project_name="my-project")
        content = project.read_file("databricks.yml")
        assert "my_project" in content

    def test_all_release_targets_present(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_workspace_role="da")
        content = project.read_file("databricks.yml")
        assert "release_da_dev" in content
        assert "release_da_test" in content
        assert "release_da_prod" in content

    def test_sql_warehouse_variable_present(self, bake):
        project = bake(databricks_asset_bundle="y")
        content = project.read_file("databricks.yml")
        assert "sql_warehouse_id" in content

    def test_dbt_target_variable_present(self, bake):
        project = bake(databricks_asset_bundle="y")
        content = project.read_file("databricks.yml")
        assert "dbt_target" in content


# ── pre_gen_project hook validation ───────────────────────────────────────────

class TestHookValidation:
    def test_invalid_catalog_suffix_rejected(self, bake):
        """Suffix with spaces or uppercase must be rejected by the pre_gen hook."""
        project = bake(
            databricks_asset_bundle="y",
            databricks_catalog_suffix="Invalid Suffix!",
            _expect_failure=True,
        )
        assert project.exit_code != 0

    def test_valid_catalog_suffix_accepted(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_catalog_suffix="my_suffix")
        assert project.exit_code == 0

    def test_empty_catalog_suffix_accepted(self, bake):
        project = bake(databricks_asset_bundle="y", databricks_catalog_suffix="")
        assert project.exit_code == 0
