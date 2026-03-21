"use client";

/**
 * F-05: 공고 상세 + AI 분석 결과 페이지
 */

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, BidAnnouncement, BidRecommendation, RecommendationReason, RiskFactor, StoredAttachment, G2bUrl } from "@/lib/api";

const GRADE_COLOR: Record<string, string> = {
  S: "text-purple-400",
  A: "text-emerald-400",
  B: "text-blue-400",
  C: "text-yellow-400",
  D: "text-[#8c8c8c]",
};

const CATEGORY_ICON: Record<string, string> = {
  전문성: "⚡", 실적: "📋", 규모: "💰", 기술: "🔧", 지역: "📍", 기타: "•",
};

const STRENGTH_WIDTH: Record<string, string> = {
  high: "w-4/5", medium: "w-3/5", low: "w-2/5",
};

const RISK_COLOR: Record<string, string> = {
  high: "text-red-400 bg-red-950/40 border-red-900/50",
  medium: "text-orange-400 bg-orange-950/40 border-orange-900/50",
  low: "text-yellow-400 bg-yellow-950/40 border-yellow-900/50",
};

function fileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  const icons: Record<string, string> = {
    pdf: "📄", hwp: "📝", hwpx: "📝", docx: "📃", doc: "📃",
    xlsx: "📊", xls: "📊", zip: "📦", pptx: "📑",
  };
  return icons[ext] ?? "📎";
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function formatBudget(amount: number | null): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

function BidDetailContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const bidNo = params.bidNo as string;
  const teamId = searchParams.get("team_id");

  const [announcement, setAnnouncement] = useState<BidAnnouncement | null>(null);
  const [recommendation, setRecommendation] = useState<BidRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [attachments, setAttachments] = useState<StoredAttachment[]>([]);
  const [g2bUrls, setG2bUrls] = useState<G2bUrl[]>([]);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.bids.getDetail(bidNo, teamId ?? undefined);
        setAnnouncement(res.data.announcement);
        setRecommendation(res.data.recommendation);
      } catch {
        // 인증 실패 시 직접 호출
        try {
          const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
          const qs = teamId ? `?team_id=${teamId}` : "";
          const directRes = await fetch(`${baseUrl}/bids/${bidNo}${qs}`);
          if (directRes.ok) {
            const json = await directRes.json();
            setAnnouncement(json.data.announcement);
            setRecommendation(json.data.recommendation);
          } else {
            setError("공고를 불러올 수 없습니다.");
          }
        } catch {
          setError("백엔드에 연결할 수 없습니다.");
        }
      }
      // 첨부파일 목록 로드
      try {
        const attRes = await api.bids.getAttachments(bidNo);
        setAttachments(attRes.data.stored_files);
        setG2bUrls(attRes.data.g2b_urls);
      } catch { /* 첨부파일 없어도 진행 */ }
      setLoading(false);
    })();
  }, [bidNo, teamId]);

  async function handleDownloadAttachment(fileName: string) {
    setDownloading(fileName);
    try {
      const res = await api.bids.getAttachmentUrl(bidNo, fileName);
      window.open(res.data.url, "_blank");
    } catch {
      alert("파일을 다운로드할 수 없습니다.");
    } finally {
      setDownloading(null);
    }
  }

  async function handleCreateProposal() {
    setCreating(true);
    try {
      const res = await api.bids.createProposalFromBid(bidNo);

      // 첨부파일 URL 추출 (raw_data에서)
      const raw = announcement?.raw_data || {};
      const files: { name: string; url: string; type: string }[] = [];
      for (let i = 1; i <= 10; i++) {
        const url = raw[`ntceSpecDocUrl${i}`];
        const name = raw[`ntceSpecFileNm${i}`];
        if (url && name) {
          const lower = (name as string).toLowerCase();
          let type = "기타";
          if (lower.includes("제안요청") || lower.includes("rfp")) type = "제안요청서";
          else if (lower.includes("과업지시") || lower.includes("과업내용")) type = "과업지시서";
          else if (lower.includes("공고") || lower.includes("입찰")) type = "공고문";
          files.push({ name: name as string, url: url as string, type });
        }
      }

      sessionStorage.setItem(
        "bid_prefill",
        JSON.stringify({
          rfp_title: res.data.bid_title,
          client_name: announcement!.agency,
          rfp_content: res.data.rfp_content,
          bid_no: bidNo,
          budget_amount: announcement!.budget_amount,
          attachments: files,
        })
      );
      router.push("/proposals/new");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "오류가 발생했습니다.");
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
      </div>
    );
  }

  if (error || !announcement) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3">
        <p className="text-sm text-red-400">{error || "공고를 찾을 수 없습니다."}</p>
        <Link href="/bids" className="text-xs text-[#3ecf8e] hover:underline">← 목록으로</Link>
      </div>
    );
  }

  const score = recommendation?.match_score;
  const grade = recommendation?.match_grade;
  const scorePercent = score != null ? `${score}%` : "0%";

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <Link href="/bids" className="text-xs text-[#5c5c5c] hover:text-[#ededed] transition-colors">
            공고 모니터링
          </Link>
          <span className="text-xs text-[#5c5c5c]">/</span>
          <span className="text-xs text-[#8c8c8c]">{announcement.bid_no}</span>
        </div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">{announcement.bid_title}</h1>
            <p className="text-xs text-[#8c8c8c] mt-1">
              {announcement.agency}
              {announcement.budget_amount && ` · ${formatBudget(announcement.budget_amount)}`}
              {announcement.days_remaining != null && ` · D-${announcement.days_remaining} 마감`}
            </p>
          </div>
          <button
            onClick={handleCreateProposal}
            disabled={creating}
            className="shrink-0 bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-4 py-2 text-xs transition-colors"
          >
            {creating ? "이동 중..." : "이 공고로 제안서 만들기"}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-5 space-y-5">
        {/* AI 분석 결과 */}
        {recommendation && score != null && (
          <section className="rounded-lg border border-[#262626] bg-[#111111] p-5">
            <h2 className="text-xs font-semibold text-[#5c5c5c] uppercase tracking-wider mb-4">
              AI 분석 결과
            </h2>

            {/* 자격 판정 경고 */}
            {recommendation.qualification_status === "ambiguous" && (
              <div className="mb-4 px-3 py-2 rounded-lg bg-orange-950/40 border border-orange-900/50">
                <p className="text-xs text-orange-400 font-medium">자격 확인 필요</p>
                {recommendation.qualification_notes && (
                  <p className="text-xs text-orange-300/70 mt-0.5">{recommendation.qualification_notes}</p>
                )}
              </div>
            )}

            {/* 매칭 점수 게이지 */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-[#5c5c5c]">매칭 점수</span>
                <span className={`text-xl font-bold ${GRADE_COLOR[grade ?? "D"]}`}>
                  {score}/100
                  <span className="text-sm ml-1.5">({grade}등급)</span>
                </span>
              </div>
              <div className="h-2 bg-[#1c1c1c] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3ecf8e] rounded-full transition-all"
                  style={{ width: scorePercent }}
                />
              </div>
            </div>

            {/* 추천 요약 */}
            {recommendation.recommendation_summary && (
              <p className="text-sm text-[#ededed] font-medium mb-5 leading-relaxed">
                "{recommendation.recommendation_summary}"
              </p>
            )}

            {/* 추천 사유 */}
            {recommendation.recommendation_reasons && recommendation.recommendation_reasons.length > 0 && (
              <div className="mb-4">
                <h3 className="text-xs font-medium text-[#5c5c5c] mb-2">추천 사유</h3>
                <div className="space-y-2">
                  {recommendation.recommendation_reasons.map((r: RecommendationReason, i: number) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm w-4 text-center shrink-0">{CATEGORY_ICON[r.category] ?? "•"}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-medium text-[#8c8c8c]">{r.category}</span>
                        </div>
                        <p className="text-xs text-[#ededed] truncate">{r.reason}</p>
                      </div>
                      <div className="w-20 h-1.5 bg-[#1c1c1c] rounded-full shrink-0">
                        <div className={`h-full bg-[#3ecf8e] rounded-full ${STRENGTH_WIDTH[r.strength] ?? "w-2/5"}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 리스크 요인 */}
            {recommendation.risk_factors && recommendation.risk_factors.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-[#5c5c5c] mb-2">리스크 요인</h3>
                <div className="space-y-1.5">
                  {recommendation.risk_factors.map((r: RiskFactor, i: number) => (
                    <div
                      key={i}
                      className={`px-3 py-1.5 rounded-lg border text-xs ${RISK_COLOR[r.level] ?? RISK_COLOR.low}`}
                    >
                      {r.risk}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 종합 의견 */}
            {(recommendation.win_probability_hint || recommendation.recommended_action) && (
              <div className="mt-4 pt-4 border-t border-[#262626] flex items-center gap-4">
                {recommendation.win_probability_hint && (
                  <div>
                    <span className="text-xs text-[#5c5c5c]">수주 가능성 </span>
                    <span className="text-xs font-medium text-[#ededed]">{recommendation.win_probability_hint}</span>
                  </div>
                )}
                {recommendation.recommended_action && (
                  <div>
                    <span className="text-xs text-[#5c5c5c]">권장 행동 </span>
                    <span className="text-xs font-medium text-[#3ecf8e]">{recommendation.recommended_action}</span>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* 첨부파일 */}
        {(attachments.length > 0 || g2bUrls.length > 0) && (
          <section className="rounded-lg border border-[#262626] bg-[#111111] p-5">
            <h2 className="text-xs font-semibold text-[#5c5c5c] uppercase tracking-wider mb-3">
              첨부파일
            </h2>
            <div className="space-y-2">
              {attachments.map((att) => (
                <div
                  key={att.storage_path}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-[#1c1c1c] border border-[#262626] hover:border-[#3ecf8e]/30 transition-colors"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="text-base shrink-0">{fileIcon(att.name)}</span>
                    <div className="min-w-0">
                      <p className="text-xs text-[#ededed] truncate">{att.name}</p>
                      {att.size > 0 && (
                        <p className="text-[10px] text-[#5c5c5c]">{formatFileSize(att.size)}</p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadAttachment(att.name)}
                    disabled={downloading === att.name}
                    className="shrink-0 px-3 py-1.5 text-[10px] font-medium rounded-md bg-[#262626] text-[#8c8c8c] hover:bg-[#3ecf8e]/20 hover:text-[#3ecf8e] disabled:opacity-40 transition-colors"
                  >
                    {downloading === att.name ? "..." : "다운로드"}
                  </button>
                </div>
              ))}
              {g2bUrls.filter(u => u.index > 0).map((u) => (
                <a
                  key={u.index}
                  href={u.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[#1c1c1c] border border-[#262626] hover:border-blue-500/30 transition-colors"
                >
                  <span className="text-base shrink-0">🔗</span>
                  <span className="text-xs text-blue-400 truncate">
                    {u.label || `규격서 원본 링크 ${u.index}`}
                  </span>
                </a>
              ))}
            </div>
            {attachments.length === 0 && g2bUrls.length > 0 && (
              <p className="text-[10px] text-[#5c5c5c] mt-2">
                파일은 제안서 프로젝트 생성 시 자동 다운로드됩니다.
              </p>
            )}
          </section>
        )}

        {/* 공고 원문 */}
        <section className="rounded-lg border border-[#262626] bg-[#111111] p-5">
          <h2 className="text-xs font-semibold text-[#5c5c5c] uppercase tracking-wider mb-3">공고 원문</h2>
          {!announcement.qualification_available && (
            <div className="mb-3 px-3 py-2 rounded-lg bg-[#1c1c1c] border border-[#262626]">
              <p className="text-xs text-[#8c8c8c]">자격요건은 첨부파일을 직접 확인하세요.</p>
            </div>
          )}
          {announcement.content_text ? (
            <pre className="text-xs text-[#8c8c8c] whitespace-pre-wrap leading-relaxed font-sans">
              {announcement.content_text}
            </pre>
          ) : (
            <p className="text-xs text-[#5c5c5c]">공고 내용이 없습니다.</p>
          )}
        </section>

        {/* 하단 CTA */}
        <div className="flex justify-center pb-4">
          <button
            onClick={handleCreateProposal}
            disabled={creating}
            className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-8 py-3 text-sm transition-colors"
          >
            {creating ? "이동 중..." : "이 공고로 제안서 만들기"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BidDetailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0f0f0f]" />}>
      <BidDetailContent />
    </Suspense>
  );
}
