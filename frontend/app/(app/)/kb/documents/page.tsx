"use client";

/**
 * 인트라넷 문서 관리 페이지 - 임시 비활성화
 * 
 * 2026-04-08: 프론트엔드 빌드 에러 진단 중
 * TODO: 빌드 에러 해결 후 page.tsx.disabled 복원
 */

import { Card } from "@/components/ui/Card";

export default function DocumentsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <Card className="max-w-2xl mx-auto p-8 text-center">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">문서 관리</h1>
        <p className="text-slate-600 mb-4">이 페이지는 현재 유지보수 중입니다.</p>
        <p className="text-sm text-slate-500">빌드 에러 해결 후 다시 활성화됩니다.</p>
      </Card>
    </div>
  );
}
