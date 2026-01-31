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
- **App Resource Name**: `genie_lamp_app` (defined in `app/databricks.yml`)
- **App Display Name**: `genie-lamp-agent`
- **Working Directory**: `app/` (where databricks.yml is located)
- **Available Environments**: `dev` (default), `prod`

## Deployment Process

### Prerequisites

Before deploying, ensure:

1. **Databricks CLI is installed** and configured
   ```bash
   databricks --version
   ```

2. **You're in the app directory**
   ```bash
   cd app/
   ```

3. **Secrets are configured** in Databricks:
   - Scope: `genie-lamp`
   - Required keys: `service-token`, `sql-warehouse-http-path`

4. **Frontend is built** (if deploying for the first time or after frontend changes)
   ```bash
   cd frontend && npm run build && cd ..
   ```

### Determining Deployment Information

The skill needs:

1. **Environment**: Target environment (`dev` or `prod`)
2. **Profile**: Databricks profile name (usually `DEFAULT`)
3. **Source Code Path**: Workspace path to the bundled files
4. **Deployment Type**: Whether this is an initial deployment or an update

### Source Code Path Pattern

The source code path for Genie Lamp Agent follows this pattern:
```
/Workspace/Users/<username>/.bundle/genie-lamp-agent/<environment>/files
```

**Example for dev environment:**
```
/Workspace/Users/jongseob.jeon@databricks.com/.bundle/genie-lamp-agent/dev/files
```

If the username is not known, ask the user for their Databricks email address.

### Determining Deployment Type

Ask the user: "Is this the first time deploying the Genie Lamp app, or is this an update to an existing deployment?"

- **Initial deployment** (`--initial`): First time deploying the app - includes `databricks apps start`
- **Update deployment** (`--update`): App already exists and you're updating the code - skips `apps start`

## Using the Deployment Script

**IMPORTANT**: Always run the deployment script from the project root, not from the app directory.

Execute the deployment using `.claude/skills/deploy-app/scripts/deploy_app.py`:

**For initial deployment:**
```bash
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target <environment> \
  --profile <profile> \
  --source-code-path <path> \
  --working-dir app \
  --initial
```

**For update deployment:**
```bash
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target <environment> \
  --profile <profile> \
  --source-code-path <path> \
  --working-dir app \
  --update
```

**Example:**
```bash
# Initial deployment to dev environment
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/jongseob.jeon@databricks.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --initial

# Update deployment to dev environment
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/jongseob.jeon@databricks.com/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --update

# Production deployment (update)
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target prod \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/jongseob.jeon@databricks.com/.bundle/genie-lamp-agent/prod/files \
  --working-dir app \
  --update
```

## What the Script Does

The deployment script changes to the `app/` directory (where `databricks.yml` is located) and executes the Databricks CLI commands.

### Initial Deployment (--initial flag)
1. Changes to working directory: `cd app/`
2. Runs `databricks bundle deploy -t <env> -p <profile>` (deploys bundle resources)
3. Runs `databricks apps start genie-lamp-agent -p <profile>` (starts the app for the first time)
4. Runs `databricks apps deploy genie-lamp-agent --source-code-path <path> -p <profile>` (deploys app code)

### Update Deployment (--update flag)
1. Changes to working directory: `cd app/`
2. Runs `databricks bundle deploy -t <env> -p <profile>` (updates bundle resources)
3. Skips the `apps start` command (app already running)
4. Runs `databricks apps deploy genie-lamp-agent --source-code-path <path> -p <profile>` (updates app code)

## Project-Specific Workflow

### Complete Deployment Workflow

When deploying the Genie Lamp Agent app, follow this complete workflow:

#### 1. Make Code Changes
```bash
# Backend changes
cd app/backend
# ... make changes ...

# Frontend changes
cd app/frontend
# ... make changes ...
```

#### 2. Build Frontend (if frontend changed)
```bash
cd app/frontend
npm run build
cd ../..
```

#### 3. Deploy Using the Script
```bash
# From project root
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev \
  --profile DEFAULT \
  --source-code-path /Workspace/Users/<username>/.bundle/genie-lamp-agent/dev/files \
  --working-dir app \
  --update
```

### Common Scenarios

**Scenario 1: Backend-only changes**
- No need to rebuild frontend
- Just run the deployment script with `--update`

**Scenario 2: Frontend changes**
- Build frontend: `cd app/frontend && npm run build && cd ../..`
- Run the deployment script with `--update`

**Scenario 3: Configuration changes in databricks.yml or app.yaml**
- Run the deployment script with `--update`
- The bundle deploy will pick up configuration changes

**Scenario 4: First-time deployment**
- Ensure secrets are configured in `genie-lamp` scope
- Build frontend: `cd app/frontend && npm run build && cd ../..`
- Run the deployment script with `--initial`

### Troubleshooting

**Error: "databricks command not found"**
- Install Databricks CLI: `pip install databricks-cli`
- Or: `brew install databricks`

**Error: "Profile DEFAULT not found"**
- Configure Databricks CLI: `databricks configure --profile DEFAULT`
- Provide host and token

**Error: "Secret scope genie-lamp not found"**
- Create secret scope in Databricks workspace
- Add required secrets: `service-token`, `sql-warehouse-http-path`

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
databricks apps list -p DEFAULT

# View app logs (if needed)
databricks apps logs genie-lamp-agent -p DEFAULT
```

Access the app through the Databricks workspace:
- Navigate to: **Workspace** > **Apps** > **genie-lamp-agent**
