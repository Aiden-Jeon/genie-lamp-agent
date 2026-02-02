---
name: deploy-dev
description: Deploy the Genie Lamp Agent to development (krafton-sandbox) with automated frontend build. Use when the user asks to deploy to dev, publish to dev, or update the dev app. Automatically builds the frontend, deploys the bundle, and updates the app with the correct source code path.
---

# Genie Lamp Agent - Development Deployment

Deploy the Genie Lamp Agent to the development environment (krafton-sandbox) with automated frontend build and deployment.

## ⚠️ CRITICAL SAFETY WARNING

**DO NOT DELETE THE APP DURING DEPLOYMENT**

The Genie Lamp Agent app has been granted permissions via the Databricks UI. **Deleting the app loses everything:**
- App identity and all granted permissions
- User access to the application
- All app configuration and state

**What NOT to do:**
- ❌ `databricks apps delete genie-lamp-agent-dev` - NEVER run this
- ❌ `databricks apps trash genie-lamp-agent-dev` - NEVER run this

**Safe operations:**
- ✅ Deploy/update app code with this skill (bundle deploy)
- ✅ View app status and logs
- ✅ Check permissions (read-only)

**See `.claude/rules/app-permissions.md` for complete safety guidelines.**

Bundle deploy automatically handles both initial and update deployments safely.

## Development Configuration

This skill is specifically configured for **development deployment** with the following hardcoded settings:

- **Environment**: `dev`
- **Profile**: `krafton-sandbox`
- **Source Code Path**: `/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files`
- **App Name**: `genie-lamp-agent-dev`

## What This Skill Does

The development deployment skill automates the complete deployment workflow:

1. **Build Frontend** - Runs `npm run build` in the frontend directory
2. **Deploy Bundle and App** - Executes `databricks bundle deploy -t dev -p krafton-sandbox`

Note: Databricks Asset Bundle deployment handles the complete app lifecycle (create/update) automatically. No separate app start or deploy commands needed.

## Prerequisites

Before deploying to development, ensure:

1. **Databricks CLI is installed** and configured
   ```bash
   databricks --version
   ```

2. **You're in the project root directory**
   ```bash
   cd /path/to/genie-lamp-agent
   ```

3. **Frontend dependencies are installed**
   ```bash
   cd frontend && npm install && cd ..
   ```

4. **Databricks profile is configured**
   ```bash
   databricks configure --profile krafton-sandbox
   ```

## Usage

Deploy to development environment:

```bash
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py
```

This single command handles both initial deployments and updates. Bundle deploy automatically detects whether the app exists and takes the appropriate action.

## Deployment Process

### Step-by-Step Workflow

#### 1. Frontend Build
The skill automatically builds the frontend:
```bash
cd frontend && npm run build && cd ..
```

This creates an optimized production build in `frontend/out/`.

#### 2. Bundle Deploy (Handles App Deployment)
Deploys the bundle to the development environment:
```bash
databricks bundle deploy -t dev -p krafton-sandbox
```

This single command:
- Uploads all files to `/Workspace/Users/p.jongseob.jeon@partner.krafton.com/.bundle/genie-lamp-agent/dev/files`
- Creates or updates the app configuration
- Starts/restarts the app automatically
- Applies all settings from databricks.yml

## Common Scenarios

### Scenario 1: Backend Code Changes
You've made changes to backend code and want to deploy to dev.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py
```

The frontend build will run (ensuring consistency) but won't change if there are no frontend modifications.

### Scenario 2: Frontend Changes
You've made changes to the frontend and want to deploy to dev.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py
```

The frontend build will create a new optimized build and deploy it.

### Scenario 3: Configuration Changes
You've updated `databricks.yml`, `app.yaml`, or environment settings.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py
```

The bundle deploy will pick up the configuration changes.

### Scenario 4: First-Time Dev Deployment
You're deploying the app to dev for the first time.

**Steps:**
1. Ensure all prerequisites are met
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-dev/scripts/deploy_dev.py
```

Bundle deploy automatically handles initial setup.

## Troubleshooting

### Error: "databricks command not found"
**Solution:** Install Databricks CLI
```bash
pip install databricks-cli
# or
brew install databricks
```

### Error: "Profile krafton-sandbox not found"
**Solution:** Configure the profile
```bash
databricks configure --profile krafton-sandbox
```

Provide:
- Host: Your Databricks workspace URL
- Token: Your personal access token

### Error: "npm: command not found"
**Solution:** Install Node.js and npm
```bash
# macOS
brew install node

# Verify installation
node --version
npm --version
```

### Error: "Frontend build failed"
**Solution:** Check frontend dependencies
```bash
cd frontend
npm install
npm run build
cd ..
```

### Error: "Bundle deploy failed"
**Solution:** Check databricks.yml configuration
- Verify `databricks.yml` exists in project root
- Check that the dev target is configured
- Ensure permissions are correct for your user workspace

### Error: "App already exists"
**Solution:** Bundle deploy handles this automatically - no action needed. If you see this error, it's likely from manual CLI commands, not from this skill.

### Error: "Source code path not found"
**Solution:** Verify bundle deployment succeeded
- Check that bundle deploy completed successfully
- Verify the source code path exists in your Workspace
- Check that the username in the path matches your Databricks email

## Verifying Deployment

After deployment, verify the app is running:

### Check App Status
```bash
databricks apps list -p krafton-sandbox | grep genie-lamp-agent-dev
```

### View App Details
```bash
databricks apps get genie-lamp-agent-dev -p krafton-sandbox
```

### Check App Logs
```bash
databricks apps logs genie-lamp-agent-dev -p krafton-sandbox
```

### Access the App
Navigate to your Databricks workspace:
- **Workspace** > **Apps** > **genie-lamp-agent-dev**

Or use the direct URL provided in the deployment output.

## Dev vs Prod Deployment

### Key Differences

| Aspect | Development (deploy-dev) | Production (deploy-prod) |
|--------|-------------------------|--------------------------|
| Profile | `krafton-sandbox` | `krafton-sandbox` |
| Target | `dev` | `prod` |
| App Name | `genie-lamp-agent-dev` | `genie-lamp-agent` |
| Source Path | `/Workspace/Users/<user>/...` | `/Workspace/Shared/...` |
| Frontend Build | Automated | Automated |
| Workflow | Fully automated | Fully automated |

### When to Use Each

**Use deploy-dev when:**
- Testing changes before production
- Rapid iteration and development
- Experimenting with new features
- User-specific testing environment

**Use deploy-prod when:**
- Deploying to production environment
- Changes that affect all users
- Stable, tested features
- Shared production workspace

## Safety Checklist

Before deploying to dev:

- [ ] Frontend dependencies are installed
- [ ] Databricks CLI is configured
- [ ] You're in the project root directory
- [ ] Using `--update` flag for existing apps
- [ ] Ready to test changes in dev environment

## Best Practices

1. **Test in dev first** - Always deploy to dev before prod
2. **Use version control** - Commit changes before deploying
3. **Verify configuration** - Check `databricks.yml` and `app.yaml`
4. **Monitor after deployment** - Watch logs for errors
5. **Keep dependencies updated** - Run `npm update` periodically
6. **Document changes** - Use clear commit messages

## Related Skills

- **deploy-prod**: Production deployment with same automated workflow
- **deploy-app**: Flexible deployment for any environment
- **deploy-local**: Local development and testing
- **genie-commit**: Automated git commits with testing and validation

## Support

If you encounter issues:

1. Check this documentation first
2. Review `.claude/rules/app-permissions.md` for safety guidelines
3. Check app logs for detailed error messages
4. Contact the workspace administrator
5. Create an issue in the project repository
