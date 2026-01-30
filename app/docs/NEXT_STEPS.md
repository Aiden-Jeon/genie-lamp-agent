# Development Plan: Next Steps

## Current Status

✅ **MVP Complete** - All core features implemented and documented
- Multi-user web application with 5-step workflow
- Background job processing with polling
- Interactive validation fixing
- Complete documentation and testing guides
- Local development environment ready

### Recent Improvements
- ✅ In-memory session store fallback for local development
- ✅ Local file storage fallback when Unity Catalog unavailable
- ✅ Graceful degradation for development without full Databricks infrastructure

---

## Phase 1: Deployment & Validation (Week 1-2)

### 1.1 Local Testing & Bug Fixes
**Priority: High**

- [ ] **End-to-End Testing**
  - [ ] Test complete workflow with real requirements files
  - [ ] Verify all 5 steps complete successfully
  - [ ] Test with multiple concurrent users (2-3 browser sessions)
  - [ ] Test error scenarios and recovery

- [ ] **Integration Testing**
  - [ ] Test with actual Databricks workspace
  - [ ] Verify Unity Catalog Volume access
  - [ ] Test SQL Warehouse connectivity
  - [ ] Validate OAuth2 flow

- [ ] **Bug Fixes**
  - [ ] Fix any issues discovered during testing
  - [ ] Add error messages for edge cases
  - [ ] Improve validation error messages
  - [ ] Add loading states where missing

### 1.2 Staging Deployment
**Priority: High**

- [ ] **Infrastructure Setup**
  - [ ] Create Unity Catalog Volumes in staging workspace
  - [ ] Configure SQL Warehouse for Lakebase
  - [ ] Set up secrets scope and credentials
  - [ ] Configure network access if needed

- [ ] **Deploy to Staging**
  - [ ] Follow DEPLOYMENT.md steps
  - [ ] Verify deployment successful
  - [ ] Test all features in staging
  - [ ] Monitor logs for errors

- [ ] **User Acceptance Testing**
  - [ ] Invite 2-3 internal users
  - [ ] Gather feedback on UX
  - [ ] Document issues and enhancement requests
  - [ ] Prioritize fixes

### 1.3 Documentation Updates
**Priority: Medium**

- [ ] **Enhance Documentation**
  - [ ] Add screenshots to README
  - [ ] Create video walkthrough
  - [ ] Add troubleshooting for common issues
  - [ ] Document environment-specific configurations

- [ ] **Developer Guides**
  - [ ] Add contributing guidelines
  - [ ] Document architecture decisions
  - [ ] Create API documentation (OpenAPI/Swagger)
  - [ ] Add component diagrams

---

## Phase 2: Enhanced User Experience (Week 3-4)

### 2.1 Real-Time Progress
**Priority: High**
**Rationale**: Polling every 2 seconds is functional but not optimal

- [ ] **Implement Server-Sent Events (SSE)**
  - [ ] Replace polling with SSE for job status
  - [ ] Add progress percentage for each job
  - [ ] Show detailed progress messages (e.g., "Parsing page 3 of 10")
  - [ ] Display time elapsed and estimated time remaining

- [ ] **Backend Changes**
  ```python
  # New endpoint: /api/jobs/{job_id}/stream
  @app.get("/api/jobs/{job_id}/stream")
  async def stream_job_progress(job_id: str):
      async def event_generator():
          while True:
              job = job_manager.get_job(job_id)
              yield f"data: {json.dumps(job.dict())}\n\n"
              if job.status in ["completed", "failed"]:
                  break
              await asyncio.sleep(0.5)
      return EventSourceResponse(event_generator())
  ```

- [ ] **Frontend Changes**
  - [ ] Replace useJobPolling with EventSource
  - [ ] Add progress bars with percentage
  - [ ] Show real-time log messages
  - [ ] Add cancel job button

### 2.2 Configuration Preview & Editing
**Priority: High**
**Rationale**: Users want to review/edit before deployment

- [ ] **Config Preview**
  - [ ] Add preview step between Generate and Validate
  - [ ] Display JSON in formatted viewer
  - [ ] Show summary statistics (tables, instructions, queries)
  - [ ] Syntax highlighting for JSON

- [ ] **In-Browser Editor**
  - [ ] Integrate Monaco Editor or CodeMirror
  - [ ] Add JSON schema validation
  - [ ] Show validation errors inline
  - [ ] Allow save and re-validate

- [ ] **Component Structure**
  ```typescript
  // New component: ConfigPreviewStep.tsx
  interface ConfigPreviewStepProps {
    configPath: string;
    onEdit: (config: any) => void;
    onContinue: () => void;
  }
  ```

### 2.3 Enhanced File Upload
**Priority: Medium**
**Rationale**: Improve upload experience

- [ ] **Drag & Drop**
  - [ ] Add drag-drop zone with react-dropzone
  - [ ] Visual feedback during drag
  - [ ] File type validation
  - [ ] Size limit validation (e.g., 10MB per file)

- [ ] **File Previews**
  - [ ] Show file list with thumbnails
  - [ ] Display file size and type
  - [ ] Allow removal before upload
  - [ ] Show upload progress per file

- [ ] **Validation**
  - [ ] Check file extensions (.pdf, .md only)
  - [ ] Validate file is not empty
  - [ ] Check for duplicate filenames
  - [ ] Limit total upload size

### 2.4 Better Error Handling
**Priority: High**
**Rationale**: Current error messages could be more helpful

- [ ] **Error Recovery**
  - [ ] Add "Retry" button for failed jobs
  - [ ] Allow resuming from failed step
  - [ ] Save workflow state to localStorage
  - [ ] Auto-recovery after transient failures

- [ ] **Error Messages**
  - [ ] Categorize errors (user error, system error, config error)
  - [ ] Add actionable suggestions
  - [ ] Link to documentation
  - [ ] Show support contact info

- [ ] **Error Boundaries**
  - [ ] Add React error boundaries for each component
  - [ ] Graceful fallback UI
  - [ ] Error reporting to backend
  - [ ] User-friendly error pages

---

## Phase 3: Session Management (Week 5-6)

### 3.1 Session History
**Priority: High**
**Rationale**: Users want to see past work

- [ ] **Session List View**
  - [ ] New page: `/sessions`
  - [ ] List all user's sessions
  - [ ] Show session date, status, and files
  - [ ] Filter by status (completed, failed, in-progress)
  - [ ] Search by filename or space name

- [ ] **Session Details**
  - [ ] View session details page
  - [ ] Show all jobs in session
  - [ ] Display generated config
  - [ ] Link to deployed space (if applicable)

- [ ] **Backend Changes**
  - [ ] Add user_id tracking in sessions
  - [ ] New endpoint: `GET /api/sessions?user_id=X`
  - [ ] New endpoint: `GET /api/sessions/{id}/details`
  - [ ] Add pagination for session list

### 3.2 Workspace Management
**Priority: Medium**
**Rationale**: Organize multiple deployments

- [ ] **Workspace View**
  - [ ] List all deployed spaces for user
  - [ ] Show space status (active, draft, archived)
  - [ ] Quick actions (view, edit, delete)
  - [ ] Group by folder/category

- [ ] **Space Operations**
  - [ ] Update existing space (re-deploy)
  - [ ] Clone space to create variations
  - [ ] Archive/delete spaces
  - [ ] Export configuration to file

### 3.3 User Preferences
**Priority: Low**
**Rationale**: Convenience for repeat users

- [ ] **Saved Settings**
  - [ ] Remember preferred LLM model
  - [ ] Save default parent path
  - [ ] Remember LLM enrichment preference
  - [ ] Save workspace layout preferences

- [ ] **Templates**
  - [ ] Save configuration templates
  - [ ] Quick start from template
  - [ ] Share templates with team
  - [ ] Template marketplace (future)

---

## Phase 4: Advanced Features (Week 7-8)

### 4.1 Collaborative Features
**Priority: Medium**
**Rationale**: Teams need to work together

- [ ] **Sharing**
  - [ ] Share session with team members
  - [ ] View-only vs edit permissions
  - [ ] Comment on configurations
  - [ ] Track changes by user

- [ ] **Approval Workflow**
  - [ ] Request review before deploy
  - [ ] Approval/rejection with comments
  - [ ] Email notifications
  - [ ] Audit trail

### 4.2 Batch Operations
**Priority: Low**
**Rationale**: Power users need efficiency

- [ ] **Batch Upload**
  - [ ] Upload multiple requirement sets
  - [ ] Process in parallel
  - [ ] Queue management
  - [ ] Batch deployment

- [ ] **Bulk Management**
  - [ ] Update multiple spaces at once
  - [ ] Bulk catalog/schema replacement
  - [ ] Mass deployment
  - [ ] Export/import configurations

### 4.3 Analytics & Monitoring
**Priority: Medium**
**Rationale**: Operational insights

- [ ] **Usage Analytics**
  - [ ] Dashboard showing usage stats
  - [ ] Success/failure rates
  - [ ] Popular models
  - [ ] Average job duration

- [ ] **Quality Metrics**
  - [ ] Track validation pass rates
  - [ ] Monitor deployed space quality scores
  - [ ] User satisfaction ratings
  - [ ] Error trend analysis

- [ ] **System Health**
  - [ ] Backend health dashboard
  - [ ] Job queue metrics
  - [ ] Database connection pool status
  - [ ] Storage usage

---

## Phase 5: Enterprise Features (Week 9-12)

### 5.1 Advanced Authentication & RBAC
**Priority: High for Enterprise**

- [ ] **Role-Based Access Control**
  - [ ] Define roles (admin, editor, viewer)
  - [ ] Permission system
  - [ ] Resource-level permissions
  - [ ] Group-based access

- [ ] **SSO Integration**
  - [ ] SAML support
  - [ ] LDAP/AD integration
  - [ ] Multi-factor authentication
  - [ ] Session timeout policies

### 5.2 Governance & Compliance
**Priority: High for Enterprise**

- [ ] **Audit Logging**
  - [ ] Log all user actions
  - [ ] Immutable audit trail
  - [ ] Compliance reporting
  - [ ] Export audit logs

- [ ] **Data Governance**
  - [ ] PII detection in requirements
  - [ ] Data classification tags
  - [ ] Retention policies
  - [ ] GDPR compliance features

### 5.3 Multi-Workspace Support
**Priority: Medium for Enterprise**

- [ ] **Workspace Switching**
  - [ ] Connect to multiple workspaces
  - [ ] Switch context easily
  - [ ] Sync configurations across workspaces
  - [ ] Cross-workspace deployment

- [ ] **Environment Management**
  - [ ] Dev/staging/prod environments
  - [ ] Promote configurations between environments
  - [ ] Environment-specific settings
  - [ ] Deployment gates

---

## Technical Debt & Maintenance

### Ongoing Tasks

- [ ] **Code Quality**
  - [ ] Add backend unit tests (pytest)
  - [ ] Add frontend unit tests (Jest + React Testing Library)
  - [ ] Add E2E tests (Playwright or Cypress)
  - [ ] Set up CI/CD pipeline
  - [ ] Code coverage reporting (target: 80%+)

- [ ] **Performance Optimization**
  - [ ] Profile slow endpoints
  - [ ] Optimize database queries
  - [ ] Add caching layer (Redis)
  - [ ] Frontend bundle optimization
  - [ ] Image optimization

- [ ] **Security Hardening**
  - [ ] Security audit
  - [ ] Dependency vulnerability scanning
  - [ ] Input validation hardening
  - [ ] Rate limiting
  - [ ] DDoS protection

- [ ] **Documentation Maintenance**
  - [ ] Keep docs up-to-date with code
  - [ ] Add API changelog
  - [ ] Update troubleshooting guide
  - [ ] Add FAQ based on user questions

---

## Technology Upgrades

### Consider for Future

- [ ] **Backend**
  - [ ] Upgrade to Python 3.12
  - [ ] Consider FastAPI 0.110+ features
  - [ ] Add async database driver (asyncpg)
  - [ ] Implement GraphQL API (optional)

- [ ] **Frontend**
  - [ ] Upgrade to Next.js 15 when stable
  - [ ] Consider React Server Components
  - [ ] Add PWA support (offline mode)
  - [ ] Implement virtual scrolling for large lists

- [ ] **Infrastructure**
  - [ ] Container orchestration (Kubernetes)
  - [ ] Service mesh (Istio)
  - [ ] Distributed tracing (Jaeger)
  - [ ] Centralized logging (ELK stack)

---

## Decision Log

### Decisions to Make

1. **Real-Time Updates**
   - **Decision Needed**: SSE vs WebSockets vs polling
   - **Recommendation**: Start with SSE (simpler than WebSockets)
   - **Due By**: Phase 2 start

2. **Session Storage**
   - **Decision Needed**: Keep Lakebase or add Redis
   - **Recommendation**: Keep Lakebase for MVP, add Redis for caching
   - **Due By**: When performance issues arise

3. **Frontend State Management**
   - **Decision Needed**: Stay with React hooks or add Redux/Zustand
   - **Recommendation**: Add Zustand when app grows more complex
   - **Due By**: When state management becomes painful

4. **Testing Strategy**
   - **Decision Needed**: Unit vs Integration vs E2E test ratio
   - **Recommendation**: 70% unit, 20% integration, 10% E2E
   - **Due By**: Before Phase 4

5. **Deployment Strategy**
   - **Decision Needed**: Blue-green, canary, or rolling updates
   - **Recommendation**: Start with blue-green for safety
   - **Due By**: Before production deployment

---

## Success Metrics

### Phase 1 (Deployment)
- [ ] App deployed to staging
- [ ] 3+ users test successfully
- [ ] Zero critical bugs
- [ ] <500ms average API latency

### Phase 2 (UX Improvements)
- [ ] 90%+ user satisfaction
- [ ] 50% reduction in support questions
- [ ] <5 seconds to first interaction
- [ ] <2% job failure rate

### Phase 3 (Session Management)
- [ ] 80% users use session history
- [ ] Average 3+ sessions per user
- [ ] <1 second session list load time

### Phase 4 (Advanced Features)
- [ ] 50% users leverage collaborative features
- [ ] 30% reduction in re-work
- [ ] Analytics dashboard adoption

### Phase 5 (Enterprise)
- [ ] Enterprise customers onboarded
- [ ] 100% compliance requirements met
- [ ] <1 hour incident response time

---

## Resource Requirements

### Immediate (Phase 1-2)
- 1 Full-stack developer (maintain and deploy)
- 1 QA engineer (testing)
- 1 DevOps engineer (infrastructure)

### Short-term (Phase 3-4)
- 2 Full-stack developers
- 1 Frontend specialist (UX improvements)
- 1 Backend specialist (performance)
- 1 QA engineer

### Long-term (Phase 5)
- 3-4 Full-stack developers
- 1 Security engineer
- 1 DevOps engineer
- 2 QA engineers
- 1 Product manager

---

## Risk Assessment

### High Priority Risks

1. **Database Performance**
   - **Risk**: Lakebase might be slow for high traffic
   - **Mitigation**: Add Redis caching, optimize queries
   - **Contingency**: Move to dedicated Postgres if needed

2. **File Storage Limits**
   - **Risk**: Unity Catalog Volume size limits
   - **Mitigation**: Implement cleanup, archive old files
   - **Contingency**: Use S3/ADLS for overflow

3. **OAuth2 Token Expiry**
   - **Risk**: Long-running jobs might lose auth
   - **Mitigation**: Token refresh mechanism
   - **Contingency**: Service principal with long-lived token

### Medium Priority Risks

4. **Concurrent Job Limits**
   - **Risk**: ProcessPoolExecutor maxes out at 4 workers
   - **Mitigation**: Monitor queue depth, add more workers
   - **Contingency**: Distribute to multiple backend instances

5. **Frontend Bundle Size**
   - **Risk**: Large JS bundle slows initial load
   - **Mitigation**: Code splitting, lazy loading
   - **Contingency**: Server-side rendering

---

## Getting Started

### For Next Developer

1. **Read These First**
   - [ ] app/README.md (setup)
   - [ ] app/IMPLEMENTATION_SUMMARY.md (architecture)
   - [ ] This file (roadmap)

2. **Set Up Local Environment**
   - [ ] Clone repo
   - [ ] Run `./app/start-local.sh`
   - [ ] Test end-to-end workflow

3. **Pick Your First Task**
   - **Easy**: Add file size validation to upload
   - **Medium**: Implement SSE for job progress
   - **Hard**: Add config preview/editor

4. **Development Workflow**
   - [ ] Create feature branch
   - [ ] Write tests first (TDD)
   - [ ] Implement feature
   - [ ] Update documentation
   - [ ] Create PR with screenshots

---

## Contact & Support

**Questions?**
- Architecture decisions: See IMPLEMENTATION_SUMMARY.md
- Deployment issues: See DEPLOYMENT.md
- Testing: See TESTING.md
- Development setup: See README.md

**For Urgent Issues:**
- Check logs: `tail -f app/backend.log` and `app/frontend.log`
- Health check: `curl http://localhost:8000/health`
- Database: Check Lakebase tables (genie_sessions, genie_jobs)

---

**Document Status**: ✅ Active
**Last Updated**: 2026-01-30
**Next Review**: Start of each phase
**Owner**: Development Team
