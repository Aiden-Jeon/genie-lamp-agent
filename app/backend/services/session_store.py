"""Session and job persistence using Databricks Lakebase (Postgres)."""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
from databricks import sql
from pydantic import BaseModel


class Job(BaseModel):
    """Job model for tracking async operations."""
    job_id: str
    session_id: str
    type: str  # parse, generate, validate, deploy
    status: str  # pending, running, completed, failed
    inputs: dict
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SessionStore:
    """Manages session and job state in Databricks SQL."""

    def __init__(self):
        """Initialize connection to Databricks SQL warehouse or use in-memory store."""
        # Use in-memory store if warehouse path is placeholder
        http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        if "your-warehouse-id" in http_path or not http_path:
            print("Warning: Using in-memory session store (no valid warehouse configured)")
            self.conn = None
            self._sessions = {}
            self._jobs = {}
        else:
            self.conn = sql.connect(
                server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                http_path=http_path,
                access_token=os.getenv("DATABRICKS_TOKEN")
            )
            self._init_tables()

    def _init_tables(self):
        """Create tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_sessions (
                session_id STRING PRIMARY KEY,
                user_id STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_jobs (
                job_id STRING PRIMARY KEY,
                session_id STRING,
                type STRING,
                status STRING,
                inputs STRING,
                result STRING,
                error STRING,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                completed_at TIMESTAMP
            )
        """)
        cursor.close()

    def create_session(self, user_id: str) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        if self.conn is None:
            self._sessions[session_id] = {"user_id": user_id, "created_at": datetime.now()}
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO genie_sessions VALUES (?, ?, CURRENT_TIMESTAMP())",
                (session_id, user_id)
            )
            cursor.close()
        return session_id

    def save_job(self, job: Job):
        """Save a new job record."""
        if self.conn is None:
            self._jobs[job.job_id] = job
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO genie_jobs
                   (job_id, session_id, type, status, inputs, created_at)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP())""",
                (job.job_id, job.session_id, job.type, job.status, json.dumps(job.inputs))
            )
            cursor.close()

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID."""
        if self.conn is None:
            return self._jobs.get(job_id)
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM genie_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return Job(
                job_id=row[0],
                session_id=row[1],
                type=row[2],
                status=row[3],
                inputs=json.loads(row[4]) if row[4] else {},
                result=json.loads(row[5]) if row[5] else None,
                error=row[6],
                created_at=row[7],
                completed_at=row[8]
            )

    def update_job(self, job: Job):
        """Update job status, result, and error."""
        if self.conn is None:
            self._jobs[job.job_id] = job
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE genie_jobs
                   SET status = ?, result = ?, error = ?, completed_at = ?
                   WHERE job_id = ?""",
                (job.status,
                 json.dumps(job.result) if job.result else None,
                 job.error,
                 job.completed_at,
                 job.job_id)
            )
            cursor.close()

    def get_jobs_for_session(self, session_id: str) -> List[Job]:
        """Get all jobs for a session."""
        if self.conn is None:
            jobs = [job for job in self._jobs.values() if job.session_id == session_id]
            return sorted(jobs, key=lambda j: j.created_at or datetime.min)
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM genie_jobs WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            rows = cursor.fetchall()
            cursor.close()

            return [
                Job(
                    job_id=row[0],
                    session_id=row[1],
                    type=row[2],
                    status=row[3],
                    inputs=json.loads(row[4]) if row[4] else {},
                    result=json.loads(row[5]) if row[5] else None,
                    error=row[6],
                    created_at=row[7],
                    completed_at=row[8]
                )
                for row in rows
            ]
