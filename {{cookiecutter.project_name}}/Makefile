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
