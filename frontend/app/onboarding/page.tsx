"use client";

/**
 * F2: 온보딩 페이지
 * - 신규 가입자가 팀 생성 또는 개인으로 시작 선택
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function OnboardingPage() {
  const router = useRouter();
  const [teamName, setTeamName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCreateTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!teamName.trim()) return;
    setLoading(true);
    setError("");
    try {
      await api.teams.create(teamName.trim());
      router.push("/proposals");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "팀 생성에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-100 rounded-full mb-4">
            <span className="text-2xl">👋</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">환영합니다!</h1>
          <p className="mt-2 text-gray-500">시작하기 전에 사용 방식을 선택해 주세요.</p>
        </div>

        <div className="space-y-4">
          {/* 팀 생성 카드 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-1">팀으로 시작하기</h2>
            <p className="text-sm text-gray-500 mb-4">
              팀을 만들고 동료를 초대하여 제안서를 함께 검토하세요.
            </p>
            {error && (
              <p className="mb-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
            )}
            <form onSubmit={handleCreateTeam} className="flex gap-2">
              <input
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="팀 이름 입력 (예: 테크노베이션 영업팀)"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={50}
              />
              <button
                type="submit"
                disabled={loading || !teamName.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors whitespace-nowrap"
              >
                {loading ? "생성 중..." : "팀 만들기"}
              </button>
            </form>
          </div>

          {/* 개인 시작 */}
          <button
            onClick={() => router.push("/proposals")}
            className="w-full bg-white hover:bg-gray-50 rounded-xl shadow-sm border border-gray-200 p-6 text-left transition-colors"
          >
            <h2 className="font-semibold text-gray-900 mb-1">개인으로 시작하기</h2>
            <p className="text-sm text-gray-500">혼자서 제안서를 생성하고 관리합니다. 나중에 팀을 만들 수 있어요.</p>
          </button>
        </div>
      </div>
    </div>
  );
}
