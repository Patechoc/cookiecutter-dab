.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' \
	$(MAKEFILE_LIST)

##@ Template

.PHONY: bake
bake: ## Bake without inputs and overwrite if exists
	@uv run cookiecutter --no-input . --overwrite-if-exists

.PHONY: bake-src
bake-src: ## Bake with src layout, no inputs, overwrite if exists
	@uv run cookiecutter --no-input . --overwrite-if-exists layout="src"

.PHONY: bake-with-inputs
bake-with-inputs: ## Bake interactively and overwrite if exists
	@uv run cookiecutter . --overwrite-if-exists

.PHONY: bake-and-test-deploy
bake-and-test-deploy: ## Bake and push to cookiecutter-uv-example to test GH Actions
	@rm -rf cookiecutter-uv-example || true
	@uv run cookiecutter --no-input . --overwrite-if-exists \
		author="Florian Maas" \
		email="foo@email.com" \
		github_author_handle=fpgmaas \
		project_name=cookiecutter-uv-example \
		project_slug=cookiecutter_uv_example
	@cd cookiecutter-uv-example; uv sync && \
		git init -b main && \
		git add . && \
		uv run pre-commit install && \
		uv run pre-commit run -a || true && \
		git add . && \
		uv run pre-commit run -a || true && \
		git add . && \
		git commit -m "init commit" && \
		git remote add origin git@github.com:osprey-oss/cookiecutter-uv-example.git && \
		git push -f origin main

##@ Environment

.PHONY: install
install: ## Create virtual environment and install dependencies
	@echo "🚀 Creating virtual environment"
	@uv sync

##@ CI / Code Quality

.PHONY: check
check: ## Run lock file check, linting, type checking, and deptry
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@uv run mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run deptry .

.PHONY: test
test: ## Run tests with pytest and coverage
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml tests

##@ Python Packaging

.PHONY: build
build: clean-build ## Build wheel file
	@echo "🚀 Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Remove build artifacts
	@echo "🚀 Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI
	@echo "🚀 Publishing: Dry run."
	@uvx --from build pyproject-build --installer uv
	@echo "🚀 Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish to PyPI

##@ Documentation

.PHONY: docs-test
docs-test: ## Build documentation (strict — fail on warnings)
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve documentation locally
	@uv run mkdocs serve
