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
  | "failed"
  | "cancelled"
  | "paused";

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
  positioning: string | null;
  win_result: string | null;
  bid_amount: number | null;
  deadline: string | null;
  client_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProposalResult {
  id: string;
  proposal_id: string;
  result: "won" | "lost" | "void";
  final_price: number | null;
  tech_score: number | null;
  price_score: number | null;
  total_score: number | null;
  rank: number | null;
  total_bidders: number | null;
  winner_name: string | null;
  feedback_notes: string | null;
  created_at: string;
}

export interface ProposalResultCreate {
  result: "won" | "lost" | "void";
  final_price?: number;
  tech_score?: number;
  price_score?: number;
  total_score?: number;
  rank?: number;
  total_bidders?: number;
  winner_name?: string;
  feedback_notes?: string;
}

export interface Lesson {
  id: string;
  strategy_summary: string | null;
  failure_category: string | null;
  failure_detail: string | null;
  improvements: string | null;
  positioning: string | null;
  result: string | null;
  created_at: string;
}

export interface LessonCreate {
  title: string;
  description: string;
  category?: string;
}

export interface SectionLock {
  section_id: string;
  locked_by: string;
  locked_by_name?: string;
  locked_at: string;
  expires_at: string;
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

// ── 프로젝트 파일 타입 ────────────────────────────────────────────────

export interface ProposalFile {
  id: string;
  proposal_id: string;
  category: string;
  filename: string;
  storage_path: string;
  file_type: string | null;
  file_size: number | null;
  uploaded_by: string | null;
  description: string | null;
  created_at: string;
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

// ── AUTH 요청 (/api/auth/*) ─────────────────────────────────────────

async function authRequest<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || "API 오류");
  }
  return res.json();
}

export const api = {
  // ── 인증 ──────────────────────────────────────────────────────────
  auth: {
    changePassword(currentPassword: string, newPassword: string) {
      return authRequest<{ message: string }>("POST", "/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
    },
    me() {
      return authRequest<Record<string, unknown>>("GET", "/auth/me");
    },
  },

  // ── 관리자 ────────────────────────────────────────────────────────
  admin: {
    // 조직
    listOrganizations() {
      return request<Array<{ id: string; name: string; created_at: string }>>("GET", "/admin/organizations");
    },
    createOrganization(name: string) {
      return request<{ id: string; name: string }>("POST", "/admin/organizations", { name });
    },
    // 본부
    listDivisions(orgId?: string) {
      return request<Array<{ id: string; org_id: string; name: string; created_at: string }>>(
        "GET", `/admin/divisions${orgId ? `?org_id=${orgId}` : ""}`
      );
    },
    createDivision(name: string, orgId: string) {
      return request<{ id: string; name: string }>("POST", "/admin/divisions", { name, org_id: orgId });
    },
    // 팀
    listTeams(divisionId?: string) {
      return request<Array<{ id: string; division_id: string; name: string; teams_webhook_url?: string; created_at: string; divisions?: { name: string; org_id: string } }>>(
        "GET", `/admin/teams${divisionId ? `?division_id=${divisionId}` : ""}`
      );
    },
    createTeam(name: string, divisionId: string, teamsWebhookUrl?: string) {
      return request<{ id: string; name: string }>("POST", "/admin/teams", {
        name, division_id: divisionId, ...(teamsWebhookUrl ? { teams_webhook_url: teamsWebhookUrl } : {}),
      });
    },
    updateTeam(teamId: string, data: { name?: string; teams_webhook_url?: string }) {
      return request<{ id: string; name: string }>("PATCH", `/admin/teams/${teamId}`, data);
    },
    // 사용자
    createUser(data: {
      email: string;
      name: string;
      role?: string;
      org_id: string;
      team_id?: string;
      division_id?: string;
      password?: string;
    }) {
      return request<Record<string, unknown>>("POST", "/admin/users", data);
    },
    bulkCreateUsers(file: File) {
      const formData = new FormData();
      formData.append("file", file);
      return request<{
        total: number;
        success_count: number;
        failed_count: number;
        results: Array<Record<string, unknown>>;
      }>("POST", "/admin/users/bulk", formData, true);
    },
    bulkSetupOrg(file: File) {
      const formData = new FormData();
      formData.append("file", file);
      return request<Record<string, unknown>>("POST", "/admin/setup/bulk", formData, true);
    },
    resetPassword(userId: string, newPassword?: string) {
      return request<{ user_id: string; temp_password: string }>(
        "POST",
        `/admin/users/${userId}/reset-password`,
        newPassword ? { new_password: newPassword } : {}
      );
    },
    listUsers(params?: { role?: string; team_id?: string; status?: string; page?: number; page_size?: number }) {
      return request<{ users: Array<Record<string, unknown>>; total: number }>(
        "GET",
        `/users${_qs(params)}`
      );
    },
    updateUser(userId: string, data: Record<string, unknown>) {
      return request<Record<string, unknown>>("PATCH", `/admin/users/${userId}`, data);
    },
    deactivateUser(userId: string) {
      return request<{ message: string }>("POST", `/admin/users/${userId}/deactivate`);
    },
  },

  proposals: {
    list(params?: { q?: string; status?: string; page?: number; scope?: string; search?: string }) {
      const qs = new URLSearchParams();
      if (params?.q) qs.set("q", params.q);
      if (params?.status) qs.set("status", params.status);
      if (params?.page) qs.set("page", String(params.page));
      if (params?.scope) qs.set("scope", params.scope);
      if (params?.search) qs.set("search", params.search);
      return request<{ items: ProposalSummary[]; total: number }>(
        "GET",
        `/proposals?${qs}`
      );
    },

    /** 프로젝트 생성 — 공고 검색(STEP 0)부터 시작 */
    create(data: { search_keywords?: string; industry?: string }) {
      return request<{ proposal_id: string; status: string }>(
        "POST",
        "/proposals",
        data
      );
    },

    /** 프로젝트 생성 — RFP 파일 업로드 기반 */
    createFromRfp(formData: FormData) {
      return request<{ proposal_id: string; status: string }>(
        "POST",
        "/proposals/from-rfp",
        formData,
        true
      );
    },

    /** 프로젝트 생성 — 공고 모니터링에서 제안 시작 */
    createFromBid(bidNo: string) {
      return request<{ proposal_id: string; title: string; entry_point: string; bid_no: string }>(
        "POST",
        "/proposals/from-bid",
        { bid_no: bidNo }
      );
    },

    get(id: string) {
      return request<ProposalStatus_>("GET", `/proposals/${id}`);
    },

    downloadUrl(id: string, type: "docx" | "pptx" | "hwpx") {
      return `${BASE}/proposals/${id}/download/${type}`;
    },

    updateWinResult(
      id: string,
      data: { win_result: string; bid_amount?: number; notes?: string }
    ) {
      return request("PATCH", `/proposals/${id}/win-result`, data);
    },

    // 성과 추적 (§12-9)
    getResult(id: string) {
      return request<ProposalResult>("GET", `/proposals/${id}/result`);
    },
    registerResult(id: string, data: ProposalResultCreate) {
      return request<{ status: string; result: string }>(
        "POST",
        `/proposals/${id}/result`,
        data
      );
    },
    updateResult(id: string, data: Partial<ProposalResultCreate>) {
      return request("PUT", `/proposals/${id}/result`, data);
    },
    getLessons(id: string) {
      return request<{ items: Lesson[]; total: number }>(
        "GET",
        `/proposals/${id}/lessons`
      );
    },
    createLesson(id: string, data: LessonCreate) {
      return request<{ status: string; lesson_id: string }>(
        "POST",
        `/proposals/${id}/lessons`,
        data
      );
    },

    // 프로젝트 파일 관리 (GAP-1~6)
    listFiles(id: string, category?: string) {
      const qs = category ? `?category=${category}` : "";
      return request<{ files: ProposalFile[] }>("GET", `/proposals/${id}/files${qs}`);
    },
    uploadFile(id: string, file: File, description?: string) {
      const formData = new FormData();
      formData.append("file", file);
      if (description) formData.append("description", description);
      return request<{ file_id: string; filename: string; storage_path: string }>(
        "POST", `/proposals/${id}/files`, formData, true
      );
    },
    /** 프로그레스 콜백 지원 업로드 (XMLHttpRequest) */
    uploadFileWithProgress(
      id: string,
      file: File,
      onProgress: (pct: number) => void,
      description?: string,
    ): { promise: Promise<{ file_id: string; filename: string; storage_path: string }>; abort: () => void } {
      const xhr = new XMLHttpRequest();
      const promise = new Promise<{ file_id: string; filename: string; storage_path: string }>(
        async (resolve, reject) => {
          const token = await getToken();
          const formData = new FormData();
          formData.append("file", file);
          if (description) formData.append("description", description);

          xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
          });
          xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(JSON.parse(xhr.responseText));
            } else {
              try {
                const err = JSON.parse(xhr.responseText);
                reject(new Error(typeof err.detail === "string" ? err.detail : "업로드 실패"));
              } catch { reject(new Error(`업로드 실패 (${xhr.status})`)); }
            }
          });
          xhr.addEventListener("error", () => reject(new Error("네트워크 오류")));
          xhr.addEventListener("abort", () => reject(new Error("업로드 취소됨")));

          xhr.open("POST", `${BASE}/proposals/${id}/files`);
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
          xhr.send(formData);
        },
      );
      return { promise, abort: () => xhr.abort() };
    },
    deleteFile(id: string, fileId: string) {
      return request<void>("DELETE", `/proposals/${id}/files/${fileId}`);
    },
    getFileUrl(id: string, fileId: string) {
      return request<{ url: string; filename: string; expires_in: number }>(
        "GET", `/proposals/${id}/files/${fileId}/url`
      );
    },
    /** 참고자료 일괄 ZIP 다운로드 URL */
    filesBundleUrl(id: string, category?: string) {
      const qs = category ? `?category=${category}` : "";
      return `${BASE}/proposals/${id}/files/bundle${qs}`;
    },
    deleteProposal(id: string) {
      return request<void>("DELETE", `/proposals/${id}`);
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
    getAttachments(bidNo: string, proposalId?: string) {
      const qs = proposalId ? `?proposal_id=${proposalId}` : "";
      return request<{ data: { stored_files: StoredAttachment[]; g2b_urls: G2bUrl[] } }>("GET", `/bids/${bidNo}/attachments${qs}`);
    },
    getAttachmentUrl(bidNo: string, fileName: string, proposalId?: string) {
      const qs = proposalId ? `?proposal_id=${proposalId}` : "";
      return request<{ data: { url: string; file_name: string; expires_in: number } }>("GET", `/bids/${bidNo}/attachments/${encodeURIComponent(fileName)}${qs}`);
    },
    // 적합도 스코어링 기반 공고 조회 (v2)
    scored(params: { dateFrom?: string; dateTo?: string; days?: number; minBudget?: number; minScore?: number; maxResults?: number } = {}) {
      const qs = new URLSearchParams();
      if (params.dateFrom) qs.set("date_from", params.dateFrom);
      if (params.dateTo) qs.set("date_to", params.dateTo);
      if (params.days) qs.set("days", String(params.days));
      if (params.minBudget) qs.set("min_budget", String(params.minBudget));
      if (params.minScore !== undefined) qs.set("min_score", String(params.minScore));
      if (params.maxResults) qs.set("max_results", String(params.maxResults));
      const q = qs.toString();
      return request<{ date_from: string; date_to: string; total_count: number; total_fetched: number; sources: Record<string, number>; data: ScoredBid[] }>(
        "GET", `/bids/scored${q ? `?${q}` : ""}`
      );
    },
    // 공고 모니터링 (스코프별)
    monitor(scope: "my" | "team" | "division" | "company" = "company", page = 1, showAll = false) {
      return request<{ data: MonitoredBid[]; meta: { total: number; page: number; scope: string; show_all: boolean } }>(
        "GET", `/bids/monitor?scope=${scope}&page=${page}&show_all=${showAll}`
      );
    },
    toggleBookmark(bidNo: string) {
      return request<{ bookmarked: boolean }>("POST", `/bids/${bidNo}/bookmark`);
    },
    updateStatus(bidNo: string, status: string) {
      return request<{ bid_no: string; status: string; decided_by: string }>("PUT", `/bids/${bidNo}/status`, { status });
    },
    analyzeBid(bidNo: string) {
      return request<{ data: BidAnalysis }>("GET", `/bids/${bidNo}/analysis`);
    },
  },

  stats: {
    winRate(scope: "personal" | "team" | "division" | "company" = "personal") {
      return request<WinRateStats>("GET", `/stats/win-rate?scope=${scope}`);
    },
  },

  // ── LangGraph 워크플로 (§12-1) ──────────────────────────────────────

  workflow: {
    start(proposalId: string, initialState?: Record<string, unknown>) {
      return request<WorkflowStartResult>(
        "POST",
        `/proposals/${proposalId}/start`,
        { initial_state: initialState ?? {} }
      );
    },
    getState(proposalId: string) {
      return request<WorkflowState>("GET", `/proposals/${proposalId}/state`);
    },
    resume(proposalId: string, data: WorkflowResumeData) {
      return request<WorkflowResumeResult>(
        "POST",
        `/proposals/${proposalId}/resume`,
        data
      );
    },
    getTokenUsage(proposalId: string) {
      return request<TokenUsageResponse>(
        "GET",
        `/proposals/${proposalId}/token-usage`
      );
    },
    getHistory(proposalId: string) {
      return request<{ proposal_id: string; history: WorkflowHistoryEntry[] }>(
        "GET",
        `/proposals/${proposalId}/history`
      );
    },
    streamUrl(proposalId: string) {
      return `${BASE}/proposals/${proposalId}/stream`;
    },
    goto(proposalId: string, step: string) {
      return request<{ success: boolean; restored_step: string; message: string }>(
        "POST",
        `/proposals/${proposalId}/goto/${step}`
      );
    },
    impact(proposalId: string, step: string) {
      return request<{
        step: string;
        step_number: number;
        downstream_nodes: string[];
        downstream_count: number;
        affected_steps: number[];
        message: string;
      }>("GET", `/proposals/${proposalId}/impact/${step}`);
    },

    // 섹션 잠금 (§24)
    listLocks(proposalId: string) {
      return request<{ locks: SectionLock[] }>(
        "GET",
        `/proposals/${proposalId}/sections/locks`
      );
    },
    lockSection(proposalId: string, sectionId: string) {
      return request<SectionLock>(
        "POST",
        `/proposals/${proposalId}/sections/${sectionId}/lock`
      );
    },
    unlockSection(proposalId: string, sectionId: string) {
      return request<{ released: boolean }>(
        "DELETE",
        `/proposals/${proposalId}/sections/${sectionId}/lock`
      );
    },
  },

  // ── 산출물 (§12-3) ────────────────────────────────────────────────

  artifacts: {
    get(proposalId: string, step: string) {
      return request<ArtifactData>(
        "GET",
        `/proposals/${proposalId}/artifacts/${step}`
      );
    },
    downloadDocxUrl(proposalId: string) {
      return `${BASE}/proposals/${proposalId}/download/docx`;
    },
    downloadPptxUrl(proposalId: string) {
      return `${BASE}/proposals/${proposalId}/download/pptx`;
    },
    getCompliance(proposalId: string) {
      return request<ComplianceData>(
        "GET",
        `/proposals/${proposalId}/compliance`
      );
    },
    checkCompliance(proposalId: string) {
      return request<ComplianceData>(
        "POST",
        `/proposals/${proposalId}/compliance/check`
      );
    },
    save(
      proposalId: string,
      step: string,
      content: unknown,
      changeSource = "human_edit"
    ) {
      return request<{ saved: boolean; step: string; message: string }>(
        "PUT",
        `/proposals/${proposalId}/artifacts/${step}`,
        { content, change_source: changeSource }
      );
    },
    regenerateSection(
      proposalId: string,
      step: string,
      sectionId: string,
      instructions = ""
    ) {
      return request<{
        regenerated: boolean;
        section_id: string;
        section_title: string;
        message: string;
      }>(
        "POST",
        `/proposals/${proposalId}/artifacts/${step}/sections/${sectionId}/regenerate`,
        { instructions }
      );
    },
    aiAssist(
      proposalId: string,
      text: string,
      mode: "improve" | "shorten" | "expand" | "formalize" = "improve",
      context = ""
    ) {
      return request<{
        suggestion: string;
        explanation: string;
        mode: string;
        original_length: number;
        suggestion_length: number;
      }>(
        "POST",
        `/proposals/${proposalId}/ai-assist`,
        { text, mode, context }
      );
    },
  },

  // ── 교훈 전체 검색 ────────────────────────────────────────────────
  lessons: {
    search(params?: { positioning?: string; category?: string; limit?: number; offset?: number }) {
      return request<{ items: Lesson[]; total: number }>(
        "GET",
        `/lessons${_qs(params)}`
      );
    },
  },

  // ── 분석 대시보드 (§12-13) ────────────────────────────────────────

  analytics: {
    failureReasons(params?: AnalyticsParams) {
      return request<FailureReasonsData>(
        "GET",
        `/analytics/failure-reasons${_qs(params)}`
      );
    },
    positioningWinRate(params?: AnalyticsParams) {
      return request<PositioningWinRateData>(
        "GET",
        `/analytics/positioning-win-rate${_qs(params)}`
      );
    },
    monthlyTrends(params?: AnalyticsParams) {
      return request<MonthlyTrendsData>(
        "GET",
        `/analytics/monthly-trends${_qs(params)}`
      );
    },
    winRate(params?: AnalyticsParams) {
      return request<WinRateDetailData>(
        "GET",
        `/analytics/win-rate${_qs(params)}`
      );
    },
    teamPerformance(params?: AnalyticsParams) {
      return request<TeamPerformanceData>(
        "GET",
        `/analytics/team-performance${_qs(params)}`
      );
    },
    competitor(params?: AnalyticsParams) {
      return request<CompetitorData>(
        "GET",
        `/analytics/competitor${_qs(params)}`
      );
    },
    clientWinRate(params?: AnalyticsParams) {
      return request<ClientWinRateData>(
        "GET",
        `/analytics/client-win-rate${_qs(params)}`
      );
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

  // ── 알림 (§12-10) ─────────────────────────────────────────────────────

  notifications: {
    list(params?: { is_read?: boolean; skip?: number; limit?: number }) {
      return request<{ items: Notification[]; unread_count: number }>(
        "GET",
        `/notifications${_qs(params)}`
      );
    },
    markRead(id: string) {
      return request<{ status: string }>("PUT", `/notifications/${id}/read`);
    },
    markAllRead() {
      return request<{ status: string }>("PUT", "/notifications/read-all");
    },
    getSettings() {
      return request<NotificationSettings>("GET", "/notifications/settings");
    },
    updateSettings(data: Partial<NotificationSettings>) {
      return request<NotificationSettings>(
        "PUT",
        "/notifications/settings",
        data
      );
    },
  },

  // ── KB 관리 (§13-13) ─────────────────────────────────────────────────

  kb: {
    laborRates: {
      list(params?: { agency?: string; year?: string; grade?: string }) {
        return request<{ items: LaborRate[] }>("GET", `/kb/labor-rates${_qs(params)}`);
      },
      create(data: Omit<LaborRate, "id" | "created_at" | "updated_at">) {
        return request<LaborRate>("POST", "/kb/labor-rates", data);
      },
      update(id: string, data: Partial<LaborRate>) {
        return request<LaborRate>("PUT", `/kb/labor-rates/${id}`, data);
      },
      delete(id: string) {
        return request<void>("DELETE", `/kb/labor-rates/${id}`);
      },
    },
    marketPrices: {
      list(params?: { domain?: string; year?: string }) {
        return request<{ items: MarketPrice[] }>("GET", `/kb/market-prices${_qs(params)}`);
      },
      create(data: Omit<MarketPrice, "id" | "created_at" | "updated_at">) {
        return request<MarketPrice>("POST", "/kb/market-prices", data);
      },
      update(id: string, data: Partial<MarketPrice>) {
        return request<MarketPrice>("PUT", `/kb/market-prices/${id}`, data);
      },
      delete(id: string) {
        return request<void>("DELETE", `/kb/market-prices/${id}`);
      },
    },
    content: {
      list(params?: { status?: string; type?: string }) {
        return request<{ items: KbContent[]; total: number }>("GET", `/kb/content${_qs(params)}`);
      },
      get(id: string) {
        return request<KbContentDetail>("GET", `/kb/content/${id}`);
      },
      create(data: KbContentCreate) {
        return request<KbContent>("POST", "/kb/content", data);
      },
      update(id: string, data: Partial<KbContentCreate>) {
        return request<KbContent>("PUT", `/kb/content/${id}`, data);
      },
      delete(id: string) {
        return request<void>("DELETE", `/kb/content/${id}`);
      },
      approve(id: string) {
        return request<KbContent>("POST", `/kb/content/${id}/approve`);
      },
    },
    clients: {
      list(params?: { relationship?: string; client_type?: string }) {
        return request<{ items: KbClient[]; total: number }>("GET", `/kb/clients${_qs(params)}`);
      },
      get(id: string) {
        return request<KbClientDetail>("GET", `/kb/clients/${id}`);
      },
      create(data: KbClientCreate) {
        return request<KbClient>("POST", "/kb/clients", data);
      },
      update(id: string, data: Partial<KbClientCreate>) {
        return request<KbClient>("PUT", `/kb/clients/${id}`, data);
      },
      delete(id: string) {
        return request<void>("DELETE", `/kb/clients/${id}`);
      },
    },
    competitors: {
      list(params?: { scale?: string }) {
        return request<{ items: KbCompetitor[]; total: number }>("GET", `/kb/competitors${_qs(params)}`);
      },
      get(id: string) {
        return request<KbCompetitorDetail>("GET", `/kb/competitors/${id}`);
      },
      create(data: KbCompetitorCreate) {
        return request<KbCompetitor>("POST", "/kb/competitors", data);
      },
      update(id: string, data: Partial<KbCompetitorCreate>) {
        return request<KbCompetitor>("PUT", `/kb/competitors/${id}`, data);
      },
      delete(id: string) {
        return request<void>("DELETE", `/kb/competitors/${id}`);
      },
    },
    lessons: {
      list(params?: { result?: string; positioning?: string }) {
        return request<{ items: KbLesson[]; total: number }>("GET", `/kb/lessons${_qs(params)}`);
      },
      get(id: string) {
        return request<KbLessonDetail>("GET", `/kb/lessons/${id}`);
      },
      create(data: KbLessonCreate) {
        return request<KbLesson>("POST", "/kb/lessons", data);
      },
    },
    search(q: string, areas?: string, top_k = 5) {
      return request<KbSearchResult>(
        "GET",
        `/kb/search?q=${encodeURIComponent(q)}${areas ? `&areas=${areas}` : ""}&top_k=${top_k}`
      );
    },
  },

  // PSM-16: Q&A 기록 CRUD + 검색
  qa: {
    list(proposalId: string) {
      return request<{ data: QARecord[]; count: number }>(
        "GET",
        `/proposals/${proposalId}/qa`
      );
    },
    create(proposalId: string, records: QARecordCreate[]) {
      return request<{ data: QARecord[]; count: number }>(
        "POST",
        `/proposals/${proposalId}/qa`,
        records
      );
    },
    update(proposalId: string, qaId: string, body: QARecordUpdate) {
      return request<{ data: QARecord }>(
        "PUT",
        `/proposals/${proposalId}/qa/${qaId}`,
        body
      );
    },
    delete(proposalId: string, qaId: string) {
      return request<void>("DELETE", `/proposals/${proposalId}/qa/${qaId}`);
    },
    search(query: string, category?: string, limit = 10) {
      let path = `/kb/qa/search?query=${encodeURIComponent(query)}&limit=${limit}`;
      if (category) path += `&category=${category}`;
      return request<{ data: QASearchResult[]; count: number }>("GET", path);
    },
  },

  // ── 프롬프트 진화 시스템 ──
  prompts: {
    dashboard() {
      return request<PromptDashboard>("GET", "/prompts/dashboard");
    },
    list(status = "active") {
      return request<{ prompts: PromptRegistryItem[] }>("GET", `/prompts/list?status=${status}`);
    },
    detail(promptId: string) {
      return request<PromptDetail>("GET", `/prompts/${encodeURIComponent(promptId)}/detail`);
    },
    effectiveness(promptId: string, version?: number) {
      let path = `/prompts/${encodeURIComponent(promptId)}/effectiveness`;
      if (version !== undefined) path += `?version=${version}`;
      return request<PromptEffectiveness>("GET", path);
    },
    sectionHeatmap() {
      return request<{ heatmap: SectionHeatmapItem[] }>("GET", "/prompts/section-heatmap");
    },
    suggestImprovement(promptId: string) {
      return request<PromptSuggestion>("POST", `/prompts/${encodeURIComponent(promptId)}/suggest-improvement`);
    },
    createCandidate(promptId: string, text: string, reason: string) {
      return request<{ version: number; status: string }>(
        "POST", `/prompts/${encodeURIComponent(promptId)}/create-candidate`, { text, reason }
      );
    },
    recordEditAction(body: EditActionBody) {
      return request<{ recorded: boolean }>("POST", "/prompts/edit-action", body);
    },
    experiments: {
      list(status?: string) {
        let path = "/prompts/experiments/list";
        if (status) path += `?status=${status}`;
        return request<{ experiments: PromptExperiment[] }>("GET", path);
      },
      create(body: ExperimentCreateBody) {
        return request<{ experiment_id: string; status: string }>(
          "POST", "/prompts/experiments/create", body
        );
      },
      evaluate(id: string) {
        return request<ExperimentEvaluation>("POST", `/prompts/experiments/${id}/evaluate`);
      },
      promote(id: string) {
        return request<{ promoted: boolean; version?: number }>("POST", `/prompts/experiments/${id}/promote`);
      },
      rollback(id: string) {
        return request<{ rolled_back: boolean }>("POST", `/prompts/experiments/${id}/rollback`);
      },
    },
  },
};

// ── 프롬프트 진화 타입 ──────────────────────────────────────────────

export interface PromptRegistryItem {
  prompt_id: string;
  version: number;
  source_file: string;
  status: string;
  content_hash: string;
  metadata: Record<string, unknown>;
  created_at: string;
  created_by: string;
}

export interface PromptDashboard {
  prompts: PromptRegistryItem[];
  effectiveness: PromptEffectivenessRow[];
  edit_stats: PromptEditStat[];
  running_experiments: PromptExperiment[];
  total_prompts: number;
}

export interface PromptEffectivenessRow {
  prompt_id: string;
  prompt_version: number;
  proposals_used: number;
  won: number;
  lost: number;
  win_rate: number | null;
  avg_quality_score: number | null;
  avg_input_tokens: number | null;
  avg_output_tokens: number | null;
  avg_duration_ms: number | null;
}

export interface PromptEditStat {
  prompt_id: string;
  edit_count: number;
  avg_edit_ratio: number;
  actions: Record<string, number>;
}

export interface PromptDetail {
  prompt_id: string;
  active_version: PromptRegistryItem | null;
  versions: (PromptRegistryItem & { content_text: string; change_reason: string })[];
  total_versions: number;
}

export interface PromptEffectiveness {
  prompt_id: string;
  prompt_version?: number;
  proposals_used: number;
  won?: number;
  lost?: number;
  win_rate?: number | null;
  avg_quality_score?: number | null;
  avg_edit_ratio?: number | null;
  avg_input_tokens?: number;
  avg_output_tokens?: number;
  avg_duration_ms?: number;
}

export interface SectionHeatmapItem {
  section_id: string;
  usage_count: number;
  avg_quality: number | null;
  unique_prompts: number;
}

export interface PromptSuggestion {
  analysis?: string;
  suggestions?: {
    title: string;
    rationale: string;
    key_changes: string[];
    prompt_text: string;
  }[];
  error?: string;
}

export interface EditActionBody {
  proposal_id: string;
  section_id: string;
  action: "accept" | "edit" | "reject" | "regenerate";
  original?: string;
  edited?: string;
}

export interface ExperimentCreateBody {
  prompt_id: string;
  candidate_version: number;
  traffic_pct?: number;
  experiment_name?: string;
  min_samples?: number;
}

export interface PromptExperiment {
  id: string;
  experiment_name: string;
  prompt_id: string;
  baseline_version: number;
  candidate_version: number;
  traffic_pct: number;
  status: string;
  min_samples: number;
  promote_threshold: number;
  conclusion?: string;
  promoted_version?: number;
  started_at: string;
  ended_at?: string;
}

export interface ExperimentEvaluation {
  experiment_id: string;
  experiment_name: string;
  baseline: Record<string, unknown>;
  candidate: Record<string, unknown>;
  min_samples_reached: boolean;
  improvement?: number;
  recommendation?: "promote" | "rollback" | "continue";
  error?: string;
}

// ── PSM-16: Q&A 타입 ─────────────────────────────────────────────────

export interface QARecord {
  id: string;
  proposal_id: string;
  question: string;
  answer: string;
  category: string;
  evaluator_reaction: string | null;
  memo: string | null;
  content_library_id: string | null;
  created_at: string;
  created_by: string | null;
}

export interface QARecordCreate {
  question: string;
  answer: string;
  category?: string;
  evaluator_reaction?: string | null;
  memo?: string | null;
}

export interface QARecordUpdate {
  question?: string;
  answer?: string;
  category?: string;
  evaluator_reaction?: string | null;
  memo?: string | null;
}

export interface QASearchResult extends QARecord {
  similarity: number | null;
  proposal_name: string | null;
  client: string | null;
}

// ── 헬퍼 ─────────────────────────────────────────────────────────────

function _qs(params?: object): string {
  if (!params) return "";
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

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

export interface BidAnalysis {
  rfp_summary: string[];
  fit_level: "적극 추천" | "추천" | "보통" | "낮음";
  positive: string[];
  negative: string[];
  recommended_teams: string[];
  suitability_score?: number;
  verdict?: "추천" | "검토 필요" | "제외";
  action_plan?: string;
}

export interface BidAttachment {
  name: string;
  url: string;
}

export interface ScoredBid {
  bid_no: string;
  title: string;
  agency: string;
  budget: number;
  deadline: string;
  d_day: number | null;
  score: number;
  role_keywords: string[];
  domain_keywords: string[];
  classification: string;
  classification_large: string;
  bid_stage: "입찰공고" | "사전규격" | "발주계획";
}

export interface MonitoredBid {
  bid_no: string;
  bid_title: string;
  agency: string;
  budget_amount: number | null;
  deadline_date: string | null;
  days_remaining: number | null;
  bid_type?: string;
  content_text?: string;
  match_score?: number | null;
  match_grade?: string | null;
  recommendation_summary?: string | null;
  recommendation_reasons?: RecommendationReason[];
  is_bookmarked?: boolean;
  qualified?: boolean;
  attachments?: BidAttachment[];
  related_teams?: string[];
  relevance?: "적극 추천" | "보통" | "낮음";
  bid_stage?: "사전공고" | "본공고";
  proposal_status?: "검토중" | "제안결정" | "제안포기" | "제안유보" | "제안착수" | "관련없음" | null;
  decided_by?: string | null;
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
  raw_data: Record<string, unknown> | null;
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

export interface StoredAttachment {
  name: string;
  size: number;
  storage_path: string;
  created_at: string;
}

export interface G2bUrl {
  index: number;
  url: string;
  label?: string;
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

// ── 워크플로 타입 ─────────────────────────────────────────────────────

export interface WorkflowStartResult {
  proposal_id: string;
  status: string;
  current_step: string;
  interrupted: boolean;
}

export interface WorkflowState {
  proposal_id: string;
  current_step: string;
  positioning: string | null;
  approval: Record<string, unknown>;
  has_pending_interrupt: boolean;
  next_nodes: string[];
  token_summary: { total_cost_usd: number; nodes_tracked: number };
  current_section_index?: number | null;
  total_sections?: number | null;
  interrupt_data?: Record<string, unknown> | null;
  review_history?: Array<{ node: string; approved: boolean; feedback?: string; timestamp: string }>;
  streams_status?: StreamsOverview | null;
}

export interface WorkflowResumeData {
  approved?: boolean;
  quick_approve?: boolean;
  feedback?: string;
  decision?: string;
  positioning_override?: string;
  rework_targets?: string[];
  picked_bid_no?: string;
  no_interest?: boolean;
  [key: string]: unknown;
}

export interface WorkflowResumeResult {
  proposal_id: string;
  current_step: string;
  interrupted: boolean;
}

export interface WorkflowHistoryEntry {
  step: string;
  next: string[];
  config: Record<string, unknown>;
}

export interface TokenUsageNode {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_create_tokens: number;
  total_tokens: number;
  cost_usd: number;
  model: string;
  num_calls: number;
  duration_ms: number;
}

export interface TokenUsageResponse {
  proposal_id: string;
  by_node: Record<string, TokenUsageNode>;
  total: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    cost_usd: number;
    nodes_executed: number;
  };
}

// ── 산출물 타입 ───────────────────────────────────────────────────────

export interface ArtifactData {
  proposal_id: string;
  step: string;
  data: Record<string, unknown>;
}

export interface ComplianceItem {
  requirement: string;
  section: string;
  status: "met" | "partial" | "not_met" | "pending";
  notes: string;
}

export interface ComplianceData {
  proposal_id: string;
  items: ComplianceItem[];
  summary: { met: number; partial: number; not_met: number; pending: number };
}

// ── 분석 대시보드 타입 ────────────────────────────────────────────────

export interface AnalyticsParams {
  period?: string;
  team_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface FailureReasonsData {
  reasons: Array<{ reason: string; count: number; percentage: number }>;
  total_failures: number;
}

export interface PositioningWinRateData {
  positioning: Array<{
    type: string;
    total: number;
    won: number;
    rate: number;
  }>;
}

export interface MonthlyTrendsData {
  months: Array<{
    month: string;
    total: number;
    won: number;
    rate: number;
  }>;
}

export interface WinRateDetailData {
  overall: { total: number; won: number; rate: number };
  by_period: Array<{ period: string; total: number; won: number; rate: number }>;
}

export interface TeamPerformanceData {
  teams: Array<{
    team_id: string;
    team_name: string;
    total: number;
    won: number;
    rate: number;
    avg_duration_days: number;
  }>;
}

export interface CompetitorData {
  competitors: Array<{
    name: string;
    encounters: number;
    wins_against: number;
    losses_against: number;
  }>;
}

export interface ClientWinRateData {
  clients: Array<{
    agency: string;
    total: number;
    won: number;
    rate: number;
  }>;
}

// ── 모의평가 타입 ─────────────────────────────────────────────────────

export interface EvaluatorScore {
  compliance: number;
  strategy: number;
  quality: number;
  trustworthiness: number;
  total: number;
}

export interface Evaluator {
  role: string;
  scores: EvaluatorScore;
  comments: string;
}

export interface EvaluationSimulation {
  evaluators: Evaluator[];
  average_scores: EvaluatorScore;
  weaknesses: Array<{ area: string; description: string; related_section: string }>;
  expected_qa: Array<{ question: string; answer: string }>;
}

// ── KB 관리 타입 ─────────────────────────────────────────────────────

export interface LaborRate {
  id: string;
  agency: string;
  year: number;
  grade: string;
  monthly_rate: number;
  source: string;
  updated_at: string;
  created_at: string;
}

export interface MarketPrice {
  id: string;
  domain: string;
  budget_range: string;
  win_rate: number;
  avg_bid_rate: number;
  source: string;
  year: number;
  updated_at: string;
  created_at: string;
}

// ── 알림 타입 ─────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  proposal_id: string | null;
  type: string;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  teams_sent: boolean;
  created_at: string;
}

export interface NotificationSettings {
  teams: boolean;
  in_app: boolean;
}

// ── KB 콘텐츠 타입 ────────────────────────────────────────────────────

export interface KbContent {
  id: string;
  title: string;
  type: string;
  status: string;
  quality_score: number | null;
  reuse_count: number;
  tags: string[];
  industry: string | null;
  tech_area: string | null;
  created_at: string;
}

export interface KbContentDetail extends KbContent {
  body: string;
  source_project_id: string | null;
}

export interface KbContentCreate {
  title: string;
  body: string;
  type?: string;
  source_project_id?: string;
  industry?: string;
  tech_area?: string;
  tags?: string[];
}

// ── KB 발주기관 타입 ──────────────────────────────────────────────────

export interface KbClient {
  id: string;
  client_name: string;
  client_type: string | null;
  scale: string | null;
  relationship: string;
  eval_tendency: string | null;
  location: string | null;
  updated_at: string;
}

export interface KbClientDetail extends KbClient {
  notes: string | null;
  parent_ministry: string | null;
  bid_history: Array<{ id: string; project_name: string; result: string; created_at: string }>;
}

export interface KbClientCreate {
  client_name: string;
  client_type?: string;
  scale?: string;
  parent_ministry?: string;
  location?: string;
  relationship?: string;
  eval_tendency?: string;
  notes?: string;
}

// ── KB 경쟁사 타입 ────────────────────────────────────────────────────

export interface KbCompetitor {
  id: string;
  company_name: string;
  scale: string | null;
  primary_area: string | null;
  price_pattern: string | null;
  avg_win_rate: number | null;
  updated_at: string;
}

export interface KbCompetitorDetail extends KbCompetitor {
  strengths: string | null;
  weaknesses: string | null;
  notes: string | null;
  competition_history: Array<{ id: string; project_name: string; result: string; created_at: string }>;
}

export interface KbCompetitorCreate {
  company_name: string;
  scale?: string;
  primary_area?: string;
  strengths?: string;
  weaknesses?: string;
  price_pattern?: string;
  notes?: string;
}

// ── KB 교훈 타입 ──────────────────────────────────────────────────────

export interface KbLesson {
  id: string;
  strategy_summary: string | null;
  result: string | null;
  positioning: string | null;
  client_name: string | null;
  industry: string | null;
  failure_category: string | null;
  created_at: string;
}

export interface KbLessonDetail extends KbLesson {
  proposal_id: string | null;
  effective_points: string | null;
  weak_points: string | null;
  improvements: string | null;
  failure_detail: string | null;
}

export interface KbLessonCreate {
  proposal_id?: string;
  strategy_summary?: string;
  effective_points?: string;
  weak_points?: string;
  improvements?: string;
  failure_category?: string;
  failure_detail?: string;
  positioning?: string;
  client_name?: string;
  industry?: string;
  result?: string;
}

// ── KB 검색 결과 타입 ─────────────────────────────────────────────────

export interface KbSearchResult {
  query: string;
  total: number;
  results: Record<string, Array<{ id: string; title?: string; summary?: string; score?: number; [key: string]: unknown }>>;
}

// ── 워크플로 STEP 정의 ───────────────────────────────────────────────

export type WorkflowStep =
  | "rfp_search"
  | "rfp_fetch"
  | "rfp_analyze"
  | "research_gather"
  | "go_no_go"
  | "strategy_generate"
  | "bid_plan"
  | "plan_team"
  | "plan_assign"
  | "plan_schedule"
  | "plan_story"
  | "plan_price"
  | "proposal_write_next"
  | "self_review"
  | "presentation_strategy"
  | "ppt_toc"
  | "ppt_visual_brief"
  | "ppt_storyboard";

export const WORKFLOW_STEPS: Array<{
  step: number;
  label: string;
  nodes: string[];
}> = [
  { step: 1, label: "RFP 분석", nodes: ["rfp_analyze", "research_gather", "go_no_go"] },
  { step: 2, label: "전략 수립", nodes: ["strategy_generate"] },
  { step: 2.5, label: "가격 결정", nodes: ["bid_plan"] },
  { step: 3, label: "실행 계획", nodes: ["plan_team", "plan_assign", "plan_schedule", "plan_story", "plan_price"] },
  { step: 4, label: "제안서 작성", nodes: ["proposal_write_next", "self_review"] },
  { step: 5, label: "PPT 생성", nodes: ["presentation_strategy", "ppt_toc", "ppt_visual_brief", "ppt_storyboard"] },
];


// ── 비딩 가격 시뮬레이션 ─────────────────────────────────────────────

export interface PricingPersonnelInput {
  role: string;
  grade: string;
  person_months: number;
  labor_type?: string;
}

export interface PricingSimulationRequest {
  budget: number;
  domain?: string;
  evaluation_method?: string;
  tech_price_ratio?: { tech: number; price: number };
  positioning?: string;
  competitor_count?: number;
  cost_standard?: string | null;
  personnel?: PricingPersonnelInput[];
  client_name?: string | null;
  proposal_id?: string | null;
}

export interface SensitivityPoint {
  ratio: number;
  bid_price: number;
  win_prob: number;
  expected_payoff: number;
}

export interface PriceScoreDetail {
  price_score: number;
  price_weight: number;
  score_ratio: number;
  total_score: number;
  formula_used: string;
  estimated_min_bid: number;
  is_disqualified: boolean;
}

export interface ScoreSimulationRow {
  bid_ratio: number;
  bid_price: number;
  bid_price_fmt: string;
  price_score: number;
  price_weight: number;
  tech_score: number;
  tech_weight: number;
  total_score: number;
  total_weight: number;
  score_ratio: number;
  formula_used: string;
  is_disqualified: boolean;
  disqualification_reason: string;
  estimated_min_bid: number;
  price_gain_per_point: number;
}

export interface PricingScenario {
  name: string;
  label: string;
  bid_ratio: number;
  bid_price: number;
  win_probability: number;
  expected_payoff: number;
  risk_level: string;
  price_score_detail?: PriceScoreDetail | null;
}

export interface CostBreakdownDetail {
  direct_labor: number;
  direct_labor_fmt: string;
  indirect_cost: number;
  indirect_fmt: string;
  technical_fee: number;
  tech_fee_fmt: string;
  subtotal: number;
  subtotal_fmt: string;
  vat: number;
  vat_fmt: string;
  total_cost: number;
  total_cost_fmt: string;
  personnel_detail: Array<{
    role: string;
    grade: string;
    monthly_rate: number;
    person_months: number;
    amount: number;
    amount_fmt: string;
  }>;
}

export interface MarketContext {
  domain: string;
  avg_bid_ratio: number | null;
  avg_num_bidders: number | null;
  total_cases: number;
  evaluation_method_distribution: Record<string, number>;
  budget_tier_distribution: Record<string, number>;
}

export interface PricingSimulationResult {
  cost_breakdown: CostBreakdownDetail | null;
  cost_standard_used: string;
  cost_standard_reason: string;
  recommended_bid: number;
  recommended_ratio: number;
  bid_range: { min_price: number; max_price: number; min_ratio: number; max_ratio: number } | null;
  win_probability: number;
  win_probability_confidence: string;
  comparable_cases: number;
  sensitivity_curve: SensitivityPoint[];
  optimal_ratio: number;
  scenarios: PricingScenario[];
  market_context: MarketContext | null;
  score_simulation: ScoreSimulationRow[];
  data_quality: string;
  created_at: string;
}

export interface QuickEstimateResult {
  recommended_ratio: number;
  recommended_bid: number;
  win_probability: number;
  win_probability_confidence: string;
  comparable_cases: number;
  data_quality: string;
  market_avg_ratio: number | null;
  positioning_adjustment: string;
}

export interface PricingSimulationSummary {
  id: string;
  proposal_id: string | null;
  budget: number;
  domain: string;
  evaluation_method: string;
  positioning: string;
  selected_scenario: string | null;
  created_at: string;
}

export interface MarketAnalysisResult {
  domain: string;
  total_cases: number;
  avg_bid_ratio: number | null;
  avg_num_bidders: number | null;
  distribution: Array<{ bucket: string; count: number }>;
  yearly_trend: Array<{ year: number; avg_ratio: number; count: number }>;
}

export interface PricingSensitivityRequest {
  budget: number;
  total_cost?: number;
  domain?: string;
  evaluation_method?: string;
  competitor_count?: number;
  positioning?: string;
  center_ratio?: number;
  range_pct?: number;
  steps?: number;
}

export interface PricingSensitivityResult {
  points: SensitivityPoint[];
  optimal_ratio: number;
  optimal_payoff: number;
}

// ── Pricing API 메서드 (api 객체에 추가) ──

export const pricingApi = {
  async simulatePricing(req: PricingSimulationRequest): Promise<PricingSimulationResult> {
    return request("POST", "/pricing/simulate", req);
  },
  async quickEstimate(params: { budget: number; evaluation_method?: string; domain?: string; positioning?: string; competitor_count?: number }): Promise<QuickEstimateResult> {
    return request("POST", "/pricing/quick-estimate", params);
  },
  async getPricingSimulations(proposalId?: string): Promise<{ items: PricingSimulationSummary[]; total: number }> {
    const qs = proposalId ? `?proposal_id=${proposalId}` : "";
    return request("GET", `/pricing/simulations${qs}`);
  },
  async getPricingSimulation(id: string): Promise<Record<string, unknown>> {
    return request("GET", `/pricing/simulations/${id}`);
  },
  async getMarketAnalysis(domain: string, method?: string): Promise<MarketAnalysisResult> {
    const qs = method ? `?domain=${encodeURIComponent(domain)}&evaluation_method=${encodeURIComponent(method)}` : `?domain=${encodeURIComponent(domain)}`;
    return request("GET", `/pricing/market-analysis${qs}`);
  },
  async runSensitivity(req: PricingSensitivityRequest): Promise<PricingSensitivityResult> {
    return request("POST", "/pricing/sensitivity", req);
  },
  async getPredictionAccuracy(): Promise<{ total_resolved: number; avg_error: number | null; accuracy_by_result: Record<string, { count: number; avg_error: number | null }> }> {
    return request("GET", "/pricing/prediction-accuracy");
  },
};


// ── 투찰 관리 API ─────────────────────────────────────────────

export interface BidSubmissionStatus {
  bid_confirmed_price: number | null;
  bid_confirmed_ratio: number | null;
  bid_confirmed_scenario: string | null;
  bid_confirmed_at: string | null;
  bid_confirmed_by: string | null;
  bid_submitted_price: number | null;
  bid_submitted_at: string | null;
  bid_submitted_by: string | null;
  bid_submission_note: string | null;
  bid_submission_status: "ready" | "submitted" | "verified" | null;
}

export interface BidPriceHistoryEntry {
  id: string;
  proposal_id: string;
  event_type: "confirmed" | "override" | "submitted" | "verified";
  price: number;
  ratio: number | null;
  scenario_name: string | null;
  reason: string | null;
  actor_id: string | null;
  actor_name: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ── 3-Stream 타입 ──────────────────────────────────────────────

export type StreamName = "proposal" | "bidding" | "documents";
export type StreamStatusType = "not_started" | "in_progress" | "blocked" | "completed" | "error";

export interface StreamProgress {
  stream: StreamName;
  status: StreamStatusType;
  progress_pct: number;
  current_phase: string | null;
  blocked_reason: string | null;
  started_at: string | null;
  completed_at: string | null;
  metadata: Record<string, unknown>;
}

export interface StreamsOverview {
  streams: StreamProgress[];
  convergence_ready: boolean;
  missing_streams: string[];
}

export type DocCategory = "proposal" | "qualification" | "certification" | "financial" | "other";
export type DocStatus = "pending" | "assigned" | "in_progress" | "uploaded" | "verified" | "rejected" | "not_applicable" | "expired";

export interface SubmissionDocument {
  id: string;
  proposal_id: string;
  doc_type: string;
  doc_category: DocCategory;
  required_format: string;
  required_copies: number;
  source: string;
  status: DocStatus;
  assignee_id: string | null;
  deadline: string | null;
  priority: string;
  notes: string | null;
  file_path: string | null;
  file_name: string | null;
  file_size: number | null;
  file_format: string | null;
  uploaded_by: string | null;
  uploaded_at: string | null;
  verified_by: string | null;
  verified_at: string | null;
  rejection_reason: string | null;
  sort_order: number;
  rfp_reference: string | null;
  created_at: string | null;
}

export interface SubmissionDocCreate {
  doc_type: string;
  doc_category?: DocCategory;
  required_format?: string;
  required_copies?: number;
  priority?: string;
  notes?: string;
  assignee_id?: string;
  deadline?: string;
  rfp_reference?: string;
}

export interface SubmissionDocUpdate {
  status?: DocStatus;
  assignee_id?: string;
  priority?: string;
  notes?: string;
  deadline?: string;
  rejection_reason?: string;
}

export interface ReadinessResult {
  ready: boolean;
  total: number;
  completed: number;
  issues: Array<{ doc_id: string; doc_type: string; status: string; issue: string | null }>;
}

export interface OrgDocTemplate {
  id: string;
  org_id: string;
  doc_type: string;
  doc_category: DocCategory;
  required_format: string | null;
  file_path: string | null;
  file_name: string | null;
  file_size: number | null;
  valid_from: string | null;
  valid_until: string | null;
  auto_include: boolean;
  notes: string | null;
  created_at: string | null;
}

export interface BiddingWorkspace {
  proposal_id: string;
  bid_status: BidSubmissionStatus;
  scenarios: Array<Record<string, unknown>>;
  price_history: BidPriceHistoryEntry[];
  market_summary: {
    comparable_cases: number;
    market_avg_ratio: number | null;
    data_quality: string;
    win_probability: number;
  };
}

// ── 3-Stream API ──

export const streamsApi = {
  async getAll(proposalId: string): Promise<StreamsOverview> {
    return request("GET", `/proposals/${proposalId}/streams`);
  },
  async getOne(proposalId: string, stream: StreamName): Promise<StreamProgress> {
    return request("GET", `/proposals/${proposalId}/streams/${stream}`);
  },
  async finalSubmit(proposalId: string): Promise<{ success: boolean; message: string; submission_gate_status: string }> {
    return request("POST", `/proposals/${proposalId}/streams/final-submit`, { confirm: true });
  },
};

export const submissionDocsApi = {
  async list(proposalId: string): Promise<SubmissionDocument[]> {
    return request("GET", `/proposals/${proposalId}/submission-docs`);
  },
  async extract(proposalId: string): Promise<SubmissionDocument[]> {
    return request("POST", `/proposals/${proposalId}/submission-docs/extract`);
  },
  async add(proposalId: string, data: SubmissionDocCreate): Promise<SubmissionDocument> {
    return request("POST", `/proposals/${proposalId}/submission-docs`, data);
  },
  async update(proposalId: string, docId: string, data: SubmissionDocUpdate): Promise<SubmissionDocument> {
    return request("PUT", `/proposals/${proposalId}/submission-docs/${docId}`, data);
  },
  async remove(proposalId: string, docId: string): Promise<void> {
    return request("DELETE", `/proposals/${proposalId}/submission-docs/${docId}`);
  },
  async upload(proposalId: string, docId: string, file: File): Promise<SubmissionDocument> {
    const formData = new FormData();
    formData.append("file", file);
    return request("POST", `/proposals/${proposalId}/submission-docs/${docId}/upload`, formData, true);
  },
  async verify(proposalId: string, docId: string): Promise<SubmissionDocument> {
    return request("POST", `/proposals/${proposalId}/submission-docs/${docId}/verify`);
  },
  async readiness(proposalId: string): Promise<ReadinessResult> {
    return request("GET", `/proposals/${proposalId}/submission-docs/readiness`);
  },
  async confirmOriginal(proposalId: string, docId: string): Promise<SubmissionDocument> {
    return request("POST", `/proposals/${proposalId}/submission-docs/${docId}/confirm-original`);
  },
  bundleUrl(proposalId: string): string {
    return `${BASE}/proposals/${proposalId}/submission-docs/bundle`;
  },
};

export const orgTemplatesApi = {
  async list(orgId: string): Promise<OrgDocTemplate[]> {
    return request("GET", `/org/${orgId}/document-templates`);
  },
  async upsert(orgId: string, data: { doc_type: string; doc_category?: string; required_format?: string; valid_from?: string; valid_until?: string; auto_include?: boolean; notes?: string }): Promise<OrgDocTemplate> {
    return request("POST", `/org/${orgId}/document-templates`, data);
  },
  async remove(orgId: string, templateId: string): Promise<void> {
    return request("DELETE", `/org/${orgId}/document-templates/${templateId}`);
  },
};

export const bidSubmissionApi = {
  async getStatus(proposalId: string): Promise<BidSubmissionStatus> {
    return request("GET", `/proposals/${proposalId}/bid-submission`);
  },
  async submitBid(proposalId: string, data: { submitted_price: number; note?: string }): Promise<{ status: string; submitted_at: string }> {
    return request("POST", `/proposals/${proposalId}/bid-submission`, data);
  },
  async verifyBid(proposalId: string): Promise<{ status: string; verified_at: string }> {
    return request("POST", `/proposals/${proposalId}/bid-submission/verify`);
  },
  async getPriceHistory(proposalId: string): Promise<BidPriceHistoryEntry[]> {
    return request("GET", `/proposals/${proposalId}/bid-price-history`);
  },
  async adjustPrice(proposalId: string, data: { adjusted_price: number; reason: string }): Promise<{ success: boolean; new_price: number; message: string }> {
    return request("PUT", `/proposals/${proposalId}/bid-submission/adjust`, data);
  },
  async getBiddingWorkspace(proposalId: string): Promise<BiddingWorkspace> {
    return request("GET", `/proposals/${proposalId}/bidding-workspace`);
  },
};

// ── 산출내역서 API ──

export interface CostSheetDraft {
  project_name: string;
  client: string;
  proposer_name: string;
  cost_standard: string;
  labor_breakdown: LaborItem[];
  labor_total: number;
  expense_items: ExpenseItem[];
  expense_total: number;
  overhead_rate: number;
  overhead_total: number;
  profit_rate: number;
  profit_total: number;
  total_cost: number;
  budget_narrative: BudgetNarrativeItem[];
}

export interface LaborItem {
  grade: string;
  role?: string;
  monthly_rate: number;
  mm: number;
  subtotal: number;
}

export interface ExpenseItem {
  name: string;
  amount: number;
  basis: string;
}

export interface BudgetNarrativeItem {
  cost_item: string;
  linked_activity: string;
  justification: string;
}

export const costSheetApi = {
  async getDraft(proposalId: string): Promise<CostSheetDraft> {
    return request("GET", `/proposals/${proposalId}/cost-sheet/draft`);
  },
  async generate(proposalId: string, data: {
    project_name: string;
    client: string;
    proposer_name: string;
    cost_standard: string;
    labor_breakdown: LaborItem[];
    expense_items: ExpenseItem[];
    overhead_rate: number;
    profit_rate: number;
    budget_narrative: BudgetNarrativeItem[];
  }): Promise<Blob> {
    const res = await fetch(`${BASE}/proposals/${proposalId}/cost-sheet/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${await getToken()}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`산출내역서 생성 실패: ${res.status}`);
    return res.blob();
  },
};
