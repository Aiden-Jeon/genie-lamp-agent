/**
 * Main application page with 6-step workflow.
 */

'use client';

import { useState } from 'react';
import { Stepper } from '@/components/Stepper';
import { ParseStep } from '@/components/ParseStep';
import { GenerateStep } from '@/components/GenerateStep';
import { ValidateStep } from '@/components/ValidateStep';
import { BenchmarkStep } from '@/components/BenchmarkStep';
import { DeployStep } from '@/components/DeployStep';

export default function Home() {
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      return crypto.randomUUID();
    }
    return '';
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [workflowState, setWorkflowState] = useState<any>({});

  const steps = ['Upload & Extract', 'Generate', 'Validate', 'Benchmark', 'Deploy', 'Complete'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto p-8 max-w-6xl">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Genie Lamp Agent
          </h1>
          <p className="text-gray-600">
            Generate Databricks Genie Spaces from natural language requirements
          </p>
          <p className="text-sm text-gray-500 mt-1" suppressHydrationWarning>
            Session: {sessionId}
          </p>
        </header>

        <Stepper currentStep={currentStep} steps={steps} />

        <div className="bg-white rounded-lg shadow-lg p-8 mt-8">
          {currentStep === 1 && (
            <ParseStep
              sessionId={sessionId}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, parseResult: result }));
                setCurrentStep(2);
              }}
              existingResult={workflowState.parseResult}
            />
          )}

          {currentStep === 2 && (
            <GenerateStep
              sessionId={sessionId}
              requirementsPath={workflowState.parseResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, generateResult: result }));
                setCurrentStep(3);
              }}
              onPrevious={() => setCurrentStep(1)}
              existingResult={workflowState.generateResult}
            />
          )}

          {currentStep === 3 && (
            <ValidateStep
              sessionId={sessionId}
              configPath={workflowState.generateResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, validateResult: result }));
                setCurrentStep(4);
              }}
              onPrevious={() => setCurrentStep(2)}
              existingResult={workflowState.validateResult}
            />
          )}

          {currentStep === 4 && (
            <BenchmarkStep
              sessionId={sessionId}
              onComplete={(benchmarks) => {
                setWorkflowState((s: any) => ({ ...s, benchmarks }));
                setCurrentStep(5);
              }}
              onPrevious={() => setCurrentStep(3)}
              existingResult={workflowState.benchmarks}
            />
          )}

          {currentStep === 5 && (
            <DeployStep
              sessionId={sessionId}
              configPath={workflowState.generateResult?.output_path}
              onComplete={(result) => {
                setWorkflowState((s: any) => ({ ...s, deployResult: result }));
                setCurrentStep(6);
              }}
              onPrevious={() => setCurrentStep(4)}
              existingResult={workflowState.deployResult}
            />
          )}

          {currentStep === 6 && (
            <div className="text-center">
              <div className="bg-green-50 p-8 rounded-lg border border-green-200">
                <h2 className="text-3xl font-bold text-green-800 mb-4">
                  ✅ Complete!
                </h2>
                <div className="space-y-3">
                  <p className="text-gray-700">
                    <span className="font-semibold">Space ID:</span>{' '}
                    <code className="bg-gray-100 px-2 py-1 rounded">
                      {workflowState.deployResult?.space_id}
                    </code>
                  </p>
                  <a
                    href={workflowState.deployResult?.space_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Open Genie Space →
                  </a>
                </div>
              </div>

              <div className="mt-6 flex gap-3 justify-center">
                <button
                  onClick={() => setCurrentStep(5)}
                  className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  ← Back to Deploy
                </button>
                <button
                  onClick={() => {
                    setCurrentStep(1);
                    setWorkflowState({});
                    window.location.reload();
                  }}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Start New Workflow
                </button>
              </div>
            </div>
          )}
        </div>

        <footer className="mt-8 text-center text-sm text-gray-500">
          <p>Powered by Databricks Foundation Models</p>
        </footer>
      </div>
    </div>
  );
}
