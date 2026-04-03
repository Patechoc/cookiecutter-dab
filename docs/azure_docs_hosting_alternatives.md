# Hosting Internal Documentation on Azure Static Web Apps

This page describes how to deploy MkDocs-generated documentation to **Azure Static Web Apps (SWA)** as an alternative to GitHub Pages, with access restricted to employees authenticated via the organization's Azure tenant (i.e. only `@redcross.no` accounts).

---

## Why Azure Static Web Apps

Azure Static Web Apps (SWA) is the natural GitHub Pages equivalent when working within the Azure ecosystem. It integrates directly with Azure DevOps pipelines and supports **Azure Entra ID (formerly Azure AD) authentication out of the box**, making it straightforward to lock down access to your organization's tenant.

---

## What needs to exist before deployment works

Three separate Azure resources must be in place, each depending on the previous:

1. **Azure Static Web App (SWA)** — the hosting resource. Once created it issues a **deployment token**, which is the credential used to push built files into the site. Without this resource nothing can be deployed.

2. **Entra ID App Registration** — an OAuth application registered in the `redcross.no` Azure tenant. SWA needs a client ID and client secret from this registration to know _which_ identity provider to use and _which_ tenant to trust. The app registration must point its redirect URI at the SWA hostname, so it must be created after the SWA hostname is known.

3. **`staticwebapp.config.json`** in the repository root — tells SWA to require authentication on all routes and which Entra ID tenant/app to use. This file references the app registration's tenant ID and the application settings (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`) that are set on the SWA resource.

The deployment itself (manual or via CI/CD) only needs the **deployment token**. Authentication enforcement is entirely driven by `staticwebapp.config.json` and the application settings on the SWA resource — the pipeline does not need to know anything about Entra ID.

**Dependency order:**

```text
1. Create SWA resource
        │ → produces: SWA hostname, deployment token
        ▼
2. Register App in Entra ID
        │ inputs:  SWA hostname (for redirect URI)
        │ outputs: client ID, client secret, tenant ID
        ▼
3. Set app settings on SWA resource
        │ inputs:  client ID, client secret (from step 2)
        ▼
4. Add staticwebapp.config.json to repository
        │ inputs:  tenant ID (from step 2)
        ▼
5. Deploy (manually or via pipeline)
           inputs:  deployment token (from step 1)
```

---

## Step 1 — Create the Azure Static Web App

1. Go to **Azure Portal → Create a resource → Static Web App**
2. Choose your subscription and resource group
3. Set the build preset to **Custom**
4. Set **App location** to `/` and **Output location** to `site`
5. Under **Authentication provider**, leave this blank for now — auth is configured via `staticwebapp.config.json` (see Step 3)

Note the **deployment token** once the resource is created (**Manage deployment token** in the SWA blade).

---

## Step 2 — Configure the Azure DevOps Pipeline

Add the following stages to your release pipeline (e.g. `azure-pipelines.yml`):

```yaml
- stage: Docs
  displayName: 'Build and Deploy Documentation'
  jobs:
    - job: BuildAndDeploy
      pool:
        vmImage: ubuntu-latest
      steps:
        - script: |
            pip install uv
            uv run mkdocs build -d site
          displayName: 'Build documentation'

        - task: AzureStaticWebApp@0
          inputs:
            app_location: '/'
            output_location: 'site'
            skip_app_build: true
          env:
            azure_static_web_apps_api_token: $(AZURE_STATIC_WEB_APPS_API_TOKEN)
          displayName: 'Deploy documentation to Azure SWA'
```

Store the deployment token as a **secret variable** in Azure DevOps:

- Go to **Pipelines → Library → Variable groups**
- Add `AZURE_STATIC_WEB_APPS_API_TOKEN` with the token value, marked as secret

---

## Step 3 — Restrict Access to `@redcross.no` Accounts

Azure SWA supports route-level authentication and authorization via a `staticwebapp.config.json` file placed at the **root of your repository** (not inside `site/` — SWA reads this file directly).

### 3a. Require login for all routes

```json
{
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/<YOUR_TENANT_ID>/v2.0",
          "clientIdSettingName": "AZURE_CLIENT_ID",
          "clientSecretSettingName": "AZURE_CLIENT_SECRET"
        }
      }
    }
  },
  "routes": [
    {
      "route": "/*",
      "allowedRoles": ["authenticated"]
    }
  ],
  "responseOverrides": {
    "401": {
      "statusCode": 302,
      "redirect": "/.auth/login/aad"
    }
  }
}
```

Replace `<YOUR_TENANT_ID>` with the **tenant ID** of the `redcross.no` Azure Entra ID tenant (find it in **Azure Portal → Entra ID → Overview**).

This configuration:

- Forces all visitors to log in via Azure Entra ID before seeing any page
- Redirects unauthenticated requests to the login page automatically

### 3b. Register an App in Entra ID

1. Go to **Azure Portal → Entra ID → App registrations → New registration**
2. Name: e.g. `docs-portal`
3. Supported account types: **Accounts in this organizational directory only (Single tenant)**
   - This ensures only accounts in your `redcross.no` tenant can authenticate
4. Redirect URI: `https://<your-swa-hostname>/.auth/login/aad/callback`
5. After creation, note the **Application (client) ID** and create a **Client secret** under **Certificates & secrets**

Add these as **application settings** in your SWA resource (Azure Portal → SWA → Configuration):

| Name                  | Value                                            |
|-----------------------|--------------------------------------------------|
| `AZURE_CLIENT_ID`     | _(Application client ID from app registration)_  |
| `AZURE_CLIENT_SECRET` | _(Client secret value)_                          |

### 3c. Why single-tenant is sufficient

By registering the app as **single-tenant** (accounts in this organizational directory only), Azure Entra ID rejects login attempts from any Microsoft account outside your `redcross.no` tenant — no additional domain filtering is needed. Any employee with a `@redcross.no` account can log in; anyone without one cannot.

If you need finer-grained control (e.g. only a specific security group within the org), see [Step 4](#step-4--optional-restrict-to-a-specific-entra-id-group).

---

## Step 4 — Optional: Restrict to a Specific Entra ID Group

If you want to limit access beyond the entire tenant (e.g. only the data platform team), you can use **custom roles** backed by an Entra ID group.

### 4a. Add a roles function

Create an Azure Function (or use SWA's built-in invitations API) to assign roles based on group membership. The simplest approach uses an **API route** in SWA:

`api/GetRoles/index.js`:

```js
const { Client } = require('@microsoft/microsoft-graph-client');

module.exports = async function (context, req) {
  const userId = req.headers['x-ms-client-principal-id'];
  // Use Microsoft Graph to check group membership and return roles
  // Return { "roles": ["docs-reader"] } if user is in the allowed group
};
```

### 4b. Update `staticwebapp.config.json`

```json
{
  "routes": [
    {
      "route": "/*",
      "allowedRoles": ["docs-reader"]
    }
  ]
}
```

This is optional — for most internal documentation the single-tenant restriction is sufficient.

---

## Step 5 — Custom Domain (Optional)

To serve the docs under a custom subdomain (e.g. `docs.redcross.no`):

1. Go to **SWA → Custom domains → Add**
2. Enter your domain and follow the CNAME/TXT verification steps
3. SSL is provisioned automatically via Let's Encrypt

---

## Summary

| Step                           | What it does                                           |
|--------------------------------|--------------------------------------------------------|
| Create SWA resource            | Provisions the hosting infrastructure                  |
| Azure DevOps pipeline          | Builds MkDocs site and deploys on every push to `main` |
| `staticwebapp.config.json`     | Forces authentication for all routes                   |
| Single-tenant app registration | Restricts login to `@redcross.no` accounts only        |
| (Optional) Group-based roles   | Further restricts access to a specific team or group   |

The result is a private internal documentation site, automatically updated on every merge, accessible only to employees authenticated with their `@redcross.no` Microsoft account.
