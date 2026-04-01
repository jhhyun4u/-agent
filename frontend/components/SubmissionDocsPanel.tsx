"use client";

/**
 * SubmissionDocsPanel — Stream 3 제출서류 체크리스트 UI
 *
 * 기능:
 * - 체크리스트 테이블 (문서명, 포맷, 상태뱃지, 담당자, 마감, 액션)
 * - AI 추출 / 수동 추가
 * - 파일 업로드 (드래그앤드롭)
 * - 담당자 배정
 * - 검증 완료
 * - 사전 제출 점검
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  submissionDocsApi,
  type SubmissionDocument,
  type ReadinessResult,
  type DocStatus,
} from "@/lib/api";

interface Props {
  proposalId: string;
}

// ── 상태 뱃지 ──
const STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: string }
> = {
  pending: { label: "대기", color: "bg-[#262626] text-[#8c8c8c]", icon: "⏳" },
  assigned: {
    label: "배정됨",
    color: "bg-blue-500/15 text-blue-400",
    icon: "👤",
  },
  in_progress: {
    label: "작성중",
    color: "bg-blue-500/15 text-blue-400",
    icon: "🔄",
  },
  uploaded: {
    label: "업로드됨",
    color: "bg-amber-500/15 text-amber-400",
    icon: "📄",
  },
  verified: {
    label: "검증완료",
    color: "bg-[#3ecf8e]/15 text-[#3ecf8e]",
    icon: "✅",
  },
  rejected: { label: "반려", color: "bg-red-500/15 text-red-400", icon: "❌" },
  not_applicable: {
    label: "해당없음",
    color: "bg-[#262626] text-[#8c8c8c]",
    icon: "—",
  },
  expired: { label: "만료", color: "bg-red-500/15 text-red-400", icon: "⚠️" },
};

function DocStatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium ${cfg.color}`}
    >
      <span>{cfg.icon}</span> {cfg.label}
    </span>
  );
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "text-red-400",
  medium: "text-amber-400",
  low: "text-[#8c8c8c]",
};

export default function SubmissionDocsPanel({ proposalId }: Props) {
  const [docs, setDocs] = useState<SubmissionDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newDocType, setNewDocType] = useState("");
  const [newDocCategory, setNewDocCategory] = useState<string>("other");
  const [newDocFormat, setNewDocFormat] = useState<string>("자유");
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // 팀원 목록 (담당자 배정용)
  const [teamMembers, setTeamMembers] = useState<
    Array<{ id: string; name: string }>
  >([]);

  // 드래그 상태
  const [dragOverDocId, setDragOverDocId] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await submissionDocsApi.list(proposalId);
      setDocs(data);
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  }, [proposalId]);

  const fetchReadiness = useCallback(async () => {
    try {
      const data = await submissionDocsApi.readiness(proposalId);
      setReadiness(data);
    } catch {
      /* empty */
    }
  }, [proposalId]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // 팀원 목록 로드
  useEffect(() => {
    (async () => {
      try {
        const res = await api.admin.listUsers({
          status: "active",
          page_size: 200,
        });
        setTeamMembers(
          (res.users || []).map((u: Record<string, unknown>) => ({
            id: u.id as string,
            name: (u.name as string) || (u.email as string) || "?",
          })),
        );
      } catch {
        /* empty */
      }
    })();
  }, []);

  // ── AI 추출 ──
  async function handleExtract() {
    setExtracting(true);
    try {
      const data = await submissionDocsApi.extract(proposalId);
      setDocs(data);
    } catch (e) {
      alert(e instanceof Error ? e.message : "AI 추출 실패");
    } finally {
      setExtracting(false);
    }
  }

  // ── 수동 추가 ──
  async function handleAddDoc() {
    if (!newDocType.trim()) return;
    try {
      await submissionDocsApi.add(proposalId, {
        doc_type: newDocType.trim(),
        doc_category: newDocCategory as SubmissionDocument["doc_category"],
        required_format: newDocFormat as SubmissionDocument["required_format"],
      });
      setNewDocType("");
      setShowAddForm(false);
      fetchDocs();
    } catch (e) {
      alert(e instanceof Error ? e.message : "추가 실패");
    }
  }

  // ── 파일 업로드 ──
  async function handleUpload(docId: string, file: File) {
    try {
      await submissionDocsApi.upload(proposalId, docId, file);
      fetchDocs();
    } catch (e) {
      alert(e instanceof Error ? e.message : "업로드 실패");
    }
  }

  // ── 검증 ──
  async function handleVerify(docId: string) {
    try {
      await submissionDocsApi.verify(proposalId, docId);
      fetchDocs();
      fetchReadiness();
    } catch (e) {
      alert(e instanceof Error ? e.message : "검증 실패");
    }
  }

  // ── 원본 준비 확인 ──
  async function handleConfirmOriginal(docId: string) {
    try {
      await submissionDocsApi.confirmOriginal(proposalId, docId);
      fetchDocs();
      fetchReadiness();
    } catch (e) {
      alert(e instanceof Error ? e.message : "원본 확인 실패");
    }
  }

  // ── 사본 묶음 다운로드 ──
  function handleBundleDownload() {
    window.open(submissionDocsApi.bundleUrl(proposalId), "_blank");
  }

  // ── 삭제 ──
  async function handleDelete(docId: string) {
    if (!confirm("이 서류를 삭제하시겠습니까?")) return;
    try {
      await submissionDocsApi.remove(proposalId, docId);
      fetchDocs();
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  // ── 담당자 배정 ──
  async function handleAssign(docId: string, assigneeId: string) {
    try {
      await submissionDocsApi.update(proposalId, docId, {
        assignee_id: assigneeId || undefined,
        status: assigneeId ? "assigned" : undefined,
      });
      fetchDocs();
    } catch {
      /* empty */
    }
  }

  // ── 상태 변경 ──
  async function handleStatusChange(docId: string, status: DocStatus) {
    try {
      await submissionDocsApi.update(proposalId, docId, { status });
      fetchDocs();
    } catch {
      /* empty */
    }
  }

  // ── 드래그앤드롭 ──
  function onDragOver(e: React.DragEvent, docId: string) {
    e.preventDefault();
    setDragOverDocId(docId);
  }
  function onDragLeave() {
    setDragOverDocId(null);
  }
  async function onDrop(e: React.DragEvent, docId: string) {
    e.preventDefault();
    setDragOverDocId(null);
    const file = e.dataTransfer.files?.[0];
    if (file) await handleUpload(docId, file);
  }

  // 통계 (가중 진행률)
  const applicable = docs.filter((d) => d.status !== "not_applicable");
  const total = applicable.length;
  const verified = applicable.filter((d) => d.status === "verified").length;
  const uploaded = applicable.filter((d) => d.status === "uploaded").length;
  const assigned = applicable.filter(
    (d) => d.status === "assigned" || d.status === "in_progress",
  ).length;
  const weightedPct =
    total > 0
      ? Math.min(
          Math.round(
            ((verified * 1.0 + uploaded * 0.7 + assigned * 0.3) / total) * 100,
          ),
          100,
        )
      : 0;
  const hasCopyFiles = docs.some(
    (d) => d.file_path && d.source === "template_matched",
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-[#8c8c8c] text-sm">
        불러오는 중...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-[#ededed]">
            제출서류 체크리스트
          </h2>
          <span className="text-xs text-[#8c8c8c]">
            {verified}/{total} 완료
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/30 hover:bg-blue-500/25 transition-colors disabled:opacity-50"
          >
            {extracting ? "추출 중..." : "AI 추출"}
          </button>
          <button
            onClick={() => setShowAddForm((v) => !v)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#1c1c1c] text-[#ededed] border border-[#262626] hover:border-[#3ecf8e]/40 transition-colors"
          >
            + 수동 추가
          </button>
          {hasCopyFiles && (
            <button
              onClick={handleBundleDownload}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-500/15 text-purple-400 border border-purple-500/30 hover:bg-purple-500/25 transition-colors"
            >
              사본 묶음 다운로드
            </button>
          )}
          <button
            onClick={fetchReadiness}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#3ecf8e]/15 text-[#3ecf8e] border border-[#3ecf8e]/30 hover:bg-[#3ecf8e]/25 transition-colors"
          >
            사전 점검
          </button>
        </div>
      </div>

      {/* 완료 배너 */}
      {verified === total && total > 0 && (
        <div className="bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 rounded-xl px-4 py-3 flex items-center gap-2">
          <span className="text-[#3ecf8e] text-sm font-semibold">
            제출서류 준비 완료
          </span>
          <span className="text-xs text-[#8c8c8c]">
            모든 서류가 검증 완료되었습니다
          </span>
        </div>
      )}

      {/* 진행률 바 */}
      <div className="w-full h-2 bg-[#262626] rounded-full overflow-hidden">
        <div
          className="h-full bg-[#3ecf8e] rounded-full transition-all duration-500"
          style={{ width: `${weightedPct}%` }}
        />
      </div>

      {/* 수동 추가 폼 */}
      {showAddForm && (
        <div className="bg-[#1c1c1c] border border-[#262626] rounded-lg p-4 flex items-end gap-3">
          <div className="flex-1">
            <label className="text-[10px] text-[#8c8c8c] uppercase tracking-wider">
              문서명
            </label>
            <input
              value={newDocType}
              onChange={(e) => setNewDocType(e.target.value)}
              placeholder="예: 사업자등록증"
              className="mt-1 w-full px-3 py-1.5 bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed] focus:outline-none focus:border-[#3ecf8e]/50"
              onKeyDown={(e) => e.key === "Enter" && handleAddDoc()}
            />
          </div>
          <div>
            <label className="text-[10px] text-[#8c8c8c] uppercase tracking-wider">
              카테고리
            </label>
            <select
              value={newDocCategory}
              onChange={(e) => setNewDocCategory(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed]"
            >
              <option value="proposal">제안 산출물</option>
              <option value="qualification">참가자격</option>
              <option value="certification">인증/자격증</option>
              <option value="financial">재무/가격</option>
              <option value="other">기타</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-[#8c8c8c] uppercase tracking-wider">
              포맷
            </label>
            <select
              value={newDocFormat}
              onChange={(e) => setNewDocFormat(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed]"
            >
              <option value="자유">자유</option>
              <option value="HWPX">HWPX</option>
              <option value="PDF">PDF</option>
              <option value="원본">원본</option>
              <option value="사본">사본</option>
            </select>
          </div>
          <button
            onClick={handleAddDoc}
            className="px-4 py-1.5 text-xs font-medium rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors"
          >
            추가
          </button>
        </div>
      )}

      {/* 체크리스트 테이블 */}
      {docs.length === 0 ? (
        <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-12 text-center">
          <p className="text-sm text-[#8c8c8c]">제출서류가 없습니다.</p>
          <p className="text-xs text-[#8c8c8c] mt-1">
            &quot;AI 추출&quot; 버튼으로 RFP에서 자동 추출하거나, 수동으로
            추가하세요.
          </p>
        </div>
      ) : (
        <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[#262626] text-[#8c8c8c]">
                <th className="text-left px-4 py-2.5 font-medium w-8">#</th>
                <th className="text-left px-4 py-2.5 font-medium">문서명</th>
                <th className="text-left px-4 py-2.5 font-medium w-20">포맷</th>
                <th className="text-left px-4 py-2.5 font-medium w-24">상태</th>
                <th className="text-left px-4 py-2.5 font-medium w-20">
                  우선순위
                </th>
                <th className="text-left px-4 py-2.5 font-medium w-28">
                  담당자
                </th>
                <th className="text-left px-4 py-2.5 font-medium w-24">파일</th>
                <th className="text-right px-4 py-2.5 font-medium w-24">
                  액션
                </th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc, idx) => (
                <tr
                  key={doc.id}
                  className={`border-b border-[#262626]/50 hover:bg-[#262626]/30 transition-colors ${
                    dragOverDocId === doc.id ? "bg-blue-500/10" : ""
                  }`}
                  onDragOver={(e) => onDragOver(e, doc.id)}
                  onDragLeave={onDragLeave}
                  onDrop={(e) => onDrop(e, doc.id)}
                >
                  <td className="px-4 py-2.5 text-[#8c8c8c]">{idx + 1}</td>
                  <td className="px-4 py-2.5">
                    <div>
                      <span className="text-[#ededed] font-medium">
                        {doc.doc_type}
                      </span>
                      {doc.rfp_reference && (
                        <span className="ml-2 text-[10px] text-[#8c8c8c]">
                          {doc.rfp_reference}
                        </span>
                      )}
                    </div>
                    {doc.notes && (
                      <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                        {doc.notes}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-[#8c8c8c]">
                      {doc.required_format}
                    </span>
                    {doc.required_copies > 1 && (
                      <span className="ml-1 text-[#8c8c8c]">
                        x{doc.required_copies}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <DocStatusBadge status={doc.status} />
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={
                        PRIORITY_COLORS[doc.priority] || "text-[#8c8c8c]"
                      }
                    >
                      {doc.priority === "high"
                        ? "높음"
                        : doc.priority === "medium"
                          ? "보통"
                          : "낮음"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <select
                      value={doc.assignee_id || ""}
                      onChange={(e) => handleAssign(doc.id, e.target.value)}
                      className="w-full px-1.5 py-0.5 bg-[#0f0f0f] border border-[#262626] rounded text-[10px] text-[#ededed] focus:outline-none focus:border-blue-500/50"
                    >
                      <option value="">미배정</option>
                      {teamMembers.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2.5">
                    {doc.required_format === "원본" ? (
                      <span className="text-[#8c8c8c] text-[10px]">
                        원본 서류
                      </span>
                    ) : doc.file_name && doc.source === "template_matched" ? (
                      <div className="flex items-center gap-1">
                        <span
                          className="text-[#3ecf8e] truncate block max-w-[60px]"
                          title={doc.file_name}
                        >
                          {doc.file_name}
                        </span>
                        <span className="inline-flex px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#3ecf8e]/15 text-[#3ecf8e]">
                          자동
                        </span>
                      </div>
                    ) : doc.file_name ? (
                      <span
                        className="text-[#3ecf8e] truncate block max-w-[80px]"
                        title={doc.file_name}
                      >
                        {doc.file_name}
                      </span>
                    ) : (
                      <button
                        onClick={() => fileInputRefs.current[doc.id]?.click()}
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        업로드
                      </button>
                    )}
                    <input
                      ref={(el) => {
                        fileInputRefs.current[doc.id] = el;
                      }}
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUpload(doc.id, f);
                        e.target.value = "";
                      }}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {doc.required_format === "원본" &&
                        doc.status !== "verified" && (
                          <button
                            onClick={() => handleConfirmOriginal(doc.id)}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 transition-colors"
                          >
                            원본 준비 완료
                          </button>
                        )}
                      {doc.required_format !== "원본" &&
                        doc.status === "uploaded" && (
                          <button
                            onClick={() => handleVerify(doc.id)}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#3ecf8e]/15 text-[#3ecf8e] hover:bg-[#3ecf8e]/25 transition-colors"
                          >
                            검증
                          </button>
                        )}
                      {doc.status === "pending" && (
                        <button
                          onClick={() =>
                            handleStatusChange(doc.id, "not_applicable")
                          }
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#262626] text-[#8c8c8c] hover:bg-[#262626]/80 transition-colors"
                          title="해당없음 처리"
                        >
                          N/A
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="px-2 py-0.5 rounded text-[10px] font-medium text-red-400 hover:bg-red-500/15 transition-colors"
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 사전 점검 결과 */}
      {readiness && (
        <div
          className={`border rounded-xl p-4 ${
            readiness.ready
              ? "bg-[#3ecf8e]/5 border-[#3ecf8e]/30"
              : "bg-amber-500/5 border-amber-500/30"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold text-[#ededed]">
              {readiness.ready ? "✅ 제출 준비 완료" : "⚠️ 미완료 항목 있음"}
            </h3>
            <span className="text-xs text-[#8c8c8c]">
              필수 {readiness.total}건 중 {readiness.completed}건 완료
            </span>
          </div>
          {readiness.issues.length > 0 && (
            <ul className="space-y-1 mt-2">
              {readiness.issues.map((issue) => (
                <li
                  key={issue.doc_id}
                  className="flex items-center gap-2 text-xs"
                >
                  <span className="text-amber-400">!</span>
                  <span className="text-[#ededed]">{issue.doc_type}:</span>
                  <span className="text-[#8c8c8c]">
                    {issue.issue || issue.status}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
