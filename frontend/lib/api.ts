/**
 * FastAPI 백엔드 API 클라이언트 (F9)
 *
 * - 모든 요청에 Supabase Bearer 토큰 자동 첨부
 * - 401 응답 → 세션 초기화 + /login 리다이렉트
 */

import { createClient } from "@/lib/supabase/client";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function getToken(): Promise<string> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? "";
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  isFormData = false
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (!isFormData) headers["Content-Type"] = "application/json";

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isFormData
      ? (body as FormData)
      : body !== undefined
      ? JSON.stringify(body)
      : undefined,
  });

  if (res.status === 401) {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API 오류");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── 제안서 ────────────────────────────────────────────────────────────

export type ProposalStatus =
  | "initialized"
  | "processing"
  | "completed"
  | "failed";

export interface ProposalSummary {
  id: string;
  title: string;
  status: ProposalStatus;
  owner_id: string;
  team_id: string | null;
  current_phase: string | null;
  phases_completed: number;
  win_result: string | null;
  bid_amount: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProposalStatus_ {
  proposal_id: string;
  rfp_title: string;
  client_name: string;
  status: ProposalStatus;
  current_phase: string;
  phases_completed: number;
  created_at: string;
  error: string;
}

export const api = {
  proposals: {
    list(params?: { q?: string; status?: string; page?: number }) {
      const qs = new URLSearchParams();
      if (params?.q) qs.set("q", params.q);
      if (params?.status) qs.set("status", params.status);
      if (params?.page) qs.set("page", String(params.page));
      return request<{ items: ProposalSummary[]; page: number; page_size: number }>(
        "GET",
        `/proposals?${qs}`
      );
    },

    generate(formData: FormData) {
      return request<{ proposal_id: string; status: string }>(
        "POST",
        "/v3.1/proposals/generate",
        formData,
        true
      );
    },

    status(id: string) {
      return request<ProposalStatus_>("GET", `/v3.1/proposals/${id}/status`);
    },

    result(id: string) {
      return request<{
        proposal_id: string;
        status: string;
        rfp_title: string;
        phases_completed: number;
        artifacts: Record<string, unknown>;
        quality_score: number;
        docx_path: string;
        pptx_path: string;
        executive_summary: string;
      }>("GET", `/v3.1/proposals/${id}/result`);
    },

    execute(id: string) {
      return request<{ proposal_id: string; status: string }>(
        "POST",
        `/v3.1/proposals/${id}/execute`
      );
    },

    downloadUrl(id: string, type: "docx" | "pptx") {
      return `${BASE}/v3.1/proposals/${id}/download/${type}`;
    },

    updateWinResult(
      id: string,
      data: { win_result: string; bid_amount?: number; notes?: string }
    ) {
      return request("PATCH", `/proposals/${id}/win-result`, data);
    },
  },

  comments: {
    list(proposalId: string) {
      return request<{ comments: Comment_[] }>(
        "GET",
        `/proposals/${proposalId}/comments`
      );
    },
    create(proposalId: string, content: string) {
      return request<{ comment_id: string }>(
        "POST",
        `/proposals/${proposalId}/comments`,
        { content }
      );
    },
    update(commentId: string, content: string) {
      return request("PATCH", `/comments/${commentId}`, { content });
    },
    delete(commentId: string) {
      return request("DELETE", `/comments/${commentId}`);
    },
  },

  teams: {
    list() {
      return request<{ teams: TeamMembership[] }>("GET", "/teams");
    },
    create(name: string) {
      return request<{ team_id: string; name: string }>("POST", "/teams", {
        name,
      });
    },
    get(teamId: string) {
      return request<Team>("GET", `/teams/${teamId}`);
    },
    update(teamId: string, name: string) {
      return request("PATCH", `/teams/${teamId}`, { name });
    },
    delete(teamId: string) {
      return request("DELETE", `/teams/${teamId}`);
    },
    stats(teamId: string) {
      return request<TeamStats>("GET", `/teams/${teamId}/stats`);
    },

    members: {
      list(teamId: string) {
        return request<{ members: TeamMember[] }>(
          "GET",
          `/teams/${teamId}/members`
        );
      },
      updateRole(teamId: string, userId: string, role: string) {
        return request("PATCH", `/teams/${teamId}/members/${userId}`, { role });
      },
      remove(teamId: string, userId: string) {
        return request("DELETE", `/teams/${teamId}/members/${userId}`);
      },
    },

    invitations: {
      list(teamId: string) {
        return request<{ invitations: Invitation[] }>(
          "GET",
          `/teams/${teamId}/invitations`
        );
      },
      create(teamId: string, email: string, role = "member") {
        return request<{ invitation_id: string }>(
          "POST",
          `/teams/${teamId}/invitations`,
          { email, role }
        );
      },
      cancel(teamId: string, invId: string) {
        return request("DELETE", `/teams/${teamId}/invitations/${invId}`);
      },
    },
  },

  invitations: {
    accept(invitationId: string) {
      return request<{ team_id: string; role: string; message: string }>(
        "POST",
        "/invitations/accept",
        { invitation_id: invitationId }
      );
    },
  },
};

// ── 타입 ─────────────────────────────────────────────────────────────

export interface Comment_ {
  id: string;
  proposal_id: string;
  user_id: string;
  content: string;
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface TeamMembership {
  team_id: string;
  role: string;
  teams: Team;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  email: string;
  role: string;
  joined_at: string;
}

export interface TeamStats {
  total: number;
  completed: number;
  processing: number;
  failed: number;
  won: number;
  win_rate: number;
}

export interface Invitation {
  id: string;
  team_id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
}
