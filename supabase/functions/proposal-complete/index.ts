/**
 * proposal-complete Edge Function
 *
 * Phase 5 완료 시 제안서 소유자에게 완료 이메일 발송 (Resend).
 *
 * 입력 payload:
 *   { proposal_id: string, owner_email?: string, proposal_title?: string }
 *
 * Secrets (Supabase Dashboard > Edge Functions > Secrets):
 *   RESEND_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, FRONTEND_URL
 */

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const FRONTEND_URL = Deno.env.get("FRONTEND_URL") ?? "http://localhost:3000";
const FROM_EMAIL = "Tenopa Proposer <noreply@tenopa.ai>";

serve(async (req: Request) => {
  if (req.method !== "POST") {
    return json({ error: "Method Not Allowed" }, 405);
  }

  let payload: { proposal_id?: string; owner_email?: string; proposal_title?: string };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  const { proposal_id, owner_email: directEmail, proposal_title: directTitle } = payload;
  if (!proposal_id) {
    return json({ error: "proposal_id is required" }, 400);
  }

  let ownerEmail = directEmail ?? "";
  let proposalTitle = directTitle ?? "";

  // DB에서 정보 조회 (payload에 직접 값이 없을 때)
  if (!ownerEmail || !proposalTitle) {
    if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      return json({ error: "Supabase credentials not configured" }, 500);
    }
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    const { data: proposal, error: propErr } = await supabase
      .from("proposals")
      .select("title, owner_id")
      .eq("id", proposal_id)
      .single();

    if (propErr || !proposal) {
      return json({ error: "proposal not found" }, 404);
    }

    proposalTitle = proposalTitle || proposal.title;

    if (!ownerEmail) {
      const { data: userData, error: userErr } =
        await supabase.auth.admin.getUserById(proposal.owner_id);
      if (userErr || !userData?.user?.email) {
        return json({ error: "owner not found" }, 404);
      }
      ownerEmail = userData.user.email;
    }
  }

  if (!RESEND_API_KEY) {
    return json({ error: "RESEND_API_KEY not configured" }, 500);
  }

  const proposalUrl = `${FRONTEND_URL}/proposals/${proposal_id}`;

  const emailRes = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: FROM_EMAIL,
      to: [ownerEmail],
      subject: `[Tenopa] 제안서 생성 완료: ${proposalTitle}`,
      html: `
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:32px 24px">
          <h2 style="color:#111827;margin-bottom:8px">제안서 생성이 완료되었습니다</h2>
          <p style="color:#6b7280;margin-top:0">5단계 AI 분석이 모두 완료되었습니다.</p>

          <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px 20px;margin:24px 0">
            <p style="margin:0;font-size:15px;font-weight:600;color:#166534">${proposalTitle}</p>
            <p style="margin:6px 0 0;font-size:13px;color:#15803d">생성 완료 ✓</p>
          </div>

          <p style="color:#374151">DOCX 제안서와 PPTX 요약본을 지금 바로 다운로드하세요.</p>

          <a href="${proposalUrl}"
             style="display:inline-block;background:#2563eb;color:#fff;padding:12px 24px;
                    border-radius:6px;text-decoration:none;font-weight:600;margin-top:8px">
            제안서 확인하기
          </a>

          <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0"/>
          <p style="color:#9ca3af;font-size:12px;margin:0">
            Tenopa Proposer — AI 제안서 자동 생성 플랫폼
          </p>
        </div>
      `,
    }),
  });

  if (!emailRes.ok) {
    const errText = await emailRes.text();
    console.error(`Resend error: ${emailRes.status} ${errText}`);
    return json({ error: "email send failed", detail: errText }, 500);
  }

  return json({ success: true, email: ownerEmail });
});

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
