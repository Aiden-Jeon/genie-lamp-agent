/**
 * Hook for polling job status
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Job } from '../api-client';

export function useJobPolling(jobId: string | null, interval: number = 2000) {
  const [job, setJob] = useState<Job | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollJob = useCallback(async () => {
    if (!jobId) return;

    try {
      const jobStatus = await apiClient.getJobStatus(jobId);
      setJob(jobStatus);

      if (jobStatus.status === 'completed') {
        setIsPolling(false);
      } else if (jobStatus.status === 'failed') {
        setIsPolling(false);
        setError(jobStatus.error || 'Job failed');
      }
    } catch (err) {
      console.error('Error polling job:', err);
      setIsPolling(false);
      setError(err instanceof Error ? err.message : 'Failed to poll job');
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      setIsPolling(false);
      setJob(null);
      setError(null);
      return;
    }

    setIsPolling(true);
    setError(null);
    pollJob(); // Initial fetch

    const intervalId = setInterval(pollJob, interval);

    return () => {
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [jobId, interval, pollJob]);

  return { job, isPolling, error };
}
