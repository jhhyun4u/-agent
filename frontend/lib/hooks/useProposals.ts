/**
 * useProposals — 제안서 목록 훅 (페이지네이션 + 검색)
 *
 * 설계: proposal-platform-v1.design.md §10 (frontend/lib/hooks/useProposals.ts)
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ProposalSummary } from "@/lib/api";

export interface UseProposalsOptions {
  q?: string;
  status?: string;
  page?: number;
}

export interface UseProposalsResult {
  proposals: ProposalSummary[];
  page: number;
  pageSize: number;
  isLoading: boolean;
  error: Error | null;
  refresh: () => void;
}

export function useProposals(opts: UseProposalsOptions = {}): UseProposalsResult {
  const { q, status, page = 1 } = opts;

  const [proposals, setProposals] = useState<ProposalSummary[]>([]);
  const [pageSize, setPageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const cancelledRef = useRef(false);

  const fetch_ = useCallback(async () => {
    cancelledRef.current = false;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.proposals.list({ q, status, page });
      if (!cancelledRef.current) {
        setProposals(data.items);
        setPageSize(data.page_size);
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
  }, [q, status, page]);

  useEffect(() => {
    fetch_();
    return () => {
      cancelledRef.current = true;
    };
  }, [fetch_]);

  return {
    proposals,
    page,
    pageSize,
    isLoading,
    error,
    refresh: fetch_,
  };
}
