"use client";

/**
 * F4: 새 제안서 생성 페이지
 *
 * 2가지 진입 경로:
 *  A. 공고 모니터링에서 선택 (bid_prefill via sessionStorage)
 *  B. RFP 파일 직접 업로드 (from-rfp API)
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, BidAnalysis } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import DuplicateBidWarning from "@/components/DuplicateBidWarning";

// ── 타입 ──

type EntryPath = "select" | "monitor" | "rfp_upload";

interface BidPrefill {
  bid_no: string;
  rfp_title: string;
  client_name?: string;
  rfp_content?: string;
  budget_amount?: number | null;
  attachments?: { name: string; url: string; type: string }[];
}

// ── 유틸 ──

function formatBudget(amount: number | null | undefined): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

async function getAuthToken(): Promise<string> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? "";
}

// ── 메인 ──

export default function NewProposalPage() {
  const router = useRouter();

  // 진입 경로 선택
  const [entryPath, setEntryPath] = useState<EntryPath>("select");

  // 공통
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Path A: 공고 모니터링 prefill
  const [bidPrefill, setBidPrefill] = useState<BidPrefill | null>(null);
  const [rfpTitle, setRfpTitle] = useState("");
  const [analysis, setAnalysis] = useState<BidAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Path B: RFP 파일 업로드
  const [rfpFile, setRfpFile] = useState<File | null>(null);
  const [rfpUploadTitle, setRfpUploadTitle] = useState("");
  const [rfpClientName, setRfpClientName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // ── sessionStorage에서 bid_prefill 체크 ──
  useEffect(() => {
    const stored = sessionStorage.getItem("bid_prefill");
    if (!stored) return;
    try {
      const data = JSON.parse(stored) as BidPrefill;
      sessionStorage.removeItem("bid_prefill");
      setBidPrefill(data);
      setRfpTitle(data.rfp_title || "");
      setEntryPath("monitor");

      // AI 분석 요청
      setAnalyzing(true);
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      fetch(`${baseUrl}/bids/${data.bid_no}/analysis`)
        .then((r) => (r.ok ? r.json() : null))
        .then((json) => {
          if (json?.data) setAnalysis(json.data);
        })
        .catch(() => {})
        .finally(() => setAnalyzing(false));
    } catch {
      // 파싱 실패 무시
    }
  }, []);

  // ── 제출 핸들러 ──

  async function submitFromMonitor(e: React.FormEvent) {
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
      const token = await getAuthToken();
      const res = await fetch(`${baseUrl}/proposals/from-rfp`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "제안서 생성 실패");
      }
      const data = await res.json();
      router.push(`/proposals/${data.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제안서 생성에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  async function submitFromRfpUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!rfpFile) return;
    setSubmitting(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("rfp_file", rfpFile);
      fd.append("rfp_title", rfpUploadTitle.trim() || rfpFile.name.replace(/\.[^.]+$/, ""));
      fd.append("client_name", rfpClientName.trim());
      const data = await api.proposals.createFromRfp(fd);
      router.push(`/proposals/${data.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제안서 생성 실패");
    } finally {
      setSubmitting(false);
    }
  }

  // ── 공통 UI 요소 ──

  const header = (
    <div className="border-b border-[#262626] px-6 py-4 shrink-0">
      <div className="flex items-center gap-3">
        {entryPath === "select" || entryPath === "monitor" ? (
          <Link href="/proposals" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
            &larr;
          </Link>
        ) : (
          <button
            onClick={() => { setEntryPath("select"); setError(""); }}
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
          >
            &larr;
          </button>
        )}
        <div>
          <h1 className="text-sm font-semibold text-[#ededed]">새 제안서 생성</h1>
          {entryPath !== "select" && (
            <p className="text-xs text-[#5c5c5c] mt-0.5">
              {entryPath === "monitor" && `공고번호: ${bidPrefill?.bid_no}`}
              {entryPath === "rfp_upload" && "RFP 파일로 시작"}
            </p>
          )}
        </div>
      </div>
    </div>
  );

  const errorBanner = error && (
    <p className="text-xs text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
  );

  const infoBanner = (
    <div className="bg-blue-950/30 border border-blue-900/50 rounded-lg px-4 py-3 text-xs text-blue-300">
      AI가 RFP 분석 &rarr; 전략 수립 &rarr; 제안서 작성까지 5단계를 수행합니다.
      각 단계마다 검토/수정할 수 있습니다.
    </div>
  );

  // ══════════════════════════════════════
  //  진입 경로 선택 화면
  // ══════════════════════════════════════

  if (entryPath === "select") {
    return (
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
        {header}
        <div className="flex-1 overflow-auto px-6 py-8">
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center space-y-2 mb-8">
              <h2 className="text-base font-semibold text-[#ededed]">어떤 방법으로 시작하시겠습니까?</h2>
              <p className="text-xs text-[#8c8c8c]">제안서 작성 방식을 선택하세요. 이후 AI가 단계별로 안내합니다.</p>
            </div>

            <div className="grid gap-4">
              {/* A. 공고 모니터링 */}
              <Link
                href="/monitoring"
                className="group flex items-start gap-4 p-5 bg-[#1c1c1c] border border-[#262626] rounded-xl hover:border-[#3ecf8e]/50 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-emerald-950/60 border border-emerald-900 flex items-center justify-center text-lg shrink-0 group-hover:bg-emerald-950/80 transition-colors">
                  A
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[#ededed] group-hover:text-[#3ecf8e] transition-colors">
                    공고 모니터링에서 선택
                  </p>
                  <p className="text-xs text-[#8c8c8c] mt-1 leading-relaxed">
                    G2B 공고 목록에서 관심 과제를 검토하고 &ldquo;제안 착수&rdquo;로 시작합니다.
                    AI 적합성 분석과 RFP 요약이 자동으로 제공됩니다.
                  </p>
                  <div className="flex gap-2 mt-2.5">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-[#3ecf8e] border border-emerald-900/50">
                      AI 적합성 분석
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/40 text-[#3ecf8e] border border-emerald-900/50">
                      첨부파일 자동 수집
                    </span>
                  </div>
                </div>
                <span className="text-[#5c5c5c] group-hover:text-[#3ecf8e] text-sm shrink-0 transition-colors">&rarr;</span>
              </Link>

              {/* B. RFP 파일 업로드 */}
              <button
                onClick={() => { setEntryPath("rfp_upload"); setError(""); }}
                className="group flex items-start gap-4 p-5 bg-[#1c1c1c] border border-[#262626] rounded-xl hover:border-purple-500/50 transition-all text-left"
              >
                <div className="w-10 h-10 rounded-lg bg-purple-950/60 border border-purple-900 flex items-center justify-center text-lg shrink-0 group-hover:bg-purple-950/80 transition-colors">
                  B
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[#ededed] group-hover:text-purple-400 transition-colors">
                    RFP 파일 직접 업로드
                  </p>
                  <p className="text-xs text-[#8c8c8c] mt-1 leading-relaxed">
                    제안요청서(RFP) 파일을 직접 업로드하여 시작합니다.
                    PDF, HWP, HWPX, TXT 형식을 지원합니다.
                  </p>
                  <div className="flex gap-2 mt-2.5">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950/40 text-purple-400 border border-purple-900/50">
                      PDF / HWP / HWPX
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950/40 text-purple-400 border border-purple-900/50">
                      자체 RFP 활용
                    </span>
                  </div>
                </div>
                <span className="text-[#5c5c5c] group-hover:text-purple-400 text-sm shrink-0 transition-colors">&rarr;</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ══════════════════════════════════════
  //  Path A: 공고 모니터링에서 진입
  // ══════════════════════════════════════

  if (entryPath === "monitor" && bidPrefill) {
    const attachments = bidPrefill.attachments || [];
    const fitColor: Record<string, string> = {
      "적극 추천": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
      "추천": "text-blue-400 bg-blue-950/60 border-blue-900",
      "보통": "text-yellow-400 bg-yellow-950/60 border-yellow-900",
      "낮음": "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]",
    };

    return (
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
        {header}
        <div className="flex-1 overflow-auto px-6 py-6">
          <form onSubmit={submitFromMonitor} className="max-w-2xl space-y-5">
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
                <span className="text-[#3ecf8e] text-sm">{"///"}</span>
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

            {/* RFP 주요내용 */}
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-blue-400 text-sm">{"[ ]"}</span>
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

            {/* 적합성 분석 */}
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400 text-sm">{"(*)"}</span>
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
                  <span className="text-emerald-400 text-sm">{"{+}"}</span>
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
                      </a>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 권고 #4: 공고 중복 프로젝트 경고 */}
            <DuplicateBidWarning bidNo={bidPrefill.bid_no} rfpTitle={rfpTitle} />

            {errorBanner}
            {infoBanner}

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

  // ══════════════════════════════════════
  //  Path B: RFP 파일 직접 업로드
  // ══════════════════════════════════════

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {header}
      <div className="flex-1 overflow-auto px-6 py-6">
        <form onSubmit={submitFromRfpUpload} className="max-w-2xl space-y-5">
          {/* 파일 업로드 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2">RFP 파일</label>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.hwp,.hwpx,.txt,.doc,.docx"
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setRfpFile(f);
                if (f && !rfpUploadTitle) {
                  setRfpUploadTitle(f.name.replace(/\.[^.]+$/, ""));
                }
              }}
              className="hidden"
            />
            {rfpFile ? (
              <div className="flex items-center gap-3 p-3 bg-[#1c1c1c] border border-purple-900/50 rounded-lg">
                <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-900 flex items-center justify-center text-xs text-purple-400 shrink-0">
                  {rfpFile.name.split(".").pop()?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-[#ededed] truncate">{rfpFile.name}</p>
                  <p className="text-[10px] text-[#5c5c5c]">{(rfpFile.size / 1024).toFixed(0)} KB</p>
                </div>
                <button
                  type="button"
                  onClick={() => { setRfpFile(null); if (fileRef.current) fileRef.current.value = ""; }}
                  className="text-[#5c5c5c] hover:text-red-400 text-xs transition-colors"
                >
                  x
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="w-full flex flex-col items-center justify-center gap-2 py-8 bg-[#1c1c1c] border-2 border-dashed border-[#333] rounded-xl hover:border-purple-500/50 transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-purple-950/40 border border-purple-900/50 flex items-center justify-center text-lg text-purple-400">
                  +
                </div>
                <p className="text-xs text-[#8c8c8c]">클릭하여 파일을 선택하세요</p>
                <p className="text-[10px] text-[#5c5c5c]">PDF, HWP, HWPX, TXT, DOC, DOCX</p>
              </button>
            )}
          </div>

          {/* 프로젝트명 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2">프로젝트명</label>
            <input
              type="text"
              value={rfpUploadTitle}
              onChange={(e) => setRfpUploadTitle(e.target.value)}
              placeholder="파일명에서 자동 추출됩니다"
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2.5 text-sm text-[#ededed] placeholder:text-[#3a3a3a] focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-colors"
            />
          </div>

          {/* 발주처 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2">
              발주처 <span className="text-[#5c5c5c] font-normal">(선택)</span>
            </label>
            <input
              type="text"
              value={rfpClientName}
              onChange={(e) => setRfpClientName(e.target.value)}
              placeholder="발주 기관명"
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2.5 text-sm text-[#ededed] placeholder:text-[#3a3a3a] focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-colors"
            />
          </div>

          {errorBanner}
          {infoBanner}

          <button
            type="submit"
            disabled={submitting || !rfpFile}
            className="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
          >
            {submitting ? "제안서 생성 중..." : "RFP 분석 및 제안서 시작"}
          </button>
        </form>
      </div>
    </div>
  );
}
