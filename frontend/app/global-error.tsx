"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-[#0f0f0f] text-[#ededed] flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <h2 className="text-lg font-semibold mb-2">시스템 오류</h2>
          <p className="text-sm text-[#8c8c8c] mb-6">
            {error.message || "시스템에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."}
          </p>
          <button
            onClick={reset}
            className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] text-sm font-medium rounded hover:bg-[#2db87a] transition-colors"
          >
            다시 시도
          </button>
        </div>
      </body>
    </html>
  );
}
