"use client";

/**
 * 개인 설정 페이지 — 프로필 + 알림 + 표시
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, NotificationSettings } from "@/lib/api";

type Tab = "profile" | "notifications" | "display";

// ── 이메일 카테고리 정의 ──

const EMAIL_CATEGORIES = [
  { key: "email_monitoring", label: "공고 모니터링", desc: "추천 공고 \u00B7 마감 임박 \u00B7 일일 요약" },
  { key: "email_proposal", label: "제안서 작성", desc: "검토 및 승인 요청 \u00B7 AI 작업 결과" },
  { key: "email_bidding", label: "입찰 \u00B7 성과", desc: "비딩 \u00B7 수주 결과" },
  { key: "email_learning", label: "지식 \u00B7 학습", desc: "회고 \u00B7 KB 환류 알림" },
] as const;

// ── 메인 ──

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("profile");

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <h1 className="text-sm font-semibold text-[#ededed]">내 설정</h1>
        <p className="text-xs text-[#8c8c8c] mt-0.5">프로필, 알림, 표시 설정을 관리합니다</p>
      </div>

      <div className="border-b border-[#262626] px-6 shrink-0">
        <div className="flex">
          {([
            { key: "profile" as Tab, label: "프로필" },
            { key: "notifications" as Tab, label: "알림" },
            { key: "display" as Tab, label: "표시" },
          ]).map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? "border-[#3ecf8e] text-[#ededed]"
                  : "border-transparent text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto px-6 py-5">
        {tab === "profile" && <ProfileTab />}
        {tab === "notifications" && <NotificationsTab />}
        {tab === "display" && <DisplayTab />}
      </div>
    </div>
  );
}

// ── 프로필 탭 ──

interface UserProfile {
  name?: string;
  email?: string;
  role?: string;
  team_name?: string;
  division_name?: string;
}

function ProfileTab() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.auth.me();
        setProfile(data as UserProfile);
      } catch {
        /* 실패 시 빈 상태 */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>;

  const ROLE_LABELS: Record<string, string> = {
    admin: "관리자",
    executive: "경영진",
    director: "본부장",
    lead: "팀장",
    member: "팀원",
  };

  return (
    <div className="max-w-lg space-y-5">
      <div className="rounded-lg border border-[#262626] bg-[#111111] p-5 space-y-3">
        <InfoRow label="이름" value={profile.name || "-"} />
        <InfoRow label="이메일" value={profile.email || "-"} />
        <InfoRow
          label="소속"
          value={
            [profile.division_name, profile.team_name].filter(Boolean).join(" > ") || "-"
          }
        />
        <InfoRow label="역할" value={ROLE_LABELS[profile.role || ""] || profile.role || "-"} />
      </div>

      <button
        onClick={() => router.push("/change-password")}
        className="text-xs text-[#3ecf8e] hover:underline"
      >
        비밀번호 변경
      </button>

      <p className="text-xs text-[#5c5c5c]">
        프로필 정보는 조직 계정에서 자동 동기화됩니다.
      </p>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-xs text-[#8c8c8c]">{label}</span>
      <span className="text-sm text-[#ededed]">{value}</span>
    </div>
  );
}

// ── 알림 탭 ──

function NotificationsTab() {
  const [settings, setSettings] = useState<Partial<NotificationSettings>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await api.notifications.getSettings();
        setSettings(data);
      } catch {
        setError("알림 설정 조회 실패");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleToggle(key: string, value: boolean) {
    setSaving(key);
    setError("");
    const prev = { ...settings };
    setSettings((s) => ({ ...s, [key]: value }));

    try {
      await api.notifications.updateSettings({ [key]: value });
    } catch {
      setSettings(prev);
      setError("설정 저장에 실패했습니다.");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>;

  const emailEnabled = settings.email_enabled;

  return (
    <div className="max-w-lg space-y-5">
      {/* 채널 설정 */}
      <div className="rounded-lg border border-[#262626] bg-[#111111] p-5 space-y-3">
        <h3 className="text-xs font-semibold text-[#8c8c8c] uppercase tracking-wide">채널 설정</h3>
        <ToggleRow
          label="Teams 알림"
          desc="Teams 채널에 Adaptive Card 발송"
          checked={settings.teams ?? true}
          onChange={(v) => handleToggle("teams", v)}
          loading={saving === "teams"}
        />
        <ToggleRow
          label="인앱 알림"
          desc="앱 내 알림 벨 표시"
          checked={settings.in_app ?? true}
          onChange={(v) => handleToggle("in_app", v)}
          loading={saving === "in_app"}
        />
      </div>

      {/* 이메일 알림 */}
      <div className="rounded-lg border border-[#262626] bg-[#111111] p-5 space-y-3">
        <h3 className="text-xs font-semibold text-[#8c8c8c] uppercase tracking-wide">이메일 알림</h3>
        {!emailEnabled && (
          <p className="text-xs text-[#5c5c5c] bg-[#1c1c1c] rounded-md px-3 py-2 border border-[#262626]">
            이메일 알림은 관리자 설정 후 사용 가능합니다.
          </p>
        )}
        {EMAIL_CATEGORIES.map((cat) => (
          <ToggleRow
            key={cat.key}
            label={cat.label}
            desc={cat.desc}
            checked={(settings as Record<string, boolean>)[cat.key] ?? false}
            onChange={(v) => handleToggle(cat.key, v)}
            disabled={!emailEnabled}
            loading={saving === cat.key}
          />
        ))}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

function ToggleRow({
  label,
  desc,
  checked,
  onChange,
  disabled,
  loading,
}: {
  label: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
  loading?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between py-1.5 ${disabled ? "opacity-40" : ""}`}>
      <div>
        <span className="text-sm text-[#ededed]">{label}</span>
        <p className="text-xs text-[#5c5c5c]">{desc}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled || loading}
        onClick={() => onChange(!checked)}
        className={`relative w-9 h-5 rounded-full transition-colors shrink-0 ${
          checked ? "bg-[#3ecf8e]" : "bg-[#3c3c3c]"
        } ${disabled ? "cursor-not-allowed" : "cursor-pointer"}`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
            checked ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}

// ── 표시 탭 ──

function DisplayTab() {
  const [theme, setTheme] = useState<"dark" | "light" | "system">("dark");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("theme");
      if (saved === "light") setTheme("light");
      else if (!saved) setTheme("system");
    } catch { /* SSR */ }
  }, []);

  function applyTheme(t: "dark" | "light" | "system") {
    setTheme(t);
    try {
      if (t === "light") {
        localStorage.setItem("theme", "light");
        document.documentElement.classList.add("light");
      } else if (t === "dark") {
        localStorage.setItem("theme", "dark");
        document.documentElement.classList.remove("light");
      } else {
        localStorage.removeItem("theme");
        if (window.matchMedia("(prefers-color-scheme: light)").matches) {
          document.documentElement.classList.add("light");
        } else {
          document.documentElement.classList.remove("light");
        }
      }
    } catch { /* 무시 */ }
  }

  return (
    <div className="max-w-lg">
      <div className="rounded-lg border border-[#262626] bg-[#111111] p-5">
        <h3 className="text-xs font-semibold text-[#8c8c8c] uppercase tracking-wide mb-3">테마</h3>
        <div className="flex gap-3">
          {([
            { key: "dark" as const, label: "다크" },
            { key: "light" as const, label: "라이트" },
            { key: "system" as const, label: "시스템 설정" },
          ]).map((opt) => (
            <label key={opt.key} className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="theme"
                checked={theme === opt.key}
                onChange={() => applyTheme(opt.key)}
                className="accent-[#3ecf8e]"
              />
              <span className="text-sm text-[#ededed]">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
