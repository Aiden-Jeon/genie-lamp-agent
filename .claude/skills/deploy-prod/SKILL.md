---
name: deploy-prod
description: Deploy the Genie Lamp Agent to production (krafton-sandbox) with automated frontend build. Use when the user asks to deploy to production, publish to prod, or update the production app. Automatically builds the frontend, deploys the bundle, and updates the app with the correct source code path.
---

# Genie Lamp Agent - Production Deployment

Deploy the Genie Lamp Agent to the production environment (krafton-sandbox) with automated frontend build and deployment.

## ⚠️ CRITICAL SAFETY WARNING

**DO NOT DELETE THE APP DURING DEPLOYMENT**

The Genie Lamp Agent app has been granted permissions via the Databricks UI. **Deleting the app loses everything:**
- App identity and all granted permissions
- User access to the application
- All app configuration and state

**What NOT to do:**
- ❌ `databricks apps delete genie-lamp-agent` - NEVER run this
- ❌ `databricks apps trash genie-lamp-agent` - NEVER run this

**Safe operations:**
- ✅ Deploy/update app code with this skill (bundle deploy)
- ✅ View app status and logs
- ✅ Check permissions (read-only)

**See `.claude/rules/app-permissions.md` for complete safety guidelines.**

Bundle deploy automatically handles both initial and update deployments safely.

## Production Configuration

This skill is specifically configured for **production deployment** with the following hardcoded settings:

- **Environment**: `prod`
- **Profile**: `krafton-sandbox`
- **Source Code Path**: `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files`
- **App Name**: `genie-lamp-agent`

## What This Skill Does

The production deployment skill automates the complete deployment workflow:

1. **Build Frontend** - Runs `npm run build` in the frontend directory
2. **Deploy Bundle and App** - Executes `databricks bundle deploy -t prod -p krafton-sandbox`

Note: Databricks Asset Bundle deployment handles the complete app lifecycle (create/update) automatically. No separate app start or deploy commands needed.

## Prerequisites

Before deploying to production, ensure:

1. **Databricks CLI is installed** and configured
   ```bash
   databricks --version
   ```

2. **You're in the project root directory**
   ```bash
   cd /path/to/genie-lamp-agent-prod
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

Deploy to production environment:

```bash
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
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
Deploys the bundle to the production environment:
```bash
databricks bundle deploy -t prod -p krafton-sandbox
```

This single command:
- Uploads all files to `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files`
- Creates or updates the app configuration
- Starts/restarts the app automatically
- Applies all settings from databricks.yml

## Common Scenarios

### Scenario 1: Backend Code Changes
You've made changes to backend code and want to deploy to production.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
```

The frontend build will run (ensuring consistency) but won't change if there are no frontend modifications.

### Scenario 2: Frontend Changes
You've made changes to the frontend and want to deploy to production.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
```

The frontend build will create a new optimized build and deploy it.

### Scenario 3: Configuration Changes
You've updated `databricks.yml`, `app.yaml`, or environment settings.

**Steps:**
1. Commit your changes
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
```

The bundle deploy will pick up the configuration changes.

### Scenario 4: First-Time Production Deployment
You're deploying the app to production for the first time.

**Steps:**
1. Ensure all prerequisites are met
2. Run the deployment skill

```bash
.venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
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
- Check that the prod target is configured
- Ensure permissions are correct for `/Workspace/Shared/databricks-agent-poc/genie-lamp-app`

### Error: "App already exists"
**Solution:** Bundle deploy handles this automatically - no action needed. If you see this error, it's likely from manual CLI commands, not from this skill.

### Error: "Source code path not found"
**Solution:** Verify bundle deployment succeeded
- Check that bundle deploy completed successfully
- Verify `/Workspace/Shared/databricks-agent-poc/genie-lamp-app/files` exists in Workspace
- Check that your user has access to the shared workspace

## Verifying Deployment

After deployment, verify the app is running:

### Check App Status
```bash
databricks apps list -p krafton-sandbox | grep genie-lamp-agent
```

### View App Details
```bash
databricks apps get genie-lamp-agent -p krafton-sandbox
```

### Check App Logs
```bash
databricks apps logs genie-lamp-agent -p krafton-sandbox
```

### Access the App
Navigate to your Databricks workspace:
- **Workspace** > **Apps** > **genie-lamp-agent**

Or use the direct URL provided in the deployment output.

## Production vs Dev Deployment

### Key Differences

| Aspect | Production (deploy-prod) | Development (deploy-app) |
|--------|-------------------------|--------------------------|
| Profile | `krafton-sandbox` | `krafton-sandbox` |
| Target | `prod` | `dev` |
| Source Path | `/Workspace/Shared/...` | `/Workspace/Users/<user>/...` |
| Frontend Build | Automated | Manual (user's responsibility) |
| Workflow | Fully automated | Flexible (manual steps) |

### When to Use Each

**Use deploy-prod when:**
- Deploying to production environment
- Want fully automated workflow
- Need consistent, reproducible deployments
- Deploying changes that affect users

**Use deploy-app when:**
- Deploying to dev environment
- Testing changes before production
- Need flexibility in deployment steps
- Want to control each step manually

## Safety Checklist

Before deploying to production:

- [ ] Code has been tested in dev environment
- [ ] All tests pass (if applicable)
- [ ] Changes have been reviewed
- [ ] Commit message follows conventions
- [ ] No sensitive data in code or logs
- [ ] Frontend builds successfully
- [ ] Bundle configuration is correct
- [ ] Backup plan in case of issues

## Rollback Procedure

If deployment causes issues:

1. **Stop immediately** - Don't make additional changes

2. **Check app logs** for errors:
   ```bash
   databricks apps logs genie-lamp-agent -p krafton-sandbox
   ```

3. **Revert code changes** and redeploy:
   ```bash
   git revert <commit-hash>
   .venv/bin/python .claude/skills/deploy-prod/scripts/deploy_prod.py
   ```

4. **Contact admin** if app is unresponsive or permissions are affected

5. **Document the issue** for post-mortem analysis

## Best Practices

1. **Always test in dev first** - Deploy to dev environment before prod
2. **Use version control** - Commit changes before deploying
3. **Deploy during low-traffic periods** - Minimize user impact
4. **Monitor after deployment** - Watch logs for errors
5. **Document changes** - Use clear commit messages
6. **Keep frontend dependencies updated** - Run `npm update` periodically
7. **Verify configuration** - Check `databricks.yml` and `app.yaml` before deploying

## Related Skills

- **genie-commit**: Automated git commits with testing and validation
- **deploy-app**: Flexible deployment for dev environment
- **deploy-local**: Local development and testing

## Support

If you encounter issues:

1. Check this documentation first
2. Review `.claude/rules/app-permissions.md` for safety guidelines
3. Check app logs for detailed error messages
4. Contact the workspace administrator
5. Create an issue in the project repository
