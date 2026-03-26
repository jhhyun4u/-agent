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
import { createClient } from "@/lib/supabase/client";

async function getToken(): Promise<string> {
  if (process.env.NODE_ENV === "development") return "";
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? "";
}

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
  const [analysis, setAnalysis] = useState<BidAnalysis | null>(() => {
    // sessionStorage에서 캐시된 분석 결과 복원 (유효한 AI 분석만)
    try {
      const cached = typeof window !== "undefined" ? sessionStorage.getItem(`bid_analysis_${bidNo}`) : null;
      if (!cached) return null;
      const parsed = JSON.parse(cached);
      // suitability_score가 없거나 0이면 fallback 결과 → 무효 캐시
      if (!parsed.suitability_score || parsed.suitability_score <= 0) return null;
      return parsed;
    } catch { return null; }
  });
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [analysisFailed, setAnalysisFailed] = useState(false);

  // 분석 결과를 sessionStorage에 캐싱하는 래퍼
  function setAnalysisWithCache(data: BidAnalysis | null) {
    setAnalysis(data);
    if (data) {
      try { sessionStorage.setItem(`bid_analysis_${bidNo}`, JSON.stringify(data)); } catch { /* quota exceeded 무시 */ }
    }
  }

  useEffect(() => {
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let cancelled = false;

    (async () => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      console.log("[review] baseUrl:", baseUrl, "bidNo:", bidNo);
      let loaded = false;

      // 인증 토큰 (실패해도 계속 진행)
      let token = "";
      try { token = await getToken(); } catch (e) { console.warn("[review] getToken 실패:", e); }
      const authHeaders: Record<string, string> = {};
      if (token) authHeaders["Authorization"] = `Bearer ${token}`;

     try {  // ← 최상위 try: 어떤 에러든 loading/analyzing 상태 복구 보장

      // 1) sessionStorage 데이터 우선 (scored 또는 monitor에서 전달)
      try {
        const storedScored = sessionStorage.getItem(`bid_scored_${bidNo}`);
        const storedMonitor = sessionStorage.getItem(`bid_monitor_${bidNo}`);
        const stored = storedScored || storedMonitor;
        if (stored) {
          const parsed = JSON.parse(stored);
          setBidInfo({
            bid_no: parsed.bid_no || bidNo,
            bid_title: parsed.title || "",
            agency: parsed.agency || "",
            budget_amount: parsed.budget ?? null,
            deadline_date: parsed.deadline || null,
            attachments: [],
          });
          loaded = true;
        }
      } catch { /* 파싱 실패 무시 */ }

      // 2) DB에서 공고 상세 조회 (10초 타임아웃)
      try {
        console.log("[review] Step 2: fetching /bids/" + bidNo);
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        const res = await fetch(`${baseUrl}/bids/${bidNo}`, {
          signal: controller.signal,
          headers: authHeaders,
        });
        clearTimeout(timeout);
        console.log("[review] Step 2 response:", res.status);
        if (res.ok) {
          const json = await res.json();
          const ann = json.data.announcement;
          const raw = ann.raw_data || {};

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
          if (ann.proposal_status) setSelectedStatus(ann.proposal_status);
          loaded = true;
        }
      } catch {
        // DB 조회 실패/타임아웃
      }

      // 3) DB 실패 + sessionStorage도 없으면 → monitor API에서 검색
      if (!loaded) {
        try {
          const controller = new AbortController();
          const timeout = setTimeout(() => controller.abort(), 10000);
          const res = await fetch(`${baseUrl}/bids/monitor?scope=company&page=1&show_all=true`, {
            signal: controller.signal,
            headers: authHeaders,
          });
          clearTimeout(timeout);
          if (res.ok) {
            const json = await res.json();
            const found = (json.data || []).find((b: { bid_no: string }) => b.bid_no === bidNo);
            if (found) {
              setBidInfo({
                bid_no: found.bid_no,
                bid_title: found.bid_title,
                agency: found.agency,
                budget_amount: found.budget_amount,
                deadline_date: found.deadline_date,
                attachments: (found.attachments || []).map((a: { name: string; url: string }) => ({
                  name: a.name, url: a.url, type: classifyAttachment(a.name),
                })),
              });
              if (found.proposal_status) setSelectedStatus(found.proposal_status);
              loaded = true;
            }
          }
        } catch { /* monitor API도 실패 */ }
      }

      if (!loaded) {
        setError("공고 정보를 불러올 수 없습니다.");
      }
      setLoading(false);

      // 캐시된 분석이 있으면 API 스킵
      if (!cancelled && analysis) {
        return;
      }

      // AI 분석 (별도, 60초 타임아웃 — 통합 단일 Claude 호출 45s + 마진)
      setAnalyzing(true);
      let analysisLoaded = false;
      try {
        console.log("[review] Step 4: fetching /bids/" + bidNo + "/analysis");
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60000);
        const res = await fetch(`${baseUrl}/bids/${bidNo}/analysis`, {
          signal: controller.signal,
          headers: authHeaders,
        });
        clearTimeout(timeout);
        console.log("[review] Step 4 response:", res.status);
        if (res.ok && !cancelled) {
          const json = await res.json();
          console.log("[review] analysis data:", JSON.stringify(json.data).substring(0, 100));
          setAnalysisWithCache(json.data);
          analysisLoaded = true;
        } else {
          console.warn(`AI 분석 실패: ${res.status}`);
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") {
          console.warn("AI 분석 타임아웃 (60초 초과)");
        } else {
          console.warn("AI 분석 오류:", e);
        }
      }

      // analysis API 실패 시 → scored/bidInfo 기반 간이 분석 생성
      if (!analysisLoaded && !cancelled) {
        setAnalysisFailed(true);
      }
      if (!analysisLoaded) {
        // scored 데이터 시도
        let score = 0;
        let classLarge = "";
        let classSmall = "";
        let roleKw: string[] = [];
        let domainKw: string[] = [];
        try {
          const storedScored = sessionStorage.getItem(`bid_scored_${bidNo}`);
          if (storedScored) {
            const scored = JSON.parse(storedScored);
            score = scored.score ?? 0;
            classLarge = scored.classification_large || "";
            classSmall = scored.classification || "";
            roleKw = scored.role_keywords || [];
            domainKw = scored.domain_keywords || [];
          }
        } catch { /* 무시 */ }

        const fitLevel = score >= 100 ? "적극 추천" : score >= 70 ? "추천" : score >= 40 ? "보통" : "낮음";
        const verdict = score >= 70 ? "추천" : score >= 40 ? "검토 필요" : "제외";
        const positive: string[] = [];
        const negative: string[] = [];
        if (roleKw.length) positive.push(`관련 역할: ${roleKw.join(", ")}`);
        if (domainKw.length) positive.push(`관련 분야: ${domainKw.join(", ")}`);
        if (classSmall) positive.push(`분류: ${classSmall}`);
        if (positive.length === 0) positive.push("공고 기본 정보만 확인 가능합니다");
        if (score > 0 && score < 50) negative.push("AI 적합성 점수가 낮습니다");

        const rfpLines: string[] = [];
        if (score > 0) rfpLines.push(`AI 추천 점수: ${score}점`);
        if (classLarge || classSmall) rfpLines.push(`분류: ${classLarge}${classLarge && classSmall ? " > " : ""}${classSmall}`);
        if (rfpLines.length === 0) rfpLines.push("상세 AI 분석은 공고 모니터링에 등록 후 이용 가능합니다");

        if (!cancelled) {
          setAnalysisWithCache({
            rfp_summary: rfpLines,
            fit_level: fitLevel as "적극 추천" | "추천" | "보통" | "낮음",
            positive,
            negative,
            recommended_teams: [],
            suitability_score: score > 0 ? score : undefined,
            verdict: score > 0 ? (verdict as "추천" | "검토 필요" | "제외") : undefined,
            action_plan: "상세 AI 분석을 위해 공고 모니터링에 등록 후 다시 검토해주세요.",
          });
        }
      }

      // 파이프라인 진행 중이면 폴링 (최대 24회 = 2분)
      const MAX_POLL = 24;
      if (!analysisLoaded && !cancelled) {
        try {
          const pRes = await fetch(`${baseUrl}/bids/pipeline/status?bid_no=${bidNo}`, { signal: AbortSignal.timeout(5000) });
          if (pRes.ok) {
            const pData = await pRes.json();
            const pStatus = pData.data?.[bidNo];
            if (pStatus && pStatus.step !== "done" && !pStatus.error) {
              let pollCount = 0;
              pollTimer = setInterval(async () => {
                pollCount++;
                if (cancelled || pollCount > MAX_POLL) {
                  if (pollTimer) clearInterval(pollTimer);
                  pollTimer = null;
                  if (!cancelled) {
                    console.warn(`폴링 ${pollCount > MAX_POLL ? "최대 횟수 초과" : "취소"}`);
                    setAnalyzing(false);
                  }
                  return;
                }
                try {
                  const r = await fetch(`${baseUrl}/bids/pipeline/status?bid_no=${bidNo}`, { signal: AbortSignal.timeout(5000) });
                  if (r.ok) {
                    const p = await r.json();
                    const s = p.data?.[bidNo];
                    if (!s || s.step === "done" || s.error) {
                      if (pollTimer) clearInterval(pollTimer);
                      pollTimer = null;
                      if (cancelled) return;
                      if (!s?.error) {
                        try {
                          const aRes = await fetch(`${baseUrl}/bids/${bidNo}/analysis`, { signal: AbortSignal.timeout(30000) });
                          if (aRes.ok) setAnalysisWithCache((await aRes.json()).data);
                        } catch { /* 재조회 실패 무시 */ }
                      }
                      setAnalyzing(false);
                    }
                  }
                } catch { /* 폴링 단건 실패 무시 — 다음 폴링에서 재시도 */ }
              }, 5000);
              return; // analyzing 상태 유지
            }
          }
        } catch { /* status API 실패 무시 */ }
      }

      if (!cancelled) setAnalyzing(false);

     } catch (e) {
       // 최상위 에러 핸들러: 어떤 에러든 UI 상태 복구
       console.error("[review] 치명적 오류:", e);
       if (!cancelled) {
         setLoading(false);
         setAnalyzing(false);
         setError("분석 중 오류가 발생했습니다. 페이지를 새로고침해주세요.");
       }
     }
    })();

    return () => {
      cancelled = true;
      if (pollTimer) clearInterval(pollTimer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bidNo]);

  async function handleDecision(status: "제안결정" | "제안포기" | "제안유보" | "관련없음") {
    setDeciding(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      const tk = await getToken();

      // 1) 공고 상태 변경
      const res = await fetch(`${baseUrl}/bids/${bidNo}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${tk}`,
        },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.message || "상태 변경 실패");
      }

      setSelectedStatus(status);

      // 2) "제안결정" → 제안 프로젝트 생성 + 제안서 목록으로 이동
      if (status === "제안결정") {
        const createRes = await fetch(`${baseUrl}/proposals/from-bid`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${tk}`,
          },
          body: JSON.stringify({ bid_no: bidNo }),
        });
        if (createRes.ok) {
          router.push("/proposals");
        } else {
          // 프로젝트 생성 실패해도 상태 변경은 완료 → 목록으로 이동
          console.warn("제안 프로젝트 생성 실패:", createRes.status);
          router.push("/proposals");
        }
      } else {
        // 제안포기/제안유보/관련없음 → 공고 모니터링으로 돌아감
        router.push("/monitoring");
      }
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
          <Link href="/monitoring" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">←</Link>
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
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[#5c5c5c]">발주처</span>
                <p className="text-[#ededed] mt-0.5">{bidInfo.agency}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">용역비</span>
                <p className="text-[#ededed] mt-0.5">{formatBudget(bidInfo.budget_amount)}</p>
              </div>
              <div>
                <span className="text-[#5c5c5c]">사업기간</span>
                <p className="text-[#ededed] mt-0.5">
                  {analyzing ? <span className="text-[#5c5c5c] animate-pulse">분석 중</span> : (analysis?.rfp_period || "-")}
                </p>
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
            ) : analysis?.rfp_sections && analysis.rfp_sections.length > 0 ? (
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-3 space-y-2.5">
                {analysis.rfp_sections.map((sec, i) => (
                  <div key={i}>
                    <p className="text-[10px] font-semibold text-[#ededed] mb-1 flex items-center gap-1.5">
                      <span className="text-blue-400">○</span>
                      {sec.label}
                      {sec.value && <span className="font-normal text-[#8c8c8c] ml-1">— {sec.value}</span>}
                    </p>
                    {sec.items && sec.items.length > 0 && (
                      <div className="ml-4 space-y-0.5">
                        {sec.items.map((item, j) => (
                          <p key={j} className="text-xs text-[#8c8c8c] leading-relaxed flex items-start gap-1.5">
                            <span className="text-[#5c5c5c] shrink-0">-</span>
                            {item}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : analysis?.rfp_summary && analysis.rfp_summary.length > 0 ? (
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-3 space-y-1">
                {analysis.rfp_summary.map((line, i) => {
                    const isTask = line.startsWith("과업:");
                    const isPurpose = line.startsWith("목적:");
                    const text = line.replace(/^(목적|과업):\s*/, "");
                    return (
                      <p key={i} className={`text-xs text-[#8c8c8c] leading-relaxed flex items-start gap-1.5 ${isTask ? "ml-4" : ""}`}>
                        <span className={`shrink-0 ${isPurpose || (!isTask && i === 0) ? "text-blue-400" : "text-[#5c5c5c]"}`}>
                          {isTask ? "-" : "○"}
                        </span>
                        {isPurpose && <span className="font-semibold text-[#ededed] mr-1">주요 과업</span>}
                        {isPurpose ? text : line}
                      </p>
                    );
                  })}
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
                {/* Action Plan — 개조식 리스트 */}
                {analysis?.action_plan && (
                  <div className="bg-[#111111] border border-[#262626] rounded-lg p-3">
                    <p className="text-[10px] font-medium text-blue-400 mb-2 uppercase tracking-wider">Action Plan</p>
                    <div className="space-y-1">
                      {analysis.action_plan
                        .split(/[.;,]\s*|\n/)
                        .map((s) => s.trim())
                        .filter((s) => s.length > 0)
                        .map((item, i) => (
                          <p key={i} className="text-xs text-[#8c8c8c] leading-relaxed flex items-start gap-1.5">
                            <span className="text-blue-400 shrink-0">-</span>
                            {item}
                          </p>
                        ))}
                    </div>
                  </div>
                )}
                {/* 분석 실패 시 재분석 버튼 */}
                {analysisFailed && !analyzing && (
                  <button
                    onClick={() => {
                      sessionStorage.removeItem(`bid_analysis_${bidNo}`);
                      setAnalysis(null);
                      setAnalysisFailed(false);
                      setAnalyzing(true);
                      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
                      (async () => {
                        try {
                          const tk = await getToken();
                          const headers: Record<string, string> = {};
                          if (tk) headers["Authorization"] = `Bearer ${tk}`;
                          const res = await fetch(`${baseUrl}/bids/${bidNo}/analysis`, {
                            signal: AbortSignal.timeout(120000),
                            headers,
                          });
                          if (res.ok) {
                            const json = await res.json();
                            setAnalysisWithCache(json.data);
                            setAnalysisFailed(false);
                          } else {
                            setAnalysisFailed(true);
                          }
                        } catch {
                          setAnalysisFailed(true);
                        } finally {
                          setAnalyzing(false);
                        }
                      })();
                    }}
                    className="w-full text-xs text-blue-400 border border-blue-900/50 bg-blue-950/20 rounded-lg py-2 hover:bg-blue-950/40 transition-colors"
                  >
                    AI 재분석 요청
                  </button>
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
