# Testing Guide for Genie Lamp Agent App

## Local Testing

### Backend Testing

#### 1. Setup Backend Environment

```bash
cd app/backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

#### 2. Test Backend Health

Start the backend:
```bash
uvicorn main:app --reload --port 8000
```

Test health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

#### 3. Test Individual Services

**Session Store:**
```python
from services.session_store import SessionStore

store = SessionStore()
session_id = store.create_session("test_user")
print(f"Created session: {session_id}")

# Verify in database
# SELECT * FROM genie_sessions WHERE session_id = '<session_id>';
```

**File Storage:**
```python
from services.file_storage import FileStorageService

storage = FileStorageService()
session_dir = storage.create_session_dir("test-session-123")
print(f"Created directory: {session_dir}")
```

**Job Manager:**
```python
from services.job_manager import JobManager
from services.session_store import SessionStore

store = SessionStore()
manager = JobManager(store)

job = manager.create_job("test", "test-session", {"input": "test"})
print(f"Created job: {job.job_id}")
```

### Frontend Testing

#### 1. Setup Frontend Environment

```bash
cd app/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit NEXT_PUBLIC_API_URL if needed
```

#### 2. Run Development Server

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

#### 3. Test Components

**Stepper:**
- Verify all 5 steps are displayed
- Check step highlighting and completion states
- Verify connecting lines between steps

**ParseStep:**
- Upload single PDF file
- Upload multiple files (.pdf and .md)
- Toggle LLM enrichment checkbox
- Verify file count display
- Check polling animation during parsing

**GenerateStep:**
- Select different LLM models
- Verify model dropdown works
- Check generation progress indicator

**ValidateStep:**
- Test validation with valid configuration
- Test validation with invalid tables
- Verify ValidationFixer appears on errors

**ValidationFixer:**
- Enter catalog/schema/table replacements
- Check suggestions display
- Verify "Apply Fixes" button activation

**DeployStep:**
- Test with optional parent path
- Test without parent path
- Verify deployment success message

## End-to-End Testing

### Test Workflow 1: Happy Path

**Goal**: Complete workflow with no validation errors

1. **Upload**: Upload `data/demo_requirements.md`
2. **Parse**: Enable LLM enrichment, wait for completion
3. **Generate**: Use `databricks-gpt-5-2`, wait for config generation
4. **Validate**: Should pass (demo data uses valid tables)
5. **Deploy**: Deploy without parent path
6. **Verify**: Click space URL, confirm Genie space opens

**Expected Behavior:**
- All steps complete without errors
- Stepper shows completed checkmarks
- Deployment shows space ID and URL
- Space URL opens working Genie space

### Test Workflow 2: Validation Errors

**Goal**: Test interactive validation fixing

1. **Upload**: Create requirements with invalid table names:
```markdown
# Test Requirements

## Tables
- `invalid_catalog.invalid_schema.invalid_table`

## Questions
- How many records?
```

2. **Parse**: Complete parsing
3. **Generate**: Generate configuration
4. **Validate**: Should fail with table not found errors
5. **Fix**: Enter correct catalog/schema/table names
6. **Re-validate**: Should pass after fixes
7. **Deploy**: Complete deployment

**Expected Behavior:**
- ValidationFixer appears with invalid tables
- Suggestions shown (if available)
- Re-validation succeeds after fixes
- Deployment proceeds normally

### Test Workflow 3: Multiple Users

**Goal**: Verify session isolation

1. Open two browser windows (or incognito + regular)
2. Start workflows in both windows simultaneously
3. Verify different session IDs displayed
4. Complete workflows independently
5. Check no state interference between sessions

**Expected Behavior:**
- Each window has unique session ID
- Files saved to separate session directories
- Jobs tracked independently
- No cross-contamination of state

### Test Workflow 4: Error Handling

**Goal**: Test error scenarios

**Scenario A - Invalid File Format:**
1. Upload `.txt` or `.docx` file
2. Verify appropriate error message
3. Workflow does not proceed

**Scenario B - Backend Unavailable:**
1. Stop backend server
2. Try to upload files
3. Verify error message displayed
4. Restart backend, retry workflow

**Scenario C - Invalid Token:**
1. Set invalid `DATABRICKS_TOKEN` in backend `.env`
2. Try to validate or deploy
3. Verify authentication error shown

## API Testing

### Using curl

**Parse Endpoint:**
```bash
SESSION_ID="test-$(date +%s)"

curl -X POST http://localhost:8000/api/parse \
  -F "session_id=$SESSION_ID" \
  -F "use_llm=true" \
  -F "files=@data/demo_requirements.md"
```

**Job Status:**
```bash
JOB_ID="<job-id-from-parse-response>"

curl http://localhost:8000/api/jobs/$JOB_ID
```

**Generate Endpoint:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "requirements_path": "/path/to/parsed_requirements.md",
    "model": "databricks-gpt-5-2"
  }'
```

**Validate Endpoint:**
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "config_path": "/path/to/genie_space_config.json"
  }'
```

**Deploy Endpoint:**
```bash
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "config_path": "/path/to/genie_space_config.json",
    "parent_path": "/Workspace/Shared/Genie Spaces"
  }'
```

### Using Python

```python
import requests
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "test-python-session"

# Upload and parse
with open("data/demo_requirements.md", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/parse?session_id={SESSION_ID}",
        files={"files": f},
        data={"use_llm": "true"}
    )
    parse_job = response.json()
    print(f"Parse job: {parse_job}")

# Poll for completion
job_id = parse_job["job_id"]
while True:
    status = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()
    print(f"Status: {status['status']}")

    if status["status"] in ["completed", "failed"]:
        print(f"Result: {status.get('result')}")
        break

    time.sleep(2)
```

## Performance Testing

### Test 1: Concurrent Users

Simulate multiple users accessing the app:

```python
import concurrent.futures
import requests
import uuid

def test_user_workflow(user_id):
    session_id = str(uuid.uuid4())
    # Run workflow for one user
    # ... (upload, parse, generate, validate, deploy)
    return session_id

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_user_workflow, i) for i in range(10)]
    results = [f.result() for f in futures]

print(f"Completed {len(results)} concurrent workflows")
```

**Expected Behavior:**
- All workflows complete successfully
- No errors due to concurrency
- Session isolation maintained
- Reasonable response times

### Test 2: Large File Upload

Test with large PDF files:

```bash
# Create large test file (10MB)
dd if=/dev/urandom of=large_test.pdf bs=1M count=10

# Upload via API
curl -X POST http://localhost:8000/api/parse \
  -F "session_id=test-large-file" \
  -F "use_llm=true" \
  -F "files=@large_test.pdf"
```

**Expected Behavior:**
- Upload completes without timeout
- Parsing handles large file
- Memory usage remains reasonable

### Test 3: Job Queue

Test multiple simultaneous jobs:

```python
import requests
import concurrent.futures

def start_job(session_id):
    response = requests.post(
        f"http://localhost:8000/api/parse?session_id={session_id}",
        files={"files": open("data/demo_requirements.md", "rb")},
        data={"use_llm": "true"}
    )
    return response.json()["job_id"]

# Start 20 jobs simultaneously
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    job_ids = list(executor.map(start_job, [f"session-{i}" for i in range(20)]))

print(f"Started {len(job_ids)} jobs")
```

**Expected Behavior:**
- All jobs accepted
- Jobs processed within ProcessPoolExecutor limits
- No crashes or memory issues
- Jobs complete successfully (may queue)

## Database Testing

### Verify Session Storage

```sql
-- Check sessions created
SELECT COUNT(*) as session_count FROM genie_sessions;

-- Check recent jobs
SELECT
    type,
    status,
    COUNT(*) as count
FROM genie_jobs
GROUP BY type, status;

-- Check job durations
SELECT
    type,
    AVG(TIMESTAMPDIFF(SECOND, created_at, completed_at)) as avg_duration_sec
FROM genie_jobs
WHERE completed_at IS NOT NULL
GROUP BY type;
```

### Verify File Storage

```bash
# List session directories
ls -la /Volumes/main/genie_lamp/uploads/

# Check session files
ls -la /Volumes/main/genie_lamp/uploads/<session-id>/

# Verify file permissions
stat /Volumes/main/genie_lamp/uploads/<session-id>/<file>
```

## Integration Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend builds and starts successfully
- [ ] Health endpoint responds
- [ ] File upload works for .pdf and .md files
- [ ] Parse job completes successfully
- [ ] Generate job creates valid JSON config
- [ ] Validate job checks Unity Catalog
- [ ] ValidationFixer applies corrections
- [ ] Deploy job creates Genie space
- [ ] Space URL opens working Genie space
- [ ] Multiple sessions work independently
- [ ] Job polling works (2-second intervals)
- [ ] Error messages display correctly
- [ ] Session data persists in database
- [ ] Files persist in Unity Catalog Volume

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.11 required)
- Verify all dependencies installed
- Check `.env` file exists and is valid
- Verify database connection settings

**Frontend build fails:**
- Check Node.js version (20 required)
- Delete `node_modules` and reinstall: `npm install`
- Clear Next.js cache: `rm -rf .next`

**Job polling never completes:**
- Check backend logs for job execution errors
- Verify ProcessPoolExecutor is working
- Check database for job status
- Verify pipeline functions can be imported

**Validation always fails:**
- Verify Unity Catalog connection
- Check SQL warehouse is running
- Verify token has SELECT permissions
- Test table access manually with SQL

**Deployment fails:**
- Check Genie Space API credentials
- Verify config JSON is valid
- Check API endpoint permissions
- Review Databricks workspace quotas

## Automated Testing

For continuous testing, create test scripts:

**Backend Tests:**
```bash
# app/backend/test_api.py
pytest tests/test_api.py -v
```

**Frontend Tests:**
```bash
# app/frontend
npm run test
```

**E2E Tests:**
```bash
# Using Playwright or Cypress
npx playwright test
```

## Success Criteria

A successful test run should demonstrate:

1. **Functionality**: All 5 workflow steps complete end-to-end
2. **Concurrency**: Multiple users can work simultaneously
3. **Reliability**: No crashes or hangs during normal operation
4. **Error Handling**: Graceful degradation with clear error messages
5. **Performance**: Jobs complete in reasonable time
6. **Data Integrity**: Session isolation and data persistence work correctly
