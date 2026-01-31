"""Session and job persistence using Databricks Lakebase (Postgres) or SQLite."""

import json
import os
import sqlite3
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
    progress: Optional[dict] = None  # Progress tracking data


class SessionStore:
    """Manages session and job state in Databricks SQL, SQLite, or in-memory."""

    def __init__(self):
        """Initialize connection to Databricks SQL warehouse, SQLite, or use in-memory store."""
        http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
        use_sqlite = os.getenv("USE_SQLITE_STORAGE", "true").lower() == "true"

        # Determine storage backend
        if use_sqlite and ("your-warehouse-id" in http_path or not http_path):
            # Use SQLite for local persistence
            print("Using SQLite local storage: backend/storage/sessions.db")
            self.conn = None
            self.sqlite_conn = None
            self._init_sqlite()
        elif "your-warehouse-id" in http_path or not http_path:
            # Use in-memory (fallback when SQLite disabled)
            print("Warning: Using in-memory session store (no valid warehouse configured)")
            self.conn = None
            self.sqlite_conn = None
            self._sessions = {}
            self._jobs = {}
        else:
            # Use Databricks SQL
            print("Using Databricks SQL warehouse storage")
            self.sqlite_conn = None
            self.conn = sql.connect(
                server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                http_path=http_path,
                access_token=os.getenv("DATABRICKS_TOKEN")
            )
            self._init_tables()
            self._migrate_sessions_table()

    def _init_sqlite(self):
        """Initialize SQLite database for local storage."""
        os.makedirs("storage", exist_ok=True)
        db_path = "storage/sessions.db"
        self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
        self._create_sqlite_tables()
        self._migrate_sqlite_tables()
        print(f"SQLite database initialized at: {os.path.abspath(db_path)}")

    def _create_sqlite_tables(self):
        """Create SQLite tables if they don't exist."""
        cursor = self.sqlite_conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                name TEXT,
                updated_at TIMESTAMP
            )
        """)

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genie_jobs (
                job_id TEXT PRIMARY KEY,
                session_id TEXT,
                type TEXT,
                status TEXT,
                inputs TEXT,
                result TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                progress TEXT,
                FOREIGN KEY (session_id) REFERENCES genie_sessions(session_id)
            )
        """)

        self.sqlite_conn.commit()
        cursor.close()

    def _migrate_sqlite_tables(self):
        """Migrate SQLite tables to add new columns if needed."""
        cursor = self.sqlite_conn.cursor()

        # Check if name and updated_at columns exist
        cursor.execute("PRAGMA table_info(genie_sessions)")
        columns = {col[1] for col in cursor.fetchall()}

        if 'name' not in columns or 'updated_at' not in columns:
            print("Migrating SQLite sessions table - adding name and updated_at columns")

            if 'name' not in columns:
                cursor.execute("ALTER TABLE genie_sessions ADD COLUMN name TEXT")

            if 'updated_at' not in columns:
                cursor.execute("ALTER TABLE genie_sessions ADD COLUMN updated_at TIMESTAMP")

            # Backfill name and updated_at
            cursor.execute("""
                UPDATE genie_sessions
                SET name = strftime('%Y-%m-%d %H:%M:%S', created_at),
                    updated_at = created_at
                WHERE name IS NULL OR updated_at IS NULL
            """)

            self.sqlite_conn.commit()
            print("SQLite migration completed")

        cursor.close()

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
                completed_at TIMESTAMP,
                progress STRING
            )
        """)
        cursor.close()

    def _migrate_sessions_table(self):
        """Add name and updated_at columns if they don't exist."""
        cursor = self.conn.cursor()

        try:
            # Check if columns exist by attempting to select them
            cursor.execute("SELECT name, updated_at FROM genie_sessions LIMIT 1")
            print("Session table already has name and updated_at columns")
        except Exception:
            # Columns don't exist, add them
            print("Migrating sessions table - adding name and updated_at columns")

            # Add name column with default value from formatted created_at
            cursor.execute("""
                ALTER TABLE genie_sessions
                ADD COLUMN name STRING
            """)

            # Add updated_at column
            cursor.execute("""
                ALTER TABLE genie_sessions
                ADD COLUMN updated_at TIMESTAMP
            """)

            # Backfill name from created_at (format as timestamp)
            cursor.execute("""
                UPDATE genie_sessions
                SET name = DATE_FORMAT(created_at, 'yyyy-MM-dd HH:mm:ss')
                WHERE name IS NULL
            """)

            # Backfill updated_at from created_at
            cursor.execute("""
                UPDATE genie_sessions
                SET updated_at = created_at
                WHERE updated_at IS NULL
            """)

            print("Session table migration completed")

        cursor.close()

    def create_session(self, user_id: str, name: Optional[str] = None) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        if name is None:
            name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "INSERT INTO genie_sessions (session_id, user_id, created_at, name, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)",
                (session_id, user_id, name)
            )
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            self._sessions[session_id] = {
                "user_id": user_id,
                "name": name,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO genie_sessions VALUES (?, ?, CURRENT_TIMESTAMP(), ?, CURRENT_TIMESTAMP())",
                (session_id, user_id, name)
            )
            cursor.close()
        return session_id

    def save_job(self, job: Job):
        """Save a new job record."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """INSERT INTO genie_jobs
                   (job_id, session_id, type, status, inputs, progress, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (job.job_id, job.session_id, job.type, job.status,
                 json.dumps(job.inputs),
                 json.dumps(job.progress) if job.progress else None)
            )
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            self._jobs[job.job_id] = job
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO genie_jobs
                   (job_id, session_id, type, status, inputs, progress, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP())""",
                (job.job_id, job.session_id, job.type, job.status,
                 json.dumps(job.inputs),
                 json.dumps(job.progress) if job.progress else None)
            )
            cursor.close()

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
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
                completed_at=row[8],
                progress=json.loads(row[9]) if row[9] else None
            )
        elif self.conn is None:
            # In-memory storage
            return self._jobs.get(job_id)
        else:
            # Databricks SQL storage
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
                completed_at=row[8],
                progress=json.loads(row[9]) if row[9] else None
            )

    def update_job(self, job: Job):
        """Update job status, result, error, and progress."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """UPDATE genie_jobs
                   SET status = ?, result = ?, error = ?, completed_at = ?, progress = ?
                   WHERE job_id = ?""",
                (job.status,
                 json.dumps(job.result) if job.result else None,
                 job.error,
                 job.completed_at,
                 json.dumps(job.progress) if job.progress else None,
                 job.job_id)
            )
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            self._jobs[job.job_id] = job
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE genie_jobs
                   SET status = ?, result = ?, error = ?, completed_at = ?, progress = ?
                   WHERE job_id = ?""",
                (job.status,
                 json.dumps(job.result) if job.result else None,
                 job.error,
                 job.completed_at,
                 json.dumps(job.progress) if job.progress else None,
                 job.job_id)
            )
            cursor.close()

    def get_jobs_for_session(self, session_id: str) -> List[Job]:
        """Get all jobs for a session."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
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
                    completed_at=row[8],
                    progress=json.loads(row[9]) if row[9] else None
                )
                for row in rows
            ]
        elif self.conn is None:
            # In-memory storage
            jobs = [job for job in self._jobs.values() if job.session_id == session_id]
            return sorted(jobs, key=lambda j: j.created_at or datetime.min)
        else:
            # Databricks SQL storage
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
                    completed_at=row[8],
                    progress=json.loads(row[9]) if len(row) > 9 and row[9] else None
                )
                for row in rows
            ]

    def list_sessions(self, user_id: str = None, limit: int = 50, offset: int = 0) -> tuple[List[dict], int]:
        """List sessions with job counts, ordered by updated_at DESC."""
        if self.sqlite_conn:
            # SQLite mode
            cursor = self.sqlite_conn.cursor()

            # Build query with optional user_id filter
            where_clause = "WHERE s.user_id = ?" if user_id else ""
            params = [user_id, limit, offset] if user_id else [limit, offset]

            query = f"""
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                {where_clause}
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                ORDER BY s.updated_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM genie_sessions s {where_clause}"
            count_params = [user_id] if user_id else []
            cursor.execute(count_query, tuple(count_params))
            total = cursor.fetchone()[0]

            cursor.close()

            sessions = [
                {
                    "session_id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "job_count": row[5]
                }
                for row in rows
            ]

            return sessions, total
        elif self.conn is None:
            # In-memory mode
            sessions = list(self._sessions.values())
            if user_id:
                sessions = [s for s in sessions if s.get("user_id") == user_id]

            # Add job counts
            for session in sessions:
                session_id = session.get("session_id")
                if session_id:
                    session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == session_id)
                else:
                    # Find session_id by matching session object
                    for sid, sdata in self._sessions.items():
                        if sdata == session:
                            session["session_id"] = sid
                            session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == sid)
                            break

            # Sort by updated_at DESC
            sessions = sorted(sessions, key=lambda s: s.get("updated_at", datetime.min), reverse=True)
            total = len(sessions)
            return sessions[offset:offset + limit], total
        else:
            cursor = self.conn.cursor()

            # Build query with optional user_id filter
            where_clause = "WHERE s.user_id = ?" if user_id else ""
            params = [user_id, limit, offset] if user_id else [limit, offset]

            query = f"""
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                {where_clause}
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                ORDER BY s.updated_at DESC
                LIMIT ? OFFSET ?
            """

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM genie_sessions s {where_clause}"
            count_params = [user_id] if user_id else []
            cursor.execute(count_query, tuple(count_params))
            total = cursor.fetchone()[0]

            cursor.close()

            sessions = [
                {
                    "session_id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "job_count": row[5]
                }
                for row in rows
            ]

            return sessions, total

    def update_session_name(self, session_id: str, name: str):
        """Update session name and updated_at timestamp."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (name, session_id)
            )
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            if session_id in self._sessions:
                self._sessions[session_id]["name"] = name
                self._sessions[session_id]["updated_at"] = datetime.now()
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET name = ?, updated_at = CURRENT_TIMESTAMP() WHERE session_id = ?",
                (name, session_id)
            )
            cursor.close()

    def update_session_activity(self, session_id: str):
        """Update session updated_at timestamp to mark activity."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            if session_id in self._sessions:
                self._sessions[session_id]["updated_at"] = datetime.now()
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE genie_sessions SET updated_at = CURRENT_TIMESTAMP() WHERE session_id = ?",
                (session_id,)
            )
            cursor.close()

    def get_session_with_stats(self, session_id: str) -> Optional[dict]:
        """Get session with job count and metadata."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                """,
                (session_id,)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "session_id": row[0],
                "user_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "job_count": row[5]
            }
        elif self.conn is None:
            # In-memory storage
            if session_id not in self._sessions:
                return None
            session = self._sessions[session_id].copy()
            session["session_id"] = session_id
            session["job_count"] = sum(1 for j in self._jobs.values() if j.session_id == session_id)
            return session
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.user_id,
                    s.name,
                    s.created_at,
                    s.updated_at,
                    COUNT(j.job_id) as job_count
                FROM genie_sessions s
                LEFT JOIN genie_jobs j ON s.session_id = j.session_id
                WHERE s.session_id = ?
                GROUP BY s.session_id, s.user_id, s.name, s.created_at, s.updated_at
                """,
                (session_id,)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                "session_id": row[0],
                "user_id": row[1],
                "name": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "job_count": row[5]
            }

    def delete_session(self, session_id: str):
        """Delete session and all associated jobs (hard delete with cascade)."""
        if self.sqlite_conn:
            # SQLite storage
            cursor = self.sqlite_conn.cursor()
            # Delete jobs first (foreign key relationship)
            cursor.execute("DELETE FROM genie_jobs WHERE session_id = ?", (session_id,))
            # Delete session
            cursor.execute("DELETE FROM genie_sessions WHERE session_id = ?", (session_id,))
            self.sqlite_conn.commit()
            cursor.close()
        elif self.conn is None:
            # In-memory storage
            # Delete all jobs for this session
            self._jobs = {jid: job for jid, job in self._jobs.items() if job.session_id != session_id}
            # Delete session
            if session_id in self._sessions:
                del self._sessions[session_id]
        else:
            # Databricks SQL storage
            cursor = self.conn.cursor()
            # Delete jobs first (foreign key relationship)
            cursor.execute("DELETE FROM genie_jobs WHERE session_id = ?", (session_id,))
            # Delete session
            cursor.execute("DELETE FROM genie_sessions WHERE session_id = ?", (session_id,))
            cursor.close()
