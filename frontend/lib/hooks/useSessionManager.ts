/**
 * Hook for managing sessions
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Session } from '../api-client';

export function useSessionManager() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const LIMIT = 50;

  // Load sessions from API
  const loadSessions = useCallback(async (reset = false) => {
    setLoading(true);
    try {
      const currentOffset = reset ? 0 : offset;
      const result = await apiClient.listSessions(undefined, LIMIT, currentOffset);

      if (reset) {
        setSessions(result.sessions);
        setOffset(0);
      } else {
        setSessions(prev => [...prev, ...result.sessions]);
      }

      setHasMore(result.sessions.length === LIMIT && result.total_count > currentOffset + LIMIT);
      setOffset(currentOffset + result.sessions.length);

      // If no current session, select the most recent one
      if (!currentSessionId && result.sessions.length > 0) {
        setCurrentSessionId(result.sessions[0].session_id);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  }, [currentSessionId, offset]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions(true);
  }, []);

  // Create new session
  const createSession = useCallback(async (name?: string) => {
    try {
      const session = await apiClient.createSession('default', name);
      setSessions(prev => [session, ...prev]);
      setCurrentSessionId(session.session_id);
      return session.session_id;
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  }, []);

  // Update session name
  const updateSessionName = useCallback(async (sessionId: string, name: string) => {
    try {
      const updatedSession = await apiClient.updateSessionName(sessionId, name);
      setSessions(prev => prev.map(s => s.session_id === sessionId ? updatedSession : s));
    } catch (error) {
      console.error('Error updating session name:', error);
      throw error;
    }
  }, []);

  // Delete session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await apiClient.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));

      // If deleted session was current, switch to another
      if (sessionId === currentSessionId) {
        const remaining = sessions.filter(s => s.session_id !== sessionId);
        setCurrentSessionId(remaining.length > 0 ? remaining[0].session_id : null);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }, [currentSessionId, sessions]);

  // Select session
  const selectSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  // Switch session and restore state
  const switchSession = useCallback(async (sessionId: string) => {
    setCurrentSessionId(sessionId);

    try {
      // Fetch session details to get jobs and restore state
      const sessionData = await apiClient.getSession(sessionId);

      // Build workflow state from jobs
      const state: any = {};
      let currentStep = 1;

      for (const job of sessionData.jobs) {
        if (job.status === 'completed' && job.result) {
          switch (job.type) {
            case 'parse':
              state.parseResult = job.result;
              currentStep = Math.max(currentStep, 2);
              break;
            case 'generate':
              state.generateResult = job.result;
              currentStep = Math.max(currentStep, 3);
              break;
            case 'validate':
              state.validateResult = job.result;
              currentStep = Math.max(currentStep, 4);
              break;
            case 'benchmark_validate':
              state.benchmarks = job.result;
              currentStep = Math.max(currentStep, 5);
              break;
            case 'deploy':
              state.deployResult = job.result;
              currentStep = Math.max(currentStep, 6);
              break;
          }
        }
      }

      return { state, currentStep };
    } catch (error) {
      console.error('Error switching session:', error);
      return { state: {}, currentStep: 1 };
    }
  }, []);

  // Load more sessions
  const loadMoreSessions = useCallback(async () => {
    await loadSessions(false);
  }, [loadSessions]);

  // Rename session (alias for updateSessionName)
  const renameSession = updateSessionName;

  return {
    sessions,
    currentSessionId,
    loading,
    hasMore,
    createSession,
    updateSessionName,
    renameSession,
    deleteSession,
    selectSession,
    switchSession,
    loadMoreSessions,
    refreshSessions: () => loadSessions(true),
  };
}
