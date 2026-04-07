#!/bin/bash
# 프로덕션 스모크 테스트 스크립트
# 사용법: ./production_smoke_test.sh <PRODUCTION_URL> <AUTH_TOKEN>

set -e

# 설정
PROD_URL="${1:-https://api.production.com}"
AUTH_TOKEN="${2:-YOUR_PROD_TOKEN}"
RESULTS_FILE="smoke_test_results_$(date +%Y%m%d_%H%M%S).json"

echo "=================================================="
echo "프로덕션 스모크 테스트 시작"
echo "=================================================="
echo "URL: $PROD_URL"
echo "결과 파일: $RESULTS_FILE"
echo ""

# 결과 초기화
declare -A results
total=0
passed=0

# 테스트 함수
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5

    echo -n "테스트: $name ... "
    total=$((total + 1))

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            "$PROD_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$PROD_URL$endpoint")
    fi

    status=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)

    if [ "$status" = "$expected_status" ]; then
        echo "✅ PASS (HTTP $status)"
        results[$name]="PASS"
        passed=$((passed + 1))
    else
        echo "❌ FAIL (HTTP $status, expected $expected_status)"
        results[$name]="FAIL"
        echo "응답: $body"
    fi
}

# 1. 헬스 체크
echo ""
echo "1️⃣  헬스 체크"
echo "---"
test_endpoint "health" "GET" "/health" "" "200"

# 2. 문서 업로드 (PDF 파일 생성 후 업로드)
echo ""
echo "2️⃣  문서 업로드 테스트"
echo "---"

# 간단한 PDF 생성
cat > /tmp/test.pdf << 'EOF'
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< >>
stream
BT
/F1 12 Tf
100 700 Td
(This is a test document for E2E testing. This is a test document for E2E testing.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
312
%%EOF
EOF

echo -n "테스트: 문서 업로드 (PDF) ... "
total=$((total + 1))

upload_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -F "file=@/tmp/test.pdf" \
    -F "doc_type=보고서" \
    "$PROD_URL/api/documents/upload")

upload_status=$(echo "$upload_response" | tail -1)
upload_body=$(echo "$upload_response" | head -n -1)

if [ "$upload_status" = "201" ]; then
    echo "✅ PASS (HTTP 201)"
    results["upload_pdf"]="PASS"
    passed=$((passed + 1))

    # 문서 ID 추출
    DOC_ID=$(echo "$upload_body" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "   문서 ID: $DOC_ID"
else
    echo "❌ FAIL (HTTP $upload_status, expected 201)"
    results["upload_pdf"]="FAIL"
    echo "   응답: $upload_body"
    DOC_ID=""
fi

# 3. 문서 목록 조회
echo ""
echo "3️⃣  문서 목록 조회 테스트"
echo "---"
test_endpoint "list_documents" "GET" "/api/documents?limit=10&offset=0" "" "200"

# 4. 문서 상세 조회
echo ""
echo "4️⃣  문서 상세 조회 테스트"
echo "---"
if [ -n "$DOC_ID" ]; then
    test_endpoint "get_document_detail" "GET" "/api/documents/$DOC_ID" "" "200"
else
    echo "스킵: 업로드 실패로 인해 문서 ID가 없음"
fi

# 5. 비동기 처리 대기 (5초)
echo ""
echo "5️⃣  비동기 처리 대기 (5초)"
echo "---"
if [ -n "$DOC_ID" ]; then
    echo "5초 대기 중..."
    sleep 5

    # 처리 상태 확인
    echo -n "처리 상태 확인 ... "
    status_response=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
        "$PROD_URL/api/documents/$DOC_ID")

    processing_status=$(echo "$status_response" | grep -o '"processing_status":"[^"]*' | cut -d'"' -f4)
    echo "상태: $processing_status"
fi

# 6. 청크 조회
echo ""
echo "6️⃣  청크 조회 테스트"
echo "---"
if [ -n "$DOC_ID" ]; then
    test_endpoint "get_chunks" "GET" "/api/documents/$DOC_ID/chunks" "" "200"
else
    echo "스킵: 업로드 실패로 인해 문서 ID가 없음"
fi

# 7. 문서 삭제
echo ""
echo "7️⃣  문서 삭제 테스트"
echo "---"
if [ -n "$DOC_ID" ]; then
    test_endpoint "delete_document" "DELETE" "/api/documents/$DOC_ID" "" "204"
else
    echo "스킵: 업로드 실패로 인해 문서 ID가 없음"
fi

# 8. 성능 측정
echo ""
echo "8️⃣  성능 측정"
echo "---"

echo -n "목록 조회 응답 시간 (3회 평균) ... "
times=()
for i in {1..3}; do
    start=$(date +%s%N)
    curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
        "$PROD_URL/api/documents?limit=10&offset=0" > /dev/null
    end=$(date +%s%N)
    elapsed=$(( (end - start) / 1000000 ))  # 나노초 -> 밀리초
    times+=($elapsed)
done

avg=$(( (${times[0]} + ${times[1]} + ${times[2]}) / 3 ))
echo "${times[0]}ms, ${times[1]}ms, ${times[2]}ms → 평균: ${avg}ms"

if [ $avg -lt 100 ]; then
    echo "✅ 목표 달성 (<100ms)"
elif [ $avg -lt 200 ]; then
    echo "🟡 경고 (100-200ms)"
else
    echo "❌ 느림 (>200ms)"
fi

# 결과 요약
echo ""
echo "=================================================="
echo "테스트 결과 요약"
echo "=================================================="
echo "총 테스트: $total개"
echo "통과: $passed개 ($(( passed * 100 / total ))%)"
echo "실패: $(( total - passed ))개"
echo ""

if [ $passed -eq $total ]; then
    echo "✅ 모든 테스트 통과!"
else
    echo "❌ 일부 테스트 실패"
fi

echo ""
echo "자세한 결과:"
for test_name in "${!results[@]}"; do
    echo "  $test_name: ${results[$test_name]}"
done

# 결과 파일 저장
cat > "$RESULTS_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "production_url": "$PROD_URL",
  "total_tests": $total,
  "passed": $passed,
  "failed": $(( total - passed )),
  "pass_rate": $(( passed * 100 / total ))%,
  "results": {
EOF

first=true
for test_name in "${!results[@]}"; do
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$RESULTS_FILE"
    fi
    echo "    \"$test_name\": \"${results[$test_name]}\"" >> "$RESULTS_FILE"
done

cat >> "$RESULTS_FILE" << EOF
  }
}
EOF

echo ""
echo "결과 파일 저장: $RESULTS_FILE"
echo ""
echo "=================================================="
echo "프로덕션 스모크 테스트 완료"
echo "=================================================="

# 정리
rm -f /tmp/test.pdf

# 실패 시 종료 코드 1
if [ $passed -ne $total ]; then
    exit 1
fi

exit 0
