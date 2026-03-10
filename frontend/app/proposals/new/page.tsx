"use client";

/**
 * F4: 새 제안서 생성 페이지
 * - 드래그앤드롭 파일 업로드 (PDF / DOCX / TXT)
 * - 형식/크기 즉시 검증 (서버 요청 전)
 * - .hwp 업로드 시 즉시 오류 메시지
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, FormTemplate, Section } from "@/lib/api";

const ALLOWED = [".pdf", ".docx", ".txt"];
const ALLOWED_MIME = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];
const MAX_MB = 10;

function validateFile(file: File): string | null {
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  if (ext === ".hwp" || ext === ".hwpx") {
    return "HWP 파일은 지원하지 않습니다. PDF 또는 DOCX로 변환 후 업로드해 주세요.";
  }
  if (!ALLOWED.includes(ext) && !ALLOWED_MIME.includes(file.type)) {
    return `지원하지 않는 파일 형식입니다. (PDF, DOCX, TXT만 가능)`;
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    return `파일 크기가 ${MAX_MB}MB를 초과합니다. (현재: ${(file.size / 1024 / 1024).toFixed(1)}MB)`;
  }
  return null;
}

export default function NewProposalPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [rfpTitle, setRfpTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [fileError, setFileError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [bidPrefill, setBidPrefill] = useState<{ bid_no: string; rfp_title: string } | null>(null);

  // 공통서식 선택
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<FormTemplate | null>(null);
  const [templateAgencyFilter, setTemplateAgencyFilter] = useState("");

  // 섹션 선택
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedSectionIds, setSelectedSectionIds] = useState<string[]>([]);
  const [sectionCategoryFilter, setSectionCategoryFilter] = useState("");

  useEffect(() => {
    api.formTemplates.list().then((res) => setTemplates(res.templates)).catch(() => {});
    api.sections.list().then((res) => setSections(res.sections)).catch(() => {});

    // 공고에서 넘어온 경우 bid 데이터 자동 입력
    const stored = sessionStorage.getItem("bid_prefill");
    if (stored) {
      try {
        const data = JSON.parse(stored);
        sessionStorage.removeItem("bid_prefill");
        if (data.rfp_title) setRfpTitle(data.rfp_title);
        if (data.client_name) setClientName(data.client_name);
        if (data.rfp_content) {
          // 공고 원문을 txt 파일로 변환하여 파일 슬롯에 채움
          const blob = new Blob([data.rfp_content], { type: "text/plain" });
          const f = new File([blob], `${data.rfp_title || "공고"}.txt`, { type: "text/plain" });
          setFile(f);
        }
        setBidPrefill({ bid_no: data.bid_no, rfp_title: data.rfp_title });
      } catch {
        // 파싱 실패 시 무시
      }
    }
  }, []);

  function handleFile(f: File) {
    const err = validateFile(f);
    if (err) {
      setFileError(err);
      setFile(null);
    } else {
      setFileError("");
      setFile(f);
      if (!rfpTitle) {
        setRfpTitle(f.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " "));
      }
    }
  }

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [rfpTitle] // eslint-disable-line react-hooks/exhaustive-deps
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !rfpTitle.trim() || !clientName.trim()) return;
    setSubmitting(true);
    setError("");

    try {
      const fd = new FormData();
      fd.append("rfp_title", rfpTitle.trim());
      fd.append("client_name", clientName.trim());
      fd.append("rfp_file", file);
      if (selectedTemplate) fd.append("form_template_id", selectedTemplate.id);
      if (selectedSectionIds.length > 0) {
        fd.append("section_ids", JSON.stringify(selectedSectionIds));
      }

      const res = await api.proposals.generate(fd);
      await api.proposals.execute(res.proposal_id);
      router.push(`/proposals/${res.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제출 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/proposals" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
            ←
          </Link>
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">새 제안서 생성</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">RFP 파일을 업로드하여 AI 제안서를 생성합니다</p>
          </div>
        </div>
      </div>

      {/* 폼 */}
      <div className="flex-1 overflow-auto px-6 py-6">
        <form onSubmit={handleSubmit} className="max-w-xl space-y-5">
              {/* 공고 자동 입력 배너 */}
          {bidPrefill && (
            <div className="flex items-center gap-3 bg-emerald-950/20 border border-emerald-900/40 rounded-lg px-4 py-2.5">
              <span className="text-emerald-400 text-base">📌</span>
              <div>
                <p className="text-xs font-medium text-emerald-400">공고 정보가 자동으로 입력되었습니다.</p>
                <p className="text-[11px] text-[#5c5c5c] mt-0.5">공고번호: {bidPrefill.bid_no} · 공고 원문이 RFP 파일로 사용됩니다.</p>
              </div>
            </div>
          )}

          {/* 파일 업로드 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2 uppercase tracking-wider">
              RFP 파일 <span className="text-red-400 normal-case">*</span>
            </label>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                dragging
                  ? "border-[#3ecf8e] bg-emerald-950/20"
                  : file
                  ? "border-[#3ecf8e] bg-emerald-950/10"
                  : "border-[#262626] bg-[#111111] hover:border-[#3a3a3a]"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              />
              {file ? (
                <div>
                  <p className="text-2xl mb-2">📎</p>
                  <p className="font-medium text-[#3ecf8e] text-sm">{file.name}</p>
                  <p className="text-xs text-[#8c8c8c] mt-1">{(file.size / 1024).toFixed(0)} KB</p>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setFile(null); setRfpTitle(""); }}
                    className="mt-2 text-xs text-red-400 hover:text-red-300 transition-colors"
                  >
                    파일 제거
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-3xl mb-2">⬆</p>
                  <p className="font-medium text-[#ededed] text-sm">파일을 드래그하거나 클릭하여 업로드</p>
                  <p className="text-xs text-[#8c8c8c] mt-1">PDF, DOCX, TXT · 최대 10MB</p>
                </div>
              )}
            </div>
            {fileError && (
              <p className="mt-2 text-xs text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{fileError}</p>
            )}
          </div>

          {/* 공통서식 선택 (선택사항) */}
          {templates.length > 0 && (
            <div className="bg-[#111111] border border-[#262626] rounded-xl p-4 space-y-3">
              <p className="text-xs font-medium text-[#ededed] uppercase tracking-wider">
                공통서식 선택 <span className="normal-case text-[#8c8c8c] font-normal">(선택사항)</span>
              </p>

              {/* 발행기관 필터 chips */}
              {(() => {
                const agencies = Array.from(
                  new Set(templates.map((t) => t.agency).filter(Boolean) as string[])
                );
                return agencies.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      type="button"
                      onClick={() => setTemplateAgencyFilter("")}
                      className={`px-2.5 py-1 text-[11px] rounded-md border transition-colors ${
                        templateAgencyFilter === ""
                          ? "bg-[#3ecf8e] text-black border-[#3ecf8e] font-medium"
                          : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                      }`}
                    >
                      전체
                    </button>
                    {agencies.map((ag) => (
                      <button
                        key={ag}
                        type="button"
                        onClick={() => setTemplateAgencyFilter(ag === templateAgencyFilter ? "" : ag)}
                        className={`px-2.5 py-1 text-[11px] rounded-md border transition-colors ${
                          templateAgencyFilter === ag
                            ? "bg-[#3ecf8e] text-black border-[#3ecf8e] font-medium"
                            : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                        }`}
                      >
                        {ag}
                      </button>
                    ))}
                  </div>
                ) : null;
              })()}

              {/* 서식 카드 그리드 */}
              <div className="grid grid-cols-2 gap-2">
                {templates
                  .filter((t) => !templateAgencyFilter || t.agency === templateAgencyFilter)
                  .map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setSelectedTemplate(selectedTemplate?.id === t.id ? null : t)}
                      className={`text-left p-3 rounded-lg border transition-colors ${
                        selectedTemplate?.id === t.id
                          ? "border-[#3ecf8e] bg-[#3ecf8e]/5"
                          : "border-[#262626] bg-[#1c1c1c] hover:border-[#3c3c3c]"
                      }`}
                    >
                      <p className="text-xs font-medium text-[#ededed] truncate">{t.title}</p>
                      {t.agency && (
                        <p className="text-[10px] text-[#3ecf8e] mt-0.5">{t.agency}</p>
                      )}
                    </button>
                  ))}
              </div>

              {/* 선택 해제 */}
              {selectedTemplate && (
                <button
                  type="button"
                  onClick={() => setSelectedTemplate(null)}
                  className="text-xs text-[#8c8c8c] hover:text-[#ededed] transition-colors"
                >
                  선택 해제 ({selectedTemplate.title})
                </button>
              )}
            </div>
          )}

          {/* 섹션 선택 (선택사항) */}
          {sections.length > 0 && (
            <div className="bg-[#111111] border border-[#262626] rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-[#ededed] uppercase tracking-wider">
                  자료 섹션 선택 <span className="normal-case text-[#8c8c8c] font-normal">(선택사항)</span>
                </p>
                {selectedSectionIds.length > 0 && (
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-[#3ecf8e]">
                      {selectedSectionIds.length}개 섹션 선택됨
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedSectionIds([])}
                      className="text-[11px] text-[#8c8c8c] hover:text-[#ededed] transition-colors"
                    >
                      선택 해제
                    </button>
                  </div>
                )}
              </div>

              {/* 카테고리 필터 chips */}
              {(() => {
                const CATEGORY_LABELS: Record<string, string> = {
                  company_intro: "회사소개",
                  track_record: "수행실적",
                  methodology: "기술방법론",
                  organization: "조직구성",
                  schedule: "추진일정",
                  cost: "원가/예산",
                  other: "기타",
                };
                const categories = Array.from(
                  new Set(sections.map((s) => s.category).filter(Boolean))
                );
                return categories.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    <button
                      type="button"
                      onClick={() => setSectionCategoryFilter("")}
                      className={`px-2.5 py-1 text-[11px] rounded-md border transition-colors ${
                        sectionCategoryFilter === ""
                          ? "bg-[#3ecf8e] text-black border-[#3ecf8e] font-medium"
                          : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                      }`}
                    >
                      전체
                    </button>
                    {categories.map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() =>
                          setSectionCategoryFilter(cat === sectionCategoryFilter ? "" : cat)
                        }
                        className={`px-2.5 py-1 text-[11px] rounded-md border transition-colors ${
                          sectionCategoryFilter === cat
                            ? "bg-[#3ecf8e] text-black border-[#3ecf8e] font-medium"
                            : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                        }`}
                      >
                        {CATEGORY_LABELS[cat] ?? cat}
                      </button>
                    ))}
                  </div>
                ) : null;
              })()}

              {/* 섹션 카드 그리드 */}
              {(() => {
                const CATEGORY_LABELS: Record<string, string> = {
                  company_intro: "회사소개",
                  track_record: "수행실적",
                  methodology: "기술방법론",
                  organization: "조직구성",
                  schedule: "추진일정",
                  cost: "원가/예산",
                  other: "기타",
                };
                const filtered = sections.filter(
                  (s) => !sectionCategoryFilter || s.category === sectionCategoryFilter
                );
                return (
                  <div className="grid grid-cols-2 gap-2">
                    {filtered.map((s) => {
                      const isSelected = selectedSectionIds.includes(s.id);
                      return (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() =>
                            setSelectedSectionIds((prev) =>
                              isSelected
                                ? prev.filter((x) => x !== s.id)
                                : [...prev, s.id]
                            )
                          }
                          className={`text-left p-3 rounded-lg border transition-colors ${
                            isSelected
                              ? "border-[#3ecf8e] bg-[#3ecf8e]/5"
                              : "border-[#262626] bg-[#1c1c1c] hover:border-[#3c3c3c]"
                          }`}
                        >
                          <p className="text-xs font-medium text-[#ededed] truncate">{s.title}</p>
                          <p className="text-[10px] text-[#3ecf8e] mt-0.5">
                            {CATEGORY_LABELS[s.category] ?? s.category}
                          </p>
                          {s.content && (
                            <p className="text-[10px] text-[#8c8c8c] mt-1 line-clamp-2 leading-relaxed">
                              {s.content.slice(0, 50)}
                            </p>
                          )}
                        </button>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
          )}

          {/* 사업명 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2 uppercase tracking-wider">
              사업명 <span className="text-red-400 normal-case">*</span>
            </label>
            <input
              type="text"
              required
              value={rfpTitle}
              onChange={(e) => setRfpTitle(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
              placeholder="예: 공공데이터 AI 분석 시스템 구축"
            />
          </div>

          {/* 발주처 */}
          <div>
            <label className="block text-xs font-medium text-[#ededed] mb-2 uppercase tracking-wider">
              발주처 <span className="text-red-400 normal-case">*</span>
            </label>
            <input
              type="text"
              required
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
              placeholder="예: 행정안전부"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="bg-blue-950/30 border border-blue-900/50 rounded-lg px-4 py-3 text-xs text-blue-300">
            AI가 5단계 분석을 수행합니다. 완료까지 <strong>5~15분</strong> 소요됩니다.
          </div>

          <button
            type="submit"
            disabled={submitting || !file || !rfpTitle.trim() || !clientName.trim()}
            className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold rounded-lg py-2.5 text-sm transition-colors"
          >
            {submitting ? "제출 중..." : "제안서 생성 시작"}
          </button>
        </form>
      </div>
    </div>
  );
}
