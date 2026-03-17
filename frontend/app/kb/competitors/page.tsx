"use client";

/**
 * 경쟁사 DB 관리 (§13 CompetitorIntelligence)
 * /kb/competitors
 */

import { useCallback, useEffect, useState } from "react";
import AppSidebar from "@/components/AppSidebar";
import { api, type KbCompetitor, type KbCompetitorCreate } from "@/lib/api";

const SCALE_OPTS = [
  { value: "", label: "전체" },
  { value: "대기업", label: "대기업" },
  { value: "중견", label: "중견" },
  { value: "중소", label: "중소" },
];

export default function CompetitorsPage() {
  const [items, setItems] = useState<KbCompetitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterScale, setFilterScale] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<KbCompetitorCreate>({ company_name: "" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterScale) params.scale = filterScale;
      const res = await api.kb.competitors.list(params);
      setItems(res.items);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, [filterScale]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.company_name) return;
    setSaving(true);
    try {
      await api.kb.competitors.create(form);
      setForm({ company_name: "" });
      setShowForm(false);
      await load();
    } catch (err) { alert(err instanceof Error ? err.message : "저장 실패"); }
    finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("삭제하시겠습니까?")) return;
    await api.kb.competitors.delete(id);
    await load();
  }

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">경쟁사 DB</h1>
          <button onClick={() => setShowForm(!showForm)} className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90">+ 경쟁사 등록</button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {/* 필터 */}
          <div className="flex gap-2">
            {SCALE_OPTS.map((s) => (
              <button key={s.value} onClick={() => setFilterScale(s.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterScale === s.value ? "bg-[#3ecf8e] text-[#0f0f0f] font-semibold" : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]"}`}>
                {s.label}
              </button>
            ))}
          </div>

          {/* 등록 폼 */}
          {showForm && (
            <form onSubmit={handleCreate} className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">업체명 *</label>
                  <input type="text" required value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">규모</label>
                  <select value={form.scale ?? ""} onChange={(e) => setForm({ ...form, scale: e.target.value || undefined })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none">
                    <option value="">선택</option>
                    {SCALE_OPTS.filter((s) => s.value).map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">주력 분야</label>
                  <input type="text" value={form.primary_area ?? ""} onChange={(e) => setForm({ ...form, primary_area: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none" placeholder="SI/컨설팅/SW개발" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">강점</label>
                  <textarea value={form.strengths ?? ""} onChange={(e) => setForm({ ...form, strengths: e.target.value })} rows={2}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none resize-none" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">약점</label>
                  <textarea value={form.weaknesses ?? ""} onChange={(e) => setForm({ ...form, weaknesses: e.target.value })} rows={2}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none resize-none" />
                </div>
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
            <p className="text-sm text-[#5c5c5c] py-8 text-center">등록된 경쟁사가 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-[#1c1c1c] border border-[#262626] rounded-xl px-4 py-3 flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[#ededed]">{item.company_name}</span>
                      {item.scale && <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#262626] text-[#8c8c8c]">{item.scale}</span>}
                    </div>
                    <div className="flex gap-3 text-[10px] text-[#8c8c8c]">
                      {item.primary_area && <span>{item.primary_area}</span>}
                      {item.price_pattern && <span>가격패턴: {item.price_pattern}</span>}
                      {item.avg_win_rate != null && <span>수주율: {Math.round(item.avg_win_rate * 100)}%</span>}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(item.id)} className="px-2.5 py-1 text-[10px] rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 shrink-0">삭제</button>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
