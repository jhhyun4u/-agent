"use client";

/**
 * Admin 페이지 — TENOPA 조직도 트리 테이블
 *
 * 상단 툴바: 편집/저장, 추가, 일괄등록, 펼침/접기
 * 본문: 본부 → 팀 → 인력 트리 (API 데이터 or 초기 시드)
 */

import { useCallback, useEffect, useState } from "react";
import AppSidebar from "@/components/AppSidebar";
import { api } from "@/lib/api";
import { SEED_ORG, SEED_EXECUTIVES, type SeedDivision } from "@/lib/org-seed-data";

// ── 타입 ──
interface Division { id: string; org_id: string; name: string }
interface AdminTeam { id: string; division_id: string; name: string; teams_webhook_url?: string }
interface User {
  id: string; email: string; name: string; role: string;
  team_id: string | null; division_id: string | null; org_id: string;
  status: string; must_change_password: boolean;
}
// 트리 렌더용 통합 행
interface TreeDivision { id: string; name: string; head?: TreeMember; teams: TreeTeam[] }
interface TreeTeam { id: string; name: string; specialty?: string; members: TreeMember[] }
interface TreeMember { id?: string; email: string; name: string; title?: string; role: string; status?: string }

type Modal = "none" | "add-division" | "add-team" | "add-user" | "bulk" | "bulk-setup";
type Source = "api" | "seed";

const ROLES = [
  { value: "member", label: "멤버" }, { value: "lead", label: "팀장" },
  { value: "director", label: "본부장" }, { value: "executive", label: "임원" }, { value: "admin", label: "관리자" },
];

export default function AdminPage() {
  // ── 데이터 ──
  const [tree, setTree] = useState<TreeDivision[]>([]);
  const [execs, setExecs] = useState<TreeMember[]>([]);
  const [source, setSource] = useState<Source>("seed");
  const [orgId, setOrgId] = useState("");
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [teams, setTeams] = useState<AdminTeam[]>([]);
  const [loading, setLoading] = useState(true);

  // ── UI ──
  const [editing, setEditing] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [modal, setModal] = useState<Modal>("none");
  const [toast, setToast] = useState<{ type: "ok" | "err"; msg: string } | null>(null);

  // ── 인라인 편집 버퍼 ──
  const [teamEdits, setTeamEdits] = useState<Record<string, { name?: string }>>({});
  const [userEdits, setUserEdits] = useState<Record<string, Partial<User>>>({});

  // ── 모달 폼 ──
  const [divForm, setDivForm] = useState({ name: "" });
  const [teamForm, setTeamForm] = useState({ name: "", divisionId: "", webhook: "" });
  const [userForm, setUserForm] = useState({ email: "", name: "", role: "member", password: "", teamId: "", divisionId: "" });
  const [tempPassword, setTempPassword] = useState("");
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkResult, setBulkResult] = useState<{ total: number; success_count: number; failed_count: number; results: Array<Record<string, unknown>> } | null>(null);

  function flash(type: "ok" | "err", msg: string) {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  }

  // ── 시드 → 트리 변환 ──
  function loadSeed() {
    const t: TreeDivision[] = SEED_ORG.map(d => ({
      id: d.id, name: d.name,
      head: d.head ? { email: d.head.email, name: d.head.name, title: d.head.title, role: d.head.role, status: "active" } : undefined,
      teams: d.teams.map(tm => ({
        id: tm.id, name: tm.name, specialty: tm.specialty,
        members: tm.members.map(m => ({ email: m.email, name: m.name, title: m.title, role: m.role, status: "active" })),
      })),
    }));
    setTree(t);
    setExecs(SEED_EXECUTIVES.map(e => ({ email: e.email, name: e.name, title: e.title, role: e.role, status: "active" })));
    setSource("seed");
    // 전체 펼침
    const keys = new Set<string>();
    t.forEach(d => { keys.add(`div-${d.id}`); d.teams.forEach(tm => keys.add(`team-${tm.id}`)); });
    keys.add("execs");
    setExpanded(keys);
  }

  // ── API → 트리 변환 ──
  // teams.division_id가 없을 수 있으므로, users의 division_id로 팀→본부 관계 추론
  function buildTreeFromApi(divs: Division[], tms: AdminTeam[], users: User[]): TreeDivision[] {
    // 팀별 본부 추론: 해당 팀 소속 사용자 중 가장 많은 division_id
    const teamDivMap = new Map<string, string>(); // team_id → division_id
    for (const t of tms) {
      if (t.division_id) {
        teamDivMap.set(t.id, t.division_id);
      } else {
        const teamUsers = users.filter(u => u.team_id === t.id && u.division_id);
        if (teamUsers.length > 0) {
          // 다수결 division_id
          const counts = new Map<string, number>();
          teamUsers.forEach(u => counts.set(u.division_id!, (counts.get(u.division_id!) ?? 0) + 1));
          let maxDiv = ""; let maxCnt = 0;
          counts.forEach((cnt, div) => { if (cnt > maxCnt) { maxCnt = cnt; maxDiv = div; } });
          if (maxDiv) teamDivMap.set(t.id, maxDiv);
        }
      }
    }

    // 본부명과 같은 팀은 제외 (본부장이 팀 대신 본부에 직접 배정된 케이스)
    const divNames = new Set(divs.map(d => d.name));
    const realTeams = tms.filter(t => !divNames.has(t.name));

    // 본부명과 같은 팀에 속한 사용자 = 본부장급 (head 후보)
    const divNameTeamIds = new Map<string, string>(); // div_name → fake_team_id
    tms.forEach(t => { if (divNames.has(t.name)) divNameTeamIds.set(t.name, t.id); });

    return divs.map(d => {
      const dTeams = realTeams.filter(t => teamDivMap.get(t.id) === d.id);
      // 본부장: 본부명 팀에 속한 director/executive, 또는 division_id만 있고 팀이 없는 director
      const fakeTeamId = divNameTeamIds.get(d.name);
      const headCandidates = users.filter(u =>
        (fakeTeamId && u.team_id === fakeTeamId) ||
        (u.division_id === d.id && !u.team_id && ["director", "executive"].includes(u.role))
      );
      const head = headCandidates[0];
      return {
        id: d.id, name: d.name,
        head: head ? { id: head.id, email: head.email, name: head.name, role: head.role, status: head.status } : undefined,
        teams: dTeams.map(t => ({
          id: t.id, name: t.name,
          members: users.filter(u => u.team_id === t.id).map(u => ({
            id: u.id, email: u.email, name: u.name, role: u.role, status: u.status,
          })),
        })),
      };
    });
  }

  // ── 데이터 로드 ──
  const fetchAll = useCallback(async () => {
    try {
      const [d, t, u, p] = await Promise.all([
        api.admin.listDivisions(),
        api.admin.listTeams(),
        api.admin.listUsers({ page: 1, page_size: 500 }),
        api.auth.me(),
      ]);
      const divs = d as Division[];
      const tms = t as AdminTeam[];
      const usrs = (u.users ?? []) as unknown as User[];
      setDivisions(divs);
      setTeams(tms);
      setOrgId((p as Record<string, string>).org_id ?? "");

      if (divs.length > 0) {
        const apiTree = buildTreeFromApi(divs, tms, usrs);
        setTree(apiTree);
        // 트리에 포함된 사용자 ID 수집
        const assignedIds = new Set<string>();
        apiTree.forEach(d => d.teams.forEach(t => t.members.forEach(m => { if (m.id) assignedIds.add(m.id); })));
        // 미배정 (팀 없거나 본부명 팀에 속한 사용자)
        const unassigned = usrs.filter(usr => !assignedIds.has(usr.id));
        setExecs(unassigned.map(usr => ({ id: usr.id, email: usr.email, name: usr.name, role: usr.role, status: usr.status })));
        setSource("api");
        const keys = new Set<string>();
        apiTree.forEach(dd => { keys.add(`div-${dd.id}`); dd.teams.forEach(tm => keys.add(`team-${tm.id}`)); });
        if (unassigned.length) keys.add("execs");
        setExpanded(keys);
      } else {
        loadSeed();
      }
    } catch {
      loadSeed();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── 토글 ──
  function toggle(key: string) {
    setExpanded(prev => { const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n; });
  }
  function expandAll() {
    const keys = new Set<string>();
    tree.forEach(d => { keys.add(`div-${d.id}`); d.teams.forEach(t => keys.add(`team-${t.id}`)); });
    keys.add("execs");
    setExpanded(keys);
  }
  function collapseAll() { setExpanded(new Set()); }

  // ── 편집 모드 ──
  function enterEdit() {
    if (source === "seed") { flash("err", "DB 데이터가 없습니다. 먼저 '조직 일괄등록'으로 데이터를 등록하세요."); return; }
    setEditing(true); setTeamEdits({}); setUserEdits({});
  }
  function cancelEdit() { setEditing(false); setTeamEdits({}); setUserEdits({}); }

  async function saveAll() {
    try {
      for (const [id, patch] of Object.entries(teamEdits)) {
        if (patch.name) await api.admin.updateTeam(id, { name: patch.name });
      }
      for (const [id, patch] of Object.entries(userEdits)) {
        const data: Record<string, unknown> = {};
        if (patch.name) data.name = patch.name;
        if (patch.role) data.role = patch.role;
        if (patch.team_id !== undefined) data.team_id = patch.team_id || null;
        if (patch.division_id !== undefined) data.division_id = patch.division_id || null;
        if (Object.keys(data).length) await api.admin.updateUser(id, data);
      }
      flash("ok", "저장되었습니다.");
      cancelEdit();
      fetchAll();
    } catch (err: unknown) { flash("err", err instanceof Error ? err.message : "저장 실패"); }
  }

  // ── 사용자 액션 ──
  async function handleResetPw(userId: string) {
    try { const r = await api.admin.resetPassword(userId); flash("ok", `임시 비밀번호: ${r.temp_password}`); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }
  async function handleDeactivate(userId: string) {
    if (!confirm("비활성화하시겠습니까?")) return;
    try { await api.admin.deactivateUser(userId); flash("ok", "비활성화됨"); fetchAll(); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }

  // ── 추가 핸들러 ──
  async function handleAddDiv(e: React.FormEvent) {
    e.preventDefault();
    try { await api.admin.createDivision(divForm.name.trim(), orgId); setModal("none"); setDivForm({ name: "" }); flash("ok", "본부 추가됨"); fetchAll(); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }
  async function handleAddTeam(e: React.FormEvent) {
    e.preventDefault();
    try { await api.admin.createTeam(teamForm.name.trim(), teamForm.divisionId, teamForm.webhook || undefined); setModal("none"); setTeamForm({ name: "", divisionId: "", webhook: "" }); flash("ok", "팀 추가됨"); fetchAll(); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }
  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await api.admin.createUser({ email: userForm.email, name: userForm.name, role: userForm.role, org_id: orgId, team_id: userForm.teamId || undefined, division_id: userForm.divisionId || undefined, password: userForm.password || undefined });
      setTempPassword((r as Record<string, string>).temp_password ?? ""); flash("ok", "사용자 등록됨"); fetchAll();
    } catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }
  async function handleBulk(e: React.FormEvent) {
    e.preventDefault(); if (!bulkFile) return; setBulkResult(null);
    try { const r = await api.admin.bulkCreateUsers(bulkFile); setBulkResult(r); fetchAll(); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }
  async function handleBulkSetup(e: React.FormEvent) {
    e.preventDefault(); if (!bulkFile) return;
    try { await api.admin.bulkSetupOrg(bulkFile); setModal("none"); flash("ok", "조직 일괄등록 완료"); fetchAll(); }
    catch (e: unknown) { flash("err", e instanceof Error ? e.message : "실패"); }
  }

  const dirtyCount = Object.keys(teamEdits).length + Object.keys(userEdits).length;
  const totalMembers = tree.reduce((s, d) => s + d.teams.reduce((s2, t) => s2 + t.members.length, 0), 0) + execs.length;

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* ━━ 상단 ━━ */}
        <header className="border-b border-[#262626] bg-[#111111] shrink-0">
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex items-center gap-3">
              <h1 className="text-base font-semibold text-[#ededed]">Admin</h1>
              <span className="text-xs text-[#555]">TENOPA · {tree.length}본부 · {totalMembers}명</span>
              {source === "seed" && <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">초기 데이터</span>}
            </div>
            <div className="flex items-center gap-2">
              <button onClick={expandAll} className="text-xs text-[#555] hover:text-[#999]">펼침</button>
              <button onClick={collapseAll} className="text-xs text-[#555] hover:text-[#999]">접기</button>
              {editing ? (
                <>
                  {dirtyCount > 0 && <span className="text-xs text-amber-400">{dirtyCount}건 변경</span>}
                  <Btn onClick={cancelEdit} variant="ghost">취소</Btn>
                  <Btn onClick={saveAll} variant="primary">저장</Btn>
                </>
              ) : (
                <Btn onClick={enterEdit} variant="default">편집</Btn>
              )}
            </div>
          </div>
        </header>

        {/* ━━ 토스트 ━━ */}
        {toast && (
          <div className={`mx-6 mt-3 rounded-lg px-4 py-2.5 text-sm ${toast.type === "ok" ? "bg-[#3ecf8e]/10 text-[#3ecf8e] border border-[#3ecf8e]/20" : "bg-red-400/10 text-red-400 border border-red-400/20"}`}>
            {toast.msg}
          </div>
        )}

        {/* ━━ 트리 테이블 ━━ */}
        <main className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-6xl mx-auto">
            {loading ? (
              <div className="text-center py-16 text-[#555] text-sm">불러오는 중...</div>
            ) : (
              <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] overflow-hidden text-sm">
                {/* 헤더 */}
                <div className="grid grid-cols-[1.2fr_180px_90px_120px_100px] border-b border-[#333] text-[#666] text-xs font-medium select-none">
                  <div className="px-4 py-2.5">조직 / 이름</div>
                  <div className="px-3 py-2.5">이메일</div>
                  <div className="px-3 py-2.5">직급</div>
                  <div className="px-3 py-2.5">역할</div>
                  <div className="px-3 py-2.5 text-right">{source === "api" ? "액션" : ""}</div>
                </div>

                {/* 경영진 */}
                {execs.length > 0 && (
                  <>
                    <GroupRow label="경영진" badge={`${execs.length}명`} accent="purple"
                      open={expanded.has("execs")} onToggle={() => toggle("execs")} />
                    {expanded.has("execs") && execs.map((m, i) => (
                      <MemberRow key={`exec-${i}`} m={m} depth={1} source={source}
                        editing={editing} patch={userEdits[m.id ?? ""]}
                        onPatch={p => m.id && setUserEdits(prev => ({ ...prev, [m.id!]: { ...prev[m.id!], ...p } }))}
                        onResetPw={handleResetPw} onDeactivate={handleDeactivate}
                        divisions={divisions} teams={teams} />
                    ))}
                  </>
                )}

                {/* 본부 → 팀 → 인력 */}
                {tree.map(div => {
                  const memberCount = div.teams.reduce((s, t) => s + t.members.length, 0) + (div.head ? 1 : 0);
                  const divOpen = expanded.has(`div-${div.id}`);
                  return (
                    <div key={div.id}>
                      <GroupRow label={div.name} badge={`${div.teams.length}팀 · ${memberCount}명`} accent="blue"
                        open={divOpen} onToggle={() => toggle(`div-${div.id}`)}
                        actions={!editing && source === "api" && (
                          <button onClick={() => { setTeamForm({ name: "", divisionId: div.id, webhook: "" }); setModal("add-team"); }}
                            className="text-xs text-[#555] hover:text-[#aaa]">+ 팀</button>
                        )} />

                      {/* 본부장/소장 — 본부 바로 아래 */}
                      {divOpen && div.head && (
                        <div className="grid grid-cols-[1.2fr_180px_90px_120px_100px] border-b border-[#1e1e1e] bg-[#161630]/30">
                          <div className="px-4 py-1.5 flex items-center gap-2" style={{ paddingLeft: 40 }}>
                            <span className="text-[10px] text-amber-400/60">★</span>
                            <span className="text-[#ededed] font-medium">{div.head.name}</span>
                            <span className="text-[10px] text-amber-400/80">{div.head.role}</span>
                          </div>
                          <div className="px-3 py-1.5 text-[#666] truncate text-xs">{div.head.email}</div>
                          <div className="px-3 py-1.5 text-[#777] text-xs">{div.head.title}</div>
                          <div className="px-3 py-1.5"><span className="text-xs text-amber-400/80">{div.head.role}</span></div>
                          <div />
                        </div>
                      )}

                      {divOpen && div.teams.map(team => {
                        const teamOpen = expanded.has(`team-${team.id}`);
                        return (
                          <div key={team.id}>
                            <div className={`grid grid-cols-[1.2fr_180px_90px_120px_100px] border-b border-[#1e1e1e] ${teamOpen ? "bg-[#162216]/50" : "bg-[#162216]/30"} hover:bg-[#162216]/60 cursor-pointer select-none`}
                              onClick={() => toggle(`team-${team.id}`)}>
                              <div className="px-4 py-2 flex items-center gap-2" style={{ paddingLeft: 40 }}>
                                <span className="text-[10px] text-[#444] w-3">{teamOpen ? "▼" : "▶"}</span>
                                {editing && source === "api" ? (
                                  <InlineInput value={teamEdits[team.id]?.name ?? team.name}
                                    onChange={v => setTeamEdits(p => ({ ...p, [team.id]: { name: v } }))} />
                                ) : (
                                  <span className="font-medium text-[#3ecf8e]">{team.name}</span>
                                )}
                                <span className="text-[10px] text-[#555]">{team.members.length}명</span>
                                {team.specialty && <span className="text-[10px] text-[#444] truncate max-w-[300px]">{team.specialty}</span>}
                              </div>
                              <div /><div /><div />
                              <div className="px-3 py-2 text-right" onClick={e => e.stopPropagation()}>
                                {!editing && source === "api" && (
                                  <button onClick={() => { setUserForm({ email: "", name: "", role: "member", password: "", teamId: team.id, divisionId: div.id }); setTempPassword(""); setModal("add-user"); }}
                                    className="text-xs text-[#555] hover:text-[#aaa]">+ 인력</button>
                                )}
                              </div>
                            </div>

                            {teamOpen && team.members.map((m, i) => (
                              <MemberRow key={m.id ?? `${team.id}-${i}`} m={m} depth={2} source={source}
                                editing={editing} patch={userEdits[m.id ?? ""]}
                                onPatch={p => m.id && setUserEdits(prev => ({ ...prev, [m.id!]: { ...prev[m.id!], ...p } }))}
                                onResetPw={handleResetPw} onDeactivate={handleDeactivate}
                                divisions={divisions} teams={teams} />
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>

        {/* ━━ 모달 ━━ */}
        {modal === "add-division" && (
          <Overlay onClose={() => setModal("none")}>
            <h2 className="text-base font-semibold text-[#ededed] mb-4">본부 추가</h2>
            <form onSubmit={handleAddDiv} className="space-y-3">
              <Inp placeholder="본부명" value={divForm.name} onChange={v => setDivForm({ name: v })} autoFocus />
              <FormActions onCancel={() => setModal("none")} label="추가" />
            </form>
          </Overlay>
        )}
        {modal === "add-team" && (
          <Overlay onClose={() => setModal("none")}>
            <h2 className="text-base font-semibold text-[#ededed] mb-4">팀 추가</h2>
            <form onSubmit={handleAddTeam} className="space-y-3">
              <Inp placeholder="팀명" value={teamForm.name} onChange={v => setTeamForm(f => ({ ...f, name: v }))} autoFocus />
              <Sel value={teamForm.divisionId} onChange={v => setTeamForm(f => ({ ...f, divisionId: v }))}
                options={[{ value: "", label: "본부 선택" }, ...divisions.map(d => ({ value: d.id, label: d.name }))]} />
              <Inp placeholder="Teams Webhook URL (선택)" value={teamForm.webhook} onChange={v => setTeamForm(f => ({ ...f, webhook: v }))} />
              <FormActions onCancel={() => setModal("none")} label="추가" disabled={!teamForm.divisionId || !teamForm.name.trim()} />
            </form>
          </Overlay>
        )}
        {modal === "add-user" && (
          <Overlay onClose={() => setModal("none")}>
            <h2 className="text-base font-semibold text-[#ededed] mb-4">사용자 등록</h2>
            <form onSubmit={handleAddUser} className="space-y-3">
              <Inp type="email" placeholder="이메일" value={userForm.email} onChange={v => setUserForm(f => ({ ...f, email: v }))} required autoFocus />
              <Inp placeholder="이름" value={userForm.name} onChange={v => setUserForm(f => ({ ...f, name: v }))} required />
              <Sel value={userForm.role} onChange={v => setUserForm(f => ({ ...f, role: v }))} options={ROLES} />
              <Sel value={userForm.divisionId} onChange={v => setUserForm(f => ({ ...f, divisionId: v }))}
                options={[{ value: "", label: "본부 (선택)" }, ...divisions.map(d => ({ value: d.id, label: d.name }))]} />
              <Sel value={userForm.teamId} onChange={v => setUserForm(f => ({ ...f, teamId: v }))}
                options={[{ value: "", label: "팀 (선택)" }, ...(userForm.divisionId ? teams.filter(t => t.division_id === userForm.divisionId) : teams).map(t => ({ value: t.id, label: t.name }))]} />
              <Inp placeholder="비밀번호 (미입력 시 자동)" value={userForm.password} onChange={v => setUserForm(f => ({ ...f, password: v }))} />
              <FormActions onCancel={() => setModal("none")} label="등록" />
            </form>
            {tempPassword && (
              <div className="mt-4 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-3">
                <p className="text-xs text-amber-400 font-medium">임시 비밀번호</p>
                <p className="text-sm text-[#ededed] font-mono mt-1 select-all">{tempPassword}</p>
              </div>
            )}
          </Overlay>
        )}
        {modal === "bulk" && (
          <Overlay onClose={() => setModal("none")}>
            <h2 className="text-base font-semibold text-[#ededed] mb-2">사용자 일괄등록</h2>
            <p className="text-xs text-[#666] mb-4">CSV (email,name,role) 또는 XLSX</p>
            <form onSubmit={handleBulk} className="space-y-3">
              <FileInput onChange={f => setBulkFile(f)} />
              <FormActions onCancel={() => setModal("none")} label="업로드" disabled={!bulkFile} />
            </form>
            {bulkResult && <BulkResultView result={bulkResult} />}
          </Overlay>
        )}
        {modal === "bulk-setup" && (
          <Overlay onClose={() => setModal("none")}>
            <h2 className="text-base font-semibold text-[#ededed] mb-2">조직 일괄등록</h2>
            <p className="text-xs text-[#666] mb-4">XLSX 5시트 (조직/본부/팀/사용자/역량)</p>
            <form onSubmit={handleBulkSetup} className="space-y-3">
              <FileInput onChange={f => setBulkFile(f)} accept=".xlsx,.xls" />
              <FormActions onCancel={() => setModal("none")} label="업로드" disabled={!bulkFile} />
            </form>
          </Overlay>
        )}
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 그룹 행 (본부 / 경영진)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const accentColor: Record<string, string> = { blue: "text-blue-300", green: "text-[#3ecf8e]", purple: "text-purple-300", amber: "text-amber-400" };
const accentBg: Record<string, string> = { blue: "bg-[#161622]/60", green: "bg-[#162216]/40", purple: "bg-[#1c1628]/60", amber: "bg-[#221c16]/60" };

function GroupRow({ label, badge, accent = "blue", open, onToggle, actions }: {
  label: string; badge?: string; accent?: string; open: boolean; onToggle: () => void; actions?: React.ReactNode;
}) {
  return (
    <div className={`grid grid-cols-[1.2fr_180px_90px_120px_100px] border-b border-[#222] ${accentBg[accent] ?? ""} hover:brightness-110 cursor-pointer select-none`}
      onClick={onToggle}>
      <div className="px-4 py-2.5 flex items-center gap-2">
        <span className="text-[10px] text-[#444] w-3">{open ? "▼" : "▶"}</span>
        <span className={`font-semibold ${accentColor[accent] ?? "text-[#ededed]"}`}>{label}</span>
        {badge && <span className="text-[10px] text-[#555]">{badge}</span>}
      </div>
      <div /><div /><div />
      <div className="px-3 py-2.5 text-right" onClick={e => e.stopPropagation()}>{actions}</div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 인력 행
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function MemberRow({ m, depth, source, editing, patch, onPatch, onResetPw, onDeactivate, divisions, teams }: {
  m: TreeMember; depth: number; source: Source;
  editing: boolean; patch?: Partial<User>;
  onPatch: (p: Partial<User>) => void;
  onResetPw: (id: string) => void; onDeactivate: (id: string) => void;
  divisions: Division[]; teams: AdminTeam[];
}) {
  const pl = 16 + depth * 24;
  const name = patch?.name ?? m.name;
  const role = patch?.role ?? m.role;

  return (
    <div className="grid grid-cols-[1.2fr_180px_90px_120px_100px] border-b border-[#1a1a1a] hover:bg-[#222]/40">
      <div className="px-4 py-1.5" style={{ paddingLeft: pl }}>
        {editing && m.id ? (
          <InlineInput value={name} onChange={v => onPatch({ name: v })} />
        ) : (
          <span className="text-[#ddd]">{m.name}</span>
        )}
      </div>
      <div className="px-3 py-1.5 text-[#666] truncate text-xs">{m.email}</div>
      <div className="px-3 py-1.5 text-[#777] text-xs">{m.title ?? ""}</div>
      <div className="px-3 py-1.5">
        {editing && m.id ? (
          <select value={role} onChange={e => onPatch({ role: e.target.value })} className={inlineSel}>
            {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        ) : (
          <span className="text-xs text-[#888]">{m.role}</span>
        )}
      </div>
      <div className="px-3 py-1.5 text-right space-x-1">
        {!editing && source === "api" && m.id && (
          <>
            <button onClick={() => onResetPw(m.id!)} className="text-[10px] text-amber-400/60 hover:text-amber-400">PW</button>
            {m.status === "active" && (
              <button onClick={() => onDeactivate(m.id!)} className="text-[10px] text-red-400/50 hover:text-red-400">비활성</button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 공용 컴포넌트
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function InlineInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input value={value} onChange={e => onChange(e.target.value)}
    className="bg-transparent border-b border-[#333] text-sm text-[#ededed] px-0.5 py-0.5 focus:outline-none focus:border-[#3ecf8e] w-full min-w-0"
    onClick={e => e.stopPropagation()} />;
}

function Btn({ children, onClick, variant = "default" }: { children: React.ReactNode; onClick: () => void; variant?: "default" | "primary" | "ghost" }) {
  const cls = variant === "primary"
    ? "bg-[#3ecf8e] hover:bg-[#36b87e] text-black font-medium"
    : variant === "ghost"
    ? "text-[#888] hover:text-[#ededed] border border-[#333]"
    : "bg-[#1c1c1c] hover:bg-[#262626] text-[#aaa] border border-[#333]";
  return <button onClick={onClick} className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${cls}`}>{children}</button>;
}

function Sep() { return <div className="w-px h-5 bg-[#333] mx-1" />; }

function Overlay({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[#1c1c1c] rounded-xl border border-[#262626] p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>{children}</div>
    </div>
  );
}

function Inp({ placeholder, value, onChange, type = "text", required, autoFocus }: {
  placeholder: string; value: string; onChange: (v: string) => void; type?: string; required?: boolean; autoFocus?: boolean;
}) {
  return <input type={type} required={required} autoFocus={autoFocus} placeholder={placeholder} value={value}
    onChange={e => onChange(e.target.value)}
    className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#555] focus:outline-none focus:border-[#3ecf8e]" />;
}

function Sel({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return <select value={value} onChange={e => onChange(e.target.value)}
    className="w-full bg-[#0f0f0f] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed]">
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>;
}

function FileInput({ onChange, accept = ".csv,.xlsx,.xls" }: { onChange: (f: File | null) => void; accept?: string }) {
  return <input type="file" accept={accept} onChange={e => onChange(e.target.files?.[0] ?? null)}
    className="w-full text-sm text-[#ededed] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-[#262626] file:text-[#ededed] hover:file:bg-[#333]" />;
}

function FormActions({ onCancel, label, disabled }: { onCancel: () => void; label: string; disabled?: boolean }) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <button type="button" onClick={onCancel} className="text-sm text-[#888] hover:text-[#ededed] px-3 py-1.5">취소</button>
      <button type="submit" disabled={disabled} className="bg-[#3ecf8e] hover:bg-[#36b87e] disabled:opacity-50 text-black text-sm font-medium px-4 py-1.5 rounded-lg">{label}</button>
    </div>
  );
}

function BulkResultView({ result }: { result: { total: number; success_count: number; failed_count: number; results: Array<Record<string, unknown>> } }) {
  return (
    <div className="mt-4 space-y-2">
      <div className="flex gap-4 text-sm">
        <span className="text-[#888]">전체: {result.total}</span>
        <span className="text-[#3ecf8e]">성공: {result.success_count}</span>
        <span className="text-red-400">실패: {result.failed_count}</span>
      </div>
      <div className="max-h-48 overflow-y-auto bg-[#0f0f0f] rounded-lg border border-[#262626] p-3 text-xs space-y-1">
        {result.results.map((r, i) => (
          <div key={i} className={r.success ? "text-[#3ecf8e]" : "text-red-400"}>
            {r.email as string}: {r.success ? `PW: ${r.temp_password}` : r.error as string}
          </div>
        ))}
      </div>
    </div>
  );
}

const inlineSel = "bg-transparent border border-[#333] rounded text-xs text-[#ccc] px-1.5 py-0.5 focus:outline-none focus:border-[#3ecf8e]";
