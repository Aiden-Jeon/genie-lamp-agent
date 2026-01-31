/**
 * Benchmark step component for managing benchmark questions.
 */

'use client';

import { useState } from 'react';

interface Benchmark {
  korean_question: string;  // Required
  expected_sql: string;     // Required
  id?: string;              // Optional
  question?: string;        // Optional (English translation)
  source_file?: string;     // Optional
  question_number?: number; // Optional
}

interface BenchmarkStepProps {
  sessionId: string;
  onComplete: (benchmarks: Benchmark[]) => void;
  onPrevious: () => void;
  existingResult?: Benchmark[];
}

export function BenchmarkStep({ sessionId, onComplete, onPrevious, existingResult }: BenchmarkStepProps) {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>(existingResult || []);
  const [showingExistingResult, setShowingExistingResult] = useState(!!existingResult);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [expandedSql, setExpandedSql] = useState<Set<number>>(new Set());

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      if (data.benchmarks && Array.isArray(data.benchmarks)) {
        setBenchmarks(data.benchmarks);
        setShowingExistingResult(false);
      } else {
        alert('Invalid benchmark file format. Expected {benchmarks: [...]}');
      }
    } catch (error) {
      alert('Failed to parse JSON file: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const addNewBenchmark = () => {
    setBenchmarks([...benchmarks, { korean_question: '', expected_sql: '' }]);
    setEditingIndex(benchmarks.length);
  };

  const updateBenchmark = (index: number, field: keyof Benchmark, value: string) => {
    const updated = [...benchmarks];
    updated[index] = { ...updated[index], [field]: value };
    setBenchmarks(updated);
  };

  const deleteBenchmark = (index: number) => {
    setBenchmarks(benchmarks.filter((_, i) => i !== index));
    if (editingIndex === index) setEditingIndex(null);
  };

  const duplicateBenchmark = (index: number) => {
    const duplicate = { ...benchmarks[index], id: undefined };
    setBenchmarks([...benchmarks, duplicate]);
  };

  const toggleSqlExpansion = (index: number) => {
    const newExpanded = new Set(expandedSql);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSql(newExpanded);
  };

  const getSqlPreview = (sql: string, isExpanded: boolean) => {
    if (!sql) return '';
    const lines = sql.trim().split('\n');
    if (isExpanded || lines.length <= 3) {
      return sql;
    }
    const preview = lines.slice(0, 3).join('\n');
    const remaining = lines.length - 3;
    return `${preview}\n... ${remaining} more lines`;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Step 4: Benchmark Questions</h2>
      <p className="text-gray-600">
        Upload benchmark questions to test your Genie space (optional).
      </p>

      {/* Show existing result if navigating back */}
      {showingExistingResult && existingResult && existingResult.length > 0 && (
        <div className="space-y-4">
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <p className="font-semibold text-green-800">✓ Benchmarks Loaded</p>
            <p className="text-sm text-gray-600 mt-1">
              {existingResult.length} benchmark question{existingResult.length > 1 ? 's' : ''} ready
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onPrevious}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              ← Back to Validate
            </button>
            <button
              onClick={() => setShowingExistingResult(false)}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Edit Benchmarks
            </button>
            <button
              onClick={() => onComplete(existingResult)}
              className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Continue to Deploy →
            </button>
          </div>
        </div>
      )}

      {!showingExistingResult && (
        <>
          {/* File upload */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <label className="block text-sm font-medium mb-2">Upload Benchmark JSON File:</label>
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-2">
              Required fields: <code className="bg-gray-100 px-1">korean_question</code>, <code className="bg-gray-100 px-1">expected_sql</code>
              <br />
              Optional: <code className="bg-gray-100 px-1">question</code> (English), <code className="bg-gray-100 px-1">id</code>, <code className="bg-gray-100 px-1">source_file</code>
            </p>
          </div>

          {/* Benchmarks table */}
          {benchmarks.length > 0 && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">
                  Benchmarks ({benchmarks.length})
                </h3>
                <button
                  onClick={addNewBenchmark}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                >
                  + Add Benchmark
                </button>
              </div>

              <div className="space-y-2">
                {benchmarks.map((benchmark, index) => (
                  <div
                    key={index}
                    className="border border-gray-300 rounded-lg overflow-hidden"
                  >
                    <div className="grid grid-cols-2 gap-0">
                      {/* Question column */}
                      <div className="p-4 border-r border-gray-300 bg-gray-50">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-sm font-semibold text-gray-700">Question</h4>
                          <div className="flex gap-2">
                            <button
                              onClick={() => duplicateBenchmark(index)}
                              className="text-gray-500 hover:text-gray-700"
                              title="Duplicate"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                            </button>
                            <button
                              onClick={() => deleteBenchmark(index)}
                              className="text-red-500 hover:text-red-700"
                              title="Delete"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                        {editingIndex === index ? (
                          <div className="space-y-2">
                            <textarea
                              value={benchmark.korean_question}
                              onChange={(e) => updateBenchmark(index, 'korean_question', e.target.value)}
                              className="w-full p-2 border border-gray-300 rounded text-sm min-h-[80px]"
                              placeholder="Enter Korean question... (Required)"
                            />
                            <textarea
                              value={benchmark.question || ''}
                              onChange={(e) => updateBenchmark(index, 'question', e.target.value)}
                              className="w-full p-2 border border-gray-200 rounded text-xs min-h-[60px] text-gray-600"
                              placeholder="English translation (Optional)"
                            />
                          </div>
                        ) : (
                          <div
                            className="cursor-pointer hover:bg-gray-100 p-2 rounded"
                            onClick={() => setEditingIndex(index)}
                          >
                            <p className="text-sm">
                              {benchmark.korean_question || <span className="text-gray-400">Click to edit...</span>}
                            </p>
                            {benchmark.question && (
                              <p className="text-xs text-gray-500 mt-2 italic">
                                {benchmark.question}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* SQL column */}
                      <div className="p-4 bg-white">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="text-sm font-semibold text-gray-700">Ground truth SQL answer</h4>
                          <button
                            onClick={() => setEditingIndex(editingIndex === index ? null : index)}
                            className="text-gray-500 hover:text-gray-700"
                            title="Edit"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                        </div>
                        {editingIndex === index ? (
                          <textarea
                            value={benchmark.expected_sql}
                            onChange={(e) => updateBenchmark(index, 'expected_sql', e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded text-sm font-mono min-h-[100px]"
                            placeholder="Enter SQL..."
                          />
                        ) : (
                          <div>
                            <pre
                              className="text-xs font-mono bg-gray-50 p-2 rounded overflow-x-auto cursor-pointer hover:bg-gray-100"
                              onClick={() => toggleSqlExpansion(index)}
                            >
                              <code className="text-blue-600">
                                {getSqlPreview(benchmark.expected_sql, expandedSql.has(index))}
                              </code>
                            </pre>
                            {benchmark.expected_sql && benchmark.expected_sql.split('\n').length > 3 && (
                              <button
                                onClick={() => toggleSqlExpansion(index)}
                                className="text-xs text-blue-500 hover:text-blue-700 mt-1"
                              >
                                {expandedSql.has(index) ? 'Show less' : 'Show more'}
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={onPrevious}
              className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              ← Previous
            </button>
            {benchmarks.length === 0 ? (
              <button
                onClick={() => onComplete([])}
                className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Skip Benchmarks & Continue to Deploy →
              </button>
            ) : (
              <button
                onClick={() => onComplete(benchmarks)}
                className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Save {benchmarks.length} Benchmark{benchmarks.length > 1 ? 's' : ''} & Continue →
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
