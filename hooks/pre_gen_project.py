from __future__ import annotations

import re
import sys

PROJECT_NAME_REGEX = r"^[-a-zA-Z][-a-zA-Z0-9]+$"
project_name = "{{cookiecutter.project_name}}"
if not re.match(PROJECT_NAME_REGEX, project_name):
    print(
        f"ERROR: The project name {project_name} is not a valid Python module name. Please do not use a _ and use - instead"
    )
    # Exit to cancel project
    sys.exit(1)

PROJECT_SLUG_REGEX = r"^[_a-zA-Z][_a-zA-Z0-9]+$"
project_slug = "{{cookiecutter.project_slug}}"
if not re.match(PROJECT_SLUG_REGEX, project_slug):
    print(
        f"ERROR: The project slug {project_slug} is not a valid Python module name. Please do not use a - and use _ instead"
    )
    # Exit to cancel project
    sys.exit(1)

# Databricks Asset Bundle validation (only when DAB is enabled)
DAB_IDENTIFIER_REGEX = r"^[a-z][a-z0-9_]*$"

if "{{cookiecutter.databricks_asset_bundle}}" == "y":
    catalog_prefix = "{{cookiecutter.databricks_catalog_prefix}}"
    if not re.match(DAB_IDENTIFIER_REGEX, catalog_prefix):
        print(
            f"ERROR: databricks_catalog_prefix '{catalog_prefix}' must be lowercase letters, "
            "digits and underscores only, and must start with a letter. "
            "It is used to build Unity Catalog names like '{catalog_prefix}_dev'. "
            "Example valid values: 'mdp', 'my_org', 'nrx'"
        )
        sys.exit(1)

    schema_prefix = "{{cookiecutter.databricks_schema_prefix}}"
    if not re.match(DAB_IDENTIFIER_REGEX, schema_prefix):
        print(
            f"ERROR: databricks_schema_prefix '{schema_prefix}' must be lowercase letters, "
            "digits and underscores only, and must start with a letter. "
            "It is used to build schema names like '{schema_prefix}_bronze'. "
            "Example valid values: 'crm_dyn365', 'npb_volunteering', 'example_source'"
        )
        sys.exit(1)
