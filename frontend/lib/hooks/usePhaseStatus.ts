"use client";

/**
 * usePhaseStatus — Supabase Realtime 기반 제안서 Phase 상태 구독
 *
 * - 초기 데이터: api.proposals.status(id) HTTP 요청 (client_name 등 세션 데이터 포함)
 * - 이후 변경: Supabase Realtime postgres_changes (proposals UPDATE)
 * - 페이지 언마운트 시 채널 구독 자동 해제 (메모리 누수 방지)
 *
 * 전제 조건:
 *   proposals 테이블: ALTER TABLE proposals REPLICA IDENTITY FULL; (schema.sql 완료)
 *   Supabase Dashboard > Database > Replication > proposals 테이블 활성화 필요
 */

import { useEffect, useState } from "react";
import { api, ProposalStatus_ } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface UsePhaseStatusResult {
  status: ProposalStatus_ | null;
  loading: boolean;
}

export function usePhaseStatus(proposalId: string): UsePhaseStatusResult {
  const [status, setStatus] = useState<ProposalStatus_ | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!proposalId) return;

    let cancelled = false;

    // 1. 초기 데이터 로드 (HTTP) — client_name 등 세션 필드 포함
    api.proposals.status(proposalId)
      .then((data) => {
        if (!cancelled) {
          setStatus(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("[usePhaseStatus] 초기 로드 실패:", err);
        if (!cancelled) setLoading(false);
      });

    // 2. Realtime 구독 — proposals UPDATE 이벤트
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
            return {
              ...prev,
              status: (row.status as ProposalStatus_["status"]) ?? prev.status,
              current_phase: (row.current_phase as string) ?? prev.current_phase,
              phases_completed: (row.phases_completed as number) ?? prev.phases_completed,
              error: (row.notes as string) ?? prev.error,
            };
          });
        }
      )
      .subscribe();

    // 3. 클린업
    return () => {
      cancelled = true;
      supabase.removeChannel(channel);
    };
  }, [proposalId]);

  return { status, loading };
}
