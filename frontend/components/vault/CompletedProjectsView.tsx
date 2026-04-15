/**
 * Completed Projects Section View
 * Displays completed projects retrieved from Vault
 */

import { AlertCircle } from "lucide-react";

interface Project {
  id: string;
  name: string;
  client: string;
  budget: number;
  duration: string;
  outcome?: string;
  lessons?: string;
}

interface CompletedProjectsViewProps {
  projects: Project[];
  isLoading: boolean;
  error?: string;
}

export default function CompletedProjectsView({
  projects,
  isLoading,
  error,
}: CompletedProjectsViewProps) {
  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-medium text-red-400">오류 발생</div>
          <div className="text-sm text-red-300">{error}</div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-4 text-center text-[#b4b4b4]">
        <div className="text-sm">로드 중...</div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="p-4 text-center text-[#b4b4b4]">
        <div className="text-sm">완료된 프로젝트가 없습니다</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {projects.map((project) => (
        <div
          key={project.id}
          className="p-3 bg-[#2d2d2d] border border-[#404040] rounded-lg hover:border-[#10a37f] transition-colors"
        >
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <h4 className="font-medium text-white">{project.name}</h4>
              <p className="text-sm text-[#b4b4b4]">{project.client}</p>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-[#10a37f]">
                ${project.budget.toLocaleString()}
              </div>
              <div className="text-xs text-[#888888]">{project.duration}</div>
            </div>
          </div>

          {project.outcome && (
            <div className="mb-2 text-sm text-[#e5e5e5]">
              <span className="text-[#888888]">결과: </span>
              {project.outcome}
            </div>
          )}

          {project.lessons && (
            <div className="text-sm text-[#e5e5e5] border-t border-[#404040] pt-2 mt-2">
              <span className="text-[#888888]">교훈: </span>
              {project.lessons}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
