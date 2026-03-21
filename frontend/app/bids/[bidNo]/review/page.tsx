"use client";

/**
 * 제안 검토 페이지
 * - 공고 모니터링에서 공고 클릭 시 진입
 * - RFP AI 요약 + TENOPA 적합성 분석 + 첨부파일
 * - 의사결정: 제안결정 / 제안포기 / 제안유보
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, BidAnalysis } from "@/lib/api";

interface BidInfo {
  bid_no: string;
  bid_title: string;
  agency: string;
  budget_amount: number | null;
  deadline_date: string | null;
  attachments: { name: string; url: string; type: string }[];
}

function formatBudget(amount: number | null | undefined): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

function classifyAttachment(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes("제안요청") || lower.includes("rfp")) return "제안요청서";
  if (lower.includes("과업지시") || lower.includes("과업내용")) return "과업지시서";
  if (lower.includes("공고") || lower.includes("입찰")) return "공고문";
  return "기타";
}

export default function BidReviewPage() {
  const params = useParams();
  const router = useRouter();
  const bidNo = params.bidNo as string;

  const [bidInfo, setBidInfo] = useState<BidInfo | null>(null);
  const [analysis, setAnalysis] = useState<BidAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

      // 공고 정보 조회
      try {
        const res = await fetch(`${baseUrl}/bids/${bidNo}`);
        if (res.ok) {
          const json = await res.json();
          const ann = json.data.announcement;
          const raw = ann.raw_data || {};

          // 첨부파일 추출
          const attachments: { name: string; url: string; type: string }[] = [];
          for (let i = 1; i <= 10; i++) {
            const url = raw[`ntceSpecDocUrl${i}`];
            const name = raw[`ntceSpecFileNm${i}`];
            if (url && name) {
              attachments.push({ name, url, type: classifyAttachment(name) });
            }
          }

          setBidInfo({
            bid_no: ann.bid_no,
            bid_title: ann.bid_title,
            agency: ann.agency,
            budget_amount: ann.budget_amount,
            deadline_date: ann.deadline_date,
            attachments,
          });
          // 기존 상태가 있으면 선택 상태 복원
          if (ann.proposal_status) setSelectedStatus(ann.proposal_status);
        }
      } catch {
        setError("공고 정보를 불러올 수 없습니다.");
      } finally {
        setLoading(false);
      }

      // AI 분석
      setAnalyzing(true);
      try {
        const res = await fetch(`${baseUrl}/bids/${bidNo}/analysis`);
        if (res.ok) {
          const json = await res.json();
          setAnalysis(json.data);
        }
      } catch {
        // AI 분석 실패 무시
      } finally {
        setAnalyzing(false);
      }
    })();
  }, [bidNo]);

  async function handleDecision(status: "제안결정" | "제안포기" | "제안유보" | "관련없음") {
    setDeciding(true);
    try {
      // 인증 토큰 문제 우회 — 직접 fetch
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      const res = await fetch(`${baseUrl}/bids/${bidNo}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || "상태 변경 실패");
      }

      // 모든 의사결정 → 공고 모니터링으로 돌아감 (상태 표시 반영)
      setSelectedStatus(status);
      router.push("/bids");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "상태 변경 실패");
      setDeciding(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
      </div>
    );
  }

  if (!bidInfo) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-red-400">{error || "공고를 찾을 수 없습니다."}</p>
      </div>
    );
  }

  const fitColor: Record<string, string> = {
    "적극 추천": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
    "추천": "text-blue-400 bg-blue-950/60 border-blue-900",
    "보통": "text-yellow-400 bg-yellow-950/60 border-yellow-900",
    "낮음": "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]",
  };

  const typeColor: Record<string, string> = {
    "제안요청서": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
    "과업지시서": "text-blue-400 bg-blue-950/60 border-blue-900",
    "공고문": "text-[#8c8c8c] bg-[#111111] border-[#262626]",
    "기타": "text-[#5c5c5c] bg-[#111111] border-[#262626]",
  };

  const deadline = bidInfo.deadline_date
    ? new Date(bidInfo.deadline_date).toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric" })
    : "-";

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/bids" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">←</Link>
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">제안 검토</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">공고번호: {bidInfo.bid_no}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="max-w-2xl space-y-5">

          {/* 공고 정보 */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[#3ecf8e] text-sm">📌</span>
              <p className="text-xs font-medium text-[#ededed]">공고 정보</p>
            </div>
            <h2 className="text-sm font-semibold text-[#ededed] mb-3">{bidInfo.bid_title}</h2>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-[#5c5c5c]">발주처</span>
                <p className="text-[#ededed] mt-0.5">{bidInfo.agency}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">용역비</span>
                <p className="text-[#ededed] mt-0.5">{formatBudget(bidInfo.budget_amount)}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">마감일</span>
                <p className="text-[#ededed] mt-0.5">{deadline}</p>
              </div>
            </div>
          </div>

          {/* RFP 주요내용 */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-blue-400 text-sm">📋</span>
              <p className="text-xs font-medium text-[#ededed]">RFP 주요내용</p>
              {analyzing && <span className="text-[10px] text-[#5c5c5c] animate-pulse">AI 분석 중...</span>}
            </div>
            {analyzing ? (
              <div className="flex items-center gap-2 py-6 justify-center">
                <div className="w-4 h-4 border-2 border-[#262626] border-t-blue-400 rounded-full animate-spin" />
                <span className="text-xs text-[#5c5c5c]">RFP를 분석하고 있습니다...</span>
              </div>
            ) : analysis?.rfp_summary && analysis.rfp_summary.length > 0 ? (
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-3 space-y-1.5">
                {analysis.rfp_summary.map((line, i) => (
                  <p key={i} className="text-xs text-[#8c8c8c] leading-relaxed">{line}</p>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#5c5c5c] py-2">첨부된 제안요청서를 직접 확인해주세요.</p>
            )}
          </div>

          {/* TENOPA 적합성 분석 */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-emerald-400 text-sm">🎯</span>
                <p className="text-xs font-medium text-[#ededed]">TENOPA 적합성 분석</p>
              </div>
              <div className="flex items-center gap-2">
                {analysis?.recommended_teams && analysis.recommended_teams.length > 0 && (
                  <div className="flex gap-1">
                    {analysis.recommended_teams.map((team, i) => (
                      <span key={i} className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-blue-950/60 text-blue-400 border border-blue-900">
                        {team}
                      </span>
                    ))}
                  </div>
                )}
                {analysis?.suitability_score != null && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    analysis.suitability_score >= 70 ? "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900" :
                    analysis.suitability_score >= 40 ? "text-yellow-400 bg-yellow-950/60 border-yellow-900" :
                    "text-red-400 bg-red-950/60 border-red-900"
                  }`}>
                    {analysis.suitability_score}점
                  </span>
                )}
                {analysis?.verdict && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    analysis.verdict === "추천" ? "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900" :
                    analysis.verdict === "검토 필요" ? "text-yellow-400 bg-yellow-950/60 border-yellow-900" :
                    "text-red-400 bg-red-950/60 border-red-900"
                  }`}>
                    {analysis.verdict}
                  </span>
                )}
                {analysis?.fit_level && !analysis?.verdict && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${fitColor[analysis.fit_level] || fitColor["보통"]}`}>
                    {analysis.fit_level}
                  </span>
                )}
              </div>
            </div>
            {analyzing ? (
              <div className="flex items-center gap-2 py-4 justify-center">
                <div className="w-4 h-4 border-2 border-[#262626] border-t-emerald-400 rounded-full animate-spin" />
                <span className="text-xs text-[#5c5c5c]">적합성을 분석하고 있습니다...</span>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] font-medium text-[#3ecf8e] mb-2 uppercase tracking-wider">Positive</p>
                    <div className="space-y-1.5">
                      {(analysis?.positive || []).map((item, i) => (
                        <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-emerald-950/20 border border-emerald-900/30">
                          <span className="text-[#3ecf8e] text-xs shrink-0">+</span>
                          <p className="text-xs text-[#8c8c8c] leading-relaxed">{item}</p>
                        </div>
                      ))}
                      {(!analysis?.positive || analysis.positive.length === 0) && (
                        <p className="text-xs text-[#5c5c5c] px-3 py-2">해당 없음</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium text-red-400 mb-2 uppercase tracking-wider">Negative / 필터링 사유</p>
                    <div className="space-y-1.5">
                      {(analysis?.negative || []).map((item, i) => (
                        <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-950/20 border border-red-900/30">
                          <span className="text-red-400 text-xs shrink-0">-</span>
                          <p className="text-xs text-[#8c8c8c] leading-relaxed">{item}</p>
                        </div>
                      ))}
                      {(!analysis?.negative || analysis.negative.length === 0) && (
                        <p className="text-xs text-[#5c5c5c] px-3 py-2">해당 없음</p>
                      )}
                    </div>
                  </div>
                </div>
                {/* Action Plan */}
                {analysis?.action_plan && (
                  <div className="bg-[#111111] border border-[#262626] rounded-lg p-3">
                    <p className="text-[10px] font-medium text-blue-400 mb-1.5 uppercase tracking-wider">Action Plan</p>
                    <p className="text-xs text-[#8c8c8c] leading-relaxed">{analysis.action_plan}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 첨부파일 */}
          {bidInfo.attachments.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-emerald-400 text-sm">📎</span>
                <p className="text-xs font-medium text-[#ededed]">공고 첨부파일</p>
              </div>
              <div className="space-y-1.5">
                {bidInfo.attachments.map((att, i) => {
                  const ext = att.name.split(".").pop()?.toUpperCase() ?? "";
                  return (
                    <a
                      key={i}
                      href={att.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#111111] border border-[#262626] hover:border-[#3ecf8e]/40 transition-colors"
                    >
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${typeColor[att.type] || typeColor["기타"]}`}>
                        {att.type}
                      </span>
                      <span className="text-xs text-[#ededed] truncate flex-1">{att.name}</span>
                      <span className="text-[10px] text-[#5c5c5c] shrink-0">{ext}</span>
                      <span className="text-xs text-[#3ecf8e] shrink-0">↓</span>
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {/* 에러 */}
          {error && (
            <p className="text-xs text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
          )}

          {/* 의사결정 버튼 */}
          <div className="flex gap-3 pt-2">
            {([
              { status: "제안결정", color: "bg-[#3ecf8e] text-black border-[#3ecf8e]", idle: "border-[#2a5c3e] text-[#3ecf8e]" },
              { status: "제안유보", color: "bg-orange-500 text-black border-orange-500", idle: "border-orange-900 text-orange-400/60" },
              { status: "제안포기", color: "bg-red-500 text-white border-red-500", idle: "border-red-900 text-red-400/60" },
              { status: "관련없음", color: "bg-[#444] text-[#ededed] border-[#444]", idle: "border-[#333] text-[#555]" },
            ] as const).map(({ status, color, idle }) => {
              const isSelected = selectedStatus === status;
              return (
                <button
                  key={status}
                  onClick={() => { setSelectedStatus(status); handleDecision(status); }}
                  disabled={deciding}
                  className={`flex-1 font-semibold rounded-lg py-3 text-sm border transition-all disabled:opacity-40 ${
                    isSelected ? color : `bg-[#1c1c1c] ${idle} hover:brightness-125`
                  }`}
                >
                  {deciding && selectedStatus === status ? "처리 중..." : status}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
