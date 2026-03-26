"use client";

/**
 * 콘텐츠 라이브러리 관리 (§13 ContentLibraryView)
 * /kb/content
 */

import { useCallback, useEffect, useState } from "react";
import { api, type KbContent, type KbContentCreate } from "@/lib/api";
import KbUsageHistory from "@/components/KbUsageHistory";

const CONTENT_TYPES = [
  { value: "", label: "전체" },
  { value: "section_block", label: "섹션 블록" },
  { value: "methodology", label: "방법론" },
  { value: "track_record", label: "실적" },
  { value: "company_intro", label: "회사 소개" },
];

const STATUS_OPTS = [
  { value: "", label: "전체" },
  { value: "draft", label: "초안" },
  { value: "published", label: "승인됨" },
  { value: "archived", label: "보관됨" },
];

export default function ContentPage() {
  const [items, setItems] = useState<KbContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<KbContentCreate>({ title: "", body: "", type: "section_block", tags: [] });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterType) params.type = filterType;
      if (filterStatus) params.status = filterStatus;
      const res = await api.kb.content.list(params);
      setItems(res.data);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, [filterType, filterStatus]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title || !form.body) return;
    setSaving(true);
    try {
      await api.kb.content.create(form);
      setForm({ title: "", body: "", type: "section_block", tags: [] });
      setShowForm(false);
      await load();
    } catch (err) { alert(err instanceof Error ? err.message : "저장 실패"); }
    finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("이 콘텐츠를 보관 처리하시겠습니까?")) return;
    await api.kb.content.delete(id);
    await load();
  }

  async function handleApprove(id: string) {
    await api.kb.content.approve(id);
    await load();
  }

  function statusBadge(status: string) {
    const m: Record<string, string> = {
      draft: "bg-[#262626] text-[#8c8c8c]",
      published: "bg-[#3ecf8e]/15 text-[#3ecf8e]",
      archived: "bg-red-500/15 text-red-400",
    };
    return <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${m[status] ?? m.draft}`}>{status}</span>;
  }

  return (
    <>
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">콘텐츠 라이브러리</h1>
          <button onClick={() => setShowForm(!showForm)} className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors">
            + 콘텐츠 등록
          </button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {/* 필터 */}
          <div className="flex gap-2">
            {CONTENT_TYPES.map((t) => (
              <button key={t.value} onClick={() => setFilterType(t.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterType === t.value ? "bg-[#3ecf8e] text-[#0f0f0f] font-semibold" : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626] hover:border-[#3c3c3c]"}`}>
                {t.label}
              </button>
            ))}
            <div className="w-px bg-[#262626] mx-1" />
            {STATUS_OPTS.map((s) => (
              <button key={s.value} onClick={() => setFilterStatus(s.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterStatus === s.value ? "bg-[#262626] text-[#ededed] font-semibold" : "text-[#5c5c5c] hover:text-[#8c8c8c]"}`}>
                {s.label}
              </button>
            ))}
          </div>

          {/* 등록 폼 */}
          {showForm && (
            <form onSubmit={handleCreate} className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">제목 *</label>
                  <input type="text" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">유형</label>
                  <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none">
                    {CONTENT_TYPES.filter((t) => t.value).map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1">본문 *</label>
                <textarea required value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} rows={4}
                  className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 resize-none" />
              </div>
              <div className="flex gap-2">
                <button type="submit" disabled={saving} className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] disabled:opacity-50">{saving ? "저장 중..." : "저장"}</button>
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-xs rounded-lg bg-[#262626] text-[#8c8c8c]">취소</button>
              </div>
            </form>
          )}

          {/* 목록 */}
          {loading ? (
            <p className="text-sm text-[#8c8c8c] py-8 text-center">로딩 중...</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-[#5c5c5c] py-8 text-center">등록된 콘텐츠가 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-[#1c1c1c] border border-[#262626] rounded-xl px-4 py-3 flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[#ededed] truncate">{item.title}</span>
                      {statusBadge(item.status)}
                    </div>
                    <div className="flex gap-3 text-[10px] text-[#8c8c8c]">
                      <span>{item.type}</span>
                      {item.quality_score != null && <span>품질: {item.quality_score}점</span>}
                      {item.reuse_count > 0 && <span>재사용: {item.reuse_count}회</span>}
                      {item.industry && <span>{item.industry}</span>}
                      {item.tags.length > 0 && <span>{item.tags.join(", ")}</span>}
                    </div>
                    {/* 권고 #5: KB ↔ 제안서 양방향 링크 */}
                    <KbUsageHistory contentId={item.id} contentTitle={item.title} />
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    {item.status === "draft" && (
                      <button onClick={() => handleApprove(item.id)} className="px-2.5 py-1 text-[10px] rounded border border-[#3ecf8e]/30 text-[#3ecf8e] hover:bg-[#3ecf8e]/10 transition-colors">승인</button>
                    )}
                    <button onClick={() => handleDelete(item.id)} className="px-2.5 py-1 text-[10px] rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors">보관</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
    </>
  );
}
