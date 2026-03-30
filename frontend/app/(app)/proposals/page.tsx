"use client";

/**
 * §13-1: 제안 프로젝트 페이지
 * - 상단: 3가지 진입 경로 카드 (A. 공고 모니터링 / B. 공고번호 / C. RFP 업로드)
 *   - A: 제안결정된 공고 목록 인라인 표시 → 선택 시 워크플로 진입
 *   - B: 공고번호 입력 인라인 폼
 *   - C: RFP 파일 업로드 인라인 폼
 * - 하단: 진행 중인 프로젝트 목록 (5컬럼)
 */

import { Suspense, useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, ProposalSummary, MonitoredBid } from "@/lib/api";
import {
  SCOPE_LABELS,
  Scope,
  getStepInfo,
  deriveStatus,
  formatDeadline,
  formatBudgetCompact,
  GRID_LAYOUT_CLASS,
  createSortComparator,
} from "@/lib/proposals-utils";
import { ProposalsTableHeader } from "@/components/ProposalsTableHeader";
import { ProposalsTableRow } from "@/components/ProposalsTableRow";
import { ProposalsTableSkeleton } from "@/components/ProposalsTableSkeleton";

/* ── 메인 컨텐츠 ── */
function ProposalsContent() {
  const router = useRouter();

  // 스코프 탭
  const [scope, setScope] = useState<Scope>("team");

  // 진입 경로 인라인 상태
  type InlineMode = "none" | "monitor_decided" | "rfp_upload";
  const [inlineMode, setInlineMode] = useState<InlineMode>("none");

  // 검색 & 필터 (디바운스)
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // 정렬
  type SortKey = "deadline" | "step" | "created_at" | null;
  const [sortKey, setSortKey] = useState<SortKey>(null);
  const [sortAsc, setSortAsc] = useState(true);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  // 프로젝트 목록
  const [proposals, setProposals] = useState<ProposalSummary[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [page, setPage] = useState(1);

  // Path A: 제안결정된 공고
  const [decidedBids, setDecidedBids] = useState<MonitoredBid[]>([]);
  const [decidedLoading, setDecidedLoading] = useState(false);
  const [startingBid, setStartingBid] = useState<string | null>(null);

  // Path C: RFP 업로드
  const [rfpFile, setRfpFile] = useState<File | null>(null);
  const [rfpUploadTitle, setRfpUploadTitle] = useState("");
  const [rfpClientName, setRfpClientName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  // 컨텍스트 메뉴
  const [menuOpen, setMenuOpen] = useState<string | null>(null);

  // 드래그 앤 드롭
  const [dragging, setDragging] = useState(false);

  // 공통
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // 메뉴 외부 클릭 시 닫기
  useEffect(() => {
    if (!menuOpen) return;
    const handler = () => setMenuOpen(null);
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [menuOpen]);

  // ── 프로젝트 목록 로드 ──
  const fetchProposals = useCallback(async () => {
    setLoading(true);
    setFetchError(false);
    try {
      const params: Record<string, string | number> = { page, scope };
      if (statusFilter !== "all") params.status = statusFilter;
      if (search.trim()) params.search = search.trim();
      const res = await api.proposals.list(params as Parameters<typeof api.proposals.list>[0]);
      setProposals(res.data);
      setTotalCount(res.meta?.total ?? res.data.length);
    } catch {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const qs = new URLSearchParams();
        qs.set("skip", String((page - 1) * 20));
        qs.set("limit", "20");
        qs.set("scope", scope);
        if (statusFilter !== "all") qs.set("status", statusFilter);
        if (search.trim()) qs.set("search", search.trim());
        const res = await fetch(`${baseUrl}/proposals?${qs}`);
        if (res.ok) {
          const data = await res.json();
          setProposals(data.data || []);
          setTotalCount(data.meta?.total ?? data.data?.length ?? 0);
        }
      } catch {
        setProposals([]);
        setFetchError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [page, scope, statusFilter, search]);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  // 필터 변경 시 page 리셋
  useEffect(() => {
    setPage(1);
  }, [scope, statusFilter, search]);

  // ── Path A: 제안결정된 공고 로드 ──
  async function loadDecidedBids() {
    setDecidedLoading(true);
    try {
      // show_all=true로 전체 목록 가져온 뒤 제안결정만 필터
      const res = await api.bids.monitor("company", 1, true);
      const decided = (res.data || []).filter(
        (b) => b.proposal_status === "제안결정" || b.proposal_status === "제안착수"
      );
      setDecidedBids(decided);
    } catch {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const res = await fetch(`${baseUrl}/bids/monitor?scope=company&page=1&show_all=true`);
        if (res.ok) {
          const json = await res.json();
          const decided = (json.data || []).filter(
            (b: MonitoredBid) => b.proposal_status === "제안결정" || b.proposal_status === "제안착수"
          );
          setDecidedBids(decided);
        }
      } catch {
        setDecidedBids([]);
      }
    } finally {
      setDecidedLoading(false);
    }
  }

  // ── Path A: 제안결정 공고에서 제안서 생성 ──
  async function startFromDecidedBid(bid: MonitoredBid) {
    setStartingBid(bid.bid_no);
    setError("");
    try {
      const data = await api.proposals.createFromBid(bid.bid_no);
      router.push(`/proposals/${data.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제안서 생성 실패");
      setStartingBid(null);
    }
  }

  // ── Path C: 제출 ──
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

  function resetInline() {
    setInlineMode("none");
    setError("");
    setRfpFile(null);
    setRfpUploadTitle("");
    setRfpClientName("");
    setDecidedBids([]);
    setStartingBid(null);
  }

  function openInline(mode: InlineMode) {
    resetInline();
    setInlineMode(mode);
    if (mode === "monitor_decided") loadDecidedBids();
  }

  const errorBanner = error && (
    <p className="text-xs text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
  );

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 페이지 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">제안 프로젝트 목록</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">
              {SCOPE_LABELS[scope].desc}
              {proposals.length > 0 && ` · ${proposals.length}건`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* 스코프 탭 */}
            <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
              {(["my", "team", "division", "company"] as Scope[]).map((s) => (
                <button
                  key={s}
                  onClick={() => setScope(s)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    scope === s
                      ? "bg-[#3ecf8e] text-[#0f0f0f]"
                      : "text-[#8c8c8c] hover:text-[#ededed]"
                  }`}
                >
                  {SCOPE_LABELS[s].label}
                </button>
              ))}
            </div>
            {inlineMode !== "none" ? (
              <button
                onClick={resetInline}
                className="font-semibold rounded-lg px-4 py-2 text-xs transition-colors bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c] hover:text-[#ededed]"
              >
                닫기
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => openInline("monitor_decided")}
                  className="font-medium rounded-lg px-3 py-2 text-xs transition-colors bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c] hover:border-[#3ecf8e]/50 hover:text-[#3ecf8e]"
                >
                  공고에서 시작
                </button>
                <button
                  onClick={() => openInline("rfp_upload")}
                  className="font-semibold rounded-lg px-3 py-2 text-xs transition-colors bg-[#3ecf8e] hover:bg-[#49e59e] text-black"
                >
                  + RFP 업로드
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 검색바 + 상태 필터 */}
      <div className="px-6 pt-4 pb-0 flex items-center gap-3 shrink-0">
        <div className="relative flex-1 max-w-xs">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="프로젝트명 검색..."
            className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#ededed] placeholder:text-[#666] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
          />
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#5c5c5c] text-xs">&#x1F50D;</span>
        </div>
        <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-0.5 border border-[#262626]">
          {[
            { value: "all", label: "전체" },
            { value: "processing", label: "진행중" },
            { value: "awaiting_result", label: "결과대기" },
            { value: "completed", label: "완료" },
            { value: "on_hold", label: "중단" },
          ].map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                statusFilter === f.value
                  ? "bg-[#262626] text-[#ededed]"
                  : "text-[#5c5c5c] hover:text-[#8c8c8c]"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-5 space-y-6">
        {/* ═══ 인라인: Path A — 제안결정된 공고 목록 ═══ */}
        {inlineMode === "monitor_decided" && (
          <div className="bg-[#141414] border border-emerald-900/40 rounded-xl p-5 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <p className="text-xs font-semibold text-[#3ecf8e]">제안작업 대기 중</p>
                <span className="text-[10px] text-[#5c5c5c]">공고 모니터링에서 제안결정된 과제</span>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  href="/monitoring"
                  className="text-[10px] text-[#8c8c8c] hover:text-[#ededed] transition-colors"
                >
                  공고 모니터링 →
                </Link>
                <button onClick={resetInline} className="text-[#5c5c5c] hover:text-[#ededed] text-xs transition-colors">닫기</button>
              </div>
            </div>

            {decidedLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-4 h-4 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
                <span className="text-xs text-[#5c5c5c] ml-2">제안결정 과제를 불러오는 중...</span>
              </div>
            ) : decidedBids.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-[#8c8c8c] mb-2">제안결정된 과제가 없습니다</p>
                <p className="text-xs text-[#5c5c5c] mb-4">공고 모니터링에서 과제를 검토하고 제안결정을 해주세요</p>
                <Link
                  href="/monitoring"
                  className="inline-flex items-center gap-1.5 bg-[#1c1c1c] hover:bg-[#262626] border border-[#262626] text-[#ededed] rounded-lg px-4 py-2 text-xs font-medium transition-colors"
                >
                  🔍 공고 모니터링으로 이동
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {decidedBids.map((bid) => {
                  const dl = bid.deadline_date ? new Date(bid.deadline_date) : null;
                  const dlText = dl ? `${dl.getMonth() + 1}/${dl.getDate()}` : "—";
                  const now = new Date();
                  const daysLeft = dl ? Math.ceil((dl.getTime() - now.getTime()) / 86400000) : null;
                  const isStarting = startingBid === bid.bid_no;

                  return (
                    <div
                      key={bid.bid_no}
                      className="flex items-center gap-4 p-3 bg-[#1c1c1c] border border-[#262626] rounded-lg hover:border-[#3ecf8e]/40 transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-[#ededed] truncate font-medium">{bid.bid_title}</p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-[#8c8c8c]">
                          <span>{bid.agency}</span>
                          <span>{formatBudget(bid.budget_amount)}</span>
                          <span className={daysLeft !== null && daysLeft <= 7 ? "text-red-400 font-semibold" : ""}>
                            마감 {dlText}
                            {daysLeft !== null && ` (D-${daysLeft})`}
                          </span>
                        </div>
                        {bid.related_teams && bid.related_teams.length > 0 && (
                          <div className="flex gap-1 mt-1.5">
                            {bid.related_teams.map((team, i) => (
                              <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950/40 text-blue-400 border border-blue-900/50">
                                {team}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded border text-[#3ecf8e] bg-emerald-950/60 border-emerald-900">
                          {bid.proposal_status}
                        </span>
                        <button
                          onClick={() => startFromDecidedBid(bid)}
                          disabled={isStarting}
                          className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 text-black font-semibold rounded-lg px-3 py-1.5 text-xs transition-colors"
                        >
                          {isStarting ? "생성 중..." : "제안서 시작"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {errorBanner}
          </div>
        )}

        {/* ═══ 인라인 폼: Path B — RFP 업로드 ═══ */}
        {inlineMode === "rfp_upload" && (
          <div className="bg-[#141414] border border-purple-900/40 rounded-xl p-5 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-semibold text-purple-400">RFP 파일 업로드</p>
              <button onClick={resetInline} className="text-[#5c5c5c] hover:text-[#ededed] text-xs transition-colors">닫기</button>
            </div>
            <form onSubmit={submitFromRfpUpload} className="space-y-4">
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.hwp,.hwpx,.txt,.doc,.docx"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  setRfpFile(f);
                  if (f && !rfpUploadTitle) setRfpUploadTitle(f.name.replace(/\.[^.]+$/, ""));
                }}
                className="hidden"
              />
              {/* 드래그 앤 드롭 상태 */}
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
                  onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragging(false);
                    const f = e.dataTransfer.files?.[0];
                    if (f) {
                      setRfpFile(f);
                      if (!rfpUploadTitle) setRfpUploadTitle(f.name.replace(/\.[^.]+$/, ""));
                    }
                  }}
                  className={`w-full flex flex-col items-center gap-2 py-6 bg-[#1c1c1c] border-2 border-dashed rounded-xl transition-colors ${
                    dragging ? "border-purple-400 bg-purple-950/20" : "border-[#333] hover:border-purple-500/50"
                  }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-purple-950/40 border border-purple-900/50 flex items-center justify-center text-purple-400">+</div>
                  <p className="text-xs text-[#8c8c8c]">{dragging ? "여기에 놓으세요" : "클릭 또는 드래그하여 파일 선택"}</p>
                  <p className="text-[10px] text-[#5c5c5c]">PDF, HWP, HWPX, TXT, DOC, DOCX</p>
                </button>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#ededed] mb-1.5">프로젝트명</label>
                  <input
                    type="text"
                    value={rfpUploadTitle}
                    onChange={(e) => setRfpUploadTitle(e.target.value)}
                    placeholder="파일명에서 자동 추출"
                    className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder:text-[#666] focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#ededed] mb-1.5">
                    발주처 <span className="text-[#5c5c5c] font-normal">(선택)</span>
                  </label>
                  <input
                    type="text"
                    value={rfpClientName}
                    onChange={(e) => setRfpClientName(e.target.value)}
                    placeholder="발주 기관명"
                    className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder:text-[#666] focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>

              {errorBanner}

              <button
                type="submit"
                disabled={submitting || !rfpFile}
                className="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
              >
                {submitting ? "제안서 생성 중..." : "RFP 분석 및 제안서 시작"}
              </button>
            </form>
          </div>
        )}

        {/* ═══ 진행 중인 프로젝트 목록 ═══ */}
        <div>
          <p className="text-xs font-medium text-[#5c5c5c] uppercase tracking-wider mb-3">
            {statusFilter === "all" ? "프로젝트" : statusFilter === "processing" ? "진행 중" : statusFilter === "completed" ? "완료" : "실패"}
            {!loading && ` · ${totalCount}건`}
          </p>

          {loading ? (
            <ProposalsTableSkeleton rows={5} />
          ) : fetchError ? (
            <div className="flex flex-col items-center justify-center py-12 text-center border border-red-900/40 rounded-xl bg-red-950/10">
              <p className="text-sm text-red-400 mb-2">프로젝트 목록을 불러올 수 없습니다</p>
              <p className="text-xs text-[#5c5c5c] mb-4">네트워크 연결을 확인하거나 다시 시도해주세요</p>
              <button
                onClick={fetchProposals}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-[#1c1c1c] border border-[#262626] text-[#ededed] hover:bg-[#262626] transition-colors"
              >
                다시 시도
              </button>
            </div>
          ) : proposals.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center border border-[#262626] rounded-xl bg-[#111111]">
              <div className="w-10 h-10 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-xl mb-3">
                📋
              </div>
              <p className="text-sm text-[#8c8c8c]">아직 진행 중인 프로젝트가 없습니다</p>
              <p className="text-xs text-[#5c5c5c] mt-1">위 경로 중 하나를 선택하여 첫 프로젝트를 시작하세요</p>
            </div>
          ) : (
            <>
              <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
                <ProposalsTableHeader
                  sortKey={sortKey}
                  sortAsc={sortAsc}
                  onSort={toggleSort}
                />
                {[...proposals]
                  .sort(
                    sortKey
                      ? createSortComparator(sortKey, sortAsc ? 1 : -1)
                      : () => 0,
                  )
                  .map((p) => (
                    <ProposalsTableRow
                      key={p.id}
                      proposal={p}
                      menuOpen={menuOpen}
                      onMenuToggle={(id) =>
                        setMenuOpen(menuOpen === id ? null : id)
                      }
                      onMenuAction={(id, action) => {
                        if (action === "view" || action === "resume") {
                          router.push(`/proposals/${id}`);
                        } else if (action === "delete") {
                          // TODO: Implement delete functionality
                        }
                        setMenuOpen(null);
                      }}
                    />
                  ))}
              </div>

              {totalCount > 20 && (() => {
                const totalPages = Math.ceil(totalCount / 20);
                const from = (page - 1) * 20 + 1;
                const to = Math.min(page * 20, totalCount);
                return (
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-xs text-[#5c5c5c]">
                      {from}-{to} / {totalCount}건
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        disabled={page === 1}
                        onClick={() => setPage((p) => p - 1)}
                        className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] disabled:opacity-40 hover:bg-[#1c1c1c] hover:text-[#ededed] transition-colors"
                      >
                        이전
                      </button>
                      <span className="px-3 py-1.5 text-xs text-[#8c8c8c]">{page} / {totalPages}</span>
                      <button
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                        className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] disabled:opacity-40 hover:bg-[#1c1c1c] hover:text-[#ededed] transition-colors"
                      >
                        다음
                      </button>
                    </div>
                  </div>
                );
              })()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProposalsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0f0f0f]" />}>
      <ProposalsContent />
    </Suspense>
  );
}
