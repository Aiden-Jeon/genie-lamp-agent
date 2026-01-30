# Databricks App Deployment Guide

## Prerequisites

Before deploying the Genie Lamp Agent as a Databricks App, ensure you have:

1. Databricks workspace with Apps enabled
2. Databricks CLI installed and configured
3. Unity Catalog enabled in your workspace
4. SQL Warehouse for Lakebase (database) operations
5. Appropriate permissions (workspace admin or app deployment permissions)

## Step-by-Step Deployment

### 1. Create Unity Catalog Volume

Create the volume for storing uploaded files and session data:

```bash
# Using Databricks CLI
databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/uploads
databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/sessions

# Or using SQL in workspace
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.genie_lamp;
CREATE VOLUME IF NOT EXISTS main.genie_lamp.uploads;
CREATE VOLUME IF NOT EXISTS main.genie_lamp.sessions;
```

Verify volume creation:
```bash
databricks fs ls dbfs:/Volumes/main/genie_lamp/
```

### 2. Create Databricks Secrets

Store sensitive credentials in Databricks Secrets:

```bash
# Create secret scope
databricks secrets create-scope genie-lamp

# Add service token (use a service principal token in production)
databricks secrets put-secret genie-lamp service-token --string-value "YOUR_DATABRICKS_TOKEN"

# Add SQL warehouse HTTP path
# Find this in: SQL Warehouses → Your Warehouse → Connection Details → HTTP Path
databricks secrets put-secret genie-lamp sql-warehouse-http-path --string-value "/sql/1.0/warehouses/YOUR_WAREHOUSE_ID"
```

List secrets to verify:
```bash
databricks secrets list-secrets genie-lamp
```

### 3. Prepare SQL Warehouse

Ensure you have a SQL Warehouse running for Lakebase operations:

```bash
# List available warehouses
databricks sql warehouses list

# Start a warehouse if needed
databricks sql warehouses start <warehouse-id>
```

Note the warehouse HTTP path for the secrets configuration above.

### 4. Build and Package the App

From the project root:

```bash
cd app

# Install backend dependencies (for validation)
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies (for build validation)
cd frontend
npm install
npm run build
cd ..
```

### 5. Build Frontend

Build the Next.js frontend before deployment:

```bash
cd app
./build-frontend.sh
```

### 6. Deploy Using Asset Bundle

Deploy the app using Databricks Asset Bundle:

```bash
# From the app/ directory

# Validate configuration
databricks bundle validate -t dev

# Deploy to development
databricks bundle deploy -t dev

# Deploy to production
databricks bundle deploy -t prod
```

### 7. Verify Deployment

Check app status:

```bash
# Get app details
databricks apps get genie-lamp-agent

# View logs
databricks apps logs genie-lamp-agent --follow
```

Access the app at:
```
https://<workspace-url>/apps/genie-lamp-agent
```

### 8. Access the App

Open the URL in your browser:
```
https://<workspace>.databricks.com/apps/genie-lamp-agent
```

You should see the Genie Lamp Agent UI with the 5-step workflow.

## Configuration

### Environment Variables

The app uses the following environment variables (configured in `databricks.yml`):

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABRICKS_HOST` | `{{workspace.host}}` | Workspace URL |
| `DATABRICKS_TOKEN` | `{{secrets.genie-lamp/service-token}}` | Service token |
| `DATABRICKS_SERVER_HOSTNAME` | `{{workspace.server_hostname}}` | SQL server hostname |
| `DATABRICKS_HTTP_PATH` | `{{secrets.genie-lamp/sql-warehouse-http-path}}` | SQL warehouse path |
| `NEXT_PUBLIC_API_URL` | Static | Backend API URL |

### Compute Resources

Default configuration (modify in `databricks.yml` if needed):
- **Type**: Standard
- **Size**: Medium (4 cores, 16GB RAM)

For higher loads, adjust to `large` or `xlarge`:
```yaml
compute:
  type: standard
  size: large  # 8 cores, 32GB RAM
```

## Monitoring and Debugging

### View App Logs

```bash
databricks apps logs genie-lamp-agent
```

### Check Backend Health

```bash
curl https://<workspace>.databricks.com/apps/genie-lamp-agent/health
```

Expected response:
```json
{"status": "healthy"}
```

### View Database Tables

Check session and job tables:
```sql
-- In Databricks SQL Editor
SELECT * FROM genie_sessions LIMIT 10;
SELECT * FROM genie_jobs ORDER BY created_at DESC LIMIT 10;
```

### Common Issues

**App fails to start:**
- Check SQL warehouse is running
- Verify secrets exist: `databricks secrets list-secrets genie-lamp`
- Check logs: `databricks apps logs genie-lamp-agent`

**Database connection errors:**
- Verify `DATABRICKS_HTTP_PATH` is correct
- Check SQL warehouse permissions
- Ensure token has SQL execution rights

**File upload errors:**
- Verify Unity Catalog Volume exists
- Check volume permissions: user needs WRITE access

## Updating the App

To deploy updates:

```bash
# Make code changes
# ...

# Redeploy
databricks apps deploy genie-lamp-agent

# Force restart if needed
databricks apps restart genie-lamp-agent
```

## Rollback

To rollback to a previous version:

```bash
databricks apps rollback genie-lamp-agent --version <previous-version>
```

## Cleanup

To delete the app and resources:

```bash
# Delete the app
databricks apps delete genie-lamp-agent

# Delete secrets
databricks secrets delete-secret genie-lamp service-token
databricks secrets delete-secret genie-lamp sql-warehouse-http-path
databricks secrets delete-scope genie-lamp

# Delete Unity Catalog volumes (optional - removes all data)
databricks fs rm -r dbfs:/Volumes/main/genie_lamp/

# Drop database tables (optional)
# In Databricks SQL Editor:
# DROP TABLE IF EXISTS genie_sessions;
# DROP TABLE IF EXISTS genie_jobs;
```

## Production Considerations

### Security

1. **Service Principal Token**: Use a service principal instead of user PAT:
```bash
databricks service-principals create --display-name genie-lamp-agent
databricks tokens create --service-principal-id <sp-id>
```

2. **Secret Rotation**: Rotate tokens regularly

3. **Network Security**: Configure network policies if needed

### Scaling

For production workloads:

1. **Increase compute resources** in `databricks.yml`:
```yaml
compute:
  type: standard
  size: large  # or xlarge
```

2. **Configure auto-scaling** (if supported):
```yaml
compute:
  type: standard
  size: medium
  auto_scaling:
    min_instances: 2
    max_instances: 10
```

3. **Job Manager Workers**: Increase `max_workers` in `job_manager.py`:
```python
job_manager = JobManager(session_store, max_workers=8)
```

### Monitoring

Set up monitoring for:
- App health checks (`/health` endpoint)
- Job success/failure rates (query `genie_jobs` table)
- API latency (FastAPI built-in metrics)
- Database connection pool health

### Backup

Regularly backup:
- Session and job data (export from Lakebase tables)
- Unity Catalog volume data
- App configuration files

## Support

For issues or questions:
1. Check logs: `databricks apps logs genie-lamp-agent`
2. Review app status: `databricks apps get genie-lamp-agent`
3. Test backend health: `curl <app-url>/health`
4. Verify Unity Catalog access and SQL warehouse status

## Next Steps

After successful deployment:
1. Test end-to-end workflow with sample requirements
2. Configure user access and permissions
3. Set up monitoring and alerting
4. Document user workflows and best practices
5. Plan for scaling based on usage patterns
