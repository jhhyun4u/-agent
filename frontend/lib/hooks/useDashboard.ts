/**
 * Dashboard KPI — useQuery 훅 (Day 3 frontend)
 *
 * - API 호출 with TanStack Query
 * - 캐싱 (5분 TTL)
 * - 에러 처리
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  DashboardType,
  DashboardFilters,
  DashboardMetricsResponse,
  IndividualMetrics,
  TeamMetrics,
  DepartmentMetrics,
  ExecutiveMetrics,
} from "@/lib/utils/dashboardTypes";

// ── Query 키 팩토리 ──

const dashboardQueryKeys = {
  all: ["dashboard"] as const,
  metrics: (dashboardType: DashboardType) =>
    [...dashboardQueryKeys.all, "metrics", dashboardType] as const,
  withFilters: (dashboardType: DashboardType, filters: DashboardFilters) =>
    [
      ...dashboardQueryKeys.metrics(dashboardType),
      "filters",
      JSON.stringify(filters),
    ] as const,
};

// ── Hook: useDashboardMetrics ──

interface UseDashboardMetricsProps {
  dashboardType: DashboardType;
  filters?: DashboardFilters;
  enabled?: boolean;
}

export function useDashboardMetrics({
  dashboardType,
  filters = { period: "ytd" },
  enabled = true,
}: UseDashboardMetricsProps) {
  return useQuery({
    queryKey: dashboardQueryKeys.withFilters(dashboardType, filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append("period", filters.period);

      if (filters.period === "custom") {
        if (filters.custom_start_date) {
          params.append("custom_start_date", filters.custom_start_date);
        }
        if (filters.custom_end_date) {
          params.append("custom_end_date", filters.custom_end_date);
        }
      }

      if (filters.team_id) {
        params.append("team_id", filters.team_id);
      }

      if (filters.metric) {
        params.append("metric", filters.metric);
      }

      const response = await fetch(
        `/api/dashboard/metrics/${dashboardType}?${params.toString()}`,
        {
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        },
      );

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("접근 권한이 없습니다.");
        }
        if (response.status === 401) {
          throw new Error("인증이 필요합니다.");
        }
        throw new Error("데이터 조회에 실패했습니다.");
      }

      return response.json() as Promise<DashboardMetricsResponse>;
    },
    staleTime: 60000, // 1분 후 stale 마크
    gcTime: 300000, // 5분 후 캐시 제거
    enabled,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
  });
}

// ── Hook: useIndividualDashboard ──

export function useIndividualDashboard(
  filters?: DashboardFilters,
  enabled?: boolean,
) {
  const query = useDashboardMetrics({
    dashboardType: "individual",
    filters,
    enabled,
  });

  return {
    ...query,
    metrics: query.data?.data?.metrics as IndividualMetrics | undefined,
    cacheHit: query.data?.data?.cache_hit ?? false,
    cacheTtl: query.data?.data?.cache_ttl_seconds ?? 0,
  };
}

// ── Hook: useTeamDashboard ──

export function useTeamDashboard(
  filters?: DashboardFilters,
  enabled?: boolean,
) {
  const query = useDashboardMetrics({
    dashboardType: "team",
    filters,
    enabled,
  });

  return {
    ...query,
    metrics: query.data?.data?.metrics as TeamMetrics | undefined,
    cacheHit: query.data?.data?.cache_hit ?? false,
    cacheTtl: query.data?.data?.cache_ttl_seconds ?? 0,
  };
}

// ── Hook: useDepartmentDashboard ──

export function useDepartmentDashboard(
  filters?: DashboardFilters,
  enabled?: boolean,
) {
  const query = useDashboardMetrics({
    dashboardType: "department",
    filters,
    enabled,
  });

  return {
    ...query,
    metrics: query.data?.data?.metrics as DepartmentMetrics | undefined,
    cacheHit: query.data?.data?.cache_hit ?? false,
    cacheTtl: query.data?.data?.cache_ttl_seconds ?? 0,
  };
}

// ── Hook: useExecutiveDashboard ──

export function useExecutiveDashboard(
  filters?: DashboardFilters,
  enabled?: boolean,
) {
  const query = useDashboardMetrics({
    dashboardType: "executive",
    filters,
    enabled,
  });

  return {
    ...query,
    metrics: query.data?.data?.metrics as ExecutiveMetrics | undefined,
    cacheHit: query.data?.data?.cache_hit ?? false,
    cacheTtl: query.data?.data?.cache_ttl_seconds ?? 0,
  };
}

// ── Hook: refetchAllDashboards ──

export function useRefreshDashboards() {
  return () => {
    // 모든 대시보드 캐시 무효화
    // invalidateQueries 로직은 컴포넌트에서 useQueryClient 사용
  };
}
