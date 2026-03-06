"use client";

/**
 * F1: 로그인 페이지
 * - 이메일/패스워드 로그인
 * - Magic Link 로그인
 * - 신규 가입 → /onboarding
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {/* 로고 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Tenopa Proposer</h1>
          <p className="mt-1 text-sm text-gray-500">AI 제안서 자동 생성 플랫폼</p>
        </div>

        {/* 카드 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {/* 탭 */}
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            {(["login", "signup", "magic"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setMessage(null); }}
                className={`flex-1 text-sm py-1.5 rounded-md transition-colors font-medium ${
                  mode === m
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {m === "login" ? "로그인" : m === "signup" ? "회원가입" : "Magic Link"}
              </button>
            ))}
          </div>

          {message && (
            <div
              className={`mb-4 rounded-lg px-4 py-3 text-sm ${
                message.type === "error"
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : "bg-green-50 text-green-700 border border-green-200"
              }`}
            >
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="you@example.com"
              />
            </div>

            {mode !== "magic" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="8자 이상"
                  minLength={8}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
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
