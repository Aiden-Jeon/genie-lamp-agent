/**
 * Validate step component for configuration validation.
 */

'use client';

import { useState, useEffect } from 'react';
import { useJobPolling } from '@/lib/hooks/useJobPolling';
import { apiClient, ValidationFix } from '@/lib/api-client';
import { ValidationFixer } from './ValidationFixer';

interface ValidateStepProps {
  sessionId: string;
  configPath: string;
  onComplete: (result: any) => void;
}

export function ValidateStep({ sessionId, configPath, onComplete }: ValidateStepProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [showFixer, setShowFixer] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const { job, isPolling, error } = useJobPolling(jobId);

  const handleValidate = async () => {
    try {
      const response = await apiClient.validate(sessionId, configPath);
      setJobId(response.job_id);
    } catch (err) {
      console.error('Validation failed:', err);
    }
  };

  const handleApplyFixes = async (
    fixes: ValidationFix[],
    bulkCatalog?: string,
    bulkSchema?: string,
    excludeTables?: string[]
  ) => {
    try {
      setShowFixer(false);
      setValidationResult(null);
      const response = await apiClient.fixValidation(
        sessionId,
        configPath,
        fixes,
        bulkCatalog,
        bulkSchema,
        excludeTables
      );
      setJobId(response.job_id);
    } catch (err) {
      console.error('Fix validation failed:', err);
    }
  };

  useEffect(() => {
    if (job?.status === 'completed' && job.result) {
      setValidationResult(job.result);
      if (job.result.has_errors) {
        setShowFixer(true);
      } else {
        onComplete(job.result);
      }
    }
  }, [job, onComplete]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Step 3: Validate Configuration</h2>
      <p className="text-gray-600">
        Verify that all tables and columns exist in Unity Catalog.
      </p>

      {!validationResult && !isPolling && (
        <button
          onClick={handleValidate}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Validate Configuration
        </button>
      )}

      {isPolling && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="font-semibold">Validating configuration...</p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
          <p className="text-sm text-gray-600 mt-2">Checking Unity Catalog tables and columns</p>
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
          <p className="font-semibold">Validation Failed</p>
          <p>{job.error}</p>
        </div>
      )}

      {showFixer && validationResult?.issues && (
        <ValidationFixer issues={validationResult.issues} onApplyFixes={handleApplyFixes} />
      )}

      {validationResult && !validationResult.has_errors && (
        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <h3 className="text-xl font-bold text-green-800 mb-2">✅ Validation Passed!</h3>
          <p className="text-green-700">
            {validationResult.tables_valid} table{validationResult.tables_valid > 1 ? 's' : ''}{' '}
            validated successfully.
          </p>
          <p className="text-sm text-gray-600 mt-2">Ready to deploy to Databricks Genie.</p>
        </div>
      )}
    </div>
  );
}
