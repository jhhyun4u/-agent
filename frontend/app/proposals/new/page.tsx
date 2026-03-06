"use client";

/**
 * F4: 새 제안서 생성 페이지
 * - 드래그앤드롭 파일 업로드 (PDF / DOCX / TXT)
 * - 형식/크기 즉시 검증 (서버 요청 전)
 * - .hwp 업로드 시 즉시 오류 메시지
 */

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

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

  function handleFile(f: File) {
    const err = validateFile(f);
    if (err) {
      setFileError(err);
      setFile(null);
    } else {
      setFileError("");
      setFile(f);
      // 파일명에서 제목 자동 추출
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

      const res = await api.proposals.generate(fd);
      // 생성 후 상세 페이지로 이동 + 즉시 실행
      await api.proposals.execute(res.proposal_id);
      router.push(`/proposals/${res.proposal_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제출 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <Link href="/proposals" className="text-gray-400 hover:text-gray-700 text-sm">
            ← 목록으로
          </Link>
          <h1 className="text-base font-semibold text-gray-900">새 제안서 생성</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 파일 업로드 존 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              RFP 파일 <span className="text-red-500">*</span>
            </label>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                dragging
                  ? "border-blue-400 bg-blue-50"
                  : file
                  ? "border-green-400 bg-green-50"
                  : "border-gray-300 bg-white hover:border-gray-400"
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
                  <p className="font-medium text-green-700">{file.name}</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {(file.size / 1024).toFixed(0)} KB
                  </p>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setFile(null); setRfpTitle(""); }}
                    className="mt-2 text-xs text-red-500 hover:text-red-700"
                  >
                    파일 제거
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-3xl mb-2">☁️</p>
                  <p className="font-medium text-gray-700">파일을 드래그하거나 클릭하여 업로드</p>
                  <p className="text-sm text-gray-400 mt-1">PDF, DOCX, TXT · 최대 10MB</p>
                </div>
              )}
            </div>
            {fileError && (
              <p className="mt-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{fileError}</p>
            )}
          </div>

          {/* RFP 제목 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사업명 (RFP 제목) <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={rfpTitle}
              onChange={(e) => setRfpTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: 공공데이터 AI 분석 시스템 구축"
            />
          </div>

          {/* 발주처 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              발주처 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="예: 행정안전부"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700">
            AI가 5단계 분석을 수행합니다. 완료까지 <strong>5~15분</strong> 소요됩니다.
            완료 시 이메일로 알림을 보내드립니다.
          </div>

          <button
            type="submit"
            disabled={submitting || !file || !rfpTitle.trim() || !clientName.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-3 text-sm transition-colors"
          >
            {submitting ? "제출 중..." : "제안서 생성 시작"}
          </button>
        </form>
      </main>
    </div>
  );
}
