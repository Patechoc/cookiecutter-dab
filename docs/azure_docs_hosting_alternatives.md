# Documentation Hosting Alternatives to GitHub Pages

When using Azure DevOps for CI/CD, there is no built-in equivalent to GitHub Pages. This page documents the main alternatives for hosting MkDocs-generated documentation.

## Overview

| Option | Cost | Complexity | Best for |
|--------|------|------------|----------|
| Azure Static Web Apps | Free tier | Low–Medium | Azure-native workflows |
| ReadTheDocs | Free (open source) | Low | Open-source projects |
| Netlify | Free tier | Low | Quick setup, any platform |
| Vercel | Free tier | Low | Quick setup, any platform |
| Azure Blob Storage | Pay-as-you-go | Medium | Full control, private docs |

---

## Option 1: Azure Static Web Apps (Recommended for Azure DevOps)

[Azure Static Web Apps](https://azure.microsoft.com/en-us/products/app-service/static) is the closest equivalent to GitHub Pages when working within the Azure ecosystem.

**Free tier includes:** 100 GB bandwidth/month, custom domains, SSL, preview environments.

### Setup Steps

1. **Build your docs first** — add a build step to your release pipeline:

   ```yaml
   - script: |
       uv run mkdocs build -d site
     displayName: 'Build documentation'
   ```

2. **Create an Azure Static Web App** in the Azure Portal:
   - Go to **Azure Portal → Create a resource → Static Web App**
   - Choose your subscription and resource group
   - Set the build preset to **Custom**
   - Set the app location to `/` and output location to `site`

3. **Add the deployment task** to your Azure pipeline (after the build step):

   ```yaml
   - task: AzureStaticWebApp@0
     inputs:
       app_location: '/'
       output_location: 'site'
       skip_app_build: true
     env:
       azure_static_web_apps_api_token: $(AZURE_STATIC_WEB_APPS_API_TOKEN)
   ```

4. **Store the deployment token** in Azure DevOps:
   - In the Azure Portal, go to your Static Web App → **Manage deployment token**
   - Copy the token
   - In Azure DevOps → **Pipelines → Library → Variable groups** → add `AZURE_STATIC_WEB_APPS_API_TOKEN` as a secret variable

### Key difference from GitHub Pages

GitHub Pages deploys via `mkdocs gh-deploy --force` (which pushes to a `gh-pages` branch). Azure Static Web Apps uses an API token and a dedicated Azure DevOps task instead.

---

## Option 2: ReadTheDocs (Recommended for Open-Source Projects)

[ReadTheDocs](https://readthedocs.org) is platform-agnostic and works with any Git host (GitHub, GitLab, Bitbucket, Azure Repos). It's free for public/open-source projects.

### Setup Steps

1. Sign up at [readthedocs.org](https://readthedocs.org)
2. Connect your repository (supports GitHub, GitLab, Bitbucket, and manual Git URL)
3. Add a `.readthedocs.yaml` config file to your repo:

   ```yaml
   version: 2
   build:
     os: ubuntu-22.04
     tools:
       python: "3.12"
   mkdocs:
     configuration: mkdocs.yml
   python:
     install:
       - requirements: docs/requirements.txt
   ```

4. ReadTheDocs will automatically build and deploy on every push — **no Azure DevOps pipeline step required**.

### Advantages

- Zero Azure DevOps integration needed
- Automatic versioning (build docs per release tag)
- Search built-in
- Works regardless of which CI/CD system you use

---

## Option 3: Netlify

[Netlify](https://www.netlify.com) offers a generous free tier and can deploy from any Git repository.

### Setup Steps

1. Sign up at [netlify.com](https://www.netlify.com)
2. Connect your repository
3. Set build command: `pip install uv && uv run mkdocs build -d site`
4. Set publish directory: `site`

Netlify deploys automatically on every push — no Azure DevOps step required.

---

## Option 4: Vercel

[Vercel](https://vercel.com) is similar to Netlify and works well for static sites.

### Setup Steps

1. Sign up at [vercel.com](https://vercel.com)
2. Import your repository
3. Add a `vercel.json`:

   ```json
   {
     "buildCommand": "pip install uv && uv run mkdocs build -d site",
     "outputDirectory": "site"
   }
   ```

---

## Option 5: Azure Blob Storage + Static Website

For private documentation or full control, use Azure Blob Storage with static website hosting enabled.

### Setup Steps

1. Create a Storage Account in the Azure Portal
2. Enable **Static website** under **Data management**
3. Note the primary endpoint URL
4. Add these steps to your Azure pipeline:

   ```yaml
   - script: |
       uv run mkdocs build -d site
     displayName: 'Build documentation'

   - task: AzureCLI@2
     inputs:
       azureSubscription: '<your-service-connection>'
       scriptType: bash
       scriptLocation: inlineScript
       inlineScript: |
         az storage blob upload-batch \
           --account-name <storage-account-name> \
           --destination '$web' \
           --source site \
           --overwrite
     displayName: 'Deploy documentation to Azure Blob Storage'
   ```

---

## Summary

- For **Azure-native** setups: use **Azure Static Web Apps**
- For **open-source** projects: use **ReadTheDocs** (simplest, no pipeline config needed)
- For **quick setup** regardless of platform: use **Netlify** or **Vercel**
- For **private/corporate** docs with Azure: use **Azure Blob Storage**
