"use client";

/**
 * 온보딩 — 셀프 가입 비활성화로 인해 /proposals로 리다이렉트
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OnboardingPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/proposals");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f]">
      <p className="text-[#8c8c8c] text-sm">리다이렉트 중...</p>
    </div>
  );
}
