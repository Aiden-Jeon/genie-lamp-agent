/**
 * Parse step component for file upload and parsing.
 */

'use client';

import { useState, useEffect } from 'react';
import { useJobPolling } from '@/lib/hooks/useJobPolling';
import { apiClient } from '@/lib/api-client';

interface ParseStepProps {
  sessionId: string;
  onComplete: (result: any) => void;
}

export function ParseStep({ sessionId, onComplete }: ParseStepProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [useLLM, setUseLLM] = useState(true);
  const { job, isPolling, error: pollingError } = useJobPolling(jobId);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (files.length === 0) return;

    try {
      setUploadError(null);
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('use_llm', String(useLLM));
      files.forEach((f) => formData.append('files', f));

      const response = await apiClient.parse(sessionId, formData);
      setJobId(response.job_id);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  useEffect(() => {
    if (job?.status === 'completed') {
      onComplete(job.result);
    }
  }, [job, onComplete]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Step 1: Upload Requirements</h2>
      <p className="text-gray-600">
        Upload PDF or Markdown files containing your Genie space requirements.
      </p>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
        <input
          type="file"
          multiple
          accept=".pdf,.md"
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
          className="w-full"
          disabled={isPolling}
        />
        <p className="text-sm text-gray-600 mt-2">
          {files.length > 0
            ? `${files.length} file${files.length > 1 ? 's' : ''} selected`
            : 'Select PDF or Markdown files'}
        </p>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="use-llm"
          checked={useLLM}
          onChange={(e) => setUseLLM(e.target.checked)}
          disabled={isPolling}
        />
        <label htmlFor="use-llm" className="text-sm">
          Use LLM enrichment (recommended for better parsing)
        </label>
      </div>

      <button
        onClick={handleUpload}
        disabled={files.length === 0 || isPolling}
        className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
      >
        {isPolling ? 'Parsing...' : 'Start Parsing'}
      </button>

      {isPolling && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="font-semibold">Parsing {files.length} files...</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '50%' }} />
          </div>
          <p className="text-sm text-gray-600 mt-2">This may take a few minutes</p>
        </div>
      )}

      {(uploadError || pollingError) && (
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
          <p className="font-semibold">Error</p>
          <p>{uploadError || pollingError}</p>
        </div>
      )}

      {job?.status === 'failed' && (
        <div className="bg-red-50 p-4 rounded-lg border border-red-200 text-red-700">
          <p className="font-semibold">Parsing Failed</p>
          <p>{job.error}</p>
        </div>
      )}
    </div>
  );
}
