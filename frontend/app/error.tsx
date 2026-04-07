"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        <h2 className="text-lg font-semibold text-[#ededed] mb-2">
          오류가 발생했습니다
        </h2>
        <p className="text-sm text-[#8c8c8c] mb-6">
          {error.message ||
            "예기치 않은 문제가 발생했습니다. 다시 시도해주세요."}
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] text-sm font-medium rounded hover:bg-[#2db87a] transition-colors"
        >
          다시 시도
        </button>
      </div>
    </div>
  );
}
