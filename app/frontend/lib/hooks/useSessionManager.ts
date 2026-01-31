/**
 * Session management hook with infinite scroll and state restoration.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Session } from '../api-client';

interface WorkflowState {
  parseResult?: any;
  generateResult?: any;
  validateResult?: any;
  benchmarks?: any;
  deployResult?: any;
}

interface UseSessionManagerResult {
  sessions: Session[];
  currentSessionId: string | null;
  loading: boolean;
  hasMore: boolean;
  fetchSessions: (reset?: boolean) => Promise<void>;
  loadMoreSessions: () => Promise<void>;
  createSession: (name?: string) => Promise<string>;
  switchSession: (sessionId: string) => Promise<{ state: WorkflowState; currentStep: number }>;
  renameSession: (sessionId: string, newName: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
}

const STORAGE_KEY = 'genie_lamp_current_session';
const LIMIT = 50;

export function useSessionManager(initialSessionId?: string): UseSessionManagerResult {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  // Fetch sessions with pagination
  const fetchSessions = useCallback(async (reset: boolean = false) => {
    try {
      setLoading(true);
      const newOffset = reset ? 0 : offset;
      const response = await apiClient.listSessions(LIMIT, newOffset);

      if (reset) {
        setSessions(response.sessions);
        setOffset(LIMIT);
      } else {
        setSessions((prev) => [...prev, ...response.sessions]);
        setOffset((prev) => prev + LIMIT);
      }

      setHasMore(response.sessions.length === LIMIT);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  }, [offset]);

  // Load more sessions (infinite scroll)
  const loadMoreSessions = useCallback(async () => {
    if (loading || !hasMore) return;
    await fetchSessions(false);
  }, [loading, hasMore, fetchSessions]);

  // Create new session
  const createSession = useCallback(async (name?: string): Promise<string> => {
    try {
      const newSession = await apiClient.createSession(name);

      // Add to top of list (most recent)
      setSessions((prev) => [newSession, ...prev]);

      // Set as current session
      setCurrentSessionId(newSession.session_id);
      localStorage.setItem(STORAGE_KEY, newSession.session_id);

      return newSession.session_id;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  }, []);

  // Switch to a different session
  const switchSession = useCallback(
    async (sessionId: string): Promise<{ state: WorkflowState; currentStep: number }> => {
      try {
        // Fetch session jobs
        const sessionData = await apiClient.getSession(sessionId);

        // Build workflow state from completed jobs
        const state: WorkflowState = {};
        const completedJobs = sessionData.jobs.filter((job) => job.status === 'completed');

        completedJobs.forEach((job) => {
          if (job.type === 'parse') {
            state.parseResult = job.result;
          } else if (job.type === 'generate') {
            state.generateResult = job.result;
          } else if (job.type === 'validate') {
            state.validateResult = job.result;
          } else if (job.type === 'deploy') {
            state.deployResult = job.result;
          }
        });

        // Calculate current step (next step after completed jobs)
        const currentStep = sessionData.current_step;

        // Update current session
        setCurrentSessionId(sessionId);
        localStorage.setItem(STORAGE_KEY, sessionId);

        return { state, currentStep };
      } catch (error) {
        console.error('Failed to switch session:', error);
        throw error;
      }
    },
    []
  );

  // Rename session
  const renameSession = useCallback(async (sessionId: string, newName: string) => {
    try {
      const updatedSession = await apiClient.updateSessionName(sessionId, newName);

      // Update in local state
      setSessions((prev) =>
        prev.map((session) =>
          session.session_id === sessionId ? updatedSession : session
        )
      );
    } catch (error) {
      console.error('Failed to rename session:', error);
      throw error;
    }
  }, []);

  // Delete session
  const deleteSession = useCallback(
    async (sessionId: string) => {
      const confirmed = window.confirm(
        `Delete this session? This will remove all jobs and cannot be undone.`
      );

      if (!confirmed) return;

      try {
        await apiClient.deleteSession(sessionId);

        // Remove from local state
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));

        // If deleting current session, switch to most recent or create new
        if (sessionId === currentSessionId) {
          const remainingSessions = sessions.filter((s) => s.session_id !== sessionId);
          if (remainingSessions.length > 0) {
            const mostRecent = remainingSessions[0];
            await switchSession(mostRecent.session_id);
          } else {
            // No sessions left, create a new one
            await createSession();
          }
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
        throw error;
      }
    },
    [currentSessionId, sessions, switchSession, createSession]
  );

  // Initial load: fetch sessions and restore current session
  useEffect(() => {
    const initialize = async () => {
      // Fetch initial sessions
      await fetchSessions(true);

      // Restore session from URL, localStorage, or create new
      const urlParams = new URLSearchParams(window.location.search);
      const sessionFromUrl = urlParams.get('session');
      const sessionFromStorage = localStorage.getItem(STORAGE_KEY);
      const sessionToRestore = initialSessionId || sessionFromUrl || sessionFromStorage;

      if (sessionToRestore) {
        try {
          // Verify session exists and set as current
          await apiClient.getSession(sessionToRestore);
          setCurrentSessionId(sessionToRestore);
          localStorage.setItem(STORAGE_KEY, sessionToRestore);
        } catch {
          // Session doesn't exist, create new one
          await createSession();
        }
      } else {
        // No session to restore, create new one
        await createSession();
      }
    };

    initialize();
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    sessions,
    currentSessionId,
    loading,
    hasMore,
    fetchSessions,
    loadMoreSessions,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
  };
}
