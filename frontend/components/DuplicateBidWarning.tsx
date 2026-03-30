"use client";

/**
 * 권고 #4: 공고 중복 프로젝트 경고
 *
 * 같은 공고번호(bid_no)로 이미 생성된 프로젝트가 있으면 경고를 표시한다.
 * proposals/new 페이지에서 사용.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type ProposalSummary } from "@/lib/api";

interface Props {
  bidNo: string;
  rfpTitle?: string;
}

export default function DuplicateBidWarning({ bidNo, rfpTitle }: Props) {
  const [existing, setExisting] = useState<ProposalSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!bidNo) { setLoading(false); return; }

    async function check() {
      setLoading(true);
      try {
        // 제안서 목록에서 같은 제목이나 bid_no로 검색
        const res = await api.proposals.list({ page: 1, search: bidNo });
        const matches = res.data.filter(
          (p) => p.title?.includes(bidNo) || p.title === rfpTitle
        );
        setExisting(matches);
      } catch {
        setExisting([]);
      } finally {
        setLoading(false);
      }
    }

    check();
  }, [bidNo, rfpTitle]);

  if (loading || existing.length === 0) return null;

  const statusLabel: Record<string, string> = {
    initialized: "시작 전",
    processing: "진행 중",
    running: "진행 중",
    completed: "완료",
    failed: "실패",
    cancelled: "취소",
    paused: "일시정지",
  };

  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-amber-400 text-sm">!</span>
        <p className="text-xs font-semibold text-amber-400">
          이 공고로 이미 생성된 프로젝트가 있습니다
        </p>
      </div>
      <p className="text-[10px] text-[#8c8c8c] mb-3">
        같은 공고번호({bidNo})로 기존에 시작된 제안서가 {existing.length}건 있습니다.
        중복으로 생성할 경우 작업이 분산될 수 있습니다.
      </p>
      <div className="space-y-1.5">
        {existing.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-3 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2"
          >
            <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${
              p.status === "completed"
                ? "bg-[#3ecf8e]/15 text-[#3ecf8e]"
                : p.status === "processing" || p.status === "running"
                ? "bg-blue-500/15 text-blue-400"
                : "bg-[#262626] text-[#8c8c8c]"
            }`}>
              {statusLabel[p.status] ?? p.status}
            </span>
            <span className="text-xs text-[#ededed] truncate flex-1">{p.title}</span>
            <span className="text-[10px] text-[#8c8c8c]">
              {new Date(p.created_at).toLocaleDateString("ko-KR")}
            </span>
            <Link
              href={`/proposals/${p.id}`}
              className="text-[10px] text-[#3ecf8e] hover:underline shrink-0"
            >
              바로가기
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
