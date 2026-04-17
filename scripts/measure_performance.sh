#!/bin/bash

# Phase 1 성능 기준선 측정 스크립트
# 용도: 핵심 API 10개의 응답시간 측정 (P95)
# 실행: bash scripts/measure_performance.sh

set -e

BASE_URL="${1:-http://localhost:8000}"
ITERATIONS=100
OUTPUT_FILE="performance_baseline_$(date +%Y%m%d_%H%M%S).txt"

echo "========================================" | tee "$OUTPUT_FILE"
echo "Phase 1 성능 기준선 측정 시작"
echo "기준시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$OUTPUT_FILE"
echo "반복 횟수: $ITERATIONS" | tee -a "$OUTPUT_FILE"
echo "========================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# 헬퍼 함수: API 응답시간 측정
measure_api() {
    local endpoint=$1
    local description=$2
    local times=()
    
    echo "[측정 중] $description ($endpoint)" | tee -a "$OUTPUT_FILE"
    
    for i in $(seq 1 $ITERATIONS); do
        response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BASE_URL$endpoint")
        times+=("$response_time")
        
        # 진행도 표시
        if [ $((i % 20)) -eq 0 ]; then
            echo "  $i/$ITERATIONS 완료"
        fi
    done
    
    # 통계 계산
    local sorted_times=$(printf '%s\n' "${times[@]}" | sort -n)
    local min=$(echo "$sorted_times" | head -1)
    local max=$(echo "$sorted_times" | tail -1)
    local avg=$(echo "${times[@]}" | awk '{sum+=$1} END {print sum/NR}')
    local p95=$(echo "$sorted_times" | awk '{sum+=$0; arr[NR]=$0} END {idx=int(NR*0.95); print arr[idx]}')
    
    # 결과 출력
    echo "  ✅ 완료" | tee -a "$OUTPUT_FILE"
    echo "    Min:  ${min}s" | tee -a "$OUTPUT_FILE"
    echo "    Max:  ${max}s" | tee -a "$OUTPUT_FILE"
    echo "    Avg:  ${avg}s" | tee -a "$OUTPUT_FILE"
    echo "    P95:  ${p95}s (목표: <3s)" | tee -a "$OUTPUT_FILE"
    echo "" | tee -a "$OUTPUT_FILE"
}

# ========================================
# 핵심 API 측정 (Hot Paths)
# ========================================

echo "1. 제안서 관련 API" | tee -a "$OUTPUT_FILE"
echo "─────────────────────────────────────" | tee -a "$OUTPUT_FILE"
measure_api "/api/proposals?skip=0&limit=10" "제안 목록 조회"
measure_api "/api/proposals/count" "제안 개수"

echo "2. 워크플로우 API" | tee -a "$OUTPUT_FILE"
echo "─────────────────────────────────────" | tee -a "$OUTPUT_FILE"
measure_api "/api/workflow/proposals?skip=0&limit=5" "워크플로우 목록"

echo "3. 검색 API" | tee -a "$OUTPUT_FILE"
echo "─────────────────────────────────────" | tee -a "$OUTPUT_FILE"
measure_api "/api/vault/search?q=test" "Vault 검색 (기본)"
measure_api "/api/kb/search?q=IoT" "KB 검색"

echo "4. 분석 API" | tee -a "$OUTPUT_FILE"
echo "─────────────────────────────────────" | tee -a "$OUTPUT_FILE"
measure_api "/api/analytics?team_id=sample" "분석 데이터"
measure_api "/api/performance/trends" "성능 추이"

echo "5. 사용자 관련 API" | tee -a "$OUTPUT_FILE"
echo "─────────────────────────────────────" | tee -a "$OUTPUT_FILE"
measure_api "/api/users/me" "현재 사용자 정보"
measure_api "/api/teams" "팀 목록"

echo "" | tee -a "$OUTPUT_FILE"
echo "========================================" | tee -a "$OUTPUT_FILE"
echo "✅ 성능 기준선 측정 완료" | tee -a "$OUTPUT_FILE"
echo "결과 파일: $OUTPUT_FILE" | tee -a "$OUTPUT_FILE"
echo "========================================" | tee -a "$OUTPUT_FILE"
