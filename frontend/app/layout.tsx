import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tenopa Proposer — AI 제안서 자동 생성",
  description: "RFP 분석부터 DOCX·PPTX 생성까지, 5단계 AI 파이프라인",
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
