"use client";

/**
 * 권고 #7: 관리자 조직도 시각화 + 역할 매트릭스
 *
 * 기존 트리 테이블 외에 시각적 조직도 뷰와 역할별 권한 매트릭스를 제공한다.
 */

import { useState } from "react";

// ── 타입 ──

interface TreeDivision {
  id: string;
  name: string;
  head?: TreeMember;
  teams: TreeTeam[];
}
interface TreeTeam {
  id: string;
  name: string;
  specialty?: string;
  members: TreeMember[];
}
interface TreeMember {
  id?: string;
  email: string;
  name: string;
  title?: string;
  role: string;
  status?: string;
}

interface Props {
  tree: TreeDivision[];
  execs: TreeMember[];
}

// ── 역할 권한 매트릭스 정의 ──

const PERMISSIONS = [
  { key: "create_proposal", label: "제안서 생성" },
  { key: "view_team_proposals", label: "팀 제안서 조회" },
  { key: "approve_go_nogo", label: "Go/No-Go 승인" },
  { key: "edit_proposal", label: "제안서 편집" },
  { key: "view_analytics", label: "분석 대시보드" },
  { key: "manage_kb", label: "KB 관리" },
  { key: "manage_users", label: "사용자 관리" },
  { key: "manage_org", label: "조직 관리" },
  { key: "view_all_division", label: "본부 전체 조회" },
  { key: "view_all_company", label: "전사 조회" },
];

const ROLE_PERMISSIONS: Record<string, Set<string>> = {
  member: new Set([
    "create_proposal",
    "edit_proposal",
    "view_team_proposals",
    "view_analytics",
  ]),
  lead: new Set([
    "create_proposal",
    "view_team_proposals",
    "approve_go_nogo",
    "edit_proposal",
    "view_analytics",
    "manage_kb",
  ]),
  director: new Set([
    "create_proposal",
    "view_team_proposals",
    "approve_go_nogo",
    "edit_proposal",
    "view_analytics",
    "manage_kb",
    "view_all_division",
    "view_all_company",
  ]),
  executive: new Set(PERMISSIONS.map((p) => p.key)),
  admin: new Set(PERMISSIONS.map((p) => p.key)),
};

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  member: { label: "멤버", color: "text-[#8c8c8c]" },
  lead: { label: "팀장", color: "text-[#3ecf8e]" },
  director: { label: "본부장", color: "text-blue-400" },
  executive: { label: "임원", color: "text-purple-400" },
  admin: { label: "관리자", color: "text-amber-400" },
};

// ── 탭 전환 ──

type ViewMode = "orgchart" | "matrix";

export default function AdminOrgChart({ tree, execs }: Props) {
  const [mode, setMode] = useState<ViewMode>("orgchart");

  return (
    <div className="space-y-4">
      {/* 탭 */}
      <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626] w-fit">
        <button
          onClick={() => setMode("orgchart")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            mode === "orgchart"
              ? "bg-[#3ecf8e] text-[#0f0f0f]"
              : "text-[#8c8c8c] hover:text-[#ededed]"
          }`}
        >
          조직도
        </button>
        <button
          onClick={() => setMode("matrix")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            mode === "matrix"
              ? "bg-[#3ecf8e] text-[#0f0f0f]"
              : "text-[#8c8c8c] hover:text-[#ededed]"
          }`}
        >
          역할 매트릭스
        </button>
      </div>

      {mode === "orgchart" ? (
        <OrgChartView tree={tree} execs={execs} />
      ) : (
        <RoleMatrixView />
      )}
    </div>
  );
}

// ── 조직도 시각화 ──

function OrgChartView({
  tree,
  execs,
}: {
  tree: TreeDivision[];
  execs: TreeMember[];
}) {
  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-6 overflow-x-auto">
      <div className="flex flex-col items-center min-w-[600px]">
        {/* 경영진 */}
        {execs.length > 0 && (
          <>
            <div className="flex gap-3 mb-2">
              {execs.map((e, i) => (
                <PersonCard
                  key={i}
                  name={e.name}
                  role={e.role}
                  title={e.title}
                  highlight
                />
              ))}
            </div>
            {/* 연결선 */}
            <div className="w-px h-6 bg-[#363636]" />
            <div className="flex items-center">
              <div
                className="h-px bg-[#363636]"
                style={{ width: `${Math.max(1, tree.length - 1) * 200}px` }}
              />
            </div>
          </>
        )}

        {/* 본부 */}
        <div className="flex gap-6 mt-2">
          {tree.map((div) => (
            <div key={div.id} className="flex flex-col items-center">
              {/* 본부 카드 */}
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-2.5 text-center mb-1">
                <p className="text-xs font-semibold text-blue-400">
                  {div.name}
                </p>
                {div.head && (
                  <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                    {div.head.name}
                  </p>
                )}
              </div>

              {/* 본부→팀 연결선 */}
              {div.teams.length > 0 && (
                <>
                  <div className="w-px h-4 bg-[#363636]" />
                  {div.teams.length > 1 && (
                    <div
                      className="h-px bg-[#363636]"
                      style={{ width: `${(div.teams.length - 1) * 120}px` }}
                    />
                  )}
                </>
              )}

              {/* 팀 */}
              <div className="flex gap-3 mt-1">
                {div.teams.map((team) => (
                  <div key={team.id} className="flex flex-col items-center">
                    <div className="w-px h-3 bg-[#363636]" />
                    <div className="bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 rounded-lg px-3 py-2 text-center min-w-[100px]">
                      <p className="text-[10px] font-medium text-[#3ecf8e]">
                        {team.name}
                      </p>
                      <p className="text-[9px] text-[#8c8c8c] mt-0.5">
                        {team.members.length}명
                      </p>
                    </div>

                    {/* 팀원 전체 목록 (세로 나열) */}
                    {team.members.length > 0 && (
                      <div className="mt-1 flex flex-col items-center">
                        <div className="w-px h-2 bg-[#262626]" />
                        <div className="flex flex-col gap-0.5 items-center">
                          {team.members.map((m, i) => (
                            <div
                              key={i}
                              className="flex items-center gap-1 px-2 py-0.5 rounded border border-[#262626] bg-[#111111]"
                              title={`${m.name} (${ROLE_LABELS[m.role]?.label ?? m.role})`}
                            >
                              <span
                                className={`text-[8px] ${ROLE_LABELS[m.role]?.color ?? "text-[#8c8c8c]"}`}
                              >
                                {ROLE_LABELS[m.role]?.label.slice(0, 1) ?? "●"}
                              </span>
                              <span className="text-[9px] text-[#ededed]">
                                {m.name}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PersonCard({
  name,
  role,
  title,
  highlight,
}: {
  name: string;
  role: string;
  title?: string;
  highlight?: boolean;
}) {
  const roleInfo = ROLE_LABELS[role] ?? ROLE_LABELS.member;
  return (
    <div
      className={`rounded-lg px-3 py-2 text-center border ${
        highlight
          ? "bg-purple-500/10 border-purple-500/30"
          : "bg-[#111111] border-[#262626]"
      }`}
    >
      <p className="text-xs font-medium text-[#ededed]">{name}</p>
      {title && <p className="text-[9px] text-[#8c8c8c] mt-0.5">{title}</p>}
      <p className={`text-[9px] mt-0.5 ${roleInfo.color}`}>{roleInfo.label}</p>
    </div>
  );
}

// ── 역할 매트릭스 ──

function RoleMatrixView() {
  const roles = ["member", "lead", "director", "executive", "admin"];

  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[#333]">
            <th className="px-4 py-3 text-left text-[#8c8c8c] font-medium w-48">
              권한
            </th>
            {roles.map((role) => {
              const info = ROLE_LABELS[role];
              return (
                <th
                  key={role}
                  className={`px-3 py-3 text-center font-medium ${info.color}`}
                >
                  {info.label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {PERMISSIONS.map((perm) => (
            <tr
              key={perm.key}
              className="border-b border-[#1e1e1e] hover:bg-[#262626]/30"
            >
              <td className="px-4 py-2.5 text-[#ededed]">{perm.label}</td>
              {roles.map((role) => {
                const has = ROLE_PERMISSIONS[role]?.has(perm.key);
                return (
                  <td key={role} className="px-3 py-2.5 text-center">
                    {has ? (
                      <span className="text-[#3ecf8e]">●</span>
                    ) : (
                      <span className="text-[#363636]">-</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
