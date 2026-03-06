"use client";

/**
 * F8: 팀 관리 페이지 (admin)
 * - 팀 생성 / 선택
 * - 팀원 목록 + 역할 변경 + 제거
 * - 이메일 초대 + 초대 목록
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Team, TeamMember, Invitation, TeamMembership } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

export default function AdminPage() {
  const [memberships, setMemberships] = useState<TeamMembership[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
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
      const [memRes, invRes] = await Promise.all([
        api.teams.members.list(selectedTeamId),
        api.teams.invitations.list(selectedTeamId).catch(() => ({ invitations: [] })),
      ]);
      setMembers(memRes.members);
      setInvitations(invRes.invitations);
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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <Link href="/proposals" className="text-gray-400 hover:text-gray-700 text-sm">← 목록</Link>
          <h1 className="text-base font-semibold text-gray-900">팀 관리</h1>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{error}</div>
        )}
        {successMsg && (
          <div className="mb-4 bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700">{successMsg}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 팀 목록 사이드바 */}
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">내 팀</h2>
              {loading ? (
                <p className="text-sm text-gray-400">불러오는 중...</p>
              ) : memberships.length === 0 ? (
                <p className="text-sm text-gray-400">팀이 없습니다.</p>
              ) : (
                <ul className="space-y-1">
                  {memberships.map((m) => (
                    <li key={m.team_id}>
                      <button
                        onClick={() => setSelectedTeamId(m.team_id)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                          selectedTeamId === m.team_id
                            ? "bg-blue-50 text-blue-700 font-medium"
                            : "text-gray-700 hover:bg-gray-50"
                        }`}
                      >
                        {m.teams.name}
                        <span className="ml-2 text-xs text-gray-400">{m.role}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* 팀 생성 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">새 팀 만들기</h2>
              <form onSubmit={handleCreateTeam} className="space-y-2">
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  placeholder="팀 이름"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={!newTeamName.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg py-2 transition-colors"
                >
                  생성
                </button>
              </form>
            </div>
          </div>

          {/* 팀 상세 */}
          <div className="md:col-span-2 space-y-4">
            {!selectedTeamId ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-10 text-center text-gray-400 text-sm">
                팀을 선택하세요.
              </div>
            ) : (
              <>
                {/* 팀원 목록 */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h2 className="font-semibold text-gray-900 mb-4">팀원</h2>
                  <ul className="divide-y divide-gray-100">
                    {members.map((m) => (
                      <li key={m.id} className="flex items-center py-3 gap-3">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500 shrink-0">
                          {m.user_id.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="flex-1 text-sm text-gray-700 truncate">{m.user_id}</span>
                        {isAdmin && m.user_id !== currentUserId ? (
                          <div className="flex items-center gap-2">
                            <select
                              value={m.role}
                              onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                              className="border border-gray-300 rounded text-xs px-2 py-1"
                            >
                              <option value="admin">admin</option>
                              <option value="member">member</option>
                            </select>
                            <button
                              onClick={() => handleRemoveMember(m.user_id)}
                              className="text-xs text-red-500 hover:text-red-700"
                            >
                              제거
                            </button>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">{m.role}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 초대 */}
                {isAdmin && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h2 className="font-semibold text-gray-900 mb-4">팀원 초대</h2>
                    <form onSubmit={handleInvite} className="flex gap-2 mb-4">
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="이메일 주소"
                        className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        <option value="member">member</option>
                        <option value="admin">admin</option>
                      </select>
                      <button
                        type="submit"
                        disabled={!inviteEmail.trim()}
                        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                      >
                        초대
                      </button>
                    </form>

                    {invitations.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">초대 목록</h3>
                        <ul className="divide-y divide-gray-100">
                          {invitations.map((inv) => (
                            <li key={inv.id} className="flex items-center py-2.5 gap-3 text-sm">
                              <span className="flex-1 text-gray-700 truncate">{inv.email}</span>
                              <span className="text-xs text-gray-400">{inv.role}</span>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                inv.status === "accepted" ? "bg-green-100 text-green-700" :
                                inv.status === "expired" ? "bg-gray-100 text-gray-500" :
                                "bg-yellow-100 text-yellow-700"
                              }`}>
                                {STATUS_LABELS[inv.status] ?? inv.status}
                              </span>
                              {inv.status === "pending" && (
                                <button
                                  onClick={() => handleCancelInvite(inv.id)}
                                  className="text-xs text-red-400 hover:text-red-600"
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
      </main>
    </div>
  );
}
