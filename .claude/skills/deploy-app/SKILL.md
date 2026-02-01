---
name: deploy-app
description: Deploy the Genie Lamp Agent Databricks app using Databricks Bundle. Use when the user asks to deploy, publish, or update the Genie Lamp app. Handles both initial deployments (first time) and update deployments (code modifications). Automatically determines deployment type and executes the appropriate sequence of databricks CLI commands.
---

# Genie Lamp Agent App Deployment

Deploy the Genie Lamp Agent Databricks app through Databricks Bundle with automatic handling of initial and update deployments.

## ⚠️ CRITICAL SAFETY WARNING

**DO NOT DELETE THE APP DURING DEPLOYMENT**

The Genie Lamp Agent app has been granted permissions via the Databricks UI. **Deleting the app loses everything:**
- App identity and all granted permissions
- User access to the application
- All app configuration and state

**What NOT to do:**
- ❌ `databricks apps delete genie-lamp-agent` - NEVER run this
- ❌ `databricks apps trash genie-lamp-agent` - NEVER run this
- ❌ Using `--initial` flag on existing app - Use `--update` instead

**Safe operations:**
- ✅ Deploy/update app code with `--update` flag (this skill)
- ✅ View app status and logs
- ✅ Check permissions (read-only)

**See `.claude/rules/app-permissions.md` for complete safety guidelines.**

When deploying, ALWAYS use `--update` for existing apps. This preserves the app and its permissions.

## Project-Specific Configuration

This skill is configured for the **Genie Lamp Agent** project with the following settings:

- **Bundle Name**: `genie-lamp-agent`
- **App Resource Name**: `genie_lamp_app` (defined in `databricks.yml`)
- **App Display Name**: `genie-lamp-agent`
- **Project Structure**: Root-level deployment (databricks.yml at project root)
- **Available Environments**: `dev` (default), `prod`

## Deployment Process

### Prerequisites

Before deploying, ensure:

1. **Databricks CLI is installed** and configured
   ```bash
   databricks --version
   ```

2. **You're in the project root directory**
   ```bash
   cd /path/to/genie-lamp-agent
   ```

3. **Environment variables are configured** in `.env` file:
   - `DATABRICKS_HOST`: Your workspace URL
   - `DATABRICKS_TOKEN`: Your personal access token
   - `DATABRICKS_HTTP_PATH`: SQL Warehouse HTTP path (optional, can be configured in app.yaml)

4. **Frontend is built** (if deploying for the first time or after frontend changes)
   ```bash
   cd frontend && npm run build && cd ..
   ```

### Determining Deployment Information

The skill needs:

1. **Environment**: Target environment (`dev` or `prod`)
2. **Profile**: Databricks profile name (use `krafton-sandbox` for this project)
3. **Source Code Path**: Workspace path to the bundled files
4. **Deployment Type**: Whether this is an initial deployment or an update

### Source Code Path Pattern

The source code path for Genie Lamp Agent follows this pattern:
```
/Workspace/Users/<username>/.bundle/genie-lamp-agent/<environment>/files
```

**Example for dev environment:**
```
/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files
```

**To find the correct source code path:**
Get the current app configuration with `databricks apps get genie-lamp-agent -p krafton-sandbox` and look for the `source_code_path` field.

### Environment Configuration

The deployment uses environment variables from your `.env` file:
- `DATABRICKS_HOST`: Workspace URL (used by Databricks CLI)
- `DATABRICKS_TOKEN`: Authentication token (used by Databricks CLI)
- `DATABRICKS_HTTP_PATH`: SQL Warehouse path (can be configured in app.yaml)

### Determining Deployment Type

Ask the user: "Is this the first time deploying the Genie Lamp app, or is this an update to an existing deployment?"

- **Initial deployment** (`--initial`): First time deploying the app - includes `databricks apps start`
- **Update deployment** (`--update`): App already exists and you're updating the code - skips `apps start`

## Using the Deployment Script

**IMPORTANT**: Always run the deployment script from the project root directory.

Execute the deployment using `.claude/skills/deploy-app/scripts/deploy_app.py`:

**For initial deployment:**
```bash
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target <environment> \
  --profile <profile> \
  --source-code-path <path> \
  --initial
```

**For update deployment:**
```bash
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target <environment> \
  --profile <profile> \
  --source-code-path <path> \
  --update
```

**Example:**
```bash
# Initial deployment to dev environment
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile krafton-sandbox \
  --source-code-path /Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files \
  --initial

# Update deployment to dev environment
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile krafton-sandbox \
  --source-code-path /Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files \
  --update

# Production deployment (update)
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target prod \
  --profile krafton-sandbox \
  --source-code-path /Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/prod/files \
  --update
```

## What the Script Does

The deployment script executes Databricks CLI commands from the project root directory (where `databricks.yml` is located).

### Initial Deployment (--initial flag)
1. Runs `databricks bundle deploy -t <env> -p <profile>` (deploys bundle resources)
2. Runs `databricks apps start genie-lamp-agent -p <profile>` (starts the app for the first time)
3. Runs `databricks apps deploy genie-lamp-agent --source-code-path <path> -p <profile>` (deploys app code)

### Update Deployment (--update flag)
1. Runs `databricks bundle deploy -t <env> -p <profile>` (updates bundle resources)
2. Skips the `apps start` command (app already running)
3. Runs `databricks apps deploy genie-lamp-agent --source-code-path <path> -p <profile>` (updates app code)

## Project-Specific Workflow

### Complete Deployment Workflow

When deploying the Genie Lamp Agent app, follow this complete workflow:

#### 1. Make Code Changes
```bash
# Backend changes
cd backend
# ... make changes ...
cd ..

# Frontend changes
cd frontend
# ... make changes ...
cd ..
```

#### 2. Build Frontend (if frontend changed)
```bash
cd frontend
npm run build
cd ..
```

#### 3. Deploy Using the Script
```bash
# From project root
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile krafton-sandbox \
  --source-code-path /Workspace/Users/<username>/.bundle/genie-lamp-agent/dev/files \
  --update
```

### Common Scenarios

**Scenario 1: Backend-only changes**
- No need to rebuild frontend
- Just run the deployment script with `--update`

**Scenario 2: Frontend changes**
- Build frontend: `cd frontend && npm run build && cd ..`
- Run the deployment script with `--update`

**Scenario 3: Configuration changes in databricks.yml or app.yaml**
- Run the deployment script with `--update`
- The bundle deploy will pick up configuration changes

**Scenario 4: First-time deployment**
- Ensure `.env` file is configured with `DATABRICKS_HOST`, `DATABRICKS_TOKEN`
- Build frontend: `cd frontend && npm run build && cd ..`
- Run the deployment script with `--initial`

### Troubleshooting

**Error: "databricks command not found"**
- Install Databricks CLI: `pip install databricks-cli`
- Or: `brew install databricks`

**Error: "Profile DEFAULT not found"**
- Configure Databricks CLI: `databricks configure --profile krafton-sandbox`
- Provide host and token
- Or ensure `.env` file contains `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

**Error: "Environment variable not set"**
- Check that `.env` file exists in project root
- Verify it contains: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`
- Source the environment: `source .env` (if needed)

**Error: "App already exists" during initial deployment**
- Use `--update` flag instead of `--initial`
- Or delete the existing app first

**Error: "Source code path not found"**
- Verify the bundle was deployed successfully
- Check the path exists in Workspace
- Ensure username in path matches your Databricks email

### Verifying Deployment

After deployment, verify the app is running:

```bash
# Check app status
databricks apps list -p krafton-sandbox

# View app logs (if needed)
databricks apps logs genie-lamp-agent -p krafton-sandbox
```

Access the app through the Databricks workspace:
- Navigate to: **Workspace** > **Apps** > **genie-lamp-agent**
