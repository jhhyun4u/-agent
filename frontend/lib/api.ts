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
    const detail = err.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
      : (typeof detail === "string" ? detail : "API 오류");
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── 제안서 ────────────────────────────────────────────────────────────

export type ProposalStatus =
  | "initialized"
  | "processing"
  | "running"
  | "completed"
  | "failed";

export interface ProposalVersion {
  id: string;
  version: number;
  status: string;
  phases_completed: number;
  created_at: string;
}

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

// ── 자료 관리 타입 ────────────────────────────────────────────────────

export interface Section {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  is_public: boolean;
  use_count: number;
  owner_id: string;
  team_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArchiveItem extends ProposalSummary {
  notes: string | null;
}

export interface AssetItem {
  id: string;
  owner_id: string;
  team_id: string | null;
  filename: string;
  storage_path: string;
  file_type: string;
  status: "pending" | "processing" | "done" | "failed";
  created_at: string;
}

export interface FormTemplate {
  id: string;
  owner_id: string;
  team_id: string | null;
  title: string;
  agency: string | null;
  category: string | null;
  description: string | null;
  storage_path: string;
  file_type: string;
  is_public: boolean;
  use_count: number;
  created_at: string;
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

    versions(id: string) {
      return request<{ versions: ProposalVersion[] }>(
        "GET",
        `/v3.1/proposals/${id}/versions`
      );
    },

    newVersion(id: string) {
      return request<{ proposal_id: string; version: number; status: string }>(
        "POST",
        `/v3.1/proposals/${id}/new-version`
      );
    },

    retryFromPhase(id: string, phaseNum: number) {
      return request<{ proposal_id: string; status: string }>(
        "POST",
        `/v3.1/proposals/${id}/execute?start_phase=${phaseNum}`
      );
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

  sections: {
    list(params?: { scope?: string; category?: string; q?: string }) {
      const qs = new URLSearchParams();
      if (params?.scope) qs.set("scope", params.scope);
      if (params?.category) qs.set("category", params.category);
      if (params?.q) qs.set("q", params.q);
      return request<{ sections: Section[] }>("GET", `/resources/sections?${qs}`);
    },
    create(data: {
      title: string;
      category: string;
      content: string;
      tags?: string[];
      is_public?: boolean;
      team_id?: string;
    }) {
      return request<{ section_id: string; title: string; category: string }>(
        "POST",
        "/resources/sections",
        data
      );
    },
    update(
      id: string,
      data: Partial<{
        title: string;
        category: string;
        content: string;
        tags: string[];
        is_public: boolean;
      }>
    ) {
      return request("PUT", `/resources/sections/${id}`, data);
    },
    delete(id: string) {
      return request("DELETE", `/resources/sections/${id}`);
    },
  },

  assets: {
    upload(formData: FormData) {
      return request<{ asset_id: string; filename: string; status: string }>(
        "POST",
        "/assets",
        formData,
        true
      );
    },
    list() {
      return request<{ assets: AssetItem[] }>("GET", "/assets");
    },
    delete(assetId: string) {
      return request("DELETE", `/assets/${assetId}`);
    },
  },

  archive: {
    list(params?: { scope?: string; win_result?: string; page?: number }) {
      const qs = new URLSearchParams();
      if (params?.scope) qs.set("scope", params.scope);
      if (params?.win_result) qs.set("win_result", params.win_result);
      if (params?.page) qs.set("page", String(params.page));
      return request<{
        items: ArchiveItem[];
        page: number;
        page_size: number;
        total: number;
        pages: number;
      }>("GET", `/archive?${qs}`);
    },
  },

  formTemplates: {
    list(params?: { agency?: string; category?: string; scope?: string }) {
      const qs = new URLSearchParams();
      if (params?.agency) qs.set("agency", params.agency);
      if (params?.category) qs.set("category", params.category);
      if (params?.scope) qs.set("scope", params.scope);
      return request<{ templates: FormTemplate[] }>("GET", `/form-templates?${qs}`);
    },
    upload(formData: FormData) {
      return request<{ template_id: string; title: string }>(
        "POST", "/form-templates", formData, true
      );
    },
    update(id: string, data: Partial<{ title: string; agency: string; category: string; description: string; is_public: boolean }>) {
      return request("PATCH", `/form-templates/${id}`, data);
    },
    delete(id: string) {
      return request("DELETE", `/form-templates/${id}`);
    },
  },

  bids: {
    getProfile(teamId: string) {
      return request<{ data: BidProfile | null }>("GET", `/teams/${teamId}/bid-profile`);
    },
    upsertProfile(teamId: string, data: BidProfileInput) {
      return request<{ data: BidProfile }>("PUT", `/teams/${teamId}/bid-profile`, data);
    },
    listPresets(teamId: string) {
      return request<{ data: SearchPreset[] }>("GET", `/teams/${teamId}/search-presets`);
    },
    createPreset(teamId: string, data: SearchPresetInput) {
      return request<{ data: SearchPreset }>("POST", `/teams/${teamId}/search-presets`, data);
    },
    updatePreset(teamId: string, presetId: string, data: SearchPresetInput) {
      return request<{ data: SearchPreset }>("PUT", `/teams/${teamId}/search-presets/${presetId}`, data);
    },
    deletePreset(teamId: string, presetId: string) {
      return request<void>("DELETE", `/teams/${teamId}/search-presets/${presetId}`);
    },
    activatePreset(teamId: string, presetId: string) {
      return request<{ data: SearchPreset }>("POST", `/teams/${teamId}/search-presets/${presetId}/activate`);
    },
    triggerFetch(teamId: string) {
      return request<{ status: string; message: string }>("POST", `/teams/${teamId}/bids/fetch`);
    },
    getRecommendations(teamId: string, refresh = false) {
      return request<RecommendationsResponse>("GET", `/teams/${teamId}/bids/recommendations${refresh ? "?refresh=true" : ""}`);
    },
    getDetail(bidNo: string, teamId?: string) {
      const qs = teamId ? `?team_id=${teamId}` : "";
      return request<{ data: { announcement: BidAnnouncement; recommendation: BidRecommendation | null } }>("GET", `/bids/${bidNo}${qs}`);
    },
    createProposalFromBid(bidNo: string) {
      return request<{ data: { bid_no: string; bid_title: string; rfp_content: string } }>("POST", `/proposals/from-bid/${bidNo}`);
    },
  },

  stats: {
    winRate(scope: "personal" | "team" | "company" = "personal") {
      return request<WinRateStats>("GET", `/stats/win-rate?scope=${scope}`);
    },
  },

  calendar: {
    list(params?: { scope?: string; status?: string }) {
      const qs = new URLSearchParams(
        params as Record<string, string>
      ).toString();
      return request<{ items: CalendarItem[] }>(
        "GET",
        `/calendar${qs ? "?" + qs : ""}`
      );
    },
    create(data: {
      title: string;
      agency?: string;
      deadline: string;
      proposal_id?: string;
    }) {
      return request<CalendarItem>("POST", "/calendar", data);
    },
    update(
      id: string,
      data: Partial<{
        title: string;
        agency: string;
        deadline: string;
        proposal_id: string;
        status: string;
      }>
    ) {
      return request<CalendarItem>("PUT", `/calendar/${id}`, data);
    },
    delete(id: string) {
      return request<void>("DELETE", `/calendar/${id}`);
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

export interface WinRateStats {
  overall: { total: number; won: number; rate: number };
  by_agency: Array<{
    agency: string;
    total: number;
    won: number;
    rate: number;
  }>;
  by_month: Array<{
    month: string;
    total: number;
    won: number;
    rate: number;
  }>;
}

// ── 입찰 추천 타입 ─────────────────────────────────────────────────────

export interface BidProfile {
  id: string;
  team_id: string;
  expertise_areas: string[];
  tech_keywords: string[];
  past_projects: string;
  company_size: string | null;
  certifications: string[];
  business_registration_type: string | null;
  employee_count: number | null;
  founded_year: number | null;
  updated_at: string;
}

export interface BidProfileInput {
  expertise_areas: string[];
  tech_keywords: string[];
  past_projects: string;
  company_size?: string;
  certifications: string[];
  business_registration_type?: string;
  employee_count?: number;
  founded_year?: number;
}

export interface SearchPreset {
  id: string;
  team_id: string;
  name: string;
  keywords: string[];
  min_budget: number;
  min_days_remaining: number;
  bid_types: string[];
  preferred_agencies: string[];
  announce_date_range_days: number;
  is_active: boolean;
  last_fetched_at: string | null;
  created_at: string;
}

export interface SearchPresetInput {
  name: string;
  keywords: string[];
  min_budget: number;
  min_days_remaining: number;
  bid_types: string[];
  preferred_agencies: string[];
  announce_date_range_days: number;
}

export interface RecommendationReason {
  category: string;
  reason: string;
  strength: "high" | "medium" | "low";
}

export interface RiskFactor {
  risk: string;
  level: "high" | "medium" | "low";
}

export interface RecommendedBid {
  bid_no: string;
  bid_title: string;
  agency: string;
  budget_amount: number | null;
  deadline_date: string | null;
  days_remaining: number | null;
  qualification_status: "pass" | "ambiguous";
  qualification_notes: string | null;
  match_score: number;
  match_grade: string;
  recommendation_summary: string;
  recommendation_reasons: RecommendationReason[];
  risk_factors: RiskFactor[];
  win_probability_hint: string;
  recommended_action: string;
}

export interface ExcludedBid {
  bid_no: string;
  bid_title: string;
  agency: string;
  budget_amount: number | null;
  deadline_date: string | null;
  qualification_status: "fail";
  disqualification_reason: string | null;
}

export interface RecommendationsResponse {
  data: { recommended: RecommendedBid[]; excluded: ExcludedBid[] };
  meta: { total_fetched: number; analyzed_at: string };
}

export interface BidAnnouncement {
  bid_no: string;
  bid_title: string;
  agency: string;
  bid_type: string | null;
  budget_amount: number | null;
  deadline_date: string | null;
  days_remaining: number | null;
  content_text: string | null;
  qualification_available: boolean;
}

export interface BidRecommendation {
  qualification_status: "pass" | "fail" | "ambiguous";
  disqualification_reason: string | null;
  qualification_notes: string | null;
  match_score: number | null;
  match_grade: string | null;
  recommendation_summary: string | null;
  recommendation_reasons: RecommendationReason[] | null;
  risk_factors: RiskFactor[] | null;
  win_probability_hint: string | null;
  recommended_action: string | null;
}

export interface CalendarItem {
  id: string;
  title: string;
  agency: string | null;
  deadline: string; // ISO string
  proposal_id: string | null;
  status: "open" | "submitted" | "won" | "lost";
  created_at: string;
}
