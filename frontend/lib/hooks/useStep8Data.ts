/**
 * useStep8Data — STEP 8 Data Fetching Hook
 *
 * Provides unified access to all STEP 8 node outputs with loading
 * and error states. Integrates with existing artifact fetching logic.
 */

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  Step8Status,
  CustomerProfile,
  ValidationReport,
  ConsolidatedProposal,
  MockEvalResult,
  FeedbackSummary,
  RewriteRecord,
  ReviewPanelData,
  NodeStatus,
} from "@/lib/types/step8";

export interface UseStep8DataOptions {
  proposalId: string;
  pollingInterval?: number; // ms, 0 to disable
  autoFetch?: boolean;
}

export interface UseStep8DataResult {
  status: Step8Status | null;
  customerProfile: CustomerProfile | null;
  validationReport: ValidationReport | null;
  consolidatedProposal: ConsolidatedProposal | null;
  mockEvalResult: MockEvalResult | null;
  feedbackSummary: FeedbackSummary | null;
  rewriteHistory: RewriteRecord | null;
  reviewPanelData: ReviewPanelData | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  validateNode: (nodeId: string) => Promise<void>;
}

/**
 * Fetch STEP 8 status and all node outputs
 * Falls back to mock data if endpoints not ready
 */
export function useStep8Data({
  proposalId,
  pollingInterval = 5000,
  autoFetch = true,
}: UseStep8DataOptions): UseStep8DataResult {
  const [status, setStatus] = useState<Step8Status | null>(null);
  const [customerProfile, setCustomerProfile] =
    useState<CustomerProfile | null>(null);
  const [validationReport, setValidationReport] =
    useState<ValidationReport | null>(null);
  const [consolidatedProposal, setConsolidatedProposal] =
    useState<ConsolidatedProposal | null>(null);
  const [mockEvalResult, setMockEvalResult] = useState<MockEvalResult | null>(
    null,
  );
  const [feedbackSummary, setFeedbackSummary] =
    useState<FeedbackSummary | null>(null);
  const [rewriteHistory, setRewriteHistory] = useState<RewriteRecord | null>(
    null,
  );
  const [reviewPanelData, setReviewPanelData] =
    useState<ReviewPanelData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Fetch node statuses
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${proposalId}/step8/status`,
      );
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch {
      // Endpoint not ready, will use fallback
      console.warn("STEP 8 status endpoint not ready");
    }
  }, [proposalId]);

  // Fetch individual node data
  const fetchNodeData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Try to fetch from dedicated endpoints first
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${proposalId}/step8/status`,
      );
      if (response.ok) {
        const data = await response.json();
        // 각 노드 데이터 분배
        if (data.customer_profile) setCustomerProfile(data.customer_profile);
        if (data.validation_report) setValidationReport(data.validation_report);
        if (data.consolidated_proposal) setConsolidatedProposal(data.consolidated_proposal);
        if (data.mock_eval_result) setMockEvalResult(data.mock_eval_result);
        if (data.feedback_summary) setFeedbackSummary(data.feedback_summary);
        if (data.rewrite_history) setRewriteHistory(data.rewrite_history);
        if (data.review_panel) setReviewPanelData(data.review_panel);
        setStatus(data);
      }
    } catch (e) {
      const err =
        e instanceof Error ? e : new Error("Failed to fetch STEP 8 data");
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [proposalId]); // removed fetchStatus as it is no longer used in this scope (or properly refactored)

  // Initial fetch
  useEffect(() => {
    if (autoFetch) {
      fetchNodeData();
    }
  }, [autoFetch, fetchNodeData]);

  // Polling
  useEffect(() => {
    if (pollingInterval <= 0) return;

    const timer = setInterval(() => {
      fetchNodeData();
    }, pollingInterval);

    return () => clearInterval(timer);
  }, [pollingInterval, fetchNodeData]);

  // Validate node
  const validateNode = useCallback(
    async (nodeId: string) => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${proposalId}/step8/validate/${nodeId}`,
          { method: "POST" },
        );
        if (response.ok) {
          // Refresh data after validation
          await fetchNodeData();
        }
      } catch (e) {
        console.error("Validation failed:", e);
      }
    },
    [proposalId, fetchNodeData],
  );

  return {
    status,
    customerProfile,
    validationReport,
    consolidatedProposal,
    mockEvalResult,
    feedbackSummary,
    rewriteHistory,
    reviewPanelData,
    isLoading,
    error,
    refresh: fetchNodeData,
    validateNode,
  };
}
