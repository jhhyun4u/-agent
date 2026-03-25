"use client";

/**
 * 발주기관 DB 관리 (§13 ClientIntelligence)
 * /kb/clients
 */

import { useCallback, useEffect, useState } from "react";
import { api, type KbClient, type KbClientCreate } from "@/lib/api";

const REL_OPTS = [
  { value: "", label: "전체" },
  { value: "strong", label: "우호적" },
  { value: "neutral", label: "중립" },
  { value: "weak", label: "미약" },
  { value: "new", label: "신규" },
];

const REL_BADGE: Record<string, string> = {
  strong: "bg-[#3ecf8e]/15 text-[#3ecf8e]",
  neutral: "bg-[#262626] text-[#8c8c8c]",
  weak: "bg-amber-500/15 text-amber-400",
  new: "bg-blue-500/15 text-blue-400",
};

export default function ClientsPage() {
  const [items, setItems] = useState<KbClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterRel, setFilterRel] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<KbClientCreate>({ client_name: "", relationship: "neutral" });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterRel) params.relationship = filterRel;
      const res = await api.kb.clients.list(params);
      setItems(res.items);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, [filterRel]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.client_name) return;
    setSaving(true);
    try {
      await api.kb.clients.create(form);
      setForm({ client_name: "", relationship: "neutral" });
      setShowForm(false);
      await load();
    } catch (err) { alert(err instanceof Error ? err.message : "저장 실패"); }
    finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    if (!confirm("삭제하시겠습니까?")) return;
    await api.kb.clients.delete(id);
    await load();
  }

  return (
    <>
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">발주기관 DB</h1>
          <button onClick={() => setShowForm(!showForm)} className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90">+ 기관 등록</button>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {/* 필터 */}
          <div className="flex gap-2">
            {REL_OPTS.map((r) => (
              <button key={r.value} onClick={() => setFilterRel(r.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterRel === r.value ? "bg-[#3ecf8e] text-[#0f0f0f] font-semibold" : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]"}`}>
                {r.label}
              </button>
            ))}
          </div>

          {/* 등록 폼 */}
          {showForm && (
            <form onSubmit={handleCreate} className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">기관명 *</label>
                  <input type="text" required value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">유형</label>
                  <input type="text" value={form.client_type ?? ""} onChange={(e) => setForm({ ...form, client_type: e.target.value })} placeholder="중앙부처/지자체/공기업"
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">관계</label>
                  <select value={form.relationship ?? "neutral"} onChange={(e) => setForm({ ...form, relationship: e.target.value })}
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none">
                    {REL_OPTS.filter((r) => r.value).map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">평가 성향</label>
                  <input type="text" value={form.eval_tendency ?? ""} onChange={(e) => setForm({ ...form, eval_tendency: e.target.value })} placeholder="기술 중시/가격 중시"
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs text-[#8c8c8c] mb-1">소재지</label>
                  <input type="text" value={form.location ?? ""} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="서울/세종/대전..."
                    className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none" />
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
            <p className="text-sm text-[#5c5c5c] py-8 text-center">등록된 발주기관이 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-[#1c1c1c] border border-[#262626] rounded-xl px-4 py-3 flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[#ededed]">{item.client_name}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${REL_BADGE[item.relationship] ?? REL_BADGE.neutral}`}>{item.relationship}</span>
                    </div>
                    <div className="flex gap-3 text-[10px] text-[#8c8c8c]">
                      {item.client_type && <span>{item.client_type}</span>}
                      {item.scale && <span>{item.scale}</span>}
                      {item.eval_tendency && <span>평가: {item.eval_tendency}</span>}
                      {item.location && <span>{item.location}</span>}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(item.id)} className="px-2.5 py-1 text-[10px] rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 shrink-0">삭제</button>
                </div>
              ))}
            </div>
          )}
        </main>
    </>
  );
}
