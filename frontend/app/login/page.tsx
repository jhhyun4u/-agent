"use client";

/**
 * F1: 로그인 페이지 — 이메일 + 비밀번호 전용
 */

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/proposals";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "error" | "success";
    text: string;
  } | null>(null);

  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;

      // 프로필 조회 → must_change_password 확인
      const { data: session } = await supabase.auth.getSession();
      const token = session.session?.access_token;
      if (token) {
        try {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (res.ok) {
            const profile = await res.json();
            if (profile.must_change_password) {
              router.push("/change-password");
              return;
            }
          } else {
            // 프로필 조회 실패 — DB 미설정 시에도 로그인 진행 (개발 모드)
          }
        } catch (err) {
          // 네트워크 오류 시에도 로그인 진행 (개발 모드)
        }
      }

      router.push(next);
      router.refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "오류가 발생했습니다.";
      setMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-[#0f0f0f]">
      {/* 좌측 브랜드 패널 */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 border-r border-[#262626]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[10px]">
            PA
          </div>
          <span className="text-[#ededed] font-semibold text-sm">
            Proposal Coworker
          </span>
        </div>
        <div>
          <blockquote className="text-[#ededed] text-xl font-medium leading-relaxed mb-4">
            &ldquo;이기는 제안서,
            <br />
            AI Coworker와 함께 만듭니다.&rdquo;
          </blockquote>
          <p className="text-[#8c8c8c] text-sm">
            프로젝트 수주 성공률을 높이는 AI Coworker
          </p>
        </div>
        <p className="text-[#8c8c8c] text-xs">&copy; 2026 tenopa</p>
      </div>

      {/* 우측 로그인 폼 */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* 모바일 로고 */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-7 h-7 rounded-md bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[10px]">
              PA
            </div>
            <span className="text-[#ededed] font-semibold text-sm">
              Proposal Coworker
            </span>
          </div>

          <h2 className="text-xl font-semibold text-[#ededed] mb-1">로그인</h2>
          <p className="text-sm text-[#8c8c8c] mb-6">계정에 로그인하세요</p>

          {message && (
            <div
              className={`mb-4 rounded-lg px-4 py-3 text-sm border ${
                message.type === "error"
                  ? "bg-red-950/40 text-red-400 border-red-900"
                  : "bg-emerald-950/40 text-emerald-400 border-emerald-900"
              }`}
            >
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#ededed] mb-1.5">
                이메일
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#ededed] mb-1.5">
                비밀번호
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
                placeholder="비밀번호 입력"
                minLength={8}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold rounded-lg py-2.5 text-sm transition-colors"
            >
              {loading ? "처리 중..." : "로그인"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0f0f0f]" />}>
      <LoginContent />
    </Suspense>
  );
}
