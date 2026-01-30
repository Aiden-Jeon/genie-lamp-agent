# Genie Lamp Agent - Databricks App

Multi-user web application for generating Databricks Genie Spaces from natural language requirements.

## Architecture

- **Backend**: FastAPI (Python 3.11) - Reuses all existing pipeline code
- **Frontend**: Next.js 14 + React + TailwindCSS
- **State Storage**: Databricks Lakebase (Postgres) for sessions/jobs
- **File Storage**: Unity Catalog Volumes
- **Auth**: Databricks OAuth2

## Local Development

### Backend Setup

```bash
cd app/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your Databricks credentials

# Run backend
uvicorn main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd app/frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### Testing the Workflow

1. Open `http://localhost:3000` in your browser
2. Upload PDF or Markdown requirements files
3. Click through the 5-step workflow:
   - **Upload/Parse**: Upload files → Parse with optional LLM enrichment
   - **Generate**: LLM generates Genie space configuration
   - **Validate**: Check tables/columns against Unity Catalog
   - **Fix** (if needed): Correct table references interactively
   - **Deploy**: Deploy to Databricks Genie

## Databricks App Deployment

### Quick Start - Databricks App Deployment

1. Build frontend:
   ```bash
   cd app && ./build-frontend.sh
   ```

2. Deploy using Asset Bundle:
   ```bash
   databricks bundle deploy -t dev
   ```

3. Access at: `https://<workspace>/apps/genie-lamp-agent`

### Prerequisites

1. Unity Catalog Volume for file storage:
```bash
databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/uploads
databricks fs mkdirs dbfs:/Volumes/main/genie_lamp/sessions
```

2. Databricks Secrets:
```bash
databricks secrets create-scope genie-lamp
databricks secrets put-secret genie-lamp service-token --string-value "YOUR_TOKEN"
databricks secrets put-secret genie-lamp sql-warehouse-http-path --string-value "/sql/1.0/warehouses/YOUR_WAREHOUSE_ID"
```

### Deploy to Databricks

See the Quick Start section above, or refer to [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## Project Structure

```
app/
├── backend/                 # FastAPI backend
│   ├── main.py             # API endpoints
│   ├── services/
│   │   ├── session_store.py    # Lakebase persistence
│   │   ├── job_manager.py      # Background jobs
│   │   ├── file_storage.py     # UC Volume storage
│   │   └── job_tasks.py        # Pipeline wrappers
│   ├── middleware/
│   │   └── auth.py             # OAuth2 auth
│   └── requirements.txt
│
├── frontend/                # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Main workflow UI
│   │   ├── layout.tsx          # App layout
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── Stepper.tsx         # Progress indicator
│   │   ├── ParseStep.tsx       # Upload/parse step
│   │   ├── GenerateStep.tsx    # Config generation step
│   │   ├── ValidateStep.tsx    # Validation step
│   │   ├── ValidationFixer.tsx # Interactive fixer
│   │   └── DeployStep.tsx      # Deployment step
│   ├── lib/
│   │   ├── api-client.ts       # Type-safe API client
│   │   └── hooks/
│   │       └── useJobPolling.ts # Job polling hook
│   └── package.json
│
└── databricks.yml          # App configuration
```

## API Endpoints

- `POST /api/parse` - Upload and parse requirements
- `POST /api/generate` - Generate Genie config
- `POST /api/validate` - Validate configuration
- `POST /api/validate/fix` - Apply fixes and re-validate
- `POST /api/deploy` - Deploy Genie space
- `GET /api/jobs/{job_id}` - Get job status (polling)
- `GET /api/sessions/{session_id}` - Get session info

## Key Features

- **Multi-user Support**: Isolated sessions per user with UUID-based storage
- **Background Jobs**: Long-running tasks don't block UI (polling every 2s)
- **Interactive Validation**: Fix table references directly in UI
- **Session Persistence**: All state stored in Databricks Lakebase
- **OAuth2 Auth**: Automatic user authentication via Databricks gateway
- **Reuses Existing Code**: All pipeline functions called as-is via wrappers

## Environment Variables

### Backend (.env)
- `DATABRICKS_HOST` - Workspace URL
- `DATABRICKS_TOKEN` - Personal access token
- `DATABRICKS_SERVER_HOSTNAME` - Server hostname for SQL
- `DATABRICKS_HTTP_PATH` - SQL warehouse HTTP path

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Troubleshooting

### Backend Issues

**Database connection errors**:
- Verify `DATABRICKS_HTTP_PATH` points to valid SQL warehouse
- Check SQL warehouse is running
- Verify token has SQL execution permissions

**File upload errors**:
- Ensure Unity Catalog Volume exists: `/Volumes/main/genie_lamp/uploads`
- Check write permissions to volume

### Frontend Issues

**CORS errors**:
- Backend must be running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Job polling hangs**:
- Check backend logs for job execution errors
- Verify job_id is valid

## Development Notes

- Frontend uses TypeScript with strict mode enabled
- Backend uses Python 3.11 with type hints
- All API responses are type-safe via Pydantic models
- Job polling interval: 2 seconds (configurable in `useJobPolling.ts`)
- Session isolation via UUID (no cross-user interference)

## Next Steps (Post-MVP)

- [ ] Real-time progress bars (replace polling with SSE)
- [ ] Config preview/edit before deployment
- [ ] Session history and workspace management
- [ ] Enhanced error recovery and retry logic
- [ ] Drag-drop file upload with previews
- [ ] User preferences and saved configurations
