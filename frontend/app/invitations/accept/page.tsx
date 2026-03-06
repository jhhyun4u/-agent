"use client";

/**
 * F7: 초대 수락 콜백 페이지
 * - URL: /invitations/accept?invitation_id=xxx
 * - 자동으로 초대를 수락하고 /proposals로 이동
 */

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

export default function AcceptInvitationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationId = searchParams.get("invitation_id") ?? "";

  const [state, setState] = useState<"loading" | "success" | "error">("loading");
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
        setMessage(err instanceof Error ? err.message : "초대 수락에 실패했습니다.");
      });
  }, [invitationId, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-10 text-center max-w-sm w-full">
        {state === "loading" && (
          <>
            <div className="text-4xl mb-4 animate-spin">⏳</div>
            <p className="text-gray-700 font-medium">초대를 처리하는 중...</p>
          </>
        )}
        {state === "success" && (
          <>
            <div className="text-4xl mb-4">🎉</div>
            <p className="text-gray-900 font-semibold text-lg">팀 합류 완료!</p>
            <p className="text-gray-500 text-sm mt-2">{message}</p>
            <p className="text-gray-400 text-xs mt-3">잠시 후 제안서 목록으로 이동합니다...</p>
          </>
        )}
        {state === "error" && (
          <>
            <div className="text-4xl mb-4">❌</div>
            <p className="text-gray-900 font-semibold">초대 수락 실패</p>
            <p className="text-red-600 text-sm mt-2">{message}</p>
            <button
              onClick={() => router.push("/proposals")}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
            >
              홈으로
            </button>
          </>
        )}
      </div>
    </div>
  );
}
