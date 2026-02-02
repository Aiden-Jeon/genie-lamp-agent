/**
 * API client for Genie Lamp Agent backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// Types matching backend models
export interface ValidationFix {
  old_catalog: string;
  old_schema: string;
  old_table: string;
  new_catalog: string;
  new_schema: string;
  new_table: string;
}

export interface Session {
  session_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  job_count: number;
}

export interface Job {
  job_id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  progress?: any; // Can be number or object with detailed progress
  created_at: string | null;
  completed_at: string | null;
}

export interface FileContentResponse {
  content: string;
  filename: string;
  size_bytes: number;
  line_count: number;
  char_count: number;
}

export interface FileProgress {
  name: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  cache_hit?: boolean;
  duration_ms?: number;
  pages_total?: number;
  pages_completed?: number;
  current_page?: number;
  error?: string;
  extracted?: {
    questions_count: number;
    tables_count: number;
    queries_count: number;
  };
}

// API client
export const apiClient = {
  // Sessions
  async createSession(userId: string = 'default', name?: string): Promise<Session> {
    const response = await fetch(`${API_BASE}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, name }),
    });
    if (!response.ok) throw new Error('Failed to create session');
    return response.json();
  },

  async listSessions(userId?: string, limit = 50, offset = 0): Promise<{ sessions: Session[]; total_count: number }> {
    const params = new URLSearchParams();
    if (userId) params.set('user_id', userId);
    params.set('limit', limit.toString());
    params.set('offset', offset.toString());

    const response = await fetch(`${API_BASE}/api/sessions?${params}`);
    if (!response.ok) throw new Error('Failed to list sessions');
    return response.json();
  },

  async getSession(sessionId: string): Promise<{ session_id: string; current_step: number; jobs: Job[] }> {
    const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
    if (!response.ok) throw new Error('Failed to get session');
    return response.json();
  },

  async updateSessionName(sessionId: string, name: string): Promise<Session> {
    const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) throw new Error('Failed to update session name');
    return response.json();
  },

  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete session');
  },

  // Jobs
  async getJobStatus(jobId: string): Promise<Job> {
    const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to get job status');
    return response.json();
  },

  // Parse
  async parse(sessionId: string, formData: FormData): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/parse`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to start parse job');
    return response.json();
  },

  // Generate
  async generate(sessionId: string, requirementsPath: string, model: string = 'databricks-gpt-5-2'): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        requirements_path: requirementsPath,
        model,
      }),
    });
    if (!response.ok) throw new Error('Failed to start generate job');
    return response.json();
  },

  // Validate
  async validate(sessionId: string, configPath: string): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        config_path: configPath,
      }),
    });
    if (!response.ok) throw new Error('Failed to start validate job');
    return response.json();
  },

  async fixValidation(
    sessionId: string,
    configPath: string,
    replacements: ValidationFix[] = [],
    bulkCatalog?: string,
    bulkSchema?: string,
    excludeTables: string[] = []
  ): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/validate/fix`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        config_path: configPath,
        replacements,
        bulk_catalog: bulkCatalog,
        bulk_schema: bulkSchema,
        exclude_tables: excludeTables,
      }),
    });
    if (!response.ok) throw new Error('Failed to fix validation');
    return response.json();
  },

  // Deploy
  async deploy(sessionId: string, configPath: string, parentPath?: string): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        config_path: configPath,
        parent_path: parentPath,
      }),
    });
    if (!response.ok) throw new Error('Failed to start deploy job');
    return response.json();
  },

  // Benchmark validation
  async validateBenchmarks(sessionId: string, benchmarks: any[]): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE}/api/benchmark/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        benchmarks,
      }),
    });
    if (!response.ok) throw new Error('Failed to start benchmark validation');
    return response.json();
  },

  // Files
  async getFileContent(sessionId: string, filename: string): Promise<FileContentResponse> {
    const response = await fetch(`${API_BASE}/api/files/${sessionId}/${filename}`);
    if (!response.ok) throw new Error('Failed to get file content');
    return response.json();
  },
};
