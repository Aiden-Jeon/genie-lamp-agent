/**
 * Type-safe API client for Genie Lamp Agent backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  type: string;
  result?: any;
  error?: string;
  created_at?: string;
  completed_at?: string;
}

export interface ValidationFix {
  old_catalog: string;
  old_schema: string;
  old_table: string;
  new_catalog: string;
  new_schema: string;
  new_table: string;
}

export const apiClient = {
  /**
   * Upload and parse requirement documents.
   */
  async parse(sessionId: string, formData: FormData): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/parse?session_id=${sessionId}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Parse failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Generate Genie space configuration from requirements.
   */
  async generate(
    sessionId: string,
    requirementsPath: string,
    model: string = 'databricks-gpt-5-2'
  ): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        requirements_path: requirementsPath,
        model,
      }),
    });
    if (!res.ok) throw new Error(`Generate failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Validate configuration against Unity Catalog.
   */
  async validate(
    sessionId: string,
    configPath: string
  ): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        config_path: configPath,
      }),
    });
    if (!res.ok) throw new Error(`Validate failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Apply validation fixes and re-validate.
   */
  async fixValidation(
    sessionId: string,
    configPath: string,
    replacements: ValidationFix[] = [],
    bulkCatalog?: string,
    bulkSchema?: string,
    excludeTables: string[] = []
  ): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/validate/fix`, {
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
    if (!res.ok) throw new Error(`Fix validation failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Deploy Genie space to Databricks.
   */
  async deploy(
    sessionId: string,
    configPath: string,
    parentPath?: string
  ): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        config_path: configPath,
        parent_path: parentPath,
      }),
    });
    if (!res.ok) throw new Error(`Deploy failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Get job status (for polling).
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
    if (!res.ok) throw new Error(`Get job status failed: ${res.statusText}`);
    return res.json();
  },

  /**
   * Get session information and all jobs.
   */
  async getSession(sessionId: string): Promise<{
    session_id: string;
    current_step: number;
    jobs: Array<{
      job_id: string;
      type: string;
      status: string;
      error?: string;
      created_at?: string;
    }>;
  }> {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`Get session failed: ${res.statusText}`);
    return res.json();
  },
};
