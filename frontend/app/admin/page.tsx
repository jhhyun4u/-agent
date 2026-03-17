"use client";

/**
 * F8: 팀 관리 페이지 (admin)
 * - 팀 생성 / 선택
 * - 팀원 목록 + 역할 변경 + 제거
 * - 이메일 초대 + 초대 목록
 */

import { useCallback, useEffect, useState } from "react";
import AppSidebar from "@/components/AppSidebar";
import { api, Team, TeamMember, TeamStats, Invitation, TeamMembership } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

export default function AdminPage() {
  const [memberships, setMemberships] = useState<TeamMembership[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [editingName, setEditingName] = useState(false);
  const [teamNameInput, setTeamNameInput] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [newTeamName, setNewTeamName] = useState("");
  const [currentUserId, setCurrentUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // 내 팀 목록
  const fetchTeams = useCallback(async () => {
    try {
      const res = await api.teams.list();
      setMemberships(res.teams);
      if (!selectedTeamId && res.teams.length > 0) {
        setSelectedTeamId(res.teams[0].team_id);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedTeamId]);

  // 선택된 팀 상세
  const fetchTeamDetail = useCallback(async () => {
    if (!selectedTeamId) return;
    try {
      const [memRes, invRes, statsRes] = await Promise.all([
        api.teams.members.list(selectedTeamId),
        api.teams.invitations.list(selectedTeamId).catch(() => ({ invitations: [] })),
        api.teams.stats(selectedTeamId).catch(() => null),
      ]);
      setMembers(memRes.members);
      setInvitations(invRes.invitations);
      setStats(statsRes);
    } catch {}
  }, [selectedTeamId]);

  useEffect(() => {
    fetchTeams();
    createClient().auth.getUser().then(({ data }) => setCurrentUserId(data.user?.id ?? ""));
  }, [fetchTeams]);

  useEffect(() => {
    fetchTeamDetail();
  }, [fetchTeamDetail]);

  const selectedMembership = memberships.find((m) => m.team_id === selectedTeamId);
  const isAdmin = selectedMembership?.role === "admin";

  async function handleRenameTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTeamId || !teamNameInput.trim()) return;
    try {
      await api.teams.update(selectedTeamId, teamNameInput.trim());
      await fetchTeams();
      setEditingName(false);
      flash("팀 이름이 변경되었습니다.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "이름 변경 실패");
    }
  }

  async function handleCreateTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    try {
      const res = await api.teams.create(newTeamName.trim());
      setNewTeamName("");
      await fetchTeams();
      setSelectedTeamId(res.team_id);
      flash("팀이 생성되었습니다.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "팀 생성 실패");
    }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTeamId || !inviteEmail.trim()) return;
    try {
      await api.teams.invitations.create(selectedTeamId, inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      fetchTeamDetail();
      flash("초대를 전송했습니다.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "초대 실패");
    }
  }

  async function handleCancelInvite(invId: string) {
    if (!selectedTeamId) return;
    try {
      await api.teams.invitations.cancel(selectedTeamId, invId);
      fetchTeamDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "취소 실패");
    }
  }

  async function handleRemoveMember(userId: string) {
    if (!selectedTeamId || !confirm("팀원을 제거하시겠습니까?")) return;
    try {
      await api.teams.members.remove(selectedTeamId, userId);
      fetchTeamDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "제거 실패");
    }
  }

  async function handleRoleChange(userId: string, role: string) {
    if (!selectedTeamId) return;
    try {
      await api.teams.members.updateRole(selectedTeamId, userId, role);
      fetchTeamDetail();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "역할 변경 실패");
    }
  }

  function flash(msg: string) {
    setError("");
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  }

  const STATUS_LABELS: Record<string, string> = {
    pending: "대기", accepted: "수락", expired: "만료",
  };

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 헤더 */}
        <header className="border-b border-[#262626] px-6 py-4 bg-[#111111] shrink-0">
          <h1 className="text-base font-semibold text-[#ededed]">팀 관리</h1>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-4xl mx-auto">
            {error && (
              <div className="mb-4 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3 text-sm text-red-400">{error}</div>
            )}
            {successMsg && (
              <div className="mb-4 bg-[#3ecf8e]/10 border border-[#3ecf8e]/20 rounded-lg px-4 py-3 text-sm text-[#3ecf8e]">{successMsg}</div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 팀 목록 사이드바 */}
              <div className="space-y-4">
                <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-4">
                  <h2 className="text-sm font-semibold text-[#8c8c8c] mb-3">내 팀</h2>
                  {loading ? (
                    <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
                  ) : memberships.length === 0 ? (
                    <p className="text-sm text-[#5c5c5c]">팀이 없습니다.</p>
                  ) : (
                    <ul className="space-y-1">
                      {memberships.map((m) => (
                        <li key={m.team_id}>
                          <button
                            onClick={() => setSelectedTeamId(m.team_id)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                              selectedTeamId === m.team_id
                                ? "bg-[#3ecf8e]/10 text-[#3ecf8e] font-medium"
                                : "text-[#ededed] hover:bg-[#262626]"
                            }`}
                          >
                            {m.teams.name}
                            <span className="ml-2 text-xs text-[#5c5c5c]">{m.role}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* 팀 생성 */}
                <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-4">
                  <h2 className="text-sm font-semibold text-[#8c8c8c] mb-3">새 팀 만들기</h2>
                  <form onSubmit={handleCreateTeam} className="space-y-2">
                    <input
                      type="text"
                      value={newTeamName}
                      onChange={(e) => setNewTeamName(e.target.value)}
                      placeholder="팀 이름"
                      className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                    />
                    <button
                      type="submit"
                      disabled={!newTeamName.trim()}
                      className="w-full bg-[#3ecf8e] hover:bg-[#36b87e] disabled:opacity-50 text-black text-sm font-medium rounded-lg py-2 transition-colors"
                    >
                      생성
                    </button>
                  </form>
                </div>
              </div>

              {/* 팀 상세 */}
              <div className="md:col-span-2 space-y-4">
                {!selectedTeamId ? (
                  <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-10 text-center text-[#5c5c5c] text-sm">
                    팀을 선택하세요.
                  </div>
                ) : (
                  <>
                    {/* 팀 이름 + 통계 */}
                    <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-6">
                      <div className="flex items-center gap-2 mb-4">
                        {isAdmin && editingName ? (
                          <form onSubmit={handleRenameTeam} className="flex gap-2 flex-1">
                            <input
                              value={teamNameInput}
                              onChange={(e) => setTeamNameInput(e.target.value)}
                              className="flex-1 bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                              autoFocus
                            />
                            <button type="submit" disabled={!teamNameInput.trim()} className="bg-[#3ecf8e] hover:bg-[#36b87e] disabled:opacity-50 text-black text-xs font-medium px-3 py-1.5 rounded-lg">저장</button>
                            <button type="button" onClick={() => setEditingName(false)} className="text-xs text-[#5c5c5c] hover:text-[#ededed] px-2">취소</button>
                          </form>
                        ) : (
                          <>
                            <h2 className="font-semibold text-[#ededed]">{selectedMembership?.teams.name}</h2>
                            {isAdmin && (
                              <button
                                onClick={() => { setTeamNameInput(selectedMembership?.teams.name ?? ""); setEditingName(true); }}
                                className="text-xs text-[#5c5c5c] hover:text-[#8c8c8c]"
                              >
                                수정
                              </button>
                            )}
                          </>
                        )}
                      </div>
                      {stats && (
                        <div className="grid grid-cols-3 gap-4 text-center border-t border-[#262626] pt-4">
                          <div>
                            <p className="text-2xl font-bold text-[#ededed]">{stats.total}</p>
                            <p className="text-xs text-[#5c5c5c] mt-0.5">전체 제안서</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-[#3ecf8e]">{stats.completed}</p>
                            <p className="text-xs text-[#5c5c5c] mt-0.5">완료</p>
                          </div>
                          <div>
                            <p className="text-2xl font-bold text-blue-400">{stats.win_rate}%</p>
                            <p className="text-xs text-[#5c5c5c] mt-0.5">수주율</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 팀원 목록 */}
                    <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-6">
                      <h2 className="font-semibold text-[#ededed] mb-4">팀원</h2>
                      <ul className="divide-y divide-[#262626]">
                        {members.map((m) => (
                          <li key={m.id} className="flex items-center py-3 gap-3">
                            <div className="w-8 h-8 rounded-full bg-[#262626] flex items-center justify-center text-xs text-[#8c8c8c] shrink-0">
                              {(m.email || m.user_id).slice(0, 2).toUpperCase()}
                            </div>
                            <span className="flex-1 text-sm text-[#ededed] truncate">{m.email || m.user_id}</span>
                            {isAdmin && m.user_id !== currentUserId ? (
                              <div className="flex items-center gap-2">
                                <select
                                  value={m.role}
                                  onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                                  className="bg-[#0f0f0f] border border-[#262626] rounded text-xs text-[#ededed] px-2 py-1"
                                >
                                  <option value="admin">admin</option>
                                  <option value="member">member</option>
                                </select>
                                <button
                                  onClick={() => handleRemoveMember(m.user_id)}
                                  className="text-xs text-red-400/70 hover:text-red-400"
                                >
                                  제거
                                </button>
                              </div>
                            ) : (
                              <span className="text-xs text-[#5c5c5c]">{m.role}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* 초대 */}
                    {isAdmin && (
                      <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-6">
                        <h2 className="font-semibold text-[#ededed] mb-4">팀원 초대</h2>
                        <form onSubmit={handleInvite} className="flex gap-2 mb-4">
                          <input
                            type="email"
                            value={inviteEmail}
                            onChange={(e) => setInviteEmail(e.target.value)}
                            placeholder="이메일 주소"
                            className="flex-1 bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] transition-colors"
                          />
                          <select
                            value={inviteRole}
                            onChange={(e) => setInviteRole(e.target.value)}
                            className="bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed]"
                          >
                            <option value="member">member</option>
                            <option value="admin">admin</option>
                          </select>
                          <button
                            type="submit"
                            disabled={!inviteEmail.trim()}
                            className="bg-[#3ecf8e] hover:bg-[#36b87e] disabled:opacity-50 text-black text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                          >
                            초대
                          </button>
                        </form>

                        {invitations.length > 0 && (
                          <div>
                            <h3 className="text-xs font-semibold text-[#5c5c5c] uppercase mb-2">초대 목록</h3>
                            <ul className="divide-y divide-[#262626]">
                              {invitations.map((inv) => (
                                <li key={inv.id} className="flex items-center py-2.5 gap-3 text-sm">
                                  <span className="flex-1 text-[#ededed] truncate">{inv.email}</span>
                                  <span className="text-xs text-[#5c5c5c]">{inv.role}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    inv.status === "accepted" ? "bg-[#3ecf8e]/10 text-[#3ecf8e]" :
                                    inv.status === "expired" ? "bg-[#262626] text-[#5c5c5c]" :
                                    "bg-amber-500/10 text-amber-400"
                                  }`}>
                                    {STATUS_LABELS[inv.status] ?? inv.status}
                                  </span>
                                  {inv.status === "pending" && (
                                    <button
                                      onClick={() => handleCancelInvite(inv.id)}
                                      className="text-xs text-red-400/70 hover:text-red-400"
                                    >
                                      취소
                                    </button>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
