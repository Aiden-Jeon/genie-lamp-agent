/**
 * Hook for polling job status until completion.
 */

import { useState, useEffect } from 'react';
import { apiClient, JobStatus } from '@/lib/api-client';

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    setIsPolling(true);
    setError(null);

    const interval = setInterval(async () => {
      try {
        const status = await apiClient.getJobStatus(jobId);
        setJob(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setIsPolling(false);
          clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch job status');
        setIsPolling(false);
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [jobId]);

  return { job, isPolling, error };
}
