/**
 * Generate step component for LLM-based config generation.
 */

'use client';

import { useState, useEffect } from 'react';
import { useJobPolling } from '@/lib/hooks/useJobPolling';
import { apiClient } from '@/lib/api-client';

interface GenerateStepProps {
  sessionId: string;
  requirementsPath: string;
  onComplete: (result: any) => void;
}

export function GenerateStep({ sessionId, requirementsPath, onComplete }: GenerateStepProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [model, setModel] = useState('databricks-gpt-5-2');
  const { job, isPolling, error } = useJobPolling(jobId);

  const handleGenerate = async () => {
    try {
      const response = await apiClient.generate(sessionId, requirementsPath, model);
      setJobId(response.job_id);
    } catch (err) {
      console.error('Generate failed:', err);
    }
  };

  useEffect(() => {
    if (job?.status === 'completed') {
      onComplete(job.result);
    }
  }, [job, onComplete]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Step 2: Generate Configuration</h2>
      <p className="text-gray-600">
        Use AI to generate a Genie space configuration from your requirements.
      </p>

      <div className="space-y-2">
        <label className="block text-sm font-medium">LLM Model:</label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          disabled={isPolling}
          className="w-full p-2 border border-gray-300 rounded-lg"
        >
          <option value="databricks-gpt-5-2">GPT-5-2 (Recommended)</option>
          <option value="databricks-claude-opus-4-5">Claude Opus 4.5</option>
          <option value="databricks-claude-sonnet-4-5">Claude Sonnet 4.5</option>
        </select>
      </div>

      <button
        onClick={handleGenerate}
        disabled={isPolling}
        className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
      >
        {isPolling ? 'Generating...' : 'Generate Configuration'}
      </button>

      {isPolling && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="font-semibold">Generating Genie configuration with {model}...</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '75%' }} />
          </div>
          <p className="text-sm text-gray-600 mt-2">This may take 30-60 seconds</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
          <p className="font-semibold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {job?.status === 'failed' && (
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
          <p className="font-semibold">Generation Failed</p>
          <p>{job.error}</p>
        </div>
      )}
    </div>
  );
}
