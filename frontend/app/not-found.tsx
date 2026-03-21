import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center px-6">
      <div className="text-center max-w-md">
        <h2 className="text-lg font-semibold text-[#ededed] mb-2">
          페이지를 찾을 수 없습니다
        </h2>
        <p className="text-sm text-[#8c8c8c] mb-6">
          요청한 페이지가 존재하지 않거나 이동되었습니다.
        </p>
        <Link
          href="/dashboard"
          className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] text-sm font-medium rounded hover:bg-[#2db87a] transition-colors inline-block"
        >
          대시보드로 이동
        </Link>
      </div>
    </div>
  );
}
