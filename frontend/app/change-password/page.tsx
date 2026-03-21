"use client";

/**
 * 비밀번호 변경 페이지 — 첫 로그인 시 임시 비밀번호 변경 강제
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("새 비밀번호가 일치하지 않습니다.");
      return;
    }

    if (newPassword.length < 8) {
      setError("비밀번호는 8자 이상이어야 합니다.");
      return;
    }

    setLoading(true);
    try {
      await api.auth.changePassword(currentPassword, newPassword);
      router.push("/proposals");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "비밀번호 변경에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f] px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-7 h-7 rounded-md bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[10px]">PA</div>
          <span className="text-[#ededed] font-semibold text-sm">Proposal Architect</span>
        </div>

        <h2 className="text-xl font-semibold text-[#ededed] mb-1">비밀번호 변경</h2>
        <p className="text-sm text-[#8c8c8c] mb-6">
          보안을 위해 임시 비밀번호를 변경해 주세요.
        </p>

        {error && (
          <div className="mb-4 rounded-lg px-4 py-3 text-sm border bg-red-950/40 text-red-400 border-red-900">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#ededed] mb-1.5">현재 비밀번호</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
              placeholder="임시 비밀번호 입력"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#ededed] mb-1.5">새 비밀번호</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
              placeholder="8자 이상"
              minLength={8}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#ededed] mb-1.5">새 비밀번호 확인</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
              placeholder="비밀번호 재입력"
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold rounded-lg py-2.5 text-sm transition-colors"
          >
            {loading ? "변경 중..." : "비밀번호 변경"}
          </button>
        </form>
      </div>
    </div>
  );
}
