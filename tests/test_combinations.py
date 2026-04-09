from __future__ import annotations

import pytest

MINIMAL = {
    "cicd_github_actions": "n",
    "cicd_azure_pipelines": "n",
    "publish_to_pypi": "n",
    "deptry": "n",
    "mkdocs": "n",
    "codecov": "n",
    "dockerfile": "n",
    "devcontainer": "n",
    "databricks_asset_bundle": "n",
    "data_contracts": "n",
}

COMBINATIONS = [
    pytest.param({}, id="all-defaults"),
    pytest.param(MINIMAL, id="minimal"),
    pytest.param({"layout": "src"}, id="src-layout-defaults"),
    pytest.param({**MINIMAL, "layout": "src"}, id="src-layout-minimal"),
    pytest.param({"publish_to_pypi": "n", "mkdocs": "n"}, id="no-publish-no-mkdocs"),
    pytest.param({"cicd_github_actions": "n"}, id="no-github-actions"),
    pytest.param({"cicd_azure_pipelines": "n"}, id="no-azure-pipelines"),
    pytest.param({"type_checker": "ty"}, id="ty-type-checker"),
    pytest.param({"mkdocs": "y", "codecov": "n"}, id="mkdocs-no-codecov"),
    pytest.param({"codecov": "n", "cicd_github_actions": "n"}, id="no-codecov-no-actions"),
    pytest.param({"layout": "src", "type_checker": "ty", "publish_to_pypi": "n"}, id="src-ty-no-publish"),
    # DAB-specific combinations
    pytest.param({"databricks_asset_bundle": "n"}, id="no-dab"),
    pytest.param({"databricks_asset_bundle": "y", "data_contracts": "n"}, id="dab-no-contracts"),
    pytest.param({"databricks_asset_bundle": "y", "cicd_azure_pipelines": "n"}, id="dab-no-azdo"),
    pytest.param({"databricks_asset_bundle": "y", "databricks_workspace_role": "ip"}, id="dab-role-ip"),
    pytest.param({"databricks_asset_bundle": "y", "databricks_catalog_suffix": ""}, id="dab-no-catalog-suffix"),
]

# Reflects cookiecutter.json defaults (first item in each list / scalar value).
DEFAULTS = {
    "layout": "flat",
    "cicd_github_actions": "n",
    "cicd_azure_pipelines": "y",
    "publish_to_pypi": "n",
    "deptry": "y",
    "mkdocs": "y",
    "codecov": "y",
    "dockerfile": "n",
    "devcontainer": "y",
    "type_checker": "ty",
    "databricks_asset_bundle": "y",
    "databricks_catalog_prefix": "mdp",
    "databricks_catalog_suffix": "bronze",
    "databricks_schema_prefix": "crm_dyn365",
    "databricks_workspace_role": "in",
    "databricks_workspace_host_dev": "https://adb-898474248012616.16.azuredatabricks.net",
    "databricks_workspace_host_test": "https://adb-466812748542263.3.azuredatabricks.net",
    "databricks_workspace_host_prod": "https://adb-3615018142746575.15.azuredatabricks.net",
    "ado_service_connection_prefix": "SC",
    "ado_keyvault_name_dev": "kv-nrx-dev-dlz-di-euw",
    "ado_keyvault_name_test": "kv-nrx-test-dlz-di-euw",
    "ado_keyvault_name_prod": "kv-nrx-prod-dlz-di-euw",
    "ado_agent_pool_dev": "MDP-MPDAAS-SELFHOSTED-DEV",
    "ado_agent_pool_test": "MDP-MPDAAS-SELFHOSTED-TEST",
    "ado_agent_pool_prod": "MDP-MPDAAS-SELFHOSTED-PROD",
    "ado_environment_dev": "dev",
    "ado_environment_test": "test",
    "ado_environment_prod": "prod",
    "data_contracts": "y",
    "open_source_license": "Not open source",
}


def resolve_options(options: dict[str, str]) -> dict[str, str]:
    """Return the full set of resolved options (defaults merged with overrides)."""
    return {**DEFAULTS, **options}


@pytest.mark.parametrize("options", COMBINATIONS)
class TestStructure:
    """Validate file presence/absence for each option combination."""

    def test_always_present_files(self, bake, options):
        EXPECTED_FILES = [
            ".gitignore",
            ".pre-commit-config.yaml",
            "CONTRIBUTING.md",
            "Makefile",
            "README.md",
            "pyproject.toml",
            "tests",
            "tox.ini",
        ]
        project = bake(**options)
        for rel_path in EXPECTED_FILES:
            assert (project.path / rel_path).exists(), f"Expected {rel_path} to exist"
        # LICENSE only exists when an open-source license is selected.
        effective = resolve_options(options)
        if effective.get("open_source_license", "Not open source") != "Not open source":
            assert project.has_file("LICENSE")
        else:
            assert not project.has_file("LICENSE")

    def test_conditional_files(self, bake, options):
        project = bake(**options)
        effective = resolve_options(options)

        if effective["dockerfile"] == "y":
            assert project.has_file("Dockerfile")
        else:
            assert not project.has_file("Dockerfile")

        if effective["mkdocs"] == "y":
            assert project.has_dir("docs")
            assert project.has_file("mkdocs.yml")
        else:
            assert not project.has_dir("docs")
            assert not project.has_file("mkdocs.yml")

        if effective["codecov"] == "y":
            assert project.has_file("codecov.yaml")
        else:
            assert not project.has_file("codecov.yaml")

        if effective["devcontainer"] == "y":
            assert project.has_dir(".devcontainer")
        else:
            assert not project.has_dir(".devcontainer")

        if effective["cicd_github_actions"] == "y":
            assert project.has_dir(".github")
        else:
            assert not project.has_dir(".github")

        if effective["cicd_azure_pipelines"] == "y":
            assert project.has_dir(".azure")
        else:
            assert not project.has_dir(".azure")

        # ── DAB conditional files ───────────────────────────────────────────
        if effective["databricks_asset_bundle"] == "y":
            assert project.has_file("databricks.yml"), "databricks.yml must exist when DAB=y"
            assert project.has_dir("notebooks"), "notebooks/ must exist when DAB=y"
            assert project.has_dir("resources"), "resources/ must exist when DAB=y"
            assert project.has_dir("dbt"), "dbt/ must exist when DAB=y"
            if effective["cicd_azure_pipelines"] == "y":
                assert project.has_dir("azuredevops"), "azuredevops/ must exist when DAB=y and azure_pipelines=y"
            else:
                assert not project.has_dir("azuredevops")
            if effective["data_contracts"] == "y":
                assert project.has_dir("data-contracts"), "data-contracts/ must exist when data_contracts=y"
            else:
                assert not project.has_dir("data-contracts")
        else:
            assert not project.has_file("databricks.yml")
            assert not project.has_dir("notebooks")
            assert not project.has_dir("resources")
            assert not project.has_dir("dbt")
            assert not project.has_dir("azuredevops")
            assert not project.has_dir("data-contracts")

    def test_layout(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        # Project slug is derived from the default project_name "npb-analytics".
        slug = "npb_analytics"
        if effective["layout"] == "src":
            assert project.has_dir(f"src/{slug}"), f"Expected src/{slug}/ for src layout"
            assert not project.has_dir(slug)
        else:
            assert project.has_dir(slug), f"Expected {slug}/ for flat layout"
            assert not project.has_dir("src")

    def test_release_workflow(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        if effective["cicd_github_actions"] != "y":
            return  # no .github at all
        has_release = effective["publish_to_pypi"] == "y" or effective["mkdocs"] == "y"
        workflow = ".github/workflows/on-release-main.yml"
        if has_release:
            assert project.has_file(workflow), "Expected release workflow to exist"
        else:
            assert not project.has_file(workflow), "Expected release workflow to be absent"

    def test_yaml_validity(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        if effective["cicd_github_actions"] == "y":
            assert project.is_valid_yaml(".github/workflows/main.yml")
        if effective["databricks_asset_bundle"] == "y":
            assert project.is_valid_yaml("databricks.yml")

    def test_pyproject_type_checker(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        content = project.read_file("pyproject.toml")
        if effective["type_checker"] == "mypy":
            assert '"mypy' in content
            assert '"ty' not in content
        else:
            assert '"ty' in content
            assert '"mypy' not in content

    def test_makefile_targets(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        content = project.read_file("Makefile")

        if effective["publish_to_pypi"] == "y":
            assert "build-and-publish" in content
        else:
            assert "build-and-publish" not in content

        if effective["mkdocs"] == "y":
            assert "docs:" in content
        else:
            assert "docs:" not in content

        if effective["databricks_asset_bundle"] == "y":
            assert "bundle-validate" in content
            assert "bundle-deploy-dev" in content
        else:
            assert "bundle-validate" not in content

    def test_codecov_workflow(self, bake, options):
        effective = resolve_options(options)
        project = bake(**options)
        if effective["cicd_github_actions"] == "y":
            if effective["codecov"] == "y":
                assert project.has_file(".github/workflows/validate-codecov-config.yml")
                assert project.has_file("codecov.yaml")
            else:
                assert not project.has_file(".github/workflows/validate-codecov-config.yml")
                assert not project.has_file("codecov.yaml")


@pytest.mark.slow
@pytest.mark.parametrize("options", COMBINATIONS)
def test_install_and_run_tests(bake, options):
    """Bake, install dependencies, and run the generated project's test suite."""
    project = bake(**options)
    project.install()
    project.run_tests()


@pytest.mark.slow
def test_check_passes_on_default_project(bake):
    """A freshly baked default project should pass its own ``make check``."""
    project = bake()
    project.install()
    project.run_check()
