"use client";

/**
 * F1: 로그인 페이지 — Supabase 스타일 다크 테마
 */

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup" | "magic";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/proposals";

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "error" | "success"; text: string } | null>(null);

  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      if (mode === "magic") {
        const { error } = await supabase.auth.signInWithOtp({
          email,
          options: { emailRedirectTo: `${window.location.origin}${next}` },
        });
        if (error) throw error;
        setMessage({ type: "success", text: "이메일을 확인해 주세요. 로그인 링크를 보냈습니다." });
        return;
      }

      if (mode === "signup") {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: `${window.location.origin}/onboarding` },
        });
        if (error) throw error;
        setMessage({ type: "success", text: "가입 확인 이메일을 보냈습니다. 이메일을 확인해 주세요." });
        return;
      }

      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      router.push(next);
      router.refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "오류가 발생했습니다.";
      setMessage({ type: "error", text: msg });
    } finally {
      setLoading(false);
    }
  }

  const TAB_LABELS: Record<Mode, string> = {
    login: "로그인",
    signup: "회원가입",
    magic: "Magic Link",
  };

  return (
    <div className="min-h-screen flex bg-[#0f0f0f]">
      {/* 좌측 브랜드 패널 */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 border-r border-[#262626]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-sm">T</div>
          <span className="text-[#ededed] font-semibold text-sm">Tenopa Proposer</span>
        </div>
        <div>
          <blockquote className="text-[#ededed] text-xl font-medium leading-relaxed mb-4">
            "RFP 하나만 업로드하면<br />AI가 제안서 전체를 작성합니다."
          </blockquote>
          <p className="text-[#8c8c8c] text-sm">5단계 Claude AI 파이프라인 · DOCX + PPTX + HWPX 자동 생성</p>
        </div>
        <p className="text-[#8c8c8c] text-xs">© 2026 Technovation Partners</p>
      </div>

      {/* 우측 로그인 폼 */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* 모바일 로고 */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-7 h-7 rounded-md bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-sm">T</div>
            <span className="text-[#ededed] font-semibold text-sm">Tenopa Proposer</span>
          </div>

          <h2 className="text-xl font-semibold text-[#ededed] mb-1">
            {mode === "login" ? "로그인" : mode === "signup" ? "계정 만들기" : "Magic Link"}
          </h2>
          <p className="text-sm text-[#8c8c8c] mb-6">
            {mode === "login"
              ? "계정에 로그인하세요"
              : mode === "signup"
              ? "새 계정을 만드세요"
              : "이메일로 링크를 받아 로그인"}
          </p>

          {/* 탭 */}
          <div className="flex border border-[#262626] rounded-lg p-0.5 mb-6 bg-[#111111]">
            {(["login", "signup", "magic"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setMessage(null); }}
                className={`flex-1 text-xs py-1.5 rounded-md transition-colors font-medium ${
                  mode === m
                    ? "bg-[#1c1c1c] text-[#ededed] shadow-sm"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {TAB_LABELS[m]}
              </button>
            ))}
          </div>

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
              <label className="block text-sm font-medium text-[#ededed] mb-1.5">이메일</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
                placeholder="you@company.com"
              />
            </div>

            {mode !== "magic" && (
              <div>
                <label className="block text-sm font-medium text-[#ededed] mb-1.5">비밀번호</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
                  placeholder="8자 이상"
                  minLength={8}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold rounded-lg py-2.5 text-sm transition-colors"
            >
              {loading
                ? "처리 중..."
                : mode === "login"
                ? "로그인"
                : mode === "signup"
                ? "가입하기"
                : "Magic Link 전송"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
