"use client";

/**
 * F-05: 팀 프로필 + 검색 조건 프리셋 설정 페이지
 * - 온보딩 가드: 미인증 → /login, 팀 미가입 → 안내
 * - 탭 1: 팀 프로필 (AI 매칭 컨텍스트)
 * - 탭 2: 검색 조건 프리셋 CRUD
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import {
  api,
  BidProfile,
  BidProfileInput,
  SearchPreset,
  SearchPresetInput,
} from "@/lib/api";

// ── 태그 입력 컴포넌트 ──────────────────────────────────────

function TagInput({
  tags,
  onChange,
  placeholder,
}: {
  tags: string[];
  onChange: (t: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");

  function addTag() {
    const v = input.trim();
    if (v && !tags.includes(v)) onChange([...tags, v]);
    setInput("");
  }

  return (
    <div className="flex flex-wrap gap-1.5 p-2 bg-[#1c1c1c] border border-[#262626] rounded-lg min-h-[40px]">
      {tags.map((t) => (
        <span
          key={t}
          className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-[#262626] text-[#ededed]"
        >
          {t}
          <button
            onClick={() => onChange(tags.filter((x) => x !== t))}
            className="text-[#5c5c5c] hover:text-red-400 leading-none"
          >
            ×
          </button>
        </span>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addTag(); } }}
        onBlur={addTag}
        placeholder={tags.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[80px] bg-transparent text-xs text-[#ededed] placeholder-[#5c5c5c] outline-none"
      />
    </div>
  );
}

// ── 메인 페이지 ──────────────────────────────────────────────

export default function BidsSettingsPage() {
  const router = useRouter();
  const [teamId, setTeamId] = useState<string | null>(null);
  const [tab, setTab] = useState<"profile" | "presets">("profile");
  const [loading, setLoading] = useState(true);
  const [noTeam, setNoTeam] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const [hasActivePreset, setHasActivePreset] = useState(false);

  useEffect(() => {
    (async () => {
      const { data } = await createClient().auth.getSession();
      if (!data.session) { router.push("/login"); return; }
      try {
        const res = await api.teams.list();
        const team = res.teams[0];
        if (!team) { setNoTeam(true); setLoading(false); return; }
        setTeamId(team.team_id);

        // 온보딩 상태 확인
        const [profileRes, presetRes] = await Promise.allSettled([
          api.bids.getProfile(team.team_id),
          api.bids.listPresets(team.team_id),
        ]);
        if (profileRes.status === "fulfilled") setHasProfile(!!profileRes.value.data);
        if (presetRes.status === "fulfilled") setHasActivePreset(presetRes.value.data.some((p) => p.is_active));
      } catch {
        setNoTeam(true);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return <div className="flex-1 flex items-center justify-center"><p className="text-sm text-[#5c5c5c]">불러오는 중...</p></div>;
  }

  if (noTeam) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl">👥</div>
        <h3 className="text-sm font-semibold text-[#ededed]">팀이 없습니다</h3>
        <p className="text-xs text-[#8c8c8c] max-w-xs">공고 추천을 사용하려면 먼저 팀을 생성하세요.</p>
        <button
          onClick={() => router.push("/admin")}
          className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          팀 생성하기
        </button>
      </div>
    );
  }

  // 스텝 완료 상태 업데이트용 콜백
  function onProfileSaved() {
    setHasProfile(true);
    if (!hasActivePreset) setTab("presets");
  }
  function onPresetActivated() {
    setHasActivePreset(true);
  }

  const step1Done = hasProfile;
  const step2Done = hasActivePreset;
  const currentStep = !step1Done ? 1 : !step2Done ? 2 : 3;

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <h1 className="text-sm font-semibold text-[#ededed]">공고 추천 설정</h1>
        <p className="text-xs text-[#8c8c8c] mt-0.5">팀 프로필과 검색 조건을 설정합니다</p>
      </div>

      {/* 온보딩 진행 상태 */}
      <div className="border-b border-[#262626] px-6 py-2.5 shrink-0 bg-[#111111]">
        <div className="flex items-center gap-2">
          {([
            { step: 1, label: "팀 프로필 저장", done: step1Done },
            { step: 2, label: "검색 조건 활성화", done: step2Done },
            { step: 3, label: "공고 수집", done: false },
          ] as const).map((s, i, arr) => (
            <div key={s.step} className="flex items-center gap-2">
              <div className={`flex items-center gap-1.5 ${s.done ? "text-[#3ecf8e]" : currentStep === s.step ? "text-[#ededed]" : "text-[#5c5c5c]"}`}>
                <span className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center border shrink-0 font-bold ${s.done ? "bg-[#3ecf8e] border-[#3ecf8e] text-black" : currentStep === s.step ? "border-[#ededed]" : "border-[#3c3c3c]"}`}>
                  {s.done ? "✓" : s.step}
                </span>
                <span className="text-xs whitespace-nowrap">{s.label}</span>
              </div>
              {i < arr.length - 1 && <span className="text-[#3c3c3c] text-xs">→</span>}
            </div>
          ))}
          {currentStep === 3 && (
            <a href="/bids" className="ml-auto text-xs text-[#3ecf8e] hover:underline">공고 수집하러 가기 →</a>
          )}
        </div>
      </div>

      {/* 탭 */}
      <div className="border-b border-[#262626] px-6 shrink-0">
        <div className="flex">
          {(["profile", "presets"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                tab === t ? "border-[#3ecf8e] text-[#ededed]" : "border-transparent text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {t === "profile" ? "팀 프로필" : "검색 조건 프리셋"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-5">
        {tab === "profile" ? (
          <ProfileTab teamId={teamId!} onSaved={onProfileSaved} />
        ) : (
          <PresetsTab teamId={teamId!} onPresetActivated={onPresetActivated} />
        )}
      </div>
    </div>
  );
}

// ── 탭 1: 팀 프로필 ──────────────────────────────────────────

function ProfileTab({ teamId, onSaved }: { teamId: string; onSaved?: () => void }) {
  const [profile, setProfile] = useState<BidProfileInput>({
    expertise_areas: [],
    tech_keywords: [],
    past_projects: "",
    company_size: "",
    certifications: [],
    business_registration_type: "",
    employee_count: undefined,
    founded_year: undefined,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await api.bids.getProfile(teamId);
        if (res.data) {
          setProfile({
            expertise_areas: res.data.expertise_areas,
            tech_keywords: res.data.tech_keywords,
            past_projects: res.data.past_projects,
            company_size: res.data.company_size ?? "",
            certifications: res.data.certifications,
            business_registration_type: res.data.business_registration_type ?? "",
            employee_count: res.data.employee_count ?? undefined,
            founded_year: res.data.founded_year ?? undefined,
          });
        }
      } catch {
        // 프로필 없음 — 빈 상태
      } finally {
        setLoading(false);
      }
    })();
  }, [teamId]);

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      await api.bids.upsertProfile(teamId, profile);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      onSaved?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="text-sm text-[#5c5c5c]">불러오는 중...</div>;

  return (
    <div className="max-w-2xl space-y-5">
      <div className="rounded-lg border border-[#262626] bg-[#111111] p-5 space-y-4">
        <Field label="전문분야" hint="Enter 또는 쉼표로 추가">
          <TagInput
            tags={profile.expertise_areas}
            onChange={(v) => setProfile((p) => ({ ...p, expertise_areas: v }))}
            placeholder="AI/ML, 컨설팅, 교육, IT개발..."
          />
        </Field>

        <Field label="보유기술 키워드" hint="Enter 또는 쉼표로 추가">
          <TagInput
            tags={profile.tech_keywords}
            onChange={(v) => setProfile((p) => ({ ...p, tech_keywords: v }))}
            placeholder="Python, LLM, React, AWS..."
          />
        </Field>

        <Field label="수행실적 요약" hint="자유 텍스트, AI 자격 판정에 활용됩니다">
          <textarea
            value={profile.past_projects}
            onChange={(e) => setProfile((p) => ({ ...p, past_projects: e.target.value }))}
            rows={4}
            placeholder="예: 행정안전부 AI 챗봇 구축 (2023, 3억), 교육부 LLM 교육 플랫폼 개발 (2024, 5억)..."
            className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] resize-none focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
          />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="기업 규모" hint="공공조달 자격 판정 기준">
            <select
              value={profile.company_size ?? ""}
              onChange={(e) => setProfile((p) => ({ ...p, company_size: e.target.value }))}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
            >
              <option value="">선택 안 함</option>
              <option value="소기업">소기업 (상시 50인 미만)</option>
              <option value="중기업">중기업 (50~300인)</option>
              <option value="중견기업">중견기업</option>
              <option value="대기업">대기업</option>
            </select>
          </Field>

          <Field label="사업자 유형" hint="일부 공고는 특정 유형만 참여 가능">
            <select
              value={profile.business_registration_type ?? ""}
              onChange={(e) => setProfile((p) => ({ ...p, business_registration_type: e.target.value }))}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
            >
              <option value="">선택 안 함</option>
              <option value="개인사업자">개인사업자</option>
              <option value="법인사업자">법인사업자</option>
              <option value="중소기업">중소기업 (확인서 보유)</option>
              <option value="중견기업">중견기업</option>
              <option value="벤처기업">벤처기업 (인증 보유)</option>
            </select>
          </Field>

          <Field label="임직원 수">
            <input
              type="number"
              min={0}
              value={profile.employee_count ?? ""}
              onChange={(e) => setProfile((p) => ({ ...p, employee_count: e.target.value ? Number(e.target.value) : undefined }))}
              placeholder="예: 25"
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
            />
          </Field>

          <Field label="설립연도">
            <input
              type="number"
              min={1900}
              max={2100}
              value={profile.founded_year ?? ""}
              onChange={(e) => setProfile((p) => ({ ...p, founded_year: e.target.value ? Number(e.target.value) : undefined }))}
              placeholder="예: 2018"
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
            />
          </Field>
        </div>

        <Field label="보유 인증·자격" hint="Enter 또는 쉼표로 추가">
          <TagInput
            tags={profile.certifications}
            onChange={(v) => setProfile((p) => ({ ...p, certifications: v }))}
            placeholder="ISO27001, GS인증, SW기업확인서..."
          />
        </Field>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        onClick={handleSave}
        disabled={saving}
        className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-6 py-2 text-sm transition-colors"
      >
        {saving ? "저장 중..." : saved ? "저장됨 ✓" : "저장"}
      </button>
    </div>
  );
}

// ── 탭 2: 검색 프리셋 ────────────────────────────────────────

const DATE_RANGE_OPTIONS = [
  { value: 7,   label: "1주일 이내" },
  { value: 14,  label: "2주일 이내" },
  { value: 30,  label: "1개월 이내" },
  { value: 90,  label: "3개월 이내" },
  { value: 0,   label: "제한 없음" },
] as const;

const DEFAULT_PRESET: SearchPresetInput = {
  name: "",
  keywords: [],
  min_budget: 100_000_000,
  min_days_remaining: 5,
  bid_types: ["용역"],
  preferred_agencies: [],
  announce_date_range_days: 14,
};

function PresetsTab({ teamId, onPresetActivated }: { teamId: string; onPresetActivated?: () => void }) {
  const [presets, setPresets] = useState<SearchPreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null); // preset id or "new"
  const [form, setForm] = useState<SearchPresetInput>(DEFAULT_PRESET);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      const res = await api.bids.listPresets(teamId);
      setPresets(res.data);
    } catch {
      setError("프리셋 목록 조회 실패");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [teamId]);

  function startNew() {
    setForm(DEFAULT_PRESET);
    setEditing("new");
    setError("");
  }

  function startEdit(preset: SearchPreset) {
    setForm({
      name: preset.name,
      keywords: preset.keywords,
      min_budget: preset.min_budget,
      min_days_remaining: preset.min_days_remaining,
      bid_types: preset.bid_types,
      preferred_agencies: preset.preferred_agencies,
      announce_date_range_days: preset.announce_date_range_days ?? 14,
    });
    setEditing(preset.id);
    setError("");
  }

  async function handleSave() {
    if (!form.name.trim() || form.keywords.length === 0) {
      setError("프리셋명과 키워드는 필수입니다."); return;
    }
    setSaving(true);
    setError("");
    try {
      if (editing === "new") {
        await api.bids.createPreset(teamId, form);
      } else if (editing) {
        await api.bids.updatePreset(teamId, editing, form);
      }
      setEditing(null);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("이 프리셋을 삭제하시겠습니까?")) return;
    try {
      await api.bids.deletePreset(teamId, id);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  async function handleActivate(id: string) {
    try {
      await api.bids.activatePreset(teamId, id);
      await load();
      onPresetActivated?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "활성화 실패");
    }
  }

  if (loading) return <div className="text-sm text-[#5c5c5c]">불러오는 중...</div>;

  return (
    <div className="max-w-2xl space-y-4">
      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* 프리셋 목록 */}
      {presets.length > 0 && !editing && (
        <div className="space-y-2">
          {presets.map((p) => (
            <div key={p.id} className="rounded-lg border border-[#262626] bg-[#111111] p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-[#ededed]">{p.name}</span>
                    {p.is_active && (
                      <span className="text-xs px-1.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-900">
                        활성
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[#5c5c5c]">
                    키워드: {p.keywords.join(", ")} · 최소 {(p.min_budget / 100_000_000).toFixed(1)}억 · 잔여 {p.min_days_remaining}일
                    {" · "}
                    {p.announce_date_range_days > 0
                      ? `최근 ${DATE_RANGE_OPTIONS.find(o => o.value === p.announce_date_range_days)?.label ?? `${p.announce_date_range_days}일`}`
                      : "기간 제한 없음"}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {!p.is_active && (
                    <button
                      onClick={() => handleActivate(p.id)}
                      className="text-xs px-2.5 py-1 rounded-md border border-[#262626] text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#1a1a1a] transition-colors"
                    >
                      활성화
                    </button>
                  )}
                  <button
                    onClick={() => startEdit(p)}
                    className="text-xs px-2.5 py-1 rounded-md border border-[#262626] text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#1a1a1a] transition-colors"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="text-xs px-2.5 py-1 rounded-md border border-red-900/50 text-red-400/70 hover:text-red-400 hover:bg-red-950/40 transition-colors"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 편집 폼 */}
      {editing ? (
        <div className="rounded-lg border border-[#3ecf8e]/30 bg-[#111111] p-5 space-y-4">
          <h3 className="text-xs font-semibold text-[#ededed]">
            {editing === "new" ? "새 프리셋 추가" : "프리셋 수정"}
          </h3>

          <Field label="프리셋명" required>
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="예: AI분야, 기본조건"
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
            />
          </Field>

          <Field label="검색 키워드" hint="Enter로 추가, 최대 5개" required>
            <TagInput
              tags={form.keywords}
              onChange={(v) => setForm((f) => ({ ...f, keywords: v.slice(0, 5) }))}
              placeholder="AI, LLM, 교육..."
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="최소 사업금액 (억원)">
              <input
                type="number"
                min={0}
                step={0.5}
                value={form.min_budget / 100_000_000}
                onChange={(e) => setForm((f) => ({ ...f, min_budget: Number(e.target.value) * 100_000_000 }))}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
              />
            </Field>

            <Field label="최소 잔여일 (일)">
              <input
                type="number"
                min={1}
                max={30}
                value={form.min_days_remaining}
                onChange={(e) => setForm((f) => ({ ...f, min_days_remaining: Number(e.target.value) }))}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
              />
            </Field>

            <Field label="검색 대상 기간" hint="공고 등록일 기준">
              <select
                value={form.announce_date_range_days}
                onChange={(e) => setForm((f) => ({ ...f, announce_date_range_days: Number(e.target.value) }))}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
              >
                {DATE_RANGE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="공고 종류">
            <div className="flex gap-3">
              {["용역", "공사", "물품"].map((type) => (
                <label key={type} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.bid_types.includes(type)}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        bid_types: e.target.checked
                          ? [...f.bid_types, type]
                          : f.bid_types.filter((t) => t !== type),
                      }))
                    }
                    className="accent-[#3ecf8e]"
                  />
                  <span className="text-xs text-[#ededed]">{type}</span>
                </label>
              ))}
            </div>
            {form.bid_types.some((t) => t !== "용역") && (
              <p className="text-xs text-orange-400 mt-1">공사·물품 공고는 일반 용역과 성격이 다를 수 있습니다.</p>
            )}
          </Field>

          <Field label="우선 발주처" hint="Enter로 추가 · 비워두면 전체 기관 대상">
            <TagInput
              tags={form.preferred_agencies}
              onChange={(v) => setForm((f) => ({ ...f, preferred_agencies: v }))}
              placeholder="행정안전부, 교육부, 한국지능정보사회진흥원..."
            />
          </Field>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-5 py-1.5 text-sm transition-colors"
            >
              {saving ? "저장 중..." : "저장"}
            </button>
            <button
              onClick={() => { setEditing(null); setError(""); }}
              className="px-4 py-1.5 text-sm text-[#8c8c8c] border border-[#262626] rounded-lg hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors"
            >
              취소
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={startNew}
          className="w-full py-2.5 rounded-lg border border-dashed border-[#262626] text-xs text-[#5c5c5c] hover:border-[#3ecf8e] hover:text-[#3ecf8e] transition-colors"
        >
          + 새 프리셋 추가
        </button>
      )}
    </div>
  );
}

// ── 공통 필드 래퍼 ────────────────────────────────────────────

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-[#8c8c8c] mb-1.5">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
        {hint && <span className="font-normal text-[#5c5c5c] ml-1.5">{hint}</span>}
      </label>
      {children}
    </div>
  );
}
