# Quick Reference Card

## 🚀 Getting Started (2 Minutes)

### Local Development
```bash
cd app
./start-local.sh
# Access: http://localhost:3000
```

### Deploy to Databricks
```bash
databricks apps deploy genie-lamp-agent
```

---

## 📁 File Structure

```
app/
├── backend/           # FastAPI (Python 3.11)
│   ├── main.py       # 7 API endpoints
│   ├── services/     # Session, jobs, storage
│   └── middleware/   # OAuth2 auth
├── frontend/         # Next.js + React
│   ├── app/          # Main UI
│   ├── components/   # 5 workflow steps
│   └── lib/          # API client + hooks
└── docs/             # Documentation
    ├── README.md
    ├── DEPLOYMENT.md
    ├── TESTING.md
    └── NEXT_STEPS.md
```

---

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/parse` | POST | Upload & parse files |
| `/api/generate` | POST | Generate config |
| `/api/validate` | POST | Validate config |
| `/api/validate/fix` | POST | Apply fixes |
| `/api/deploy` | POST | Deploy space |
| `/api/jobs/{id}` | GET | Job status (polling) |
| `/api/sessions/{id}` | GET | Session info |

---

## 🎯 5-Step Workflow

```
1. UPLOAD → Parse documents (PDF/MD)
2. GENERATE → LLM creates config (30-60s)
3. VALIDATE → Check Unity Catalog
4. FIX (optional) → Correct table names
5. DEPLOY → Create Genie space
```

---

## 🔧 Common Commands

### Backend
```bash
cd app/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd app/frontend
npm install
npm run dev    # Development
npm run build  # Production build
```

### Testing
```bash
# Backend
cd app/backend
pytest tests/ -v

# Frontend
cd app/frontend
npm test
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list

# Check .env file
cat app/backend/.env
```

### Frontend won't start
```bash
# Clear cache
rm -rf app/frontend/.next

# Reinstall dependencies
cd app/frontend
rm -rf node_modules package-lock.json
npm install
```

### Database connection errors
```bash
# Check SQL warehouse is running
databricks sql warehouses list

# Verify secrets
databricks secrets list-secrets genie-lamp
```

### File upload fails
```bash
# Check Unity Catalog Volume
databricks fs ls /Volumes/main/genie_lamp/

# Check permissions
databricks fs ls /Volumes/main/genie_lamp/uploads/
```

---

## 📊 Database Schema

### genie_sessions
```sql
session_id STRING PRIMARY KEY
user_id STRING
created_at TIMESTAMP
```

### genie_jobs
```sql
job_id STRING PRIMARY KEY
session_id STRING
type STRING       -- parse, generate, validate, deploy
status STRING     -- pending, running, completed, failed
inputs STRING     -- JSON
result STRING     -- JSON
error STRING
created_at TIMESTAMP
completed_at TIMESTAMP
```

---

## 🎨 Architecture Overview

```
┌─────────────┐
│  Browser    │ → http://localhost:3000
└──────┬──────┘
       │ REST API
       ▼
┌─────────────┐
│  FastAPI    │ → http://localhost:8000
└──┬─────┬────┘
   │     │
   ▼     ▼
┌──────┐ ┌──────────┐
│Volume│ │ Lakebase │ → Sessions/Jobs
└──────┘ └──────────┘
```

---

## 📝 Development Workflow

1. **Start servers**: `./start-local.sh`
2. **Make changes**: Edit code
3. **Test locally**: Use browser at localhost:3000
4. **Stop servers**: `./stop-local.sh` or Ctrl+C
5. **Commit**: `git commit -m "feat: description"`
6. **Deploy**: `databricks apps deploy genie-lamp-agent`

---

## 🔑 Environment Variables

### Backend (.env)
```env
DATABRICKS_HOST=https://...
DATABRICKS_TOKEN=dapi...
DATABRICKS_SERVER_HOSTNAME=...
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/...
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📖 Documentation Links

| Document | Purpose |
|----------|---------|
| **README.md** | Setup & usage guide |
| **DEPLOYMENT.md** | Deploy to Databricks |
| **TESTING.md** | Test strategies |
| **NEXT_STEPS.md** | Development roadmap |
| **IMPLEMENTATION_SUMMARY.md** | What was built |
| **CHECKLIST.md** | Verification checklist |

---

## 🎯 Next Priorities

### Phase 1: Deployment (Now)
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Fix bugs

### Phase 2: UX (Week 3-4)
- [ ] Real-time progress (SSE)
- [ ] Config preview/editor
- [ ] Enhanced file upload
- [ ] Better error handling

### Phase 3: Management (Week 5-6)
- [ ] Session history
- [ ] Workspace management
- [ ] User preferences

See **NEXT_STEPS.md** for complete roadmap.

---

## 💡 Tips

**Performance**
- Jobs run in ProcessPoolExecutor (4 workers)
- Polling interval: 2 seconds
- Local storage fallback for development
- In-memory sessions if no warehouse configured

**Development**
- Hot reload enabled for both backend and frontend
- Check logs: `tail -f app/backend.log`
- API docs: http://localhost:8000/docs
- Zero modifications to existing `src/` code

**Debugging**
- Backend logs: `app/backend.log`
- Frontend logs: `app/frontend.log`
- Health check: `curl http://localhost:8000/health`
- Session state: Check `genie_sessions` table

---

## 🆘 Quick Help

```bash
# Local development
./app/start-local.sh       # Start everything
./app/stop-local.sh        # Stop everything

# Check status
curl http://localhost:8000/health
curl http://localhost:3000

# View logs
tail -f app/backend.log
tail -f app/frontend.log

# Restart backend only
pkill -f uvicorn
cd app/backend && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Restart frontend only
pkill -f "next dev"
cd app/frontend && npm run dev
```

---

**Last Updated**: 2026-01-30
**Status**: ✅ MVP Complete
**Next**: Deploy to staging & start Phase 2
