# Setting Up Azure DevOps CI/CD for Your Project

This guide walks you through setting up Azure DevOps continuous integration and deployment for your Python project.

> **📌 Important**: These pipelines work with any Git platform (GitHub, Azure Repos, GitLab, Bitbucket). Steps and configuration may vary depending on your repository host. When you see platform-specific instructions (e.g., GitHub Pages deployment), adapt them to your platform's equivalent.

## Quick Start

1. Create an Azure DevOps organization at [https://dev.azure.com](https://dev.azure.com)
2. Create a new project
3. Connect your repository to Azure DevOps (supports GitHub, Azure Repos, GitLab, Bitbucket)
4. Create pipelines using the provided YAML files
5. (Optional) Add secrets for PyPI publishing and documentation deployment

## Step-by-Step Setup

### 1. Create Azure DevOps Organization and Project

1. Go to [https://dev.azure.com](https://dev.azure.com)
2. Click **Create project**
3. Enter your project name
4. Choose visibility (Private or Public)
5. Click **Create**

### 2. Connect Your Repository

1. In your Azure DevOps project, go to **Pipelines** → **Create Pipeline**
2. Select your repository source:
   - **GitHub**: Authorize Azure Pipelines to access your GitHub account
   - **Azure Repos**: Select your repository directly
   - **GitLab** or **Bitbucket**: Authorize and select your repository
3. Approve any authorization prompts
4. Select your repository

### 3. Create the Main CI/CD Pipeline

This pipeline runs tests, linting, and type checking on every push and pull request.

1. Click **Create Pipeline** → Select your repository source → select your repo
2. When asked "How do you want to configure your pipeline?", choose **Existing Azure Pipelines YAML file**
3. Select branch: `main`
4. Path: `/.azure/azure-pipelines-main.yml`
5. Click **Continue** → **Save and run** (or just **Save** to save without running)

**What it does:**
- ✓ Runs code quality checks (linting, formatting)
- ✓ Runs tests on Python 3.10-3.14
- ✓ Checks types with mypy{% if cookiecutter.type_checker == "pyright" %}/Pyright{% endif %}
- ✓ Publishes code coverage reports
{% if cookiecutter.mkdocs == "y" -%}
- ✓ Builds documentation
{% endif %}

### 4. (Optional) Create the Release Pipeline

This pipeline publishes your package to PyPI and deploys documentation when you create a release tag.

Only proceed if you plan to publish to PyPI or deploy documentation.

1. Click **Pipelines** → **New Pipeline**
2. Select your repository source → your repository
3. Choose **Existing Azure Pipelines YAML file**
4. Path: `/.azure/azure-pipelines-release.yml`
5. Click **Continue** → **Save**

**Before using the release pipeline:**

If you plan to **publish to PyPI**:
- Generate a PyPI API token at [https://pypi.org/account/](https://pypi.org/account/)
- In Azure DevOps: Go to your release pipeline → **Edit** → **Variables**
- Click **+ New variable**
  - Name: `pypiToken`
  - Value: *(paste your PyPI token)*
  - Check "Keep this value secret" ✓
  - Click **Save**

{% if cookiecutter.mkdocs == "y" %}If you plan to **deploy documentation**:

Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](azure_docs_hosting_alternatives.md) for options (Azure Static Web Apps, ReadTheDocs, Netlify, and others) and their setup instructions.
{% endif %}

## How the Pipelines Work

### Main Pipeline (`azure-pipelines-main.yml`)

Triggers on:
- Push to `main` branch
- Pull requests to `main`

**Stages:**

1. **Quality Checks** (runs once)
   - Pre-commit hooks (formatting, linting)
   - Lock file consistency check
   - Dependency analysis (deptry)

2. **Tests and Type Checking** (runs in parallel for Python 3.10-3.14)
   - Unit tests with pytest
   - Code coverage analysis
   - Type checking
   - Coverage report upload (Python 3.11 only)

3. **Documentation** (runs once, if enabled)
   - Builds documentation with MkDocs to catch errors early

### Release Pipeline (`azure-pipelines-release.yml`)

Triggers when you create a Git tag (release).

**How to trigger:**

```bash
# Create a tag locally and push
git tag v1.0.0
git push origin v1.0.0
```

**What happens:**

1. Extracts version from tag (e.g., `v1.0.0` → `1.0.0`)
2. Updates `pyproject.toml` with the version
3. Builds your package
4. Publishes to PyPI (if enabled in template)

{% if cookiecutter.mkdocs == "y" %}> **Note on documentation deployment**: Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](azure_docs_hosting_alternatives.md) for options such as Azure Static Web Apps, ReadTheDocs, and Netlify.
{% endif %}

## Viewing Pipeline Results

### All Pipeline Runs

1. Go to **Pipelines** in your Azure DevOps project
2. Click your pipeline name
3. See list of recent runs with status (✓ Passed, ✗ Failed, ⏳ Running)

### Detailed Results for a Run

1. Click on a pipeline run
2. Review the **Summary** tab for overview
3. Click on **Jobs** to see individual job logs
4. Expand **Steps** within jobs to see detailed output

### Finding What Failed

When a pipeline fails:

1. Look for the red ✗ in the pipeline run
2. Click that job/stage to see the logs
3. Look for error messages in the step output

**Common failures:**

| Problem | Solution |
|---------|----------|
| "Lock file out of date" | Run `uv lock` locally and commit |
| "Test failed" | Run `python -m pytest` locally to debug |
| "Type check failed" | Run `mypy` locally to find type issues |
| "Pre-commit failed" | Run `pre-commit run -a` locally to fix |
| "Documentation build failed" | Run `mkdocs build -s` locally to find issues |

## Comparing with GitHub Actions

If you previously used GitHub Actions, here are the key differences. **Note:** The example sections below show GitHub Actions syntax, but the same concepts apply to Azure Pipelines regardless of your repository platform.

### Secrets

**GitHub Actions:**
```yaml
env:
  TOKEN: {% raw %}${{ secrets.MY_TOKEN }}{% endraw %}
```

**Azure Pipelines:**
```yaml
env:
  TOKEN: $(myTokenVariable)
```

Secrets are configured in the **Pipelines** → **Variables** section (not in code).

### Matrix (multiple Python versions)

**GitHub Actions:**
```yaml
matrix:
  python-version: ["3.10", "3.11", "3.12"]
```

**Azure Pipelines:**
```yaml
strategy:
  matrix:
    Python310:
      pythonVersion: '3.10'
    Python311:
      pythonVersion: '3.11'
    Python312:
      pythonVersion: '3.12'
```

### Triggering on Tags

**GitHub Actions:**
```yaml
on:
  release:
    types: [published]
```

**Azure Pipelines:**
```yaml
trigger:
  tags:
    include:
      - 'v*'
```

## Troubleshooting

### "Permission denied" when publishing to PyPI

- Verify your PyPI token is correct (copy directly from PyPI, no extra spaces)
- Ensure the token secret is properly saved in Azure DevOps Variables
- Check that you're using the correct variable name: `$(pypiToken)`

### Documentation not deployed after release

Documentation deployment is not wired up by default — Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](azure_docs_hosting_alternatives.md) to choose and configure a hosting option.

### Pipeline not triggering on push/PR

- Verify the pipeline files exist in `.azure/` in your repository
- Check branch name in the `trigger` section of YAML matches your branch
- In Azure DevOps, make sure the pipeline isn't **Disabled**
- Try manually running "Run pipeline" to test

### Tests pass locally but fail in pipeline

- Check Python version matches: `python --version`
- Reinstall dependencies: `uv sync --frozen`
- Check for platform-specific code (Windows vs Linux)
- Review exact error message in pipeline logs

### Cache showing "miss" (slow first run)

This is normal! The cache stores dependencies from the first run. Subsequent runs will be faster.

## Next Steps

Once pipelines are working:

1. **Monitor on updates**: Watch your pipelines run on every push/PR
2. **Fix issues early**: Address test or type-check failures immediately
3. **Keep secrets secure**: Never commit tokens or API keys
4. **Enable branch protection**: Require pipelines to pass before merging PRs

**To enable branch protection** (steps vary by platform):

**GitHub:**
1. Go to repository **Settings** → **Branches**
2. Click **Add rule** under "Branch protection rules"
3. Enter branch name: `main`
4. Check "Require status checks to pass before merging"
5. Select your Azure Pipeline checks
6. Click **Create**

**Azure Repos:**
1. Go to **Branches**
2. Select `main` branch
3. Click **Branch policies**
4. Configure "Build policy" to require successful pipeline runs

**GitLab/Bitbucket:**
- Consult your platform's documentation for protected branch rules

## Getting Help

- Check pipeline **Logs** for error details
- See the [main guide](../azure_devops_setup.md) for more detailed explanations
- Review [Azure Pipelines documentation](https://docs.microsoft.com/azure/devops/pipelines)
- Ask your team lead or senior developer
