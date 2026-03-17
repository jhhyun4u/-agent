"use client";

/**
 * usePhaseStatus — Supabase Realtime + 폴링 fallback 기반 Phase 상태 구독
 *
 * - 초기 데이터: api.proposals.get(id) HTTP 요청
 * - 이후 변경: Supabase Realtime postgres_changes (proposals UPDATE)
 * - Realtime 미작동 대비: processing 상태일 때 5초마다 HTTP 폴링 fallback
 */

import { useEffect, useRef, useState } from "react";
import { api, ProposalStatus_ } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface UsePhaseStatusResult {
  status: ProposalStatus_ | null;
  loading: boolean;
}

const POLL_INTERVAL = 5000;

export function usePhaseStatus(proposalId: string): UsePhaseStatusResult {
  const [status, setStatus] = useState<ProposalStatus_ | null>(null);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!proposalId) return;

    let cancelled = false;

    const fetchStatus = async () => {
      try {
        const data = await api.proposals.get(proposalId);
        if (!cancelled) setStatus(data);
        return data;
      } catch (err) {
        console.error("[usePhaseStatus] 상태 조회 실패:", err);
        return null;
      }
    };

    // 1. 초기 데이터 로드
    fetchStatus().then((data) => {
      if (!cancelled) setLoading(false);

      // processing 상태면 폴링 시작
      if (data && (data.status === "processing" || data.status === "initialized" || data.status === "running")) {
        pollRef.current = setInterval(async () => {
          const updated = await fetchStatus();
          // 완료/실패 시 폴링 중단
          if (updated && updated.status !== "processing" && updated.status !== "initialized" && updated.status !== "running") {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        }, POLL_INTERVAL);
      }
    });

    // 2. Realtime 구독
    const supabase = createClient();
    const channel = supabase
      .channel(`proposal-status-${proposalId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "proposals",
          filter: `id=eq.${proposalId}`,
        },
        (payload) => {
          if (cancelled) return;
          const row = payload.new as Record<string, unknown>;
          setStatus((prev) => {
            if (!prev) return prev;
            const updated = {
              ...prev,
              status: (row.status as ProposalStatus_["status"]) ?? prev.status,
              current_phase: (row.current_phase as string) ?? prev.current_phase,
              phases_completed: (row.phases_completed as number) ?? prev.phases_completed,
              error: (row.notes as string) ?? prev.error,
            };
            // Realtime으로 완료/실패 수신 시 폴링 중단
            if (updated.status !== "processing" && updated.status !== "initialized" && updated.status !== "running") {
              if (pollRef.current) clearInterval(pollRef.current);
            }
            return updated;
          });
        }
      )
      .subscribe();

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
      supabase.removeChannel(channel);
    };
  }, [proposalId]);

  return { status, loading };
}
