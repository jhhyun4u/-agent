"use client";

/**
 * F4: 새 제안서 생성 페이지
 * - 공고 모니터링에서 넘어온 경우: 공고 정보 + RFP AI 요약 + 적합성 분석 + 첨부파일
 * - 공고명 편집 가능
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, BidAnalysis } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface BidPrefill {
  bid_no: string;
  rfp_title: string;
  client_name?: string;
  rfp_content?: string;
  budget_amount?: number | null;
  attachments?: { name: string; url: string; type: string }[];
}

function formatBudget(amount: number | null | undefined): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

export default function NewProposalPage() {
  const router = useRouter();

  const [bidPrefill, setBidPrefill] = useState<BidPrefill | null>(null);
  const [rfpTitle, setRfpTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // AI 분석 결과
  const [analysis, setAnalysis] = useState<BidAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("bid_prefill");
    if (stored) {
      try {
        const data = JSON.parse(stored) as BidPrefill;
        sessionStorage.removeItem("bid_prefill");
        setBidPrefill(data);
        setRfpTitle(data.rfp_title || "");

        // AI 분석 요청
        setAnalyzing(true);
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        fetch(`${baseUrl}/bids/${data.bid_no}/analysis`)
          .then((r) => r.ok ? r.json() : null)
          .then((json) => {
            if (json?.data) setAnalysis(json.data);
          })
          .catch(() => {})
          .finally(() => setAnalyzing(false));
      } catch {
        // 파싱 실패
      }
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rfpTitle.trim() || !bidPrefill) return;
    setSubmitting(true);
    setError("");

    try {
      const content = bidPrefill.rfp_content || rfpTitle;
      const blob = new Blob([content], { type: "text/plain" });
      const file = new File([blob], `${rfpTitle}.txt`, { type: "text/plain" });

      const fd = new FormData();
      fd.append("rfp_title", rfpTitle.trim());
      fd.append("client_name", bidPrefill.client_name || "");
      fd.append("rfp_file", file);

      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      const supabase = createClient();
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token ?? "";
      const res = await fetch(`${baseUrl}/proposals/from-rfp`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || "제안서 생성 실패");
      }

      const data = await res.json();
      router.push(`/proposals/${data.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제안서 생성에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  // 공고에서 넘어오지 않은 경우
  if (!bidPrefill) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
        <div className="border-b border-[#262626] px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <Link href="/proposals" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">←</Link>
            <h1 className="text-sm font-semibold text-[#ededed]">새 제안서 생성</h1>
          </div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
          <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl">📡</div>
          <h3 className="text-sm font-semibold text-[#ededed]">공고를 먼저 선택해주세요</h3>
          <p className="text-xs text-[#8c8c8c] max-w-xs">
            공고 모니터링에서 원하는 공고의 &quot;제안 착수&quot; 버튼을 눌러 제안서를 시작할 수 있습니다.
          </p>
          <Link
            href="/bids"
            className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
          >
            공고 모니터링으로 이동
          </Link>
        </div>
      </div>
    );
  }

  const attachments = bidPrefill.attachments || [];
  const fitColor: Record<string, string> = {
    "적극 추천": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
    "추천": "text-blue-400 bg-blue-950/60 border-blue-900",
    "보통": "text-yellow-400 bg-yellow-950/60 border-yellow-900",
    "낮음": "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]",
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/bids" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">←</Link>
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">새 제안서 생성</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">공고번호: {bidPrefill.bid_no}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6">
        <form onSubmit={handleSubmit} className="max-w-2xl space-y-5">

          {/* 공고명 (편집 가능) */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2">공고명</label>
            <input
              type="text"
              required
              value={rfpTitle}
              onChange={(e) => setRfpTitle(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
            />
          </div>

          {/* 공고 정보 */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[#3ecf8e] text-sm">📌</span>
              <p className="text-xs font-medium text-[#ededed]">공고 정보</p>
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-[#5c5c5c]">발주처</span>
                <p className="text-[#ededed] mt-0.5">{bidPrefill.client_name || "-"}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">용역비</span>
                <p className="text-[#ededed] mt-0.5">{formatBudget(bidPrefill.budget_amount)}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">공고번호</span>
                <p className="text-[#ededed] mt-0.5">{bidPrefill.bid_no}</p>
              </div>
            </div>
          </div>

          {/* RFP 주요내용 (AI 개조식 요약) */}
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
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-3">
                <p className="text-xs text-[#5c5c5c]">
                  공고 상세 텍스트를 가져올 수 없습니다. 첨부된 제안요청서를 직접 확인해주세요.
                </p>
              </div>
            )}
          </div>

          {/* TENOPA 적합성 분석 (Positive/Negative 2축 + 추천 팀) */}
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
                {analysis?.fit_level && (
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
              <div className="grid grid-cols-2 gap-3">
                {/* Positive */}
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
                {/* Negative */}
                <div>
                  <p className="text-[10px] font-medium text-red-400 mb-2 uppercase tracking-wider">Negative</p>
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
            )}
          </div>

          {/* 첨부파일 */}
          {attachments.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-emerald-400 text-sm">📎</span>
                <p className="text-xs font-medium text-[#ededed]">공고 첨부파일</p>
              </div>
              <div className="space-y-1.5">
                {attachments.map((att, i) => {
                  const ext = att.name.split(".").pop()?.toUpperCase() ?? "";
                  const typeColor: Record<string, string> = {
                    "제안요청서": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
                    "과업지시서": "text-blue-400 bg-blue-950/60 border-blue-900",
                    "공고문": "text-[#8c8c8c] bg-[#111111] border-[#262626]",
                    "기타": "text-[#5c5c5c] bg-[#111111] border-[#262626]",
                  };
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

          {/* 안내 */}
          <div className="bg-blue-950/30 border border-blue-900/50 rounded-lg px-4 py-3 text-xs text-blue-300">
            AI가 RFP 분석 → 전략 수립 → 제안서 작성까지 5단계를 수행합니다. 완료까지 <strong>5~15분</strong> 소요됩니다.
          </div>

          {/* 제출 */}
          <button
            type="submit"
            disabled={submitting || !rfpTitle.trim()}
            className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold rounded-lg py-2.5 text-sm transition-colors"
          >
            {submitting ? "제안서 생성 중..." : "제안서 생성 시작"}
          </button>
        </form>
      </div>
    </div>
  );
}
