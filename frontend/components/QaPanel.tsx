"use client";

/**
 * PSM-16: Q&A 기록 입력/관리 패널
 *
 * 프로젝트 상세 페이지에서 사용.
 * - Q&A 목록 조회
 * - 새 Q&A 추가 (질문, 답변, 카테고리, 평가위원 반응, 메모)
 * - 개별 수정/삭제
 */

import { useCallback, useEffect, useState } from "react";
import { api, type QARecord, type QARecordCreate } from "@/lib/api";

const CATEGORIES = [
  { value: "general", label: "일반" },
  { value: "technical", label: "기술" },
  { value: "management", label: "관리" },
  { value: "pricing", label: "가격/예산" },
  { value: "experience", label: "수행실적" },
  { value: "team", label: "투입인력" },
];

const REACTIONS = [
  { value: "", label: "미선택" },
  { value: "positive", label: "긍정" },
  { value: "neutral", label: "중립" },
  { value: "negative", label: "부정" },
];

function categoryLabel(value: string) {
  return CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

function reactionBadge(reaction: string | null) {
  if (!reaction) return null;
  const colors: Record<string, string> = {
    positive: "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/30",
    neutral: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
    negative: "bg-red-500/15 text-red-400 border-red-500/30",
  };
  const labels: Record<string, string> = {
    positive: "긍정", neutral: "중립", negative: "부정",
  };
  return (
    <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium border ${colors[reaction] ?? ""}`}>
      {labels[reaction] ?? reaction}
    </span>
  );
}

export default function QaPanel({ proposalId }: { proposalId: string }) {
  const [records, setRecords] = useState<QARecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // 새 Q&A 폼
  const [form, setForm] = useState<QARecordCreate>({
    question: "",
    answer: "",
    category: "general",
    evaluator_reaction: null,
    memo: null,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchRecords = useCallback(async () => {
    try {
      const res = await api.qa.list(proposalId);
      setRecords(res.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [proposalId]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  function resetForm() {
    setForm({ question: "", answer: "", category: "general", evaluator_reaction: null, memo: null });
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.question.trim() || !form.answer.trim()) return;
    setSubmitting(true);
    try {
      if (editingId) {
        await api.qa.update(proposalId, editingId, {
          question: form.question,
          answer: form.answer,
          category: form.category,
          evaluator_reaction: form.evaluator_reaction || null,
          memo: form.memo || null,
        });
      } else {
        await api.qa.create(proposalId, [form]);
      }
      resetForm();
      fetchRecords();
    } catch (err) {
      alert(err instanceof Error ? err.message : "저장 실패");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(qaId: string) {
    if (!confirm("이 Q&A 기록을 삭제하시겠습니까?")) return;
    try {
      await api.qa.delete(proposalId, qaId);
      fetchRecords();
    } catch (err) {
      alert(err instanceof Error ? err.message : "삭제 실패");
    }
  }

  function handleEdit(qa: QARecord) {
    setForm({
      question: qa.question,
      answer: qa.answer,
      category: qa.category as QARecordCreate["category"],
      evaluator_reaction: qa.evaluator_reaction as QARecordCreate["evaluator_reaction"],
      memo: qa.memo,
    });
    setEditingId(qa.id);
    setShowForm(true);
  }

  if (loading) {
    return (
      <div className="text-sm text-[#8c8c8c] py-8 text-center">
        Q&A 기록 불러오는 중...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#ededed]">
          Q&A 기록{" "}
          <span className="text-[#8c8c8c] font-normal">({records.length}건)</span>
        </h3>
        <button
          onClick={() => { resetForm(); setShowForm(!showForm); }}
          className="text-xs text-[#3ecf8e] hover:text-[#3ecf8e]/80 font-medium transition-colors"
        >
          {showForm ? "취소" : "+ 추가"}
        </button>
      </div>

      {/* Q&A 목록 */}
      {records.length === 0 && !showForm && (
        <p className="text-sm text-[#8c8c8c] py-4 text-center">
          등록된 Q&A 기록이 없습니다.
        </p>
      )}

      <div className="space-y-2.5">
        {records.map((qa) => (
          <div
            key={qa.id}
            className="bg-[#111111] border border-[#262626] rounded-xl p-4 space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#ededed]">
                  Q: {qa.question}
                </p>
                <p className="text-sm text-[#8c8c8c] mt-1 whitespace-pre-wrap">
                  A: {qa.answer}
                </p>
              </div>
              <div className="flex gap-1.5 shrink-0">
                <button
                  onClick={() => handleEdit(qa)}
                  className="text-[10px] text-[#8c8c8c] hover:text-[#ededed] transition-colors"
                >
                  수정
                </button>
                <button
                  onClick={() => handleDelete(qa.id)}
                  className="text-[10px] text-red-400/70 hover:text-red-400 transition-colors"
                >
                  삭제
                </button>
              </div>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-[#8c8c8c]">
              <span className="px-1.5 py-0.5 rounded bg-[#262626] text-[#8c8c8c]">
                {categoryLabel(qa.category)}
              </span>
              {reactionBadge(qa.evaluator_reaction)}
              {qa.memo && (
                <span className="truncate max-w-[200px]" title={qa.memo}>
                  {qa.memo}
                </span>
              )}
              <span className="ml-auto">
                {new Date(qa.created_at).toLocaleDateString("ko-KR")}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 입력 폼 */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-[#111111] border border-[#262626] rounded-xl p-4 space-y-3">
          <p className="text-xs font-semibold text-[#ededed]">
            {editingId ? "Q&A 수정" : "새 Q&A 추가"}
          </p>

          <div>
            <label className="text-[10px] text-[#8c8c8c] block mb-1">질문</label>
            <textarea
              value={form.question}
              onChange={(e) => setForm((f) => ({ ...f, question: e.target.value }))}
              rows={2}
              placeholder="평가위원 질문..."
              className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 resize-none"
              required
            />
          </div>

          <div>
            <label className="text-[10px] text-[#8c8c8c] block mb-1">답변</label>
            <textarea
              value={form.answer}
              onChange={(e) => setForm((f) => ({ ...f, answer: e.target.value }))}
              rows={3}
              placeholder="답변 내용..."
              className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 resize-none"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-[#8c8c8c] block mb-1">카테고리</label>
              <select
                value={form.category}
                onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as QARecordCreate["category"] }))}
                className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-[#8c8c8c] block mb-1">평가위원 반응</label>
              <select
                value={form.evaluator_reaction ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, evaluator_reaction: e.target.value || null }))}
                className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40"
              >
                {REACTIONS.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-[10px] text-[#8c8c8c] block mb-1">메모 (선택)</label>
            <input
              type="text"
              value={form.memo ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, memo: e.target.value || null }))}
              placeholder="참고 사항..."
              className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-1.5 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !form.question.trim() || !form.answer.trim()}
            className="w-full bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] font-semibold rounded-lg py-2 text-sm transition-colors"
          >
            {submitting ? "저장 중..." : editingId ? "수정" : "등록"}
          </button>
        </form>
      )}
    </div>
  );
}
