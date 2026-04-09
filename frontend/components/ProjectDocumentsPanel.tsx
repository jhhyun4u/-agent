"use client";

/**
 * ProjectDocumentsPanel — 프로젝트별 문서 관리
 *
 * 제안 프로젝트 상세 페이지에서 문서 업로드, 검색, 삭제를 수행.
 * 글로벌 KB 문서를 프로젝트 컨텍스트에서 접근.
 */

import { useCallback, useEffect, useState } from "react";
import { documentsApi, type DocumentResponse } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

const DOC_TYPES = ["보고서", "제안서", "실적", "기타"];
const STATUS_OPTS = [
  { value: "", label: "전체" },
  { value: "extracting", label: "추출 중" },
  { value: "chunking", label: "청킹 중" },
  { value: "embedding", label: "임베딩 중" },
  { value: "completed", label: "완료" },
  { value: "failed", label: "실패" },
];

const STATUS_VARIANTS: Record<string, "success" | "warning" | "error" | "info" | "neutral"> = {
  extracting: "info",
  chunking: "info",
  embedding: "info",
  completed: "success",
  failed: "error",
};

export default function ProjectDocumentsPanel() {
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [docTypeFilter, setDocTypeFilter] = useState("");

  // Upload
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string>("보고서");

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Load documents
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await documentsApi.list({
        status: statusFilter || undefined,
        doc_type: docTypeFilter || undefined,
        search: search || undefined,
      });
      setDocuments(res.items);
    } catch (err) {
      console.error("문서 목록 조회 실패:", err);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, docTypeFilter]);

  useEffect(() => {
    load();
  }, [load]);

  // Handle file upload with validation
  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploading(true);

    try {
      await documentsApi.upload(file, uploadDocType);
      setUploadDocType("보고서");
      e.target.value = "";
      await load();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "업로드 실패";
      setUploadError(message);
    } finally {
      setUploading(false);
    }
  }

  // Handle delete with confirmation
  async function handleDelete(documentId: string) {
    if (deleteConfirm !== documentId) {
      setDeleteConfirm(documentId);
      return;
    }

    setDeleting(documentId);
    try {
      await documentsApi.delete(documentId);
      setDeleteConfirm(null);
      await load();
    } catch (err) {
      console.error("문서 삭제 실패:", err);
      alert("문서 삭제 실패: " + (err instanceof Error ? err.message : ""));
    } finally {
      setDeleting(null);
    }
  }

  // Format date
  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card className="border-blue-200 bg-blue-50">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">문서 업로드</h3>

          {uploadError && (
            <div className="p-3 mb-4 bg-red-100 border border-red-300 rounded-md text-red-800 text-sm">
              <div className="font-medium">업로드 실패</div>
              <div>{uploadError}</div>
              <div className="text-xs mt-1 opacity-75">
                지원 형식: .pdf, .hwp, .hwpx, .docx, .doc (최대 500MB)
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <select
              value={uploadDocType}
              onChange={(e) => setUploadDocType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              {DOC_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>

            <label className="flex-1">
              <input
                type="file"
                onChange={handleUpload}
                disabled={uploading}
                className="hidden"
                accept=".pdf,.hwp,.hwpx,.docx,.doc"
              />
              <Button
                disabled={uploading}
                className="w-full cursor-pointer"
                onClick={(e) => {
                  const input = (e.target as HTMLButtonElement)
                    .previousElementSibling as HTMLInputElement;
                  input?.click();
                }}
              >
                {uploading ? "업로드 중..." : "파일 선택"}
              </Button>
            </label>
          </div>
        </div>
      </Card>

      {/* Filters Section */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">필터</h3>

          {/* Search Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              파일명 검색
            </label>
            <input
              type="text"
              placeholder="파일명 입력..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {/* Status and Type Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-2">상태</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                {STATUS_OPTS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">유형</label>
              <select
                value={docTypeFilter}
                onChange={(e) => setDocTypeFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">전체</option>
                {DOC_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </Card>

      {/* Document List */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold">
          문서 {documents.length > 0 && `(${documents.length}개)`}
        </h2>

        {loading ? (
          <div className="flex justify-center py-8 text-gray-400">
            로딩 중...
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">문서가 없습니다.</div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <Card key={doc.id} className="hover:shadow-md transition-shadow">
                <div className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium truncate">{doc.filename}</h3>
                        <Badge variant={STATUS_VARIANTS[doc.processing_status]}>
                          {STATUS_OPTS.find(
                            (s) => s.value === doc.processing_status,
                          )?.label || doc.processing_status}
                        </Badge>
                      </div>

                      <div className="text-sm text-gray-600 space-y-1">
                        <div>
                          유형: <span className="font-medium">{doc.doc_type}</span>
                        </div>
                        <div>
                          생성: {formatDate(doc.created_at)} • 수정:{" "}
                          {formatDate(doc.updated_at)}
                        </div>
                        <div>
                          크기: {doc.total_chars.toLocaleString()} 자 • 청크:{" "}
                          {doc.chunk_count}개
                        </div>

                        {doc.error_message && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
                            <div className="font-medium">오류:</div>
                            <div className="break-words">
                              {doc.error_message}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Delete Button */}
                    <div className="flex gap-2 flex-shrink-0">
                      {deleteConfirm === doc.id ? (
                        <div className="flex gap-2">
                          <Button
                            onClick={() => setDeleteConfirm(null)}
                            variant="secondary"
                            size="sm"
                          >
                            취소
                          </Button>
                          <Button
                            onClick={() => handleDelete(doc.id)}
                            disabled={deleting === doc.id}
                            size="sm"
                            className="bg-red-600 hover:bg-red-700"
                          >
                            {deleting === doc.id ? "삭제 중..." : "삭제"}
                          </Button>
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          className="bg-red-600 hover:bg-red-700"
                          onClick={() => handleDelete(doc.id)}
                          disabled={deleting === doc.id}
                        >
                          {deleting === doc.id ? "삭제 중..." : "삭제"}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
