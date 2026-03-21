import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Proposal Architect — 프로젝트 수주 성공률을 높이는 AI Coworker",
  description: "RFP 분석부터 전략 수립, 제안서 작성까지 — AI 동료와 함께하는 용역 제안",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-[#0f0f0f] text-[#ededed] antialiased">
        {children}
      </body>
    </html>
  );
}
