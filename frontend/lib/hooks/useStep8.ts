/**
 * useStep8 — STEP 8A-8F Node API Hooks
 *
 * Provides real-time access to all STEP 8 node outputs with loading
 * and error states. Integrates with /api/proposals/{id}/step8a/* endpoints.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  CustomerProfile,
  ValidationReport,
  ConsolidatedProposal,
  MockEvalResult,
  FeedbackSummary,
  RewriteRecord,
  NodeStatus,
  Step8Status,
  ArtifactVersion,
} from "@/lib/types/step8";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

/** ============ useNodeStatus ============ */
export interface UseNodeStatusOptions {
  proposalId: string;
  pollInterval?: number; // ms, 0 = no polling
}

export interface UseNodeStatusResult {
  status: Step8Status | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => void;
}

export function useNodeStatus(opts: UseNodeStatusOptions): UseNodeStatusResult {
  const { proposalId, pollInterval = 0 } = opts;
  const [status, setStatus] = useState<Step8Status | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cancelledRef = useRef(false);
  const pollTimerRef = useRef<NodeJS.Timeout>();

  const fetch_ = useCallback(async () => {
    if (!proposalId) return;
    cancelledRef.current = false;
    setIsLoading(true);
    setError(null);

    try {
      const token = await getAuthToken();
      const response = await fetch(
        `${BASE}/proposals/${proposalId}/step8a/node-status`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        throw new Error(`Node status request failed: ${response.statusText}`);
      }

      const data = await response.json();
      if (!cancelledRef.current) {
        // Convert API response to Step8Status
        setStatus({
          proposal_id: proposalId,
          nodes: data.nodes || [],
          overall_progress: calculateProgress(data.nodes),
          last_updated: new Date().toISOString(),
        });
      }
    } catch (err) {
      if (!cancelledRef.current) {
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (!cancelledRef.current) {
        setIsLoading(false);
      }
    }
  }, [proposalId]);

  // Initial fetch
  useEffect(() => {
    fetch_();
    return () => {
      cancelledRef.current = true;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [fetch_]);

  // Polling
  useEffect(() => {
    if (pollInterval <= 0 || !proposalId) return;

    const poll = () => {
      fetch_();
      pollTimerRef.current = setTimeout(poll, pollInterval);
    };

    pollTimerRef.current = setTimeout(poll, pollInterval);
    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [pollInterval, proposalId, fetch_]);

  return { status, isLoading, error, refresh: fetch_ };
}

/** ============ useValidateNode ============ */
export interface ValidateNodeRequest {
  node_name: string;
}

export interface ValidateNodeResult {
  proposal_id: string;
  node_name: string;
  status: "queued";
  job_id: string;
  estimated_duration_seconds: number;
}

export function useValidateNode() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const validate = useCallback(
    async (proposalId: string, nodeName: string): Promise<ValidateNodeResult | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getAuthToken();
        const response = await fetch(
          `${BASE}/proposals/${proposalId}/step8a/validate-node`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ node_name: nodeName }),
          }
        );

        if (!response.ok) {
          throw new Error(`Validation request failed: ${response.statusText}`);
        }

        return await response.json();
      } catch (err) {
        const error_ = err instanceof Error ? err : new Error(String(err));
        setError(error_);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { validate, isLoading, error };
}

/** ============ useVersionHistory ============ */
export interface UseVersionHistoryOptions {
  proposalId: string;
  outputKey: string;
}

export interface UseVersionHistoryResult {
  versions: ArtifactVersion[];
  activeVersion: number;
  isLoading: boolean;
  error: Error | null;
  refresh: () => void;
}

export function useVersionHistory(
  opts: UseVersionHistoryOptions
): UseVersionHistoryResult {
  const { proposalId, outputKey } = opts;
  const [versions, setVersions] = useState<ArtifactVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cancelledRef = useRef(false);

  const fetch_ = useCallback(async () => {
    if (!proposalId || !outputKey) return;
    cancelledRef.current = false;
    setIsLoading(true);
    setError(null);

    try {
      const token = await getAuthToken();
      const response = await fetch(
        `${BASE}/proposals/${proposalId}/step8a/versions/${outputKey}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        throw new Error(`Version history request failed: ${response.statusText}`);
      }

      const data = await response.json();
      if (!cancelledRef.current) {
        setVersions(data.versions || []);
        setActiveVersion(data.active_version || 0);
      }
    } catch (err) {
      if (!cancelledRef.current) {
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (!cancelledRef.current) {
        setIsLoading(false);
      }
    }
  }, [proposalId, outputKey]);

  useEffect(() => {
    fetch_();
    return () => {
      cancelledRef.current = true;
    };
  }, [fetch_]);

  return { versions, activeVersion, isLoading, error, refresh: fetch_ };
}

/** ============ useNodeData ============ */
export type NodeDataType =
  | CustomerProfile
  | ValidationReport
  | ConsolidatedProposal
  | MockEvalResult
  | FeedbackSummary
  | RewriteRecord;

export function useNodeData<T extends NodeDataType>(
  proposalId: string,
  nodeOutputKey: string
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cancelledRef = useRef(false);

  const fetch_ = useCallback(async () => {
    if (!proposalId || !nodeOutputKey) return;
    cancelledRef.current = false;
    setIsLoading(true);
    setError(null);

    try {
      const token = await getAuthToken();
      // This would be implemented as a new endpoint or via state query
      // For now, mock the fetch
      const response = await fetch(
        `${BASE}/proposals/${proposalId}/step8a/versions/${nodeOutputKey}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        throw new Error(`Node data request failed: ${response.statusText}`);
      }

      const result = await response.json();
      if (!cancelledRef.current && result.versions && result.versions.length > 0) {
        // Get the latest version data
        // In a real implementation, this would fetch the actual artifact data
        setData(result.versions[0] as T);
      }
    } catch (err) {
      if (!cancelledRef.current) {
        setError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (!cancelledRef.current) {
        setIsLoading(false);
      }
    }
  }, [proposalId, nodeOutputKey]);

  useEffect(() => {
    fetch_();
    return () => {
      cancelledRef.current = true;
    };
  }, [fetch_]);

  const refresh = useCallback(() => {
    fetch_();
  }, [fetch_]);

  return { data, isLoading, error, refresh };
}

/** ============ Helper Functions ============ */

async function getAuthToken(): Promise<string> {
  if (typeof window === "undefined") return "";
  if (process.env.NODE_ENV === "development") return "";

  try {
    // In a real app, get from Supabase session
    const sessionStr = localStorage.getItem("sb-auth-session");
    if (!sessionStr) return "";
    const session = JSON.parse(sessionStr);
    return session?.access_token ?? "";
  } catch {
    return "";
  }
}

function calculateProgress(nodes: NodeStatus[]): number {
  if (nodes.length === 0) return 0;
  const completed = nodes.filter((n) => n.status === "completed").length;
  return Math.round((completed / nodes.length) * 100);
}
