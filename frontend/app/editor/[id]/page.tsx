"use client";

import { useParams } from "next/navigation";
import ProposalEditView from "@/components/ProposalEditView";

/**
 * /editor/[id] — 별도 창에서 열리는 편집 전용 라우트
 * AppSidebar 없이 전체화면으로 표시
 */
export default function EditorPage() {
  const { id } = useParams<{ id: string }>();
  return <ProposalEditView id={id} standalone />;
}
