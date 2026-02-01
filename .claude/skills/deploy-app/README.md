# Deploy App Skill

Automated Databricks app deployment using Asset Bundles.

## Overview

This skill deploys the Genie Lamp Agent web application to Databricks Apps using `databricks bundle sync` and `databricks bundle deploy`.

## Features

- Source code upload via `databricks bundle sync`
- Configuration deployment via `databricks bundle deploy`
- Support for both initial and update deployments
- Environment-specific deployments (dev, prod)
- Pre-deployment validation (frontend build, config files)
- Automatic app name resolution based on environment

## Usage

### Update Deployment (Most Common)

For existing apps, use the `--update` flag:

```bash
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py \
  --target dev \
  --profile DEFAULT \
  --update
```

This is safe for all deployments after the initial one and preserves:
- App identity and service principal
- All UI-granted permissions
- App state and configuration

### Initial Deployment (First Time Only)

For the very first deployment, use the `--initial` flag:

```bash
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py \
  --target dev \
  --profile DEFAULT \
  --initial
```

**⚠️ Warning:** Only use `--initial` when deploying for the first time. Using it on an existing app may cause issues.

## Parameters

- `--target`, `-t`: Environment (dev or prod), default: dev
- `--profile`, `-p`: Databricks CLI profile, default: DEFAULT
- `--initial`: Flag for initial deployment (includes app start)
- `--update`: Flag for update deployment (skips app start)

If neither `--initial` nor `--update` is specified, defaults to `--update` (safe choice).

## Prerequisites

1. **Databricks CLI** installed and authenticated:
   ```bash
   databricks current-user me --profile DEFAULT
   ```

2. **Frontend built** (if deploying after frontend changes):
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

3. **databricks.yml** exists in project root

4. **Running from project root** (where databricks.yml is located)

## How It Works

### 1. Bundle Sync

Uploads source code to workspace:

```bash
databricks bundle sync -t <env> -p <profile>
```

**Uploads:**
- `frontend/out/**` - Production frontend build
- `backend/**` - Backend Python code
- `app.yaml` - App runtime configuration

**Destination:** `/Workspace/Users/<user>/.bundle/genie-lamp-agent/<env>/files/`

### 2. Bundle Deploy

Applies configuration from databricks.yml:

```bash
databricks bundle deploy -t <env> -p <profile>
```

**Creates/Updates:**
- App resource
- SQL warehouse access
- Permissions
- App metadata

**Important:** Bundle deploy automatically triggers the app to reload with new code and configuration. **No manual stop/start is needed** for updates - the app picks up changes automatically.

### 3. App Start (Initial Only)

For initial deployments, starts the app:

```bash
databricks apps start <app-name> -p <profile>
```

For updates, this step is **skipped** - the app auto-reloads from bundle deploy.

## Examples

### Full Workflow with Frontend Changes

```bash
# 1. Rebuild frontend
cd frontend && npm run build && cd ..

# 2. Deploy to dev
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py \
  --target dev \
  --profile DEFAULT \
  --update

# 3. Verify
databricks apps list | grep genie-lamp-agent
```

### Deploy to Production

```bash
.venv/bin/python .claude/skills/deploy-app/scripts/deploy_app.py \
  --target prod \
  --profile DEFAULT \
  --update
```

### Verify Deployment

```bash
# List apps
databricks apps list --profile DEFAULT | grep genie-lamp-agent

# Get app details
databricks apps get genie-lamp-agent --profile DEFAULT

# View logs
databricks apps logs genie-lamp-agent --profile DEFAULT
```

## Troubleshooting

### Frontend Not Updated

**Issue:** App shows old frontend after deployment

**Solution:** Rebuild frontend before deploying
```bash
cd frontend && npm run build && cd ..
```

### Bundle Sync Fails

**Issue:** Permission errors during sync

**Solution:** Verify CLI authentication
```bash
databricks current-user me --profile DEFAULT
```

### Bundle Deploy Fails

**Issue:** Validation errors during deploy

**Solution:** Validate bundle configuration
```bash
databricks bundle validate -t dev
cat databricks.yml
```

### App Won't Start

**Issue:** App deployed but not running

**Solution:** Check logs and manually start if needed
```bash
databricks apps logs genie-lamp-agent --profile DEFAULT
databricks apps start genie-lamp-agent --profile DEFAULT
```

## Safety Rules

**⚠️ CRITICAL: Never delete the app**

See `.claude/rules/app-permissions.md` for detailed safety rules.

**Safe operations:**
- ✅ Update with `--update`
- ✅ Bundle sync and deploy
- ✅ View status and logs

**Dangerous operations:**
- ❌ NEVER `databricks apps delete`
- ❌ NEVER `databricks apps trash`
- ❌ NEVER use `--initial` on existing apps

Deleting the app destroys the service principal identity and all permissions.

## Development Workflow

1. **Local Development**: Use `/deploy-local` to run locally
2. **Make Changes**: Edit code (auto-reload in local)
3. **Test Locally**: http://localhost:3000
4. **Build Frontend**: `cd frontend && npm run build && cd ..`
5. **Deploy to Databricks**: Use this skill
6. **Test in Workspace**: Access app URL

## Access URLs

After deployment:

- **Dev**: `https://<workspace-url>/apps/genie-lamp-agent`
- **Prod**: `https://<workspace-url>/apps/genie-lamp-agent-prod`

## Integration with Claude Code

This skill is automatically triggered when you ask Claude Code to:
- "deploy the app"
- "deploy genie-lamp-agent"
- "update the app"
- "publish the app to databricks"

Claude will guide you through the deployment process and handle all the commands.

## Related Skills

- **deploy-local**: Run app locally for development
- **stop-local**: Stop local development servers
- **genie-deploy**: Deploy Genie spaces from requirements
- **genie-commit**: Commit changes with validation

## References

- [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/)
- [Databricks Apps](https://docs.databricks.com/en/apps/)
- Project rules: `.claude/rules/app-permissions.md`
- Project guide: `CLAUDE.md`
