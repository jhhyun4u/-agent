"use client";

import { useParams } from "next/navigation";
import ProposalEditView from "@/components/ProposalEditView";

/**
 * /proposals/[id]/edit — 기존 경로 호환 유지 (import wrapper)
 */
export default function ProposalEditPage() {
  const { id } = useParams<{ id: string }>();
  return <ProposalEditView id={id} />;
}
