/**
 * Deploy step component for Genie space deployment.
 */

'use client';

import { useState, useEffect } from 'react';
import { useJobPolling } from '@/lib/hooks/useJobPolling';
import { apiClient } from '@/lib/api-client';

interface DeployStepProps {
  sessionId: string;
  configPath: string;
  onComplete: (result: any) => void;
  onPrevious: () => void;
}

export function DeployStep({ sessionId, configPath, onComplete, onPrevious }: DeployStepProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [parentPath, setParentPath] = useState('');
  const { job, isPolling, error } = useJobPolling(jobId);

  const handleDeploy = async () => {
    try {
      const response = await apiClient.deploy(
        sessionId,
        configPath,
        parentPath || undefined
      );
      setJobId(response.job_id);
    } catch (err) {
      console.error('Deploy failed:', err);
    }
  };

  useEffect(() => {
    if (job?.status === 'completed') {
      onComplete(job.result);
    }
  }, [job, onComplete]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Step 4: Deploy Genie Space</h2>
      <p className="text-gray-600">
        Deploy your validated configuration to Databricks Genie.
      </p>

      <div className="space-y-2">
        <label className="block text-sm font-medium">
          Parent Path (Optional):
        </label>
        <input
          type="text"
          placeholder="/Workspace/Shared/Genie Spaces"
          value={parentPath}
          onChange={(e) => setParentPath(e.target.value)}
          disabled={isPolling}
          className="w-full p-2 border border-gray-300 rounded-lg"
        />
        <p className="text-xs text-gray-500">
          Leave empty to deploy to your user workspace
        </p>
      </div>

      <div className="flex gap-3">
        <button
          onClick={onPrevious}
          disabled={isPolling}
          className="px-6 py-3 bg-gray-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
        >
          ← Previous
        </button>
        <button
          onClick={handleDeploy}
          disabled={isPolling}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
        >
          {isPolling ? 'Deploying...' : 'Deploy Genie Space'}
        </button>
      </div>

      {isPolling && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="font-semibold">Deploying to Databricks Genie...</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '85%' }} />
          </div>
          <p className="text-sm text-gray-600 mt-2">Creating space via API</p>
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
          <p className="font-semibold">Deployment Failed</p>
          <p>{job.error}</p>
        </div>
      )}
    </div>
  );
}
