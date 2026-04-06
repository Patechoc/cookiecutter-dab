CURRENT_VERSION := $(shell grep '^version' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' \
	$(MAKEFILE_LIST)

##@ Environment

.PHONY: install
install: ## Create virtual environment and install pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

##@ CI / Code Quality

.PHONY: check
check: ## Run lock file check, linting, type checking{% if cookiecutter.deptry == 'y' %}, and deptry{% endif %}
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running {{ cookiecutter.type_checker }}"
	@uv run {% if cookiecutter.type_checker == "mypy" %}mypy{% else %}ty check{% endif %}
{%- if cookiecutter.deptry == 'y' %}
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry {% if cookiecutter.layout == "src" %}src{% else %}.{% endif %}
{%- endif %}

.PHONY: test
test: ## Run tests with pytest{% if cookiecutter.codecov == "y" %} and coverage{% endif %}
	@echo "🚀 Testing code: Running pytest"
{%- if cookiecutter.codecov == "y"%}
	@uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml
{%- else %}
	@uv run python -m pytest --doctest-modules
{%- endif%}

##@ Release

.PHONY: release
release: ## Release a new version (usage: make release VERSION=X.Y.Z)
ifndef VERSION
	$(error ❌ VERSION not set. Usage: make release VERSION=X.Y.Z (e.g. 0.2.0). Current version: $(CURRENT_VERSION))
endif
	@if [ "$(VERSION)" = "$(CURRENT_VERSION)" ]; then \
		echo "❌ VERSION $(VERSION) is the same as current version. Please specify a new version."; \
		exit 1; \
	fi
	@if git tag -l | grep -q "^v$(VERSION)$$"; then \
		echo "❌ Tag v$(VERSION) already exists. Please choose a different version."; \
		exit 1; \
	fi
	@echo "🚀 Releasing version $(VERSION) (current: $(CURRENT_VERSION))..."
	@sed -i.bak 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml && rm -f pyproject.toml.bak
	@uv lock
	@uv sync
	@uv run git-cliff --config cliff.toml --tag v$(VERSION) --output CHANGELOG.md
	@git add pyproject.toml uv.lock CHANGELOG.md
	@git commit -m "bump version to v$(VERSION)"
	@git tag -a v$(VERSION) -m "Release v$(VERSION)"
	@git push origin main --tags
	@echo "✅ Release v$(VERSION) pushed successfully."

##@ Python Packaging

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Remove build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"
{%- if cookiecutter.publish_to_pypi == "y"%}

.PHONY: publish
publish: ## Publish a release to PyPI
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish to PyPI
{%- endif%}
{%- if cookiecutter.mkdocs == "y" %}

##@ Documentation

.PHONY: docs-test
docs-test: ## Build documentation (strict — fail on warnings)
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve documentation locally
	@uv run mkdocs serve
{%- endif %}
{% if cookiecutter.databricks_asset_bundle == 'y' %}
##@ Databricks Asset Bundle

# Requires the Databricks CLI installed and configured:
#   curl -fsSL https://raw.githubusercontent.com/databricks/setup-databricks-cli/v0/install.sh | sh
# For local runs, set DATABRICKS_HOST + DATABRICKS_TOKEN (or service principal vars) in your shell.

DAB_ROLE := {{cookiecutter.databricks_workspace_role}}

.PHONY: bundle-validate
bundle-validate: ## Validate the bundle against the dev_personal target (no deployment)
	@echo "🔍 Validating DAB bundle..."
	@databricks bundle validate --target dev_personal

.PHONY: bundle-deploy-dev
bundle-deploy-dev: build ## Build wheel and deploy bundle to DEV workspace
	@echo "🚀 Deploying bundle to DEV (target: release_$(DAB_ROLE)_dev)..."
	@databricks bundle deploy --target release_$(DAB_ROLE)_dev --force-lock

.PHONY: bundle-deploy-test
bundle-deploy-test: build ## Build wheel and deploy bundle to TEST workspace
	@echo "🚀 Deploying bundle to TEST (target: release_$(DAB_ROLE)_test)..."
	@databricks bundle deploy --target release_$(DAB_ROLE)_test --force-lock

.PHONY: bundle-deploy-prod
bundle-deploy-prod: build ## Build wheel and deploy bundle to PROD workspace
	@echo "🚀 Deploying bundle to PROD (target: release_$(DAB_ROLE)_prod)..."
	@databricks bundle deploy --target release_$(DAB_ROLE)_prod --force-lock

.PHONY: bundle-destroy-dev
bundle-destroy-dev: ## Destroy bundle resources in DEV (jobs, schedules, artifacts — NOT tables)
	@echo "⚠️  Destroying bundle resources in DEV (target: release_$(DAB_ROLE)_dev)..."
	@databricks bundle destroy --target release_$(DAB_ROLE)_dev --auto-approve

.PHONY: bundle-run-bronze
bundle-run-bronze: ## Trigger the bronze ingestion job in DEV immediately (bypasses schedule)
	@echo "▶️  Running bronze ingestion job in DEV..."
	@databricks bundle run --target release_$(DAB_ROLE)_dev bronze_ingestion

.PHONY: bundle-run-silver
bundle-run-silver: ## Trigger the silver transform job in DEV immediately
	@echo "▶️  Running silver transform job in DEV..."
	@databricks bundle run --target release_$(DAB_ROLE)_dev silver_transform

.PHONY: bundle-run-gold
bundle-run-gold: ## Trigger the gold aggregation job in DEV immediately
	@echo "▶️  Running gold aggregation job in DEV..."
	@databricks bundle run --target release_$(DAB_ROLE)_dev gold_aggregate

.PHONY: bundle-run-dbt
bundle-run-dbt: ## Trigger the dbt transformations job in DEV immediately
	@echo "▶️  Running dbt transformations job in DEV..."
	@databricks bundle run --target release_$(DAB_ROLE)_dev dbt_transformations
{%- endif %}
