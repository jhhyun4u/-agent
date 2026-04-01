"use client";

/**
 * F7: 초대 수락 콜백 페이지
 * - URL: /invitations/accept?invitation_id=xxx
 * - 자동으로 초대를 수락하고 /proposals로 이동
 */

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

function AcceptInvitationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationId = searchParams.get("invitation_id") ?? "";

  const [state, setState] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!invitationId) {
      setState("error");
      setMessage("유효하지 않은 초대 링크입니다.");
      return;
    }

    api.invitations
      .accept(invitationId)
      .then((res) => {
        setState("success");
        setMessage(res.message);
        setTimeout(() => router.push("/proposals"), 2500);
      })
      .catch((err: unknown) => {
        setState("error");
        setMessage(
          err instanceof Error ? err.message : "초대 수락에 실패했습니다.",
        );
      });
  }, [invitationId, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f] px-4">
      <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-10 text-center max-w-sm w-full">
        {state === "loading" && (
          <>
            <div className="flex justify-center mb-4">
              <div className="w-8 h-8 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
            </div>
            <p className="text-[#ededed] font-medium">초대를 처리하는 중...</p>
          </>
        )}
        {state === "success" && (
          <>
            <div className="w-12 h-12 rounded-full bg-[#3ecf8e]/15 flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-6 h-6 text-[#3ecf8e]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p className="text-[#ededed] font-semibold text-lg">
              팀 합류 완료!
            </p>
            <p className="text-[#8c8c8c] text-sm mt-2">{message}</p>
            <p className="text-[#5c5c5c] text-xs mt-3">
              잠시 후 제안서 목록으로 이동합니다...
            </p>
          </>
        )}
        {state === "error" && (
          <>
            <div className="w-12 h-12 rounded-full bg-red-400/10 flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-6 h-6 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <p className="text-[#ededed] font-semibold">초대 수락 실패</p>
            <p className="text-red-400 text-sm mt-2">{message}</p>
            <button
              onClick={() => router.push("/proposals")}
              className="mt-4 bg-[#3ecf8e] hover:bg-[#36b87e] text-black text-sm font-medium px-5 py-2 rounded-lg transition-colors"
            >
              홈으로
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f]">
          <div className="w-6 h-6 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
        </div>
      }
    >
      <AcceptInvitationContent />
    </Suspense>
  );
}
