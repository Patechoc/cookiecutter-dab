# Azure DevOps CI/CD Setup Guide

This guide explains how to set up and use the Azure DevOps CI/CD pipelines for this project. Azure DevOps provides continuous integration and deployment automation similar to GitHub Actions, but with Azure-specific features and integrations.

> **📌 Important**: Azure Pipelines work with any Git platform (GitHub, Azure Repos, GitLab, Bitbucket). When you see platform-specific examples (e.g., GitHub Pages, GitHub tokens), adapt the instructions to your repository platform's equivalent.

## Table of Contents

1. [What is Azure DevOps?](#what-is-azure-devops)
2. [Prerequisites](#prerequisites)
3. [Initial Setup Steps](#initial-setup-steps)
4. [Configuring Pipeline Variables and Secrets](#configuring-pipeline-variables-and-secrets)
5. [Understanding the Pipelines](#understanding-the-pipelines)
6. [Triggering Pipelines](#triggering-pipelines)
7. [Monitoring Pipeline Runs](#monitoring-pipeline-runs)
8. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
9. [Key Differences from GitHub Actions](#key-differences-from-github-actions)

## What is Azure DevOps?

Azure Pipelines is part of Azure DevOps, Microsoft's cloud-based platform for project management, version control, and CI/CD. Key benefits include:

- **Free tier**: 1 free parallel job for public repos, same as GitHub Actions
- **Deep Azure integration**: Built-in support for Azure services
- **YAML-based pipelines**: Infrastructure-as-code approach (similar to GitHub Actions)
- **Multiple trigger types**: Branches, tags, schedules, pull requests
- **Built-in artifact management**: Easy storage and sharing of build outputs

## Prerequisites

Before you start, you'll need:

1. **Azure DevOps Organization**: Go to [https://dev.azure.com](https://dev.azure.com) and create a free organization
2. **Azure DevOps Project**: Create a new project within your organization
3. **Repository connected**: Your source code repository (GitHub, Azure Repos, GitLab, or Bitbucket) accessible to Azure Pipelines
4. **Python knowledge**: Basic understanding of Python and virtual environments
5. **Access to secrets**: PyPI token (for package publishing) and any platform-specific tokens needed (e.g., for documentation deployment)

## Initial Setup Steps

### Step 1: Create an Azure DevOps Organization

1. Visit [https://dev.azure.com](https://dev.azure.com)
2. Click "Create project"
3. Enter a project name (e.g., `my-python-project`)
4. Choose **Private** or **Public** visibility
5. Click "Create"

### Step 2: Connect Your Repository

1. In your Azure DevOps project, go to **Pipelines**
2. Click **Create Pipeline**
3. Select your repository source:
   - **GitHub**: Authorize Azure Pipelines to access your GitHub account
   - **Azure Repos**: Select your repository directly
   - **GitLab** or **Bitbucket**: Authorize and select your repository
4. Approve any authorization prompts or app installations
5. Select your repository from the list

### Step 3: Configure Pipeline Files

The pipeline YAML files live in the `.azure/` folder of your repository (analogous to `.github/` for GitHub Actions):

- **Main CI/CD Pipeline**: `.azure/azure-pipelines-main.yml`
  - Runs on pushes to `main` and pull requests
  - Performs code quality checks, tests, and documentation builds

- **Release Pipeline**: `.azure/azure-pipelines-release.yml`
  - Runs when you create a release tag
  - Builds and publishes packages to PyPI

### Step 4: Create Pipeline in Azure DevOps

1. In Azure DevOps **Pipelines** section, click **New Pipeline**
2. Select your repository source (GitHub, Azure Repos, GitLab, or Bitbucket)
3. Select your repository
4. When asked "How do you want to configure your pipeline?", select **Existing Azure Pipelines YAML file**
5. Select branch: `main`
6. Select path: `/.azure/azure-pipelines-main.yml`
7. Click **Continue**
8. Click **Save and run** (or **Save** to just save without running)

Repeat for the release pipeline, selecting `/.azure/azure-pipelines-release.yml` instead.

## Configuring Pipeline Variables and Secrets

### Setting Up Variables

Some pipelines need sensitive information (tokens, credentials). Here's how to configure them:

#### PyPI Token (for package publishing)

1. Go to your PyPI account on [https://pypi.org](https://pypi.org)
2. Generate an API token in Account Settings → API tokens
3. In your Azure DevOps project:
   - Go to **Pipelines** → Select your release pipeline
   - Click **Edit**
   - Click **Variables** (top-right)
   - Click **New variable**
   - Name: `pypiToken`
   - Value: **(paste your PyPI API token)**
   - **Check "Keep this value secret"** ✓
   - Click **OK**, then **Save**

#### Documentation Hosting Token (optional)

Documentation deployment is not included in the release pipeline by default. Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](./azure_docs_hosting_alternatives.md) for setup instructions for Azure Static Web Apps, ReadTheDocs, Netlify, and other options — each with their own token/secret requirements.

### Using Variables in Pipelines

Variables are referenced in YAML with `$(variableName)` syntax. For example:

```yaml
- script: |
    uv publish
  env:
    UV_PUBLISH_TOKEN: $(pypiToken)
```

## Understanding the Pipelines

### Main Pipeline (`azure-pipelines-main.yml`)

This pipeline runs automatically on:

- **Push to main branch**
- **Pull requests** targeting main

**Stages:**

1. **Quality Checks**
   - Runs pre-commit hooks (linting, formatting)
   - Checks for obsolete dependencies (deptry)
   - Verifies lock file consistency

2. **Tests and Type Checking** (runs in parallel for Python 3.10-3.14)
   - Runs pytest with code coverage
   - Performs type checking (mypy or Pyright)
   - Publishes coverage reports (for Python 3.11)

3. **Documentation** (if enabled in template)
   - Builds documentation with MkDocs
   - Ensures no build errors or warnings

### Release Pipeline (`azure-pipelines-release.yml`)

This pipeline runs when you create a release (Git tag).

**Stages:**

1. **Set Version** (if publishing to PyPI)
   - Extracts version from Git tag
   - Updates `pyproject.toml` with the version

2. **Publish** (if publishing to PyPI)
   - Builds the Python package
   - Publishes to PyPI using credentials

3. **Publish** (if publishing to PyPI)
   - Builds the Python package and publishes to PyPI

> **Note on documentation deployment**: Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](./azure_docs_hosting_alternatives.md) for options including Azure Static Web Apps, ReadTheDocs, and Netlify.

## Triggering Pipelines

### Automatic Triggers

#### Main Pipeline

```bash
# Trigger automatically on push to main
git push origin main

# Trigger automatically on PR
# Create a pull request on your repository platform
git push origin feature-branch
```

#### Release Pipeline

```bash
# Create a release tag to trigger the release pipeline
git tag v1.0.0
git push origin v1.0.0
```

### Manual Triggers

In Azure DevOps:

1. Go to **Pipelines**
2. Select the pipeline you want to run
3. Click **Run pipeline** (or **Create pipeline** if it's your first run)
4. Select the branch
5. Click **Run**

## Monitoring Pipeline Runs

### Viewing Pipeline Results

1. In Azure DevOps, go to **Pipelines**
2. Select your pipeline
3. You'll see a list of recent runs with their status (✓ Passed, ✗ Failed, ⏸ In Progress)

### Checking Detailed Logs

1. Click on a pipeline run
2. Click on a **Job** to see details
3. Each **Step** shows:
   - Output/logs
   - Duration
   - Status (passed/failed)

### Finding Failed Stages

When a pipeline fails:

1. Click on the failed run
2. Look for the red ✗ marker
3. Click the job/stage with the failure
4. Review the logs to identify the issue

Example common failures:

- **"Lock file out of date"**: Run `uv lock` locally and commit
- **"Test failed"**: Check test output in logs
- **"Type check failed"**: Run `mypy` locally to find issues
- **"Pre-commit failed"**: Run `pre-commit run -a` locally to fix formatting

## Common Issues and Troubleshooting

### Issue: "Permission denied" when publishing to PyPI

**Solution:**

1. Verify your PyPI token is correct and not expired
2. Check that the token secret in Azure DevOps matches exactly what you copied
3. Ensure you're using the correct variable name: `$(pypiToken)`

### Issue: Documentation not deployed after release

**Solution:** Documentation deployment is not wired up by default — Azure DevOps has no built-in equivalent to GitHub Pages. See [Documentation Hosting Alternatives](./azure_docs_hosting_alternatives.md) to choose and configure a hosting option.

### Issue: "Tests fail on my machine but pass in pipeline" (or vice versa)

**Solution:**

1. Check Python version: `python --version` (should match pipeline version)
2. Reinstall dependencies: `uv sync --frozen`
3. Check for platform-specific issues (Windows vs Linux)
4. Look at pipeline logs to see the exact error

### Issue: "Cache miss" or "Cache not found"

**This is normal** - it just means dependencies are being downloaded. It won't cause failures, but can slow down the first run. Subsequent runs will use the cache.

### Issue: Pipeline not triggering automatically

**Checklist:**

1. ✓ Pipeline files exist in repository (`.azure/azure-pipelines-main.yml` or `.azure/azure-pipelines-release.yml`)
2. ✓ File is on the monitored branch (check `trigger` in YAML)
3. ✓ Pipeline is enabled in Azure DevOps (not disabled)
4. ✓ For releases: you created a Git tag starting with `v` (e.g., `v1.0.0`)

**Solution:**

- Manually trigger in Azure DevOps ("Run pipeline" button)
- Check "All" pipelines, not just "Recent"

## Key Differences from GitHub Actions

### 1. Secrets Storage

| GitHub Actions | Azure Pipelines |
| --- | --- |
| Settings → Secrets and variables → Actions | Pipelines → (Select pipeline) → Variables |
| `${{ secrets.TOKEN }}` | `$(tokenVariableName)` |
| Auto-detected from environment | Must explicitly add to pipeline variables |

### 2. Artifact Management

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `actions/upload-artifact@v4` | `PublishBuildArtifacts@1` task |
| `actions/download-artifact@v4` | `DownloadBuildArtifacts@1` task |
| Limited retention by default | 30 days retention by default |

### 3. Job Matrix

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `matrix: python-version: [...]` | `strategy: matrix: { pythonVersion: [...] }` |
| `${{ matrix.python-version }}` | `$(pythonVersion)` |

### 4. Cache

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `actions/cache@v4` | `Cache@2` task |
| Automatic cleanup after 7 days | Automatic cleanup after 7 days |
| Simple key syntax | More explicit key/path configuration |

### 5. Triggers

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `on: push:` or `on: pull_request:` | `trigger:` and `pr:` |
| Tag triggers in workflow | `trigger: tags:` for releases |
| No native tag filtering | Built-in tag include/exclude patterns |

### 6. Cron Jobs

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `schedule: - cron: '0 0 * * 0'` | `schedules: - cron: "0 0 * * 0"` with `always: false` |

### 7. Conditional Execution

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `if: ${{ condition }}` | `condition: eq(...)`, `ne()`, etc. or `condition: succeeded()` |

### 8. Using External Actions

| GitHub Actions | Azure Pipelines |
| --- | --- |
| `uses: owner/repo@v1` | `task: TaskName@version` (official) or `job` templates |
| Community actions very common | Fewer but well-maintained official tasks |

---

## Additional Resources

- **Azure Pipelines Documentation**: [https://docs.microsoft.com/azure/devops/pipelines](https://docs.microsoft.com/azure/devops/pipelines)
- **YAML Schema Reference**: [https://docs.microsoft.com/azure/devops/pipelines/yaml-schema](https://docs.microsoft.com/azure/devops/pipelines/yaml-schema)
- **Azure DevOps Marketplace**: [https://marketplace.visualstudio.com/azuredevops](https://marketplace.visualstudio.com/azuredevops)

## Questions?

For issues or questions:

1. Check the **Troubleshooting** section above
2. Review pipeline logs in Azure DevOps
3. Consult the [official documentation](https://docs.microsoft.com/azure/devops/pipelines)
4. Ask your team lead or senior developer
