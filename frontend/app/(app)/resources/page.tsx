"use client";

/**
 * 자료 관리 페이지
 * - 섹션 라이브러리: CRUD, 카테고리 필터, 검색, 스코프 탭
 * - 회사 자료: 준비 중 플레이스홀더
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api, AssetItem, FormTemplate, Section } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

// ── 카테고리 정의 ──────────────────────────────────────────────────────

const CATEGORIES = [
  { value: "", label: "전체" },
  { value: "company_intro", label: "회사소개" },
  { value: "track_record", label: "수행실적" },
  { value: "methodology", label: "기술방법론" },
  { value: "organization", label: "조직인력" },
  { value: "schedule", label: "추진일정" },
  { value: "cost", label: "원가예산" },
  { value: "other", label: "기타" },
];

const CATEGORY_LABELS: Record<string, string> = {
  company_intro: "회사소개",
  track_record: "수행실적",
  methodology: "기술방법론",
  organization: "조직인력",
  schedule: "추진일정",
  cost: "원가예산",
  other: "기타",
};

const SCOPE_TABS = [
  { value: "all", label: "전체" },
  { value: "team", label: "팀" },
  { value: "personal", label: "나의" },
];

// ── 빈 모달 폼 ────────────────────────────────────────────────────────

interface SectionForm {
  title: string;
  category: string;
  content: string;
  tags: string;
  is_public: boolean;
}

const EMPTY_FORM: SectionForm = {
  title: "",
  category: "company_intro",
  content: "",
  tags: "",
  is_public: false,
};

// ── 공통서식 업로드 폼 ─────────────────────────────────────────────────

interface TemplateUploadForm {
  title: string;
  agency: string;
  category: string;
  description: string;
  is_public: boolean;
  file: File | null;
}

const EMPTY_TEMPLATE_FORM: TemplateUploadForm = {
  title: "",
  agency: "",
  category: "",
  description: "",
  is_public: true,
  file: null,
};

// ── 페이지 컴포넌트 ───────────────────────────────────────────────────

export default function ResourcesPage() {
  const [pageTab, setPageTab] = useState<"sections" | "company" | "templates">("sections");
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [scope, setScope] = useState("all");
  const [category, setCategory] = useState("");
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [currentUserId, setCurrentUserId] = useState("");

  // 공통서식 상태
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templateAgency, setTemplateAgency] = useState("");
  const [templateCategory, setTemplateCategory] = useState("");
  const [uploadingTemplate, setUploadingTemplate] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateUploadForm, setTemplateUploadForm] = useState<TemplateUploadForm>(EMPTY_TEMPLATE_FORM);
  const [templateFormError, setTemplateFormError] = useState("");

  // 모달 상태
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Section | null>(null);
  const [form, setForm] = useState<SectionForm>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  // 검색어 디바운스
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedQ(q), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [q]);

  // 현재 유저 ID
  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data }) => setCurrentUserId(data.user?.id ?? ""));
  }, []);

  // 섹션 목록 로드
  const loadSections = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.sections.list({
        scope,
        category: category || undefined,
        q: debouncedQ || undefined,
      });
      setSections(res.sections);
    } catch (e) {
      setError(e instanceof Error ? e.message : "목록 로드 실패");
    } finally {
      setLoading(false);
    }
  }, [scope, category, debouncedQ]);

  useEffect(() => {
    if (pageTab === "sections") loadSections();
  }, [pageTab, loadSections]);

  // 공통서식 목록 로드
  const loadTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const res = await api.formTemplates.list({
        agency: templateAgency || undefined,
        category: templateCategory || undefined,
      });
      setTemplates(res.templates);
    } catch {
      // 오류 시 빈 목록 유지
    } finally {
      setTemplatesLoading(false);
    }
  }, [templateAgency, templateCategory]);

  useEffect(() => {
    if (pageTab === "templates") loadTemplates();
  }, [pageTab, loadTemplates]);

  // 공통서식 업로드
  async function handleTemplateUpload() {
    if (!templateUploadForm.title.trim()) {
      setTemplateFormError("제목을 입력하세요.");
      return;
    }
    if (!templateUploadForm.file) {
      setTemplateFormError("파일을 선택하세요.");
      return;
    }
    setUploadingTemplate(true);
    setTemplateFormError("");
    try {
      const fd = new FormData();
      fd.append("title", templateUploadForm.title.trim());
      if (templateUploadForm.agency) fd.append("agency", templateUploadForm.agency.trim());
      if (templateUploadForm.category) fd.append("category", templateUploadForm.category.trim());
      if (templateUploadForm.description) fd.append("description", templateUploadForm.description.trim());
      fd.append("is_public", String(templateUploadForm.is_public));
      fd.append("file", templateUploadForm.file);
      await api.formTemplates.upload(fd);
      setShowTemplateModal(false);
      setTemplateUploadForm(EMPTY_TEMPLATE_FORM);
      loadTemplates();
    } catch (e) {
      setTemplateFormError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setUploadingTemplate(false);
    }
  }

  // 공통서식 삭제
  async function handleTemplateDelete(id: string) {
    if (!confirm("서식을 삭제하시겠습니까?")) return;
    try {
      await api.formTemplates.delete(id);
      setTemplates((prev) => prev.filter((t) => t.id !== id));
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  // 모달 열기
  function openCreate() {
    setEditTarget(null);
    setForm(EMPTY_FORM);
    setFormError("");
    setModalOpen(true);
  }

  function openEdit(s: Section) {
    setEditTarget(s);
    setForm({
      title: s.title,
      category: s.category,
      content: s.content,
      tags: s.tags.join(", "),
      is_public: s.is_public,
    });
    setFormError("");
    setModalOpen(true);
  }

  // 저장
  async function handleSave() {
    if (!form.title.trim()) {
      setFormError("제목을 입력하세요.");
      return;
    }
    if (!form.content.trim()) {
      setFormError("내용을 입력하세요.");
      return;
    }
    setSaving(true);
    setFormError("");
    try {
      const tags = form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      if (editTarget) {
        await api.sections.update(editTarget.id, {
          title: form.title,
          category: form.category,
          content: form.content,
          tags,
          is_public: form.is_public,
        });
      } else {
        await api.sections.create({
          title: form.title,
          category: form.category,
          content: form.content,
          tags,
          is_public: form.is_public,
        });
      }
      setModalOpen(false);
      loadSections();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  // 삭제
  async function handleDelete(id: string) {
    if (!confirm("섹션을 삭제하시겠습니까?")) return;
    try {
      await api.sections.delete(id);
      loadSections();
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  return (
    <>
        {/* 헤더 */}
        <header className="border-b border-[#262626] px-6 py-4 bg-[#111111] shrink-0">
          <h1 className="text-base font-semibold text-[#ededed]">자료 관리</h1>
        </header>

        {/* 페이지 탭 */}
        <div className="border-b border-[#262626] px-6 bg-[#111111] shrink-0">
          <div className="flex gap-0">
            {(["sections", "company", "templates"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setPageTab(tab)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  pageTab === tab
                    ? "border-[#3ecf8e] text-[#ededed]"
                    : "border-transparent text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {tab === "sections" ? "섹션 라이브러리" : tab === "company" ? "회사 자료" : "공통서식"}
              </button>
            ))}
          </div>
        </div>

        {/* 콘텐츠 */}
        <div className="flex-1 overflow-y-auto">
          {pageTab === "sections" ? (
            <SectionsTab
              sections={sections}
              loading={loading}
              error={error}
              scope={scope}
              setScope={setScope}
              category={category}
              setCategory={setCategory}
              q={q}
              setQ={setQ}
              currentUserId={currentUserId}
              onEdit={openEdit}
              onDelete={handleDelete}
              onAdd={openCreate}
            />
          ) : pageTab === "company" ? (
            <CompanyTab />
          ) : (
            <TemplatesTab
              templates={templates}
              loading={templatesLoading}
              agency={templateAgency}
              setAgency={setTemplateAgency}
              category={templateCategory}
              setCategory={setTemplateCategory}
              onSearch={loadTemplates}
              onDelete={handleTemplateDelete}
              onAdd={() => { setTemplateFormError(""); setTemplateUploadForm(EMPTY_TEMPLATE_FORM); setShowTemplateModal(true); }}
            />
          )}
        </div>

      {/* 공통서식 업로드 모달 */}
      {showTemplateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#262626]">
              <h2 className="text-sm font-semibold text-[#ededed]">서식 추가</h2>
              <button
                onClick={() => setShowTemplateModal(false)}
                className="text-[#8c8c8c] hover:text-[#ededed] text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {templateFormError && (
                <p className="text-xs text-red-400 bg-red-400/10 rounded-md px-3 py-2">
                  {templateFormError}
                </p>
              )}

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">제목 *</label>
                <input
                  type="text"
                  value={templateUploadForm.title}
                  onChange={(e) => setTemplateUploadForm((f) => ({ ...f, title: e.target.value }))}
                  placeholder="서식 제목"
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">발행기관</label>
                <input
                  type="text"
                  value={templateUploadForm.agency}
                  onChange={(e) => setTemplateUploadForm((f) => ({ ...f, agency: e.target.value }))}
                  placeholder="예: 행안부, 과기부"
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">카테고리</label>
                <input
                  type="text"
                  value={templateUploadForm.category}
                  onChange={(e) => setTemplateUploadForm((f) => ({ ...f, category: e.target.value }))}
                  placeholder="예: 제안요청서, 계약서"
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">설명</label>
                <textarea
                  value={templateUploadForm.description}
                  onChange={(e) => setTemplateUploadForm((f) => ({ ...f, description: e.target.value }))}
                  placeholder="서식에 대한 간단한 설명"
                  rows={3}
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors resize-none"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">파일 *</label>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    setTemplateUploadForm((prev) => ({ ...prev, file: f }));
                  }}
                  className="w-full text-sm text-[#8c8c8c] file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-[#262626] file:text-[#ededed] hover:file:bg-[#333] cursor-pointer"
                />
                <p className="text-[10px] text-[#5c5c5c] mt-1">PDF 또는 DOCX</p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={templateUploadForm.is_public}
                  onClick={() => setTemplateUploadForm((f) => ({ ...f, is_public: !f.is_public }))}
                  className={`relative w-10 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#3ecf8e] ${
                    templateUploadForm.is_public ? "bg-[#3ecf8e]" : "bg-[#262626]"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      templateUploadForm.is_public ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
                <span className="text-sm text-[#8c8c8c]">팀 공개</span>
              </div>
            </div>

            <div className="flex gap-2 px-5 py-4 border-t border-[#262626]">
              <button
                onClick={() => setShowTemplateModal(false)}
                className="flex-1 py-2 text-sm text-[#8c8c8c] border border-[#262626] rounded-md hover:bg-[#1a1a1a] transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleTemplateUpload}
                disabled={uploadingTemplate}
                className="flex-1 py-2 text-sm font-medium bg-[#3ecf8e] text-black rounded-md hover:bg-[#36b87e] disabled:opacity-50 transition-colors"
              >
                {uploadingTemplate ? "업로드 중..." : "업로드"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 섹션 추가/편집 모달 */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl w-full max-w-lg mx-4 flex flex-col max-h-[90vh]">
            {/* 모달 헤더 */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#262626]">
              <h2 className="text-sm font-semibold text-[#ededed]">
                {editTarget ? "섹션 편집" : "섹션 추가"}
              </h2>
              <button
                onClick={() => setModalOpen(false)}
                className="text-[#8c8c8c] hover:text-[#ededed] text-lg leading-none"
              >
                ×
              </button>
            </div>

            {/* 모달 바디 */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {formError && (
                <p className="text-xs text-red-400 bg-red-400/10 rounded-md px-3 py-2">
                  {formError}
                </p>
              )}

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">
                  제목 *
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, title: e.target.value }))
                  }
                  placeholder="섹션 제목"
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">
                  카테고리 *
                </label>
                <select
                  value={form.category}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, category: e.target.value }))
                  }
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                >
                  {CATEGORIES.filter((c) => c.value).map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">
                  내용 *
                </label>
                <textarea
                  value={form.content}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, content: e.target.value }))
                  }
                  placeholder="마크다운 텍스트 입력..."
                  rows={8}
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors resize-none font-mono"
                />
              </div>

              <div>
                <label className="block text-xs text-[#8c8c8c] mb-1.5">
                  태그 (쉼표로 구분)
                </label>
                <input
                  type="text"
                  value={form.tags}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, tags: e.target.value }))
                  }
                  placeholder="예: 공공, 클라우드, 보안"
                  className="w-full bg-[#0f0f0f] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={form.is_public}
                  onClick={() =>
                    setForm((f) => ({ ...f, is_public: !f.is_public }))
                  }
                  className={`relative w-10 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#3ecf8e] ${
                    form.is_public ? "bg-[#3ecf8e]" : "bg-[#262626]"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      form.is_public ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
                <span className="text-sm text-[#8c8c8c]">팀 공개</span>
              </div>
            </div>

            {/* 모달 푸터 */}
            <div className="flex gap-2 px-5 py-4 border-t border-[#262626]">
              <button
                onClick={() => setModalOpen(false)}
                className="flex-1 py-2 text-sm text-[#8c8c8c] border border-[#262626] rounded-md hover:bg-[#1a1a1a] transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 py-2 text-sm font-medium bg-[#3ecf8e] text-black rounded-md hover:bg-[#36b87e] disabled:opacity-50 transition-colors"
              >
                {saving ? "저장 중..." : "저장"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── 섹션 라이브러리 탭 ────────────────────────────────────────────────

interface SectionsTabProps {
  sections: Section[];
  loading: boolean;
  error: string;
  scope: string;
  setScope: (v: string) => void;
  category: string;
  setCategory: (v: string) => void;
  q: string;
  setQ: (v: string) => void;
  currentUserId: string;
  onEdit: (s: Section) => void;
  onDelete: (id: string) => void;
  onAdd: () => void;
}

function SectionsTab({
  sections,
  loading,
  error,
  scope,
  setScope,
  category,
  setCategory,
  q,
  setQ,
  currentUserId,
  onEdit,
  onDelete,
  onAdd,
}: SectionsTabProps) {
  return (
    <div className="px-6 py-5 space-y-4">
      {/* 필터 영역 */}
      <div className="space-y-3">
        {/* 카테고리 버튼 */}
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              onClick={() => setCategory(c.value)}
              className={`px-3 py-1.5 text-xs rounded-md border transition-colors ${
                category === c.value
                  ? "bg-[#3ecf8e] text-black border-[#3ecf8e] font-medium"
                  : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="flex gap-3 items-center">
          {/* 검색 */}
          <div className="relative flex-1 max-w-xs">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#5c5c5c] text-xs">
              ⌕
            </span>
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="검색..."
              className="w-full bg-[#111111] border border-[#262626] rounded-md pl-7 pr-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
            />
          </div>

          {/* 스코프 탭 */}
          <div className="flex border border-[#262626] rounded-md overflow-hidden">
            {SCOPE_TABS.map((t) => (
              <button
                key={t.value}
                onClick={() => setScope(t.value)}
                className={`px-3 py-2 text-xs transition-colors ${
                  scope === t.value
                    ? "bg-[#1c1c1c] text-[#ededed]"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 추가 버튼 */}
          <button
            onClick={onAdd}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[#3ecf8e] text-black rounded-md hover:bg-[#36b87e] transition-colors"
          >
            <span>+</span>
            <span>섹션 추가</span>
          </button>
        </div>
      </div>

      {/* 결과 영역 */}
      {error && (
        <div className="bg-red-400/10 border border-red-400/20 rounded-md px-4 py-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-40 bg-[#1c1c1c] rounded-xl border border-[#262626] animate-pulse"
            />
          ))}
        </div>
      ) : sections.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="text-4xl mb-3 opacity-30">□</div>
          <p className="text-sm text-[#5c5c5c]">섹션이 없습니다.</p>
          <button
            onClick={onAdd}
            className="mt-4 text-xs text-[#3ecf8e] hover:underline"
          >
            + 첫 번째 섹션 추가
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {sections.map((s) => (
            <SectionCard
              key={s.id}
              section={s}
              isOwner={s.owner_id === currentUserId}
              onEdit={() => onEdit(s)}
              onDelete={() => onDelete(s.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── 섹션 카드 ─────────────────────────────────────────────────────────

interface SectionCardProps {
  section: Section;
  isOwner: boolean;
  onEdit: () => void;
  onDelete: () => void;
}

function SectionCard({ section, isOwner, onEdit, onDelete }: SectionCardProps) {
  const categoryLabel = CATEGORY_LABELS[section.category] ?? section.category;

  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 flex flex-col gap-2.5 hover:border-[#3c3c3c] transition-colors">
      {/* 제목 + 카테고리 */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-[#ededed] leading-snug flex-1 min-w-0 truncate">
          {section.title}
        </h3>
        <span className="shrink-0 text-[10px] px-2 py-0.5 rounded-full bg-[#3ecf8e]/10 text-[#3ecf8e] font-medium">
          {categoryLabel}
        </span>
      </div>

      {/* 내용 미리보기 */}
      <p className="text-xs text-[#8c8c8c] leading-relaxed line-clamp-3">
        {section.content}
      </p>

      {/* 태그 */}
      {section.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {section.tags.slice(0, 4).map((tag) => (
            <span
              key={tag}
              className="text-[10px] px-1.5 py-0.5 rounded bg-[#262626] text-[#8c8c8c]"
            >
              {tag}
            </span>
          ))}
          {section.tags.length > 4 && (
            <span className="text-[10px] text-[#5c5c5c]">
              +{section.tags.length - 4}
            </span>
          )}
        </div>
      )}

      {/* 하단: 사용횟수 + 버튼 */}
      <div className="flex items-center justify-between mt-auto pt-1 border-t border-[#262626]">
        <span className="text-[10px] text-[#5c5c5c]">
          사용 {section.use_count}회
        </span>
        {isOwner && (
          <div className="flex gap-1.5">
            <button
              onClick={onEdit}
              className="text-[11px] text-[#8c8c8c] hover:text-[#ededed] transition-colors px-2 py-0.5 rounded hover:bg-[#262626]"
            >
              편집
            </button>
            <button
              onClick={onDelete}
              className="text-[11px] text-[#8c8c8c] hover:text-red-400 transition-colors px-2 py-0.5 rounded hover:bg-[#262626]"
            >
              삭제
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── 공통서식 탭 ───────────────────────────────────────────────────────

interface TemplatesTabProps {
  templates: FormTemplate[];
  loading: boolean;
  agency: string;
  setAgency: (v: string) => void;
  category: string;
  setCategory: (v: string) => void;
  onSearch: () => void;
  onDelete: (id: string) => void;
  onAdd: () => void;
}

function TemplatesTab({
  templates,
  loading,
  agency,
  setAgency,
  category,
  setCategory,
  onSearch,
  onDelete,
  onAdd,
}: TemplatesTabProps) {
  return (
    <div className="px-6 py-5 space-y-4">
      {/* 필터 + 추가 버튼 */}
      <div className="flex flex-wrap gap-2 items-center">
        <input
          type="text"
          value={agency}
          onChange={(e) => setAgency(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="발행기관 (예: 행안부)"
          className="bg-[#111111] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors w-44"
        />
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="카테고리"
          className="bg-[#111111] border border-[#262626] rounded-md px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors w-36"
        />
        <button
          onClick={onSearch}
          className="px-3 py-2 text-xs border border-[#262626] rounded-md text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3c3c3c] transition-colors"
        >
          검색
        </button>
        <button
          onClick={onAdd}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[#3ecf8e] text-black rounded-md hover:bg-[#36b87e] transition-colors ml-auto"
        >
          <span>+</span>
          <span>서식 추가</span>
        </button>
      </div>

      {/* 목록 */}
      {loading ? (
        <div className="grid grid-cols-2 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-40 bg-[#1c1c1c] rounded-xl border border-[#262626] animate-pulse" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="text-4xl mb-3 opacity-30">□</div>
          <p className="text-sm text-[#5c5c5c]">등록된 서식이 없습니다.</p>
          <button
            onClick={onAdd}
            className="mt-4 text-xs text-[#3ecf8e] hover:underline"
          >
            + 첫 번째 서식 추가
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {templates.map((t) => (
            <TemplateCard key={t.id} template={t} onDelete={() => onDelete(t.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── 서식 카드 ──────────────────────────────────────────────────────────

interface TemplateCardProps {
  template: FormTemplate;
  onDelete: () => void;
}

function TemplateCard({ template, onDelete }: TemplateCardProps) {
  const date = new Date(template.created_at).toLocaleDateString("ko-KR");
  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 flex flex-col gap-2.5 hover:border-[#3c3c3c] transition-colors">
      {/* 제목 + 배지들 */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-[#ededed] leading-snug flex-1 min-w-0 truncate">
          {template.title}
        </h3>
        <span className="shrink-0 text-[10px] px-2 py-0.5 rounded-full bg-[#262626] text-[#8c8c8c] uppercase font-medium">
          {template.file_type}
        </span>
      </div>

      {/* 기관 / 카테고리 배지 */}
      <div className="flex flex-wrap gap-1.5">
        {template.agency && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#3ecf8e]/10 text-[#3ecf8e] font-medium">
            {template.agency}
          </span>
        )}
        {template.category && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-400/10 text-blue-400 font-medium">
            {template.category}
          </span>
        )}
      </div>

      {/* 설명 */}
      {template.description && (
        <p className="text-xs text-[#8c8c8c] leading-relaxed line-clamp-2">
          {template.description}
        </p>
      )}

      {/* 하단: 날짜 + 사용횟수 + 삭제 */}
      <div className="flex items-center justify-between mt-auto pt-1 border-t border-[#262626]">
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[#5c5c5c]">{date}</span>
          <span className="text-[10px] text-[#5c5c5c]">· 사용 {template.use_count}회</span>
        </div>
        <button
          onClick={onDelete}
          className="text-[11px] text-[#8c8c8c] hover:text-red-400 transition-colors px-2 py-0.5 rounded hover:bg-[#262626]"
        >
          삭제
        </button>
      </div>
    </div>
  );
}

// ── 회사 자료 탭 ──────────────────────────────────────────────────────

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  done:       { label: "완료",     cls: "bg-[#3ecf8e]/10 text-[#3ecf8e]" },
  processing: { label: "처리 중", cls: "bg-yellow-400/10 text-yellow-400" },
  pending:    { label: "대기",     cls: "bg-[#5c5c5c]/20 text-[#8c8c8c]" },
  failed:     { label: "실패",     cls: "bg-red-400/10 text-red-400" },
};

function CompanyTab() {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.assets.list();
      setAssets(res.assets);
    } catch (e) {
      setError(e instanceof Error ? e.message : "목록 로드 실패");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAssets(); }, [loadAssets]);

  // processing/pending 상태 자료가 있으면 3초 폴링으로 갱신
  useEffect(() => {
    const hasPending = assets.some(
      (a) => a.status === "processing" || a.status === "pending"
    );
    if (!hasPending) return;
    const timer = setInterval(loadAssets, 3000);
    return () => clearInterval(timer);
  }, [assets, loadAssets]);

  async function uploadFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setError("PDF 또는 DOCX 파일만 업로드할 수 있습니다.");
      return;
    }
    setUploading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.assets.upload(fd);
      await loadAssets();
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  }

  async function handleDelete(id: string) {
    if (!confirm("자료를 삭제하시겠습니까?")) return;
    try {
      await api.assets.delete(id);
      setAssets((prev) => prev.filter((a) => a.id !== id));
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  return (
    <div className="px-6 py-5 space-y-5">
      {/* 업로드 존 */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex flex-col items-center justify-center gap-2 py-12 rounded-xl border-2 border-dashed cursor-pointer transition-colors ${
          dragging
            ? "border-[#3ecf8e] bg-[#3ecf8e]/5"
            : "border-[#262626] hover:border-[#3c3c3c] bg-[#111111]"
        }`}
      >
        <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl text-[#5c5c5c]">
          {uploading ? "..." : "↑"}
        </div>
        <p className="text-sm font-medium text-[#ededed]">
          {uploading ? "업로드 중..." : "PDF / DOCX 파일을 드래그하거나 클릭하여 업로드"}
        </p>
        <p className="text-xs text-[#5c5c5c]">업로드한 문서를 AI가 제안서 작성에 활용합니다.</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
            e.target.value = "";
          }}
        />
      </div>

      {/* 오류 */}
      {error && (
        <div className="bg-red-400/10 border border-red-400/20 rounded-md px-4 py-3">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* 자료 목록 */}
      {loading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-14 bg-[#1c1c1c] rounded-lg border border-[#262626] animate-pulse" />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <p className="text-sm text-[#5c5c5c] text-center py-8">업로드된 자료가 없습니다.</p>
      ) : (
        <div className="space-y-2">
          {assets.map((asset) => {
            const badge = STATUS_BADGE[asset.status] ?? STATUS_BADGE.pending;
            const date = new Date(asset.created_at).toLocaleDateString("ko-KR");
            return (
              <div
                key={asset.id}
                className="flex items-center gap-3 px-4 py-3 bg-[#1c1c1c] border border-[#262626] rounded-lg hover:border-[#3c3c3c] transition-colors"
              >
                <div className="w-8 h-8 rounded-md bg-[#262626] flex items-center justify-center text-xs text-[#8c8c8c] shrink-0 uppercase">
                  {asset.file_type}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#ededed] truncate">{asset.filename}</p>
                  <p className="text-xs text-[#5c5c5c]">{date}</p>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${badge.cls}`}>
                  {badge.label}
                </span>
                <button
                  onClick={() => handleDelete(asset.id)}
                  className="text-xs text-[#5c5c5c] hover:text-red-400 transition-colors px-2 py-0.5 rounded hover:bg-[#262626] shrink-0"
                >
                  삭제
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
