#!/usr/bin/env python
from __future__ import annotations

import os
import shutil

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


def remove_file(filepath: str) -> None:
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


def remove_dir(filepath: str) -> None:
    shutil.rmtree(os.path.join(PROJECT_DIRECTORY, filepath))


def move_file(filepath: str, target: str) -> None:
    os.rename(os.path.join(PROJECT_DIRECTORY, filepath), os.path.join(PROJECT_DIRECTORY, target))


def move_dir(src: str, target: str) -> None:
    shutil.move(os.path.join(PROJECT_DIRECTORY, src), os.path.join(PROJECT_DIRECTORY, target))


if __name__ == "__main__":
    if "{{cookiecutter.cicd_github_actions}}" != "y":
        remove_dir(".github")

    if "{{cookiecutter.cicd_azure_pipelines}}" != "y":
        remove_dir(".azure")
    else:
        if "{{cookiecutter.mkdocs}}" != "y" and "{{cookiecutter.publish_to_pypi}}" == "n":
            remove_file(".github/workflows/on-release-main.yml")

    if "{{cookiecutter.mkdocs}}" != "y":
        remove_dir("docs")
        remove_file("mkdocs.yml")

    if "{{cookiecutter.dockerfile}}" != "y":
        remove_file("Dockerfile")

    if "{{cookiecutter.codecov}}" != "y":
        remove_file("codecov.yaml")
        if "{{cookiecutter.cicd_github_actions}}" == "y":
            remove_file(".github/workflows/validate-codecov-config.yml")

    if "{{cookiecutter.devcontainer}}" != "y":
        remove_dir(".devcontainer")

    if "{{cookiecutter.open_source_license}}" == "MIT license":
        move_file("LICENSE_MIT", "LICENSE")
        remove_file("LICENSE_BSD")
        remove_file("LICENSE_ISC")
        remove_file("LICENSE_APACHE")
        remove_file("LICENSE_GPL")

    if "{{cookiecutter.open_source_license}}" == "BSD license":
        move_file("LICENSE_BSD", "LICENSE")
        remove_file("LICENSE_MIT")
        remove_file("LICENSE_ISC")
        remove_file("LICENSE_APACHE")
        remove_file("LICENSE_GPL")

    if "{{cookiecutter.open_source_license}}" == "ISC license":
        move_file("LICENSE_ISC", "LICENSE")
        remove_file("LICENSE_MIT")
        remove_file("LICENSE_BSD")
        remove_file("LICENSE_APACHE")
        remove_file("LICENSE_GPL")

    if "{{cookiecutter.open_source_license}}" == "Apache Software License 2.0":
        move_file("LICENSE_APACHE", "LICENSE")
        remove_file("LICENSE_MIT")
        remove_file("LICENSE_BSD")
        remove_file("LICENSE_ISC")
        remove_file("LICENSE_GPL")

    if "{{cookiecutter.open_source_license}}" == "GNU General Public License v3":
        move_file("LICENSE_GPL", "LICENSE")
        remove_file("LICENSE_MIT")
        remove_file("LICENSE_BSD")
        remove_file("LICENSE_ISC")
        remove_file("LICENSE_APACHE")

    if "{{cookiecutter.open_source_license}}" == "Not open source":
        remove_file("LICENSE_GPL")
        remove_file("LICENSE_MIT")
        remove_file("LICENSE_BSD")
        remove_file("LICENSE_ISC")
        remove_file("LICENSE_APACHE")

    if "{{cookiecutter.layout}}" == "src":
        if os.path.isdir("src"):
            remove_dir("src")
        move_dir("{{cookiecutter.project_slug}}", os.path.join("src", "{{cookiecutter.project_slug}}"))

    # Databricks Asset Bundle cleanup
    if "{{cookiecutter.databricks_asset_bundle}}" != "y":
        for dab_path in ["databricks.yml", "notebooks", "resources", "azuredevops", "data-contracts", "dbt"]:
            full_path = os.path.join(PROJECT_DIRECTORY, dab_path)
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)

        # Remove DAB-specific Python subpackages (bronze/silver/gold/utils).
        # These are only meaningful in a DAB project; a plain Python package
        # should only have the generic foo.py example.
        if "{{cookiecutter.layout}}" == "src":
            pkg_root = os.path.join(PROJECT_DIRECTORY, "src", "{{cookiecutter.project_slug}}")
        else:
            pkg_root = os.path.join(PROJECT_DIRECTORY, "{{cookiecutter.project_slug}}")

        for dab_pkg in ["bronze", "silver", "gold", "utils"]:
            dir_path = os.path.join(pkg_root, dab_pkg)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

        # Remove DAB-specific test files and subdirectories.
        tests_root = os.path.join(PROJECT_DIRECTORY, "tests")
        for dab_test in ["bronze", "silver", "conftest.py", "test_catalog.py"]:
            dab_test_path = os.path.join(tests_root, dab_test)
            if os.path.isfile(dab_test_path):
                os.remove(dab_test_path)
            elif os.path.isdir(dab_test_path):
                shutil.rmtree(dab_test_path)

    else:
        # DAB is enabled — apply sub-option cleanup.
        if "{{cookiecutter.cicd_azure_pipelines}}" != "y":
            # Azure Pipelines not wanted: remove the DAB pipeline files.
            azuredevops_path = os.path.join(PROJECT_DIRECTORY, "azuredevops")
            if os.path.isdir(azuredevops_path):
                shutil.rmtree(azuredevops_path)

        if "{{cookiecutter.data_contracts}}" != "y":
            data_contracts_path = os.path.join(PROJECT_DIRECTORY, "data-contracts")
            if os.path.isdir(data_contracts_path):
                shutil.rmtree(data_contracts_path)
