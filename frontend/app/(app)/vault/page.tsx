import { Metadata } from "next";
import { createClient } from "@/lib/supabase/server";
import VaultLayout from "@/components/VaultLayout";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Vault AI Chat",
  description: "조직의 지식 기반과 대화하는 AI 채팅",
};

export default async function VaultPage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getSession();
  const session = data.session;

  if (!session?.user?.id) {
    redirect("/login");
  }

  return (
    <div className="h-screen">
      <VaultLayout userId={session.user.id} />
    </div>
  );
}
