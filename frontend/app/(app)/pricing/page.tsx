"use client";

/**
 * 비딩 가격 시뮬레이터 대시보드
 *
 * /pricing
 */

import Link from "next/link";
import PricingSimulator from "@/components/pricing/PricingSimulator";

export default function PricingPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#ededed]">비딩 가격 시뮬레이터</h1>
          <p className="text-sm text-[#8c8c8c] mt-0.5">
            조달방식·포지셔닝·경쟁환경을 반영한 최적 입찰가 시뮬레이션
          </p>
        </div>
        <Link
          href="/pricing/history"
          className="text-sm text-[#8c8c8c] hover:text-[#ededed] border border-[#333] rounded px-3 py-1.5 transition-colors"
        >
          시뮬레이션 이력
        </Link>
      </div>

      {/* 시뮬레이터 */}
      <PricingSimulator />
    </div>
  );
}
