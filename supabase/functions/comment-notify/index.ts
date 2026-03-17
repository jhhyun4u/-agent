/**
 * comment-notify Edge Function
 *
 * 댓글 작성 시 제안서 소유자 + 팀원에게 알림 이메일 발송 (Resend).
 * 댓글 작성자 본인은 제외.
 *
 * 입력 payload:
 *   { comment_id: string }
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
const FROM_EMAIL = "용역제안 Coworker <noreply@tenopa.ai>";

serve(async (req: Request) => {
  if (req.method !== "POST") {
    return json({ error: "Method Not Allowed" }, 405);
  }

  let payload: { comment_id?: string };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "Invalid JSON" }, 400);
  }

  const { comment_id } = payload;
  if (!comment_id) {
    return json({ error: "comment_id is required" }, 400);
  }

  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    return json({ error: "Supabase credentials not configured" }, 500);
  }
  if (!RESEND_API_KEY) {
    return json({ error: "RESEND_API_KEY not configured" }, 500);
  }

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

  // 댓글 조회
  const { data: comment, error: commentErr } = await supabase
    .from("comments")
    .select("proposal_id, user_id, content")
    .eq("id", comment_id)
    .single();

  if (commentErr || !comment) {
    return json({ error: "comment not found" }, 404);
  }

  // 제안서 조회
  const { data: proposal, error: propErr } = await supabase
    .from("proposals")
    .select("title, team_id, owner_id")
    .eq("id", comment.proposal_id)
    .single();

  if (propErr || !proposal) {
    return json({ error: "proposal not found" }, 404);
  }

  // 댓글 작성자 정보
  const { data: commenterData } = await supabase.auth.admin.getUserById(comment.user_id);
  const commenterEmail = commenterData?.user?.email ?? "";
  const commenterName =
    commenterData?.user?.user_metadata?.full_name ??
    commenterData?.user?.user_metadata?.name ??
    commenterEmail.split("@")[0];

  // 알림 대상 user_id 수집 (소유자 + 팀원, 작성자 제외)
  const notifyUserIds = new Set<string>();
  notifyUserIds.add(proposal.owner_id);

  if (proposal.team_id) {
    const { data: members } = await supabase
      .from("team_members")
      .select("user_id")
      .eq("team_id", proposal.team_id);
    (members ?? []).forEach((m: { user_id: string }) => notifyUserIds.add(m.user_id));
  }

  notifyUserIds.delete(comment.user_id); // 작성자 본인 제외

  if (notifyUserIds.size === 0) {
    return json({ success: true, sent: 0, reason: "no recipients" });
  }

  // 이메일 주소 수집
  const recipientEmails: string[] = [];
  for (const uid of notifyUserIds) {
    const { data: ud } = await supabase.auth.admin.getUserById(uid);
    if (ud?.user?.email) recipientEmails.push(ud.user.email);
  }

  if (recipientEmails.length === 0) {
    return json({ success: true, sent: 0, reason: "no email addresses found" });
  }

  const preview =
    comment.content.length > 120
      ? comment.content.slice(0, 120) + "…"
      : comment.content;
  const proposalUrl = `${FRONTEND_URL}/proposals/${comment.proposal_id}`;

  // Resend 일괄 발송
  const emailRes = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: FROM_EMAIL,
      to: recipientEmails,
      subject: `[Tenopa] 새 댓글: ${proposal.title}`,
      html: `
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:32px 24px">
          <h2 style="color:#111827;margin-bottom:8px">새 댓글이 작성되었습니다</h2>

          <p style="color:#374151;margin-top:0">
            <strong>${commenterName}</strong>님이
            <strong>${proposal.title}</strong>에 댓글을 남겼습니다.
          </p>

          <blockquote style="border-left:4px solid #e5e7eb;padding:12px 16px;
                             color:#374151;background:#f9fafb;border-radius:4px;
                             margin:16px 0;font-style:italic">
            ${preview}
          </blockquote>

          <a href="${proposalUrl}"
             style="display:inline-block;background:#2563eb;color:#fff;padding:12px 24px;
                    border-radius:6px;text-decoration:none;font-weight:600;margin-top:8px">
            댓글 확인하기
          </a>

          <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0"/>
          <p style="color:#9ca3af;font-size:12px;margin:0">
            용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker
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

  return json({ success: true, sent: recipientEmails.length });
});

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
